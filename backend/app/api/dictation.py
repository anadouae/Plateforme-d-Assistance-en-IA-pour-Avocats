"""API dictée arabe → document officiel (+ transcription Whisper)."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import log_audit, require_roles
from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import check_rate_limit
from app.models import User, UserRole
from app.services.dictation import compose_official_document, polish_arabic_dictation
from app.services.plaidoirie_prompt import PLAIDOIRIE_TYPES
from app.services.whisper_stt import transcribe_audio_bytes, whisper_status

router = APIRouter(prefix="/api/dictation", tags=["dictation"])

MAX_AUDIO_MB = 25

_PLAIDOIRIE_TYPE_PATTERN = (
    "^(civil-general|civil-defense|penal-defense|partie-civile|commercial|"
    "social-travail|famille|appel|cassation|administratif|foncier|memo-final|"
    "libre|custom)$"
)


class PolishRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=20000)


class PolishResponse(BaseModel):
    polished: str
    provider: str


class ComposeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=20000)
    doc_type: str = Field(
        "plaidoirie",
        pattern="^(plaidoirie|general|petition|memo|letter|minutes)$",
    )
    title: str | None = Field(None, max_length=255)
    polish_first: bool = True
    plaidoirie_type: str | None = Field(
        None,
        pattern=_PLAIDOIRIE_TYPE_PATTERN,
        description="Type de plaidoirie marocaine (injecté dans le system prompt)",
    )


class ComposeResponse(BaseModel):
    title: str
    body: str
    polished: str | None = None
    provider: str
    checks: list[str] = []
    plaidoirie_type: str | None = None
    header_ar: str = "المملكة المغربية"
    header_fr: str = "Royaume du Maroc"
    motto_ar: str = "الله · الوطن · الملك"


class TranscribeResponse(BaseModel):
    text: str
    provider: str
    language: str | None = None
    degraded: bool = False


@router.get("/stt-status")
def dictation_stt_status(
    user: User = Depends(require_roles(UserRole.AVOCAT, UserRole.ADMIN_CABINET)),
):
    return whisper_status()


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_dictation(
    request: Request,
    file: UploadFile = File(...),
    language: str = Form("ar"),
    user: User = Depends(require_roles(UserRole.AVOCAT, UserRole.ADMIN_CABINET)),
    db: Session = Depends(get_db),
):
    """Audio (webm/wav/mp3…) → texte via faster-whisper local."""
    check_rate_limit(request, key="dictation.transcribe", limit=40, window_sec=60)

    if not settings.WHISPER_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Whisper désactivé. Activez WHISPER_ENABLED ou utilisez la dictée navigateur.",
        )

    raw = await file.read()
    if len(raw) > MAX_AUDIO_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Fichier audio trop volumineux (max {MAX_AUDIO_MB} Mo).",
        )
    if len(raw) < 64:
        raise HTTPException(status_code=400, detail="Fichier audio vide")

    # Produit Maroc : transcription forcée en arabe
    lang = "ar"
    text, provider = transcribe_audio_bytes(
        raw,
        filename=file.filename or "audio.webm",
        language="ar",
    )

    if not text:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Transcription Whisper indisponible. "
                "Vérifiez faster-whisper / le modèle, ou dictez via Chrome, ou tapez le texte."
            ),
        )

    log_audit(db, "dictation.transcribe", user=user, request=request, details=provider)
    db.commit()
    return TranscribeResponse(
        text=text,
        provider=provider,
        language=lang,
        degraded=False,
    )


@router.post("/polish", response_model=PolishResponse)
def polish_dictation(
    data: PolishRequest,
    request: Request,
    user: User = Depends(require_roles(UserRole.AVOCAT, UserRole.ADMIN_CABINET)),
    db: Session = Depends(get_db),
):
    check_rate_limit(request, key="dictation.polish", limit=20, window_sec=60)
    polished, provider = polish_arabic_dictation(data.text)
    if not polished:
        raise HTTPException(status_code=400, detail="نص فارغ / texte vide")
    log_audit(db, "dictation.polish", user=user, request=request, details=provider)
    db.commit()
    return PolishResponse(polished=polished, provider=provider)


@router.post("/compose", response_model=ComposeResponse)
def compose_dictation_document(
    data: ComposeRequest,
    request: Request,
    user: User = Depends(require_roles(UserRole.AVOCAT, UserRole.ADMIN_CABINET)),
    db: Session = Depends(get_db),
):
    check_rate_limit(request, key="dictation.compose", limit=15, window_sec=60)
    source = data.text.strip()
    polished = None
    if data.polish_first:
        polished, _ = polish_arabic_dictation(source)
        source = polished or source

    city = None
    cabinet_name = None
    if user.cabinet:
        cabinet_name = user.cabinet.name
        city = getattr(user.cabinet, "city", None)

    ptype = data.plaidoirie_type
    if data.doc_type == "plaidoirie" and ptype and ptype not in PLAIDOIRIE_TYPES:
        ptype = "civil-general"

    title, body, provider, checks = compose_official_document(
        source,
        doc_type=data.doc_type,
        title=data.title,
        city=city,
        cabinet_name=cabinet_name,
        plaidoirie_type=ptype,
    )
    if not body:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="خدمة التحرير غير متاحة مؤقتًا — réessayez.",
        )

    log_audit(
        db,
        "dictation.compose",
        user=user,
        request=request,
        details=f"{data.doc_type}:{ptype or '-'}",
    )
    db.commit()
    return ComposeResponse(
        title=title,
        body=body,
        polished=polished,
        provider=provider,
        checks=checks,
        plaidoirie_type=ptype,
    )
