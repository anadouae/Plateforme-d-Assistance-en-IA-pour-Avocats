"""Génération d'une clé de barre à partir des pièces d'un dossier (avec PII masking)."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Case, Document, DocumentStatus
from app.services.billing import (
    FEATURE_PII,
    assert_can_use_cle_de_barre,
    get_entitlements,
    increment_cle_usage,
)
from app.services.free_llm_router import chat_free_tier
from app.services.pii_mask import build_mask_from_parties, unmask_text

logger = logging.getLogger(__name__)

SYSTEM_CLE = (
    "Tu es un assistant juridique marocain spécialisé dans la préparation de clés de barre "
    "(fiche orale d'audience) pour les tribunaux du Royaume du Maroc.\n\n"
    "Règles strictes :\n"
    "- N'invente JAMAIS de faits, dates, montants ou articles absents du dossier.\n"
    "- Réponds dans UNE seule langue : français si le dossier est surtout en français, arabe sinon. Ne mélange pas.\n"
    "- Pas de Markdown (pas d'étoiles **, pas de #, pas de listes à puces crues). Titres en capitales simples : FAITS / MOYENS / DEMANDES / POINTS D'AUDIENCE.\n"
    "- Style : phrases courtes, prêtes à être lues à l'audience.\n"
    "- L'avocat reste seul responsable du fond ; tu proposes une trame.\n"
    "- Termine par : « Ceci ne constitue pas un avis juridique. »"
)


def _collect_case_text(db: Session, case: Case, *, max_chars: int = 24000) -> tuple[str, list[str]]:
    docs = (
        db.query(Document)
        .filter(
            Document.case_id == case.id,
            Document.cabinet_id == case.cabinet_id,
            Document.status == DocumentStatus.INDEXED,
        )
        .order_by(Document.created_at.desc())
        .limit(20)
        .all()
    )
    parts: list[str] = []
    parties: list[str] = []
    if case.client_name:
        parties.append(case.client_name)
    total = 0
    for d in docs:
        chunk = (d.extracted_text or "").strip()
        if not chunk:
            continue
        header = f"--- Pièce : {d.original_name or d.filename} ---\n"
        piece = header + chunk[:8000]
        if total + len(piece) > max_chars:
            remain = max_chars - total
            if remain > 500:
                parts.append(piece[:remain])
            break
        parts.append(piece)
        total += len(piece)
    return "\n\n".join(parts), parties


def generate_cle_de_barre(
    db: Session,
    *,
    cabinet_id: str,
    case_id: str,
    extra_instructions: str | None = None,
    skip_spend: bool = False,
) -> dict[str, Any]:
    if not skip_spend:
        assert_can_use_cle_de_barre(db, cabinet_id)
    ent = get_entitlements(db, cabinet_id)

    case = (
        db.query(Case).filter(Case.id == case_id, Case.cabinet_id == cabinet_id).first()
    )
    if not case:
        raise HTTPException(status_code=404, detail="Dossier introuvable")

    raw_text, parties = _collect_case_text(db, case)
    if not raw_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Aucune pièce extractible dans ce dossier. Uploadez des documents d'abord.",
        )

    use_pii = ent.has(FEATURE_PII)
    mapping: dict[str, str] = {}
    dossier_for_llm = raw_text
    if use_pii:
        masked = build_mask_from_parties(raw_text, parties=parties)
        dossier_for_llm = masked.text
        mapping = masked.mapping

    prompt = (
        f"Dossier référence : {case.reference}\n"
        f"Type : {case.case_type}\n"
        f"Client : {'(anonymisé — voir PARTIE_*)' if mapping else case.client_name}\n\n"
        f"Pièces :\n{dossier_for_llm}\n"
    )
    if extra_instructions:
        prompt += f"\nInstructions avocat : {extra_instructions.strip()}\n"

    preferred = "openai"
    text, provider = chat_free_tier(
        prompt,
        SYSTEM_CLE,
        preferred=preferred,
        max_tokens=3500,
        temperature=0.2,
    )
    if not text:
        raise HTTPException(status_code=503, detail="IA indisponible pour la clé de barre.")

    content = text
    if use_pii and mapping:
        content = unmask_text(content, mapping)

    if not skip_spend:
        increment_cle_usage(db, cabinet_id)

    return {
        "case_id": case.id,
        "reference": case.reference,
        "cle_de_barre": content,
        "pii_masked": use_pii,
        "parties_tokens": mapping,
        "provider": provider,
        "model_premium": True,
    }
