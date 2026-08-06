import logging

from app.core.database import SessionLocal
from app.models import Document
from app.services.celery_app import celery_app
from app.services.document_pipeline import process_document_record
from app.services.object_storage import read_file

logger = logging.getLogger(__name__)


@celery_app.task(name="process_document", bind=True, max_retries=2)
def process_document(self, document_id: str):
    db = SessionLocal()
    doc = None
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return {"status": "not_found"}

        content = read_file(doc.storage_path)
        return process_document_record(doc, content, db)

    except Exception as exc:
        logger.exception("Document processing failed: %s", exc)
        if doc:
            from app.models import DocumentStatus
            doc.status = DocumentStatus.FAILED
            db.commit()
        raise self.retry(exc=exc, countdown=10)
    finally:
        db.close()
