import logging

from celery.exceptions import SoftTimeLimitExceeded

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.logging_config import set_correlation_id
from app.models import Document, DocumentStatus
from app.services.celery_app import celery_app
from app.services.document_pipeline import process_document_record
from app.services.object_storage import TransientStorageError, read_file

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
