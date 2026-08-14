import json
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, log_audit, require_not_assistant
from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import check_rate_limit
from app.models import Case, Document, DocumentStatus, User, UserRole
from app.schemas import (
    AIResponse,
    Citation,
    DocumentAskRequest,
    DocumentDetailResponse,
    DocumentResponse,
    SynthesisResponse,
)
from app.services.agent import route_and_answer
from app.services.language import get_disclaimer, normalize_locale, resolve_response_language
from app.services.extraction import (
    ALLOWED_EXTENSIONS,
    ALLOWED_MIMES,
    document_kind,
    find_relevant_excerpt,
    get_extension,
    is_audio_document,
    is_scrambled_arabic,
    safe_repair_arabic_text,
)
from app.services.storage import delete_file, read_file, save_file
from app.services.rag import delete_document_index

def _enqueue_document(doc_id: str):
    try:
        from app.services.tasks import process_document
        process_document.delay(doc_id)
        return True
    except Exception:
        return False

router = APIRouter(prefix="/api/documents", tags=["documents"])

MAX_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


def _doc_response(doc: Document, case: Case | None = None) -> DocumentResponse:
    ocr_alert = (
        doc.ocr_score is not None
        and doc.ocr_score < settings.OCR_QUALITY_THRESHOLD
        and doc.status == DocumentStatus.INDEXED
    )
    kind = document_kind(doc.original_name, doc.mime_type)
    return DocumentResponse(
        id=doc.id,
        original_name=doc.original_name,
        mime_type=doc.mime_type,
        file_size=doc.file_size,
        ocr_score=doc.ocr_score,
        ocr_alert=ocr_alert,
        status=doc.status.value,
        case_id=doc.case_id,
        case_reference=case.reference if case else None,
        created_at=doc.created_at,
        kind=kind,
        error_message=doc.error_message,
    )


def _get_document_for_user(db: Session, doc_id: str, user: User) -> Document:
    doc = (
        db.query(Document)
        .filter(Document.id == doc_id, Document.cabinet_id == user.cabinet_id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document introuvable")
    return doc


def _list_documents_impl(
    case_id: str | None,
    user: User,
    db: Session,
) -> list:
    query = db.query(Document).filter(Document.cabinet_id == user.cabinet_id)
    if case_id:
        query = query.filter(Document.case_id == case_id)
    docs = query.order_by(Document.created_at.desc()).all()
    result = []
    for doc in docs:
        case = db.query(Case).filter(Case.id == doc.case_id).first()
        result.append(_doc_response(doc, case))
    return result


@router.get("", response_model=list[DocumentResponse])
@router.get("/", response_model=list[DocumentResponse], include_in_schema=False)
def list_documents(
    case_id: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _list_documents_impl(case_id, user, db)


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    request: Request,
    case_id: str = Form(...),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    check_rate_limit(
        request,
        key="documents.upload",
        limit=settings.UPLOAD_RATE_LIMIT,
        window_sec=settings.UPLOAD_RATE_WINDOW_SEC,
        subject=user.id,
    )
    case = (
        db.query(Case)
        .filter(Case.id == case_id, Case.cabinet_id == user.cabinet_id)
        .first()
    )
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dossier introuvable")

    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Fichier invalide")

    ext = get_extension(file.filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Type de fichier non autorisé. Formats : PDF, DOCX, images, audio (webm, wav, mp3, m4a, ogg, mp4).",
        )

    content = await file.read()
    if len(content) > MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fichier trop volumineux (max {settings.MAX_UPLOAD_SIZE_MB} Mo).",
        )

    from app.services.file_sniff import sniff_allowed_upload

    sniff_error = sniff_allowed_upload(content, ext)
    if sniff_error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=sniff_error)

    mime = file.content_type or "application/octet-stream"
    audio = is_audio_document(file.filename, mime)
    if (
        mime not in ALLOWED_MIMES
        and not mime.startswith("image/")
        and not (audio and (mime.startswith("audio/") or mime in {"video/webm", "video/mp4", "application/octet-stream"}))
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Type MIME non autorisé")

    # Normaliser le MIME audio si le navigateur envoie octet-stream
    if audio and mime == "application/octet-stream":
        mime = {
            ".webm": "audio/webm",
            ".wav": "audio/wav",
            ".mp3": "audio/mpeg",
            ".mpeg": "audio/mpeg",
            ".mpga": "audio/mpeg",
            ".m4a": "audio/mp4",
            ".mp4": "audio/mp4",
            ".ogg": "audio/ogg",
        }.get(ext, "audio/webm")

    storage_path = save_file(content, user.cabinet_id, case_id, ext)

    doc = Document(
        filename=Path(storage_path).name if not storage_path.startswith("minio://") else storage_path.split("/")[-1],
        original_name=file.filename,
        mime_type=mime,
        file_size=len(content),
        storage_path=storage_path,
        extracted_text=None,
        ocr_score=None,
        error_message=None,
        status=DocumentStatus.PENDING,
        case_id=case_id,
        cabinet_id=user.cabinet_id,
        uploaded_by=user.id,
    )
    db.add(doc)
    log_audit(db, "document.upload", user=user, request=request, details=file.filename)
    db.commit()
    db.refresh(doc)

    if not _enqueue_document(doc.id):
        from app.services.document_pipeline import process_document_record

        content = read_file(doc.storage_path)
        process_document_record(doc, content, db)
        db.refresh(doc)

    return _doc_response(doc, case)


@router.get("/alerts/ocr", response_model=list[DocumentResponse])
def list_ocr_alerts(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Documents indexés avec qualité OCR insuffisante (< seuil)."""
    docs = (
        db.query(Document)
        .filter(
            Document.cabinet_id == user.cabinet_id,
            Document.status == DocumentStatus.INDEXED,
            Document.ocr_score.isnot(None),
            Document.ocr_score < settings.OCR_QUALITY_THRESHOLD,
        )
        .order_by(Document.created_at.desc())
        .all()
    )
    result = []
    for doc in docs:
        case = db.query(Case).filter(Case.id == doc.case_id).first()
        result.append(_doc_response(doc, case))
    return result


@router.get("/{doc_id}", response_model=DocumentDetailResponse)
def get_document(
    doc_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = _get_document_for_user(db, doc_id, user)
    case = db.query(Case).filter(Case.id == doc.case_id).first()
    raw_text = doc.extracted_text or ""
    fixed = safe_repair_arabic_text(raw_text)
    if fixed and fixed != raw_text and len(fixed) > 50:
        doc.extracted_text = fixed
        db.commit()
        raw_text = fixed
    preview = raw_text[:2000] if raw_text else None
    return DocumentDetailResponse(
        **_doc_response(doc, case).model_dump(),
        extracted_text_preview=preview,
    )


@router.post("/{doc_id}/reextract", response_model=DocumentDetailResponse)
def reextract_document(
    doc_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Ré-extrait le texte (RTL arabe + OCR amélioré) sans ré-uploader le fichier."""
    from app.services.document_pipeline import process_document_record

    doc = _get_document_for_user(db, doc_id, user)
    content = read_file(doc.storage_path)
    process_document_record(doc, content, db)
    db.refresh(doc)
    # Réparer l'ordre arabe après extraction pipeline
    fixed = safe_repair_arabic_text(doc.extracted_text or "")
    if fixed and fixed != (doc.extracted_text or ""):
        doc.extracted_text = fixed
        db.commit()
        db.refresh(doc)
    log_audit(db, "document.reextract", user=user, request=request, details=doc.original_name)
    db.commit()
    case = db.query(Case).filter(Case.id == doc.case_id).first()
    preview = (doc.extracted_text or "")[:2000] if doc.extracted_text else None
    return DocumentDetailResponse(
        **_doc_response(doc, case).model_dump(),
        extracted_text_preview=preview,
    )


@router.get("/{doc_id}/download")
def download_document(
    doc_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = _get_document_for_user(db, doc_id, user)
    log_audit(db, "document.download", user=user, request=request, details=doc.original_name)
    db.commit()
    content = read_file(doc.storage_path)
    from fastapi.responses import Response
    return Response(
        content=content,
        media_type=doc.mime_type,
        headers={"Content-Disposition": f'inline; filename="{doc.original_name}"'},
    )


@router.get("/{doc_id}/synthese", response_model=SynthesisResponse)
def synthesize_document(
    doc_id: str,
    lang: str | None = None,
    user: User = Depends(require_not_assistant),
    db: Session = Depends(get_db),
):
    doc = _get_document_for_user(db, doc_id, user)
    from app.services.agent import generate_synthesis

    locale = normalize_locale(lang)
    text = safe_repair_arabic_text(doc.extracted_text or "")
    if text and text != (doc.extracted_text or ""):
        doc.extracted_text = text
        db.commit()
    # Texte arabe brouillé + jamais vraiment OCRisé (score 100 = couche PDF) → OCR forcé.
    # Skip auto-reprocess pour l'audio (ocr_score toujours None) : l'utilisateur peut ré-extraire.
    if (
        text
        and is_scrambled_arabic(text)
        and (doc.ocr_score is None or doc.ocr_score >= 90)
        and not is_audio_document(doc.original_name, doc.mime_type)
    ):
        from app.services.document_pipeline import process_document_record

        content = read_file(doc.storage_path)
        process_document_record(doc, content, db)
        db.refresh(doc)
        text = safe_repair_arabic_text(doc.extracted_text or "")
    data = generate_synthesis(doc.original_name, text, language=locale)
    return SynthesisResponse(
        document_id=doc.id,
        document_name=doc.original_name,
        parties=data["parties"],
        key_dates=data["key_dates"],
        amounts=data["amounts"],
        risk_clauses=data["risk_clauses"],
        attention_points=data["attention_points"],
        summary=data["summary"],
        sources=data["sources"],
        disclaimer=data.get("disclaimer", get_disclaimer(locale)),
    )


@router.post("/{doc_id}/ask", response_model=AIResponse)
def ask_document(
    doc_id: str,
    data: DocumentAskRequest,
    request: Request,
    user: User = Depends(require_not_assistant),
    db: Session = Depends(get_db),
):
    doc = _get_document_for_user(db, doc_id, user)
    text = doc.extracted_text or ""
    excerpt = find_relevant_excerpt(text, data.question)
    locale = resolve_response_language(data.question, data.language)

    result = route_and_answer(
        data.question,
        document_text=text,
        document_name=doc.original_name,
        document_id=doc.id,
        cabinet_id=user.cabinet_id,
        case_id=doc.case_id,
        excerpt=excerpt,
        confidence_threshold=settings.AI_CONFIDENCE_THRESHOLD,
        language=locale,
    )

    log_audit(db, "document.ask", user=user, request=request, details=doc.original_name)
    db.commit()

    return AIResponse(
        answer=result.answer,
        source_type=result.source_type,
        sources=result.sources if result.sources else [],
        confidence_score=result.confidence_score,
        disclaimer=get_disclaimer(locale),
    )


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    doc_id: str,
    request: Request,
    user: User = Depends(require_not_assistant),
    db: Session = Depends(get_db),
):
    doc = _get_document_for_user(db, doc_id, user)
    log_audit(db, "document.delete", user=user, request=request, details=doc.original_name)
    delete_document_index(doc.cabinet_id, doc.case_id, doc.id)
    delete_file(doc.storage_path)
    db.delete(doc)
    db.commit()
