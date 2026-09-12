import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging_config import get_correlation_id, set_correlation_id
from app.core.timeouts import OperationTimeout
from app.models import Document, DocumentStatus
from app.services.extraction import (
    arabic_char_ratio,
    extract_text,
    is_audio_document,
    is_native_office_document,
    is_scrambled_arabic,
    safe_repair_arabic_text,
)
from app.services.rag import index_document

logger = logging.getLogger(__name__)

_WHISPER_DISABLED_MSG = (
    "La transcription audio n’est pas activée sur le serveur. "
    "Contactez l’administrateur LexHub ou joignez un document texte."
)
_WHISPER_EMPTY_MSG = (
    "Aucune parole n’a pu être reconnue dans ce fichier audio. "
    "Vérifiez le volume / la clarté, ou réessayez avec un extrait plus court."
)
_WHISPER_TIMEOUT_MSG = (
    "La transcription a été interrompue (délai dépassé). "
    "Réessayez avec un extrait audio plus court."
)
_OCR_TIMEOUT_MSG = (
    "Lecture interrompue (délai dépassé). PDF scanné volumineux : réessayez avec moins de pages "
    "ou exportez en Word/PDF natif. / انقطع الاستخراج — جرّب ملفاً أصغر أو PDF نصي."
)


def process_document_record(doc: Document, content: bytes, db: Session) -> dict:
    """Extract text, index vectors, update document status."""
    if not get_correlation_id():
        set_correlation_id(f"doc:{doc.id}")

    doc.status = DocumentStatus.PROCESSING
    doc.error_message = None
    db.commit()

    is_audio = is_audio_document(doc.original_name, doc.mime_type)

    if is_audio and not settings.WHISPER_ENABLED:
        doc.extracted_text = None
        doc.ocr_score = None
        doc.error_message = _WHISPER_DISABLED_MSG
        doc.status = DocumentStatus.FAILED
        db.commit()
        logger.warning(
            "Audio doc failed: Whisper disabled",
            extra={"document_id": doc.id, "cabinet_id": doc.cabinet_id},
        )
        return {"status": "failed", "reason": "whisper_disabled", "ocr_score": None}

    try:
        text, ocr_score = extract_text(content, doc.original_name, doc.mime_type)
    except OperationTimeout as exc:
        doc.extracted_text = None
        doc.ocr_score = None
        doc.error_message = _WHISPER_TIMEOUT_MSG if is_audio else _OCR_TIMEOUT_MSG
        doc.status = DocumentStatus.FAILED
        db.commit()
        logger.error(
            "Document processing timeout: %s",
            exc,
            extra={"document_id": doc.id, "cabinet_id": doc.cabinet_id},
        )
        return {"status": "failed", "reason": "timeout", "ocr_score": None}

    # DOCX / audio : texte déjà ordonné — ne pas appliquer les réparations BIDI PDF
    is_docx = is_native_office_document(doc.original_name or "", doc.mime_type or "")
    if is_docx or is_audio:
        text = (text or "").strip()
    else:
        text = safe_repair_arabic_text(text or "")

    # Ne pas inventer un faux score « 55% » sur un long texte juridique déjà utilisable
    if (
        text
        and not is_audio
        and not is_docx
        and is_scrambled_arabic(text)
        and (ocr_score is None or ocr_score >= 90)
    ):
        if len(text) >= 12000 and arabic_char_ratio(text) >= 0.4:
            ocr_score = 78  # utilisable, légère réserve
        else:
            ocr_score = 55

    if is_docx or is_audio:
        ocr_score = None

    doc.extracted_text = text
    doc.ocr_score = ocr_score
    # Persist the extracted text immediately so synthesis / Q&A work even if the
    # (slow, model-dependent) vector indexing step is still running or fails.
    db.commit()

    if not text or len(text.strip()) < 10:
        doc.status = DocumentStatus.FAILED
        if is_audio:
            doc.error_message = _WHISPER_EMPTY_MSG
        else:
            doc.error_message = (
                "Aucun texte extractible. Vérifiez le fichier (scan illisible ou format incorrect)."
            )
        db.commit()
        return {"status": "failed", "reason": "no_text", "ocr_score": ocr_score}

    # Débloquer l’UI tout de suite : le texte est prêt (synthèse / aperçu),
    # l’index vectoriel peut encore tourner en arrière-plan.
    doc.status = DocumentStatus.INDEXED
    doc.error_message = None
    db.commit()
    logger.info(
        "Document text ready (pre-index)",
        extra={"document_id": doc.id, "cabinet_id": doc.cabinet_id, "chars": len(text)},
    )

    if ocr_score is not None and ocr_score < settings.OCR_QUALITY_THRESHOLD:
        logger.warning(
            "Low OCR quality %d%% for doc %s — flagged for rescan",
            ocr_score,
            doc.id,
        )

    chunks = 0
    try:
        from app.services.tasks import index_document_vectors

        index_document_vectors.delay(doc.id)
        logger.info("Vector indexing queued", extra={"document_id": doc.id})
    except Exception:
        try:
            chunks = index_document(
                doc.cabinet_id,
                doc.case_id,
                doc.id,
                doc.original_name,
                text,
            )
        except Exception as exc:
            logger.exception("Vector indexing failed for doc %s: %s", doc.id, exc)
            chunks = 0

    db.commit()
    logger.info(
        "Document indexed",
        extra={
            "document_id": doc.id,
            "cabinet_id": doc.cabinet_id,
            "task": "process_document",
        },
    )
    return {
        "status": "indexed",
        "chunks": chunks,
        "ocr_score": ocr_score,
        "ocr_alert": ocr_score is not None and ocr_score < settings.OCR_QUALITY_THRESHOLD,
    }
