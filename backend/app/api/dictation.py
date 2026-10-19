"""API dictée AR/FR → document officiel (+ transcription Whisper local)."""

import re

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import log_audit, require_roles
from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import check_rate_limit
from app.models import User, UserRole
from app.services.dictation import compose_official_document, polish_dictation
from app.services.dictation_contradictions import detect_dictation_contradictions
from app.services.plaidoirie_prompt import PLAIDOIRIE_TYPES
from app.services.whisper_stt import transcribe_audio_bytes, whisper_status

router = APIRouter(prefix="/api/dictation", tags=["dictation"])

MAX_AUDIO_MB = 40

# Regex dérivé de PLAIDOIRIE_TYPES (évite de rejeter fiscal, circulation, etc.)
_PLAIDOIRIE_TYPE_PATTERN = "^(" + "|".join(re.escape(k) for k in sorted(PLAIDOIRIE_TYPES.keys())) + ")$"


def _norm_lang(language: str | None) -> str:
    lang = (language or "ar").strip().lower()
    if lang in ("auto", "detect", ""):
        return "auto"
    if lang.startswith("fr"):
        return "fr"
    return "ar"


class PolishRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=80000)
    language: str = Field("ar", pattern="^(ar|fr|AR|FR)$")
    source: str = Field("audio", pattern="^(dictation|audio)$")
    case_id: str | None = Field(None, max_length=64, description="Dossier — masquage PII")


class ContradictionOut(BaseModel):
    kind: str
    values: list[str]
    message_ar: str
    message_fr: str


class FormEditOut(BaseModel):
    id: str
    original: str
    proposed: str
    kind: str = "form"


class PleaVariableOut(BaseModel):
    kind: str
    value: str
    label_ar: str
    label_fr: str


class StructureHintOut(BaseModel):
    section_ar: str
    section_fr: str
    excerpt: str
    message_ar: str
    message_fr: str


class LawSuggestionOut(BaseModel):
    code_ar: str
    code_fr: str
    article: str
    reason_ar: str
    reason_fr: str
    insert_ar: str


class PolishResponse(BaseModel):
    polished: str
    provider: str
    contradictions: list[ContradictionOut] = []
    guessed_words: list[str] = []
    edits: list[FormEditOut] = []
    variables: list[PleaVariableOut] = []
    structure_hints: list[StructureHintOut] = []
    law_suggestions: list[LawSuggestionOut] = []
    pii_masked: bool = False
    pii_summary: dict[str, int] = {}

class ComposeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=80000)
    doc_type: str = Field(
        "plaidoirie",
        pattern="^(plaidoirie|general|petition|memo|letter|minutes)$",
    )
    title: str | None = Field(None, max_length=255)
    polish_first: bool = True
    language: str = Field("ar", pattern="^(ar|fr|AR|FR)$")
    plaidoirie_type: str | None = Field(
        None,
        pattern=_PLAIDOIRIE_TYPE_PATTERN,
        description="Type de plaidoirie marocaine (injecté dans le system prompt)",
    )
    case_id: str | None = Field(None, max_length=64, description="Dossier lié — pièces + PII")
    brief_posture: str | None = Field(None, max_length=200)
    brief_jurisdiction: str | None = Field(None, max_length=200)
    clarifications: list[dict] | None = Field(
        None,
        description="Réponses QCM avocat avant rédaction [{id, choice, other?}]",
    )


class ClarifyOption(BaseModel):
    id: str
    label_ar: str
    label_fr: str


class ClarifyQuestion(BaseModel):
    id: str
    prompt_ar: str
    prompt_fr: str
    options: list[ClarifyOption]
    allow_other: bool = True


class ClarifyRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=80000)
    case_id: str = Field(..., min_length=1, max_length=64)
    plaidoirie_type: str | None = Field(None, pattern=_PLAIDOIRIE_TYPE_PATTERN)
    language: str = Field("ar", pattern="^(ar|fr|AR|FR)$")
    brief_posture: str | None = Field(None, max_length=200)
    brief_jurisdiction: str | None = Field(None, max_length=200)


class ClarifyResponse(BaseModel):
    questions: list[ClarifyQuestion] = []
    summary_fr: str = ""
    summary_ar: str = ""
    pieces_noted: int = 0
    pii_tokens: list[str] = []
    provider: str = "none"


class ComposeResponse(BaseModel):
    title: str
    body: str
    polished: str | None = None
    provider: str
    checks: list[str] = []
    plaidoirie_type: str | None = None
    language: str = "ar"
    header_ar: str = "المملكة المغربية"
    header_fr: str = "Royaume du Maroc"
    motto_ar: str = "الله · الوطن · الملك"
    pii_masked: bool = False
    case_enriched: bool = False


class TranscribeResponse(BaseModel):
    text: str
    provider: str
    language: str | None = None
    degraded: bool = False


@router.get("/stt-status")
def dictation_stt_status(
    user: User = Depends(require_roles(UserRole.AVOCAT, UserRole.ADMIN_CABINET)),
):
    status_payload = whisper_status()
    status_payload["languages"] = ["ar", "fr"]
    status_payload["local_only"] = bool(settings.DICTATION_LOCAL_ONLY)
    groq_ok = bool((settings.GROQ_API_KEY or "").strip())
    status_payload["groq_fallback"] = groq_ok
    status_payload["groq_primary"] = groq_ok and bool(settings.DICTATION_STT_PREFER_GROQ)
    status_payload["ready"] = bool(
        status_payload.get("enabled")
        and (
            status_payload["groq_primary"]
            or status_payload.get("loaded")
            or (groq_ok and not settings.DICTATION_LOCAL_ONLY)
        )
    )
    status_payload["pipeline"] = (
        "mediarecorder→groq|whisper"
        if status_payload["groq_primary"]
        else "mediarecorder→whisper"
    )
    return status_payload


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_dictation(
    request: Request,
    file: UploadFile = File(...),
    language: str = Form("ar"),
    user: User = Depends(require_roles(UserRole.AVOCAT, UserRole.ADMIN_CABINET)),
    db: Session = Depends(get_db),
):
    """Audio (webm/wav/mp3…) → texte via API OpenAI (ou Whisper local si activé)."""
    check_rate_limit(
        request,
        key=f"dictation.transcribe:{user.id}",
        limit=15,
        window_sec=60,
    )

    openai_ok = bool((settings.OPENAI_API_KEY or "").strip())
    if not settings.WHISPER_ENABLED and not openai_ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Transcription indisponible. Configurez OPENAI_API_KEY ou utilisez la dictée navigateur.",
        )

    raw = await file.read()
    if len(raw) > MAX_AUDIO_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Fichier audio trop volumineux (max {MAX_AUDIO_MB} Mo).",
        )
    if len(raw) < 64:
        raise HTTPException(status_code=400, detail="Fichier audio vide")

    from app.services.file_sniff import sniff_allowed_upload

    name = file.filename or "audio.webm"
    ext = ("." + name.rsplit(".", 1)[-1].lower()) if "." in name else ".webm"
    sniff_err = sniff_allowed_upload(raw, ext)
    if sniff_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=sniff_err,
        )

    lang = _norm_lang(language)
    text, provider = transcribe_audio_bytes(
        raw,
        filename=name,
        language=lang,
    )

    if not text:
        if provider == "whisper:busy":
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="تفريغ قيد التنفيذ — انتظروا نهاية الإملاء الحالية.",
            )
        if provider == "whisper:timeout":
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="استغرق التفريغ وقتًا طويلاً. أوقفوا ثم أعيدوا مقطعاً أقصر إن لزم.",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="لم يُكتشف كلام واضح. قرّبوا الميكروفون وتكلّموا بالعربية الفصحى بوضوح.",
        )

    log_audit(db, "dictation.transcribe", user=user, request=request, details=f"{provider}:{lang}")
    db.commit()
    return TranscribeResponse(
        text=text,
        provider=provider,
        language=lang,
        degraded=False,
    )


@router.post("/polish", response_model=PolishResponse)
def polish_dictation_endpoint(
    data: PolishRequest,
    request: Request,
    user: User = Depends(require_roles(UserRole.AVOCAT, UserRole.ADMIN_CABINET)),
    db: Session = Depends(get_db),
):
    check_rate_limit(request, key="dictation.polish", limit=20, window_sec=60)
    from app.core.config import settings as _settings
    from app.models import Case
    from app.services.billing import assert_can_use_ai_action, spend_ai_action
    from app.services.pii_mask import (
        build_full_mask,
        collect_all_party_names,
        inventory_summary,
        unmask_text,
    )
    from app.services.pii_store import (
        load_case_pii_mapping,
        parties_from_case,
        save_case_pii_mapping,
    )

    charge_ai = bool(getattr(_settings, "DICTATION_POLISH_USE_LLM", False))
    if charge_ai:
        assert_can_use_ai_action(db, user.cabinet_id, "polish")
    lang = _norm_lang(data.language)
    source = (data.source or "audio").strip().lower()

    # Pseudonymisation avant ChatGPT (noms dossier + CIN/tél/email détectés)
    case = None
    parties: list[str] = []
    base_map: dict[str, str] = {}
    if (data.case_id or "").strip():
        case = (
            db.query(Case)
            .filter(Case.id == data.case_id, Case.cabinet_id == user.cabinet_id)
            .first()
        )
        if case:
            parties = collect_all_party_names(
                known_parties=parties_from_case(case),
                texts=[data.text],
            )
            base_map = load_case_pii_mapping(case)
    else:
        parties = collect_all_party_names(known_parties=[], texts=[data.text], max_extra=8)

    masked = build_full_mask(
        data.text, parties=parties, structured=True, base_mapping=base_map
    )
    pii_map = masked.mapping
    text_for_llm = masked.text
    if case and pii_map:
        save_case_pii_mapping(db, case, pii_map)

    polished, provider = polish_dictation(text_for_llm, language=lang, source=source)
    if pii_map and polished:
        polished = unmask_text(polished, pii_map)

    if provider == "nonsense":
        log_audit(
            db,
            "dictation.polish",
            user=user,
            request=request,
            details=f"nonsense:{lang}",
        )
        db.commit()
        return PolishResponse(
            polished="",
            provider="nonsense",
            contradictions=[],
            guessed_words=[],
            edits=[],
            variables=[],
            structure_hints=[],
            law_suggestions=[],
            pii_masked=bool(pii_map),
            pii_summary=inventory_summary(pii_map),
        )
    if not polished:
        raise HTTPException(status_code=400, detail="نص فارغ / texte vide")
    alerts = detect_dictation_contradictions(polished, source=data.text)

    # Ne JAMAIS écraser ChatGPT à cause de missing_fact.
    # Noms : si tous les morceaux du nom sont encore dans le corrigé → pas d'alerte.
    filtered = []
    for a in alerts:
        if a.kind != "missing_fact":
            filtered.append(a)
            continue
        hard_vals = []
        pol_norm = re.sub(r"[‹›«»\s]+", " ", polished or "")
        for v in a.values or []:
            vv = (v or "").strip()
            if not vv:
                continue
            parts = [p for p in re.split(r"\s+", vv) if len(p) >= 2]
            if parts and all(p in pol_norm for p in parts):
                continue  # nom encore présent (éventuellement découpé / surligné)
            if re.search(r"\d", vv) or re.search(
                r"(درهم|DH|€|\$|ألف|مليون|بن\s|بنت\s|ابن\s)", vv, re.I
            ):
                hard_vals.append(vv)
        if hard_vals:
            a.values = hard_vals
            filtered.append(a)
    alerts = filtered
    contradictions = [
        ContradictionOut(
            kind=a.kind,
            values=a.values,
            message_ar=a.message_ar,
            message_fr=a.message_fr,
        )
        for a in alerts
    ]
    guessed = re.findall(r"‹([^›]{1,80})›", polished)
    from app.services.dictation_assist import build_assist_payload

    assist = build_assist_payload(data.text, polished)
    log_audit(
        db,
        "dictation.polish",
        user=user,
        request=request,
        details=f"{provider}:{lang}:c{len(contradictions)}:e{len(assist['edits'])}:pii{len(pii_map)}",
    )
    if charge_ai and provider not in ("fidelity", "local", "rules", "none", "nonsense"):
        spend_ai_action(db, user.cabinet_id, "polish")
    db.commit()
    return PolishResponse(
        polished=polished,
        provider=provider,
        contradictions=contradictions,
        guessed_words=guessed,
        edits=assist["edits"],
        variables=assist["variables"],
        structure_hints=assist["structure_hints"],
        law_suggestions=assist["law_suggestions"],
        pii_masked=bool(pii_map),
        pii_summary=inventory_summary(pii_map),
    )

@router.post("/clarify", response_model=ClarifyResponse)
def clarify_before_compose(
    data: ClarifyRequest,
    request: Request,
    user: User = Depends(require_roles(UserRole.AVOCAT, UserRole.ADMIN_CABINET)),
    db: Session = Depends(get_db),
):
    """Analyse anonymisée → QCM de clarification (0–5) avant rédaction."""
    check_rate_limit(request, key="dictation.clarify", limit=20, window_sec=60)
    from app.services.billing import begin_ai_action, finish_ai_action
    from app.services.plaidoirie_clarify import clarify_plaidoirie_from_case

    _ent, slot = begin_ai_action(db, user.cabinet_id, "clarify", request=request)
    lang = _norm_lang(data.language)
    ptype = data.plaidoirie_type
    if ptype and ptype not in PLAIDOIRIE_TYPES:
        ptype = "libre"
    result = clarify_plaidoirie_from_case(
        db,
        cabinet_id=user.cabinet_id,
        case_id=data.case_id,
        dictation_text=data.text.strip(),
        plaidoirie_type=ptype,
        language=lang,
        brief_posture=data.brief_posture,
        brief_jurisdiction=data.brief_jurisdiction,
    )
    log_audit(
        db,
        "dictation.clarify",
        user=user,
        request=request,
        details=f"q{len(result.get('questions') or [])}:{result.get('provider')}",
    )
    ok = str(result.get("provider") or "none") not in ("none", "")
    finish_ai_action(db, user.cabinet_id, "clarify", slot_token=slot, success=ok)
    db.commit()
    return ClarifyResponse(
        questions=[ClarifyQuestion(**q) for q in (result.get("questions") or [])],
        summary_fr=result.get("summary_fr") or "",
        summary_ar=result.get("summary_ar") or "",
        pieces_noted=int(result.get("pieces_noted") or 0),
        pii_tokens=list(result.get("pii_tokens") or []),
        provider=str(result.get("provider") or "none"),
    )


@router.post("/compose", response_model=ComposeResponse)
def compose_dictation_document(
    data: ComposeRequest,
    request: Request,
    user: User = Depends(require_roles(UserRole.AVOCAT, UserRole.ADMIN_CABINET)),
    db: Session = Depends(get_db),
):
    check_rate_limit(request, key="dictation.compose", limit=8, window_sec=60)
    from app.core.rate_limit import check_named_rate_limit
    from app.services.billing import begin_ai_action, finish_ai_action

    # Anti-abus : 20 compositions / heure / cabinet (en plus du quota mensuel).
    check_named_rate_limit(
        name=f"compose.cabinet:{user.cabinet_id}",
        limit=20,
        window_sec=3600,
    )
    _ent, slot = begin_ai_action(db, user.cabinet_id, "compose", request=request)
    try:
    lang = _norm_lang(data.language)
    source = data.text.strip()
    polished = None
    if data.polish_first:
        polished, _ = polish_dictation(source, language=lang)
        source = polished or source

    city = None
    cabinet_name = None
    if user.cabinet:
        cabinet_name = user.cabinet.name
        city = getattr(user.cabinet, "city", None)

    ptype = data.plaidoirie_type
    if data.doc_type == "plaidoirie" and ptype and ptype not in PLAIDOIRIE_TYPES:
            ptype = "libre"

        if data.doc_type == "plaidoirie" and not (data.case_id or "").strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un dossier est obligatoire : liez l’affaire avant la rédaction IA.",
            )

        pii_masked = False
        case_enriched = False
        if data.doc_type == "plaidoirie" and data.case_id:
            from app.services.plaidoirie_case_compose import compose_plaidoirie_from_case

            title, body, provider, checks, pii_masked = compose_plaidoirie_from_case(
                db,
                cabinet_id=user.cabinet_id,
                case_id=data.case_id,
                dictation_text=source,
                plaidoirie_type=ptype,
                title=data.title,
                language=lang,
                brief_posture=data.brief_posture,
                brief_jurisdiction=data.brief_jurisdiction,
                clarifications=data.clarifications,
            )
            case_enriched = True
            polished = polished or source
        else:
    title, body, provider, checks = compose_official_document(
        source,
        doc_type=data.doc_type,
        title=data.title,
        city=city,
        cabinet_name=cabinet_name,
        plaidoirie_type=ptype,
        language=lang,
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
        details=f"{data.doc_type}:{ptype or '-'}:{lang}",
    )
        finish_ai_action(db, user.cabinet_id, "compose", slot_token=slot, success=True)
    db.commit()
    return ComposeResponse(
        title=title,
        body=body,
        polished=polished,
        provider=provider,
        checks=checks,
        plaidoirie_type=ptype,
        language=lang,
            pii_masked=pii_masked,
            case_enriched=case_enriched,
        )
    except Exception:
        finish_ai_action(db, user.cabinet_id, "compose", slot_token=slot, success=False)
        db.rollback()
        raise


class ReviseRequest(BaseModel):
    title: str = Field("", max_length=500)
    body: str = Field(..., min_length=40, max_length=120000)
    instruction: str = Field(..., min_length=3, max_length=4000)
    case_id: str | None = Field(None, max_length=64)
    language: str = Field("ar", pattern="^(ar|fr|AR|FR)$")


class ReviseResponse(BaseModel):
    title: str
    body: str
    provider: str
    reply: str = ""


@router.post("/revise", response_model=ReviseResponse)
def revise_plaidoirie(
    data: ReviseRequest,
    request: Request,
    user: User = Depends(require_roles(UserRole.AVOCAT, UserRole.ADMIN_CABINET)),
    db: Session = Depends(get_db),
):
    """Après rédaction : demander à l’IA d’ajouter / modifier un point précis."""
    check_rate_limit(request, key="dictation.revise", limit=12, window_sec=60)
    from app.core.rate_limit import check_named_rate_limit
    from app.services.plaidoirie_revise import revise_plaidoirie_body

    check_named_rate_limit(
        name=f"revise.cabinet:{user.cabinet_id}",
        limit=30,
        window_sec=3600,
    )
    from app.services.billing import begin_ai_action, finish_ai_action

    _ent, slot = begin_ai_action(db, user.cabinet_id, "revise", request=request)
    try:
        title, body, provider, reply = revise_plaidoirie_body(
            db,
            cabinet_id=user.cabinet_id,
            case_id=data.case_id,
            title=data.title,
            body=data.body,
            instruction=data.instruction,
            language=_norm_lang(data.language),
            skip_quota_assert=True,
        )
        log_audit(
            db,
            "dictation.revise",
            user=user,
            request=request,
            details=(data.instruction or "")[:120],
        )
        finish_ai_action(db, user.cabinet_id, "revise", slot_token=slot, success=True)
        db.commit()
        return ReviseResponse(title=title, body=body, provider=provider, reply=reply or "")
    except Exception:
        finish_ai_action(db, user.cabinet_id, "revise", slot_token=slot, success=False)
        db.rollback()
        raise
