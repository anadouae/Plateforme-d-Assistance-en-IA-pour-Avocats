import logging

from celery.exceptions import SoftTimeLimitExceeded

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.logging_config import set_correlation_id
from app.models import Document, DocumentStatus
from app.services.celery_app import celery_app
from app.services.document_pipeline import process_document_record
from app.services.object_storage import TransientStorageError, assert_plaintext_file, read_file

logger = logging.getLogger(__name__)

# Backoff : 5s, 20s, 60s
_RETRY_COUNTDOWNS = (5, 20, 60)


def _is_transient(exc: BaseException) -> bool:
    if isinstance(exc, (TransientStorageError, TimeoutError, ConnectionError, OSError)):
        return True
    name = type(exc).__name__.lower()
    msg = str(exc).lower()
    if "timeout" in name or "timeout" in msg:
        return True
    if "connection" in msg or "temporarily" in msg or "503" in msg or "502" in msg:
        return True
    return False


def _mark_failed(db, doc: Document | None, message: str) -> None:
    if not doc:
        return
    doc.status = DocumentStatus.FAILED
    doc.error_message = message[:2000]
    db.commit()


@celery_app.task(
    name="process_document",
    bind=True,
    max_retries=3,
    soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
    time_limit=settings.CELERY_TASK_TIME_LIMIT,
    acks_late=True,
)
def process_document(self, document_id: str):
    set_correlation_id(f"celery:doc:{document_id}")
    db = SessionLocal()
    doc = None
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.warning("Document not found for processing", extra={"document_id": document_id})
            return {"status": "not_found"}

        try:
            content = read_file(doc.storage_path)
            assert_plaintext_file(content, filename=doc.original_name or "")
        except FileNotFoundError as exc:
            _mark_failed(db, doc, "Fichier introuvable dans le stockage. Réimportez le document.")
            logger.error(
                "Document file missing: %s",
                exc,
                extra={"document_id": document_id, "cabinet_id": doc.cabinet_id},
            )
            return {"status": "failed", "reason": "file_missing"}

        result = process_document_record(doc, content, db)
        # Échec définitif (texte vide, Whisper off, etc.) — pas de retry
        if result.get("status") == "failed":
            return result
        return result

    except SoftTimeLimitExceeded:
        logger.error(
            "Celery soft time limit exceeded",
            extra={"document_id": document_id, "task": "process_document"},
        )
        _mark_failed(
            db,
            doc,
            "Traitement interrompu (délai dépassé). Réessayez ou contactez le support.",
        )
        return {"status": "failed", "reason": "time_limit"}

    except Exception as exc:
        retries = int(getattr(self.request, "retries", 0) or 0)
        max_retries = int(settings.CELERY_MAX_RETRIES or 3)
        if _is_transient(exc) and retries < max_retries:
            countdown = _RETRY_COUNTDOWNS[min(retries, len(_RETRY_COUNTDOWNS) - 1)]
            logger.warning(
                "Transient error on document %s (retry %s/%s in %ss): %s",
                document_id,
                retries + 1,
                max_retries,
                countdown,
                exc,
                extra={"document_id": document_id, "task": "process_document"},
            )
            raise self.retry(exc=exc, countdown=countdown)

        logger.exception(
            "Document processing failed permanently: %s",
            exc,
            extra={"document_id": document_id, "task": "process_document"},
        )
        _mark_failed(
            db,
            doc,
            f"Échec du traitement après retries : {type(exc).__name__}. "
            "Vérifiez le fichier ou réessayez plus tard.",
        )
        return {"status": "failed", "reason": "permanent_error"}
    finally:
        db.close()


@celery_app.task(
    name="index_document_vectors",
    bind=True,
    max_retries=2,
    soft_time_limit=300,
    time_limit=360,
    acks_late=True,
)
def index_document_vectors(self, document_id: str):
    """Indexation vectorielle en arrière-plan — ne bloque pas l'extraction OCR."""
    set_correlation_id(f"celery:index:{document_id}")
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc or not doc.extracted_text or len(doc.extracted_text.strip()) < 20:
            return {"status": "skipped"}

        from app.services.rag import index_document

        chunks = index_document(
            doc.cabinet_id,
            doc.case_id,
            doc.id,
            doc.original_name,
            doc.extracted_text,
        )
        logger.info(
            "Vector index complete",
            extra={"document_id": document_id, "chunks": chunks},
        )
        return {"status": "indexed", "chunks": chunks}
    except SoftTimeLimitExceeded:
        logger.error("Vector index timeout for doc %s", document_id)
        return {"status": "timeout"}
    except Exception as exc:
        retries = int(getattr(self.request, "retries", 0) or 0)
        if _is_transient(exc) and retries < 2:
            raise self.retry(exc=exc, countdown=10)
        logger.exception("Vector index failed for doc %s: %s", document_id, exc)
        return {"status": "failed", "reason": str(exc)[:200]}
    finally:
        db.close()


@celery_app.task(name="agenda_remind_48h")
def agenda_remind_48h():
    """Rappels agenda ~48 h avant l'événement (beat toutes les 15 min)."""
    set_correlation_id("celery:agenda_remind_48h")
    db = SessionLocal()
    try:
        from app.services.agenda_reminders import send_due_agenda_reminders

        result = send_due_agenda_reminders(db)
        if result.get("processed"):
            logger.info("Agenda 48h reminders: %s", result)
        return result
    except Exception as exc:
        logger.exception("agenda_remind_48h failed: %s", exc)
        return {"status": "failed", "reason": str(exc)[:200]}
    finally:
        db.close()


@celery_app.task(name="trial_lifecycle_hourly")
def trial_lifecycle_hourly():
    """Rappels fin d'essai (D-7 / D-3 / D-1) + e-mail fin d'essai → Découverte."""
    set_correlation_id("celery:trial_lifecycle")
    db = SessionLocal()
    try:
        from app.services.trial_lifecycle import process_trial_lifecycle

        result = process_trial_lifecycle(db)
        if result.get("reminders_sent") or result.get("trials_ended_emailed"):
            logger.info("Trial lifecycle: %s", result)
        return result
    except Exception as exc:
        logger.exception("trial_lifecycle_hourly failed: %s", exc)
        return {"status": "failed", "reason": str(exc)[:200]}
    finally:
        db.close()

@celery_app.task(name="retention_lifecycle_daily")
def retention_lifecycle_daily():
    """Renouvellement J-7/J-1, tips J+1/J+2, inactivité 14j, 2FA, changelog mensuel."""
    set_correlation_id("celery:retention_daily")
    db = SessionLocal()
    try:
        from app.services.retention_lifecycle import process_retention_daily

        result = process_retention_daily(db)
        logger.info("Retention daily: %s", result)
        return result
    except Exception as exc:
        logger.exception("retention_lifecycle_daily failed: %s", exc)
        return {"status": "failed", "reason": str(exc)[:200]}
    finally:
        db.close()


@celery_app.task(name="retention_weekly_digest")
def retention_weekly_digest():
    """Digest hebdomadaire activité cabinet (lundi)."""
    set_correlation_id("celery:retention_weekly")
    db = SessionLocal()
    try:
        from app.services.retention_lifecycle import process_weekly_digests

        result = process_weekly_digests(db)
        logger.info("Weekly digest: %s", result)
        return result
    except Exception as exc:
        logger.exception("retention_weekly_digest failed: %s", exc)
        return {"status": "failed", "reason": str(exc)[:200]}
    finally:
        db.close()

