"""Endpoint de synthèse (Mistral cloud / Ollama) — mode dégradé si offline."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, log_audit
from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import check_rate_limit
from app.models import Document, User, UserRole
from app.services.ollama_summarize import ollama_available, summarize_long

router = APIRouter(prefix="/api/summarize", tags=["summarize"])


class SummarizeRequest(BaseModel):
    text: str = Field(..., min_length=20, max_length=100_000)
    document_id: str | None = None


class SummarizeResponse(BaseModel):
    summary: str
    provider: str
    model: str
    degraded: bool = False


class DocumentSummarizeResponse(SummarizeResponse):
    document_id: str
    document_name: str
    extracted_preview: str | None = None


def _any_provider() -> bool:
    return bool(settings.MISTRAL_API_KEY) or ollama_available()


@router.post("", response_model=SummarizeResponse)
def summarize_raw(
    data: SummarizeRequest,
    request: Request,
    user: User = Depends(get_current_user),
):
    if user.role == UserRole.ASSISTANT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas l'autorisation d'accéder à la synthèse IA.",
        )
    check_rate_limit(request, key="summarize", limit=20, window_sec=60)

    if not _any_provider():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Aucun moteur de synthèse disponible (Mistral API ou Ollama).",
        )

    summary, provider, model = summarize_long(data.text)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Synthèse indisponible. Vérifiez la clé Mistral ou Ollama.",
        )
    return SummarizeResponse(
        summary=summary,
        provider=provider,
        model=model,
        degraded=False,
    )


@router.post("/document/{doc_id}", response_model=DocumentSummarizeResponse)
def summarize_document(
    doc_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role == UserRole.ASSISTANT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas l'autorisation d'accéder à la synthèse IA.",
        )
    check_rate_limit(request, key="summarize", limit=20, window_sec=60)

    doc = (
        db.query(Document)
        .filter(Document.id == doc_id, Document.cabinet_id == user.cabinet_id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document introuvable")

    text = (doc.extracted_text or "").strip()
    preview = text[:2000] if text else None
    if len(text) < 20:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Pas assez de texte extrait. Lancez l'OCR / extraction avant la synthèse.",
        )

    if not _any_provider():
        degraded_summary = (
            "## Synthèse (mode dégradé)\n\n"
            "Aucun moteur IA disponible. Extrait OCR :\n\n"
            f"{text[:1500]}…"
        )
        log_audit(db, "document.summarize_degraded", user=user, request=request, details=doc.original_name)
        db.commit()
        return DocumentSummarizeResponse(
            document_id=doc.id,
            document_name=doc.original_name,
            summary=degraded_summary,
            provider="none",
            model="",
            degraded=True,
            extracted_preview=preview,
        )

    summary, provider, model = summarize_long(text)
    if not summary:
        degraded_summary = (
            "## Synthèse (mode dégradé)\n\n"
            f"Le modèle n'a pas répondu. Extrait OCR :\n\n{text[:1500]}…"
        )
        return DocumentSummarizeResponse(
            document_id=doc.id,
            document_name=doc.original_name,
            summary=degraded_summary,
            provider="none",
            model=model,
            degraded=True,
            extracted_preview=preview,
        )

    log_audit(db, "document.summarize", user=user, request=request, details=doc.original_name)
    db.commit()
    return DocumentSummarizeResponse(
        document_id=doc.id,
        document_name=doc.original_name,
        summary=summary,
        provider=provider,
        model=model,
        degraded=False,
        extracted_preview=preview,
    )
