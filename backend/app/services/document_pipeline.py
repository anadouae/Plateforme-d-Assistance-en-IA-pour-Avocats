import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Document, DocumentStatus
from app.services.extraction import extract_text, is_scrambled_arabic, safe_repair_arabic_text
from app.services.rag import index_document

logger = logging.getLogger(__name__)


def process_document_record(doc: Document, content: bytes, db: Session) -> dict:
    """Extract text, index vectors, update document status."""
    doc.status = DocumentStatus.PROCESSING
    db.commit()

    text, ocr_score = extract_text(content, doc.original_name, doc.mime_type)
    text = safe_repair_arabic_text(text or "")
    # Si encore brouillé malgré OCR, baisser le score affiché (pas « OCR 100% »)
    if text and is_scrambled_arabic(text) and (ocr_score is None or ocr_score >= 90):
        ocr_score = 55
    doc.extracted_text = text
    doc.ocr_score = ocr_score
    # Persist the extracted text immediately so synthesis / Q&A work even if the
    # (slow, model-dependent) vector indexing step is still running or fails.
    db.commit()

    if not text or len(text.strip()) < 10:
        doc.status = DocumentStatus.FAILED
        db.commit()
        return {"status": "failed", "reason": "no_text", "ocr_score": ocr_score}

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

    doc.status = DocumentStatus.INDEXED
    db.commit()
    return {
        "status": "indexed",
        "chunks": chunks,
        "ocr_score": ocr_score,
        "ocr_alert": ocr_score is not None and ocr_score < settings.OCR_QUALITY_THRESHOLD,
    }
