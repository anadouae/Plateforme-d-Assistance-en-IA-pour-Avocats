import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging_config import get_correlation_id, set_correlation_id
from app.core.timeouts import OperationTimeout
from app.models import Document, DocumentStatus
from app.services.extraction import (
    extract_text,
    is_audio_document,
    is_scrambled_arabic,
    safe_repair_arabic_text,
)
from app.services.rag import index_document

logger = logging.getLogger(__name__)

_WHISPER_DISABLED_MSG = (
    "Transcription impossible : Whisper est désactivé (WHISPER_ENABLED=false)."
)
_WHISPER_EMPTY_MSG = (
    "Transcription vide ou Whisper indisponible. Vérifiez le fichier audio."
)
_WHISPER_TIMEOUT_MSG = (
    "Transcription Whisper interrompue (timeout). Réessayez ou découpez le fichier audio."
)
_OCR_TIMEOUT_MSG = (
    "OCR interrompu (timeout). Réessayez ou réduisez le nombre de pages scannées."
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

    text = safe_repair_arabic_text(text or "")
    # Si encore brouillé malgré OCR, baisser le score affiché (pas « OCR 100% »)
    if text and is_scrambled_arabic(text) and (ocr_score is None or ocr_score >= 90):
        # Pas de score OCR pour l'audio ; ne pas inventer un faux score
        if not is_audio:
            ocr_score = 55
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

    try:
        chunks = index_document(
            doc.cabinet_id,
            doc.case_id,
            doc.id,
            doc.original_name,
            text,
        )
    except Exception as exc:
        # Indexing failure (e.g. embedding model unavailable) must not lose the
        # extracted text: the document stays usable for synthesis and keyword Q&A.
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
