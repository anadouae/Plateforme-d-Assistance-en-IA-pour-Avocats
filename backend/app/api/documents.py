import json
import logging
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import Response
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
    DocumentMetaUpdate,
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
    is_native_office_document,
    is_scrambled_arabic,
    safe_repair_arabic_text,
)
from app.services.storage import delete_file, read_file, save_file
from app.services.rag import delete_document_index

logger = logging.getLogger(__name__)


def _enqueue_document(doc_id: str) -> bool:
    try:
        from app.services.tasks import process_document

        process_document.delay(doc_id)
        return True
    except Exception as exc:
        logger.warning("Celery enqueue failed for doc %s: %s", doc_id, exc)
        return False


def _process_document_background(doc_id: str, content: bytes | None = None) -> None:
    """Fallback / traitement immédiat — content= bytes d'upload évite re-lecture MinIO."""
    from app.core.database import SessionLocal
    from app.services.document_pipeline import process_document_record

    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            return
        payload = content
        if payload is None:
            payload = read_file(doc.storage_path)
        process_document_record(doc, payload, db)
    except Exception:
        logger.exception("Background document processing failed for %s", doc_id)
        try:
            doc = db.query(Document).filter(Document.id == doc_id).first()
            if doc and doc.status != DocumentStatus.INDEXED:
                doc.status = DocumentStatus.FAILED
                doc.error_message = (
                    "Échec du traitement du document. Réessayez l’import."
                )[:2000]
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


def _schedule_document_processing(
    doc_id: str,
    background_tasks: BackgroundTasks | None,
    *,
    content: bytes | None = None,
    filename: str = "",
) -> None:
    """
    DOCX / texte : traiter en mémoire dans le backend (évite BadZipFile si Celery
    a une ENCRYPTION_KEY différente). PDF/images/audio : Celery.
    """
    name = (filename or "").lower()
    light = name.endswith((".docx", ".txt", ".md", ".markdown"))
    if light and content is not None and background_tasks is not None:
        background_tasks.add_task(_process_document_background, doc_id, content)
        return
    if _enqueue_document(doc_id):
        return
    if background_tasks is not None:
        background_tasks.add_task(_process_document_background, doc_id, content)
    else:
        _process_document_background(doc_id, content)

router = APIRouter(prefix="/api/documents", tags=["documents"])

MAX_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


def _doc_response(doc: Document, case: Case | None = None) -> DocumentResponse:
    # Long texte arabe utilisable : ne pas afficher une fausse alerte « OCR faible »
    text_len = len((doc.extracted_text or "").strip())
    score = doc.ocr_score
    if (
        score is not None
        and score < settings.OCR_QUALITY_THRESHOLD
        and text_len >= 12000
        and doc.status == DocumentStatus.INDEXED
    ):
        score = max(score, 85)
    ocr_alert = (
        score is not None
        and score < settings.OCR_QUALITY_THRESHOLD
        and doc.status == DocumentStatus.INDEXED
        and text_len < 12000
    )
    kind = document_kind(doc.original_name, doc.mime_type)
    return DocumentResponse(
        id=doc.id,
        original_name=doc.original_name,
        mime_type=doc.mime_type,
        file_size=doc.file_size,
        ocr_score=score,
        ocr_alert=ocr_alert,
        status=doc.status.value,
        case_id=doc.case_id,
        case_reference=case.reference if case else None,
        created_at=doc.created_at,
        kind=kind,
        error_message=doc.error_message,
        inventory_number=getattr(doc, "inventory_number", None),
        exhibit_type=getattr(doc, "exhibit_type", None),
        produced_by=getattr(doc, "produced_by", None),
        exhibit_version=getattr(doc, "exhibit_version", None),
        cited_in_plea=getattr(doc, "cited_in_plea", None),
        uploaded_by=getattr(doc, "uploaded_by", None),
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
    background_tasks: BackgroundTasks,
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
            detail="Type de fichier non autorisé. Formats : PDF, DOCX, TXT, MD, images, audio (webm, wav, mp3, m4a, ogg, mp4).",
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
    if ext == ".txt" and mime == "application/octet-stream":
        mime = "text/plain"
    if ext in {".md", ".markdown"} and mime in {
        "application/octet-stream",
        "text/plain",
        "",
    }:
        mime = "text/markdown"
    if (
        mime not in ALLOWED_MIMES
        and not mime.startswith("image/")
        and not mime.startswith("text/")
        and not (ext in {".txt", ".md", ".markdown"})
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

    from app.services.object_storage import TransientStorageError

    try:
        storage_path = save_file(content, user.cabinet_id, case_id, ext)
    except TransientStorageError as exc:
        logger.exception("Upload stockage échoué: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stockage fichiers temporairement indisponible. Réessayez dans un instant.",
        ) from exc

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
    from sqlalchemy import func
    max_n = (
        db.query(func.max(Document.inventory_number))
        .filter(Document.case_id == case_id, Document.cabinet_id == user.cabinet_id)
        .scalar()
    )
    doc.inventory_number = int(max_n or 0) + 1
    if getattr(doc, "exhibit_version", None) is None:
        doc.exhibit_version = "copie"
    if getattr(doc, "produced_by", None) is None:
        doc.produced_by = "client"
    db.add(doc)
    log_audit(db, "document.upload", user=user, request=request, details=file.filename)
    db.commit()
    db.refresh(doc)

    _schedule_document_processing(
        doc.id,
        background_tasks,
        content=content,
        filename=file.filename or "",
    )
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
    # Word / texte natif : jamais de réparation BIDI (sinon inversion + même pied de page
    # en tête de tous les DOCX arabes). PDF/OCR seulement.
    if raw_text and not is_native_office_document(doc.original_name, doc.mime_type):
        fixed = safe_repair_arabic_text(raw_text)
        if fixed and fixed != raw_text and len(fixed) > 50:
            doc.extracted_text = fixed
            db.commit()
            raw_text = fixed
    # Texte intégral pour la lecture (pas un extrait tronqué à 2000 car.)
    preview = raw_text if raw_text else None
    return DocumentDetailResponse(
        **_doc_response(doc, case).model_dump(),
        extracted_text_preview=preview,
    )


@router.post("/{doc_id}/reextract", response_model=DocumentDetailResponse)
def reextract_document(
    doc_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Relance l'extraction en arrière-plan (ne bloque pas l'interface)."""
    from app.models import DocumentStatus

    doc = _get_document_for_user(db, doc_id, user)
    doc.status = DocumentStatus.PROCESSING
    doc.error_message = None
    db.commit()
    # DOCX : relire + traiter dans le backend (évite BadZipFile si Celery ≠ ENCRYPTION_KEY)
    content = None
    try:
        content = read_file(doc.storage_path)
    except Exception:
        content = None
    name = doc.original_name or ""
    if name.lower().endswith((".docx", ".txt", ".md", ".markdown")) and content is not None:
        _schedule_document_processing(
            doc.id,
            background_tasks,
            content=content,
            filename=name,
        )
    elif not _enqueue_document(doc.id):
        _schedule_document_processing(
            doc.id,
            background_tasks,
            content=content,
            filename=name,
        )
    db.refresh(doc)
    log_audit(db, "document.reextract", user=user, request=request, details=doc.original_name)
    db.commit()
    case = db.query(Case).filter(Case.id == doc.case_id).first()
    preview = (doc.extracted_text or "") or None
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
    try:
        content = read_file(doc.storage_path)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fichier introuvable. Réimportez le document.",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fichier introuvable. Réimportez le document.",
        )
    from urllib.parse import quote

    from fastapi.responses import Response

    # Noms arabes : filename ASCII seul + filename* UTF-8 (sinon header latin-1 → 500)
    raw_name = (doc.original_name or "document").replace('"', "").replace("\n", " ").strip()
    safe_ascii = "document"
    if "." in raw_name:
        ext = raw_name.rsplit(".", 1)[-1]
        if ext.isalnum() and len(ext) <= 8:
            safe_ascii = f"document.{ext.lower()}"
    encoded = quote(raw_name)
    return Response(
        content=content,
        media_type=doc.mime_type or "application/octet-stream",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{safe_ascii}"; filename*=UTF-8\'\'{encoded}'
            ),
        },
    )


@router.get("/{doc_id}/synthese", response_model=SynthesisResponse)
def synthesize_document(
    doc_id: str,
    request: Request,
    lang: str | None = None,
    user: User = Depends(require_not_assistant),
    db: Session = Depends(get_db),
):
    doc = _get_document_for_user(db, doc_id, user)
    from app.services.agent import generate_synthesis
    from app.services.billing import begin_ai_action, finish_ai_action

    _ent, slot = begin_ai_action(db, user.cabinet_id, "synthesis", request=request)
    try:
        locale = normalize_locale(lang)
        raw = doc.extracted_text or ""
        if is_native_office_document(doc.original_name, doc.mime_type):
            text = raw
            if doc.ocr_score is not None:
                doc.ocr_score = None
                db.commit()
        else:
            text = safe_repair_arabic_text(raw)
            if text and text != raw:
                doc.extracted_text = text
                db.commit()
        if (
            text
            and is_scrambled_arabic(text)
            and (doc.ocr_score is None or doc.ocr_score >= 90)
            and not is_audio_document(doc.original_name, doc.mime_type)
            and not is_native_office_document(doc.original_name, doc.mime_type)
        ):
            from app.services.document_pipeline import process_document_record

            content = read_file(doc.storage_path)
            process_document_record(doc, content, db)
            db.refresh(doc)
            text = safe_repair_arabic_text(doc.extracted_text or "")
        data = generate_synthesis(doc.original_name, text, language=locale)
        finish_ai_action(db, user.cabinet_id, "synthesis", slot_token=slot, success=True)
        db.commit()
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
    except Exception:
        finish_ai_action(db, user.cabinet_id, "synthesis", slot_token=slot, success=False)
        db.rollback()
        raise


@router.post("/{doc_id}/ask", response_model=AIResponse)
def ask_document(
    doc_id: str,
    data: DocumentAskRequest,
    request: Request,
    user: User = Depends(require_not_assistant),
    db: Session = Depends(get_db),
):
    doc = _get_document_for_user(db, doc_id, user)
    from app.services.billing import begin_ai_action, finish_ai_action
    from app.core.rate_limit import check_rate_limit

    check_rate_limit(request, key="documents.ask", limit=20, window_sec=60, subject=user.id)
    _ent, slot = begin_ai_action(db, user.cabinet_id, "ask", request=request)
    text = doc.extracted_text or ""
    excerpt = find_relevant_excerpt(text, data.question)
    locale = resolve_response_language(data.question, data.language)

    try:
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
            history=list(data.history or []) if getattr(data, "history", None) else None,
        )
    except Exception:
        finish_ai_action(db, user.cabinet_id, "ask", slot_token=slot, success=False)
        raise

    log_audit(db, "document.ask", user=user, request=request, details=doc.original_name)
    finish_ai_action(db, user.cabinet_id, "ask", slot_token=slot, success=True)
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
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = _get_document_for_user(db, doc_id, user)
    if doc.uploaded_by != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne pouvez supprimer que les pièces que vous avez déposées.",
        )
    log_audit(db, "document.delete", user=user, request=request, details=doc.original_name)
    try:
        delete_document_index(doc.cabinet_id, doc.case_id, doc.id)
    except Exception:
        logger.warning("Index delete skipped for %s", doc.id)
    try:
        delete_file(doc.storage_path)
    except Exception:
        logger.warning("Storage delete skipped for %s", doc.id)
    db.delete(doc)
    db.commit()


@router.patch("/{doc_id}/meta", response_model=DocumentResponse)
def update_document_meta(
    doc_id: str,
    data: DocumentMetaUpdate,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = _get_document_for_user(db, doc_id, user)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(doc, field, value)
    case = db.query(Case).filter(Case.id == doc.case_id).first()
    log_audit(db, "document.meta", user=user, request=request, details=doc.original_name)
    db.commit()
    db.refresh(doc)
    return _doc_response(doc, case)


@router.get("/bordereau/{case_id}")
def export_bordereau(
    case_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    case = (
        db.query(Case)
        .filter(Case.id == case_id, Case.cabinet_id == user.cabinet_id)
        .first()
    )
    if not case:
        raise HTTPException(status_code=404, detail="Dossier introuvable")
    docs_list = (
        db.query(Document)
        .filter(Document.case_id == case_id, Document.cabinet_id == user.cabinet_id)
        .order_by(Document.inventory_number.asc().nullslast(), Document.created_at.asc())
        .all()
    )
    lines = [
        f"BORDEREAU DE PIECES — {case.reference}",
        f"Client : {case.client_name}",
        f"N° RG : {getattr(case, 'court_file_number', None) or '—'}",
        f"Tribunal : {case.tribunal or '—'}",
        "",
        f"{'N°':<4} {'Type':<16} {'Producteur':<12} {'Version':<12} Intitulé / citation",
        "-" * 88,
    ]
    for d in docs_list:
        n = getattr(d, "inventory_number", None) or "—"
        et = getattr(d, "exhibit_type", None) or "—"
        pb = getattr(d, "produced_by", None) or "—"
        ev = getattr(d, "exhibit_version", None) or "—"
        cite = getattr(d, "cited_in_plea", None) or ""
        title = d.original_name
        if cite:
            title = f"{title} [cité : {cite}]"
        lines.append(f"{str(n):<4} {et:<16} {pb:<12} {ev:<12} {title}")
    lines.append("")
    lines.append("Document généré par LexHub — sans logo sur l'acte d'audience.")
    body = "\n".join(lines)
    filename = f"bordereau-{case.reference}.txt"
    return Response(
        content=body.encode("utf-8"),
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

