"""Génération d'une clé de barre à partir des pièces d'un dossier (avec PII masking)."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Case, Document, DocumentStatus
from app.services.billing import (
    assert_can_use_cle_de_barre,
    increment_cle_usage,
)
from app.services.free_llm_router import chat_free_tier
from app.services.language import normalize_locale
from app.services.pii_mask import build_full_mask, unmask_text
from app.services.pii_store import load_case_pii_mapping, save_case_pii_mapping

logger = logging.getLogger(__name__)


def _system_cle(locale: str) -> str:
    if locale == "ar":
        return (
            "أنت مساعد قانوني مغربي لإعداد مذكرة المرافعة الشفهية (clé de barre).\n"
            "قواعد:\n"
            "- لا تختلق وقائع أو تواريخ أو مبالغ أو فصول غير موجودة في الملف.\n"
            "- أجب بالعربية الفصحى فقط — حتى لو كانت الوثائق بالفرنسية.\n"
            "- استخدم Markdown الواضح:\n"
            "## الوقائع\n## الوسائل\n## الطلبات\n## نقاط الجلسة\n"
            "- قوائم مرقمة 1. 2. 3. و**كلمات مهمة بالخط العريض** (أسماء، مبالغ، تواريخ، فصول).\n"
            "- فقرات قصيرة — ممنوع جدار نص.\n"
            "- اختم بـ: « هذا لا يشكل استشارة قانونية. »"
        )
    return (
        "Tu es un assistant juridique marocain spécialisé dans la préparation de clés de barre "
        "(fiche orale d'audience) pour les tribunaux du Royaume du Maroc.\n\n"
        "Règles strictes :\n"
        "- N'invente JAMAIS de faits, dates, montants ou articles absents du dossier.\n"
        "- Réponds UNIQUEMENT en français.\n"
        "- Markdown OBLIGATOIRE, clair et lisible :\n"
        "## FAITS\n## MOYENS\n## DEMANDES\n## POINTS D'AUDIENCE\n"
        "- Listes numérotées (1. 2. 3.), **gras** pour noms / montants / dates / articles.\n"
        "- Phrases courtes, prêtes à être lues à l'audience — jamais un mur de texte.\n"
        "- L'avocat reste seul responsable du fond.\n"
        "- Termine par : « Ceci ne constitue pas un avis juridique. »"
    )


def _collect_case_text(db: Session, case: Case, *, max_chars: int = 28000) -> tuple[str, list[str]]:
    docs = (
        db.query(Document)
        .filter(
            Document.case_id == case.id,
            Document.cabinet_id == case.cabinet_id,
            Document.status == DocumentStatus.INDEXED,
        )
        .order_by(Document.created_at.desc())
        .limit(25)
        .all()
    )
    # Inclure aussi les pièces extractibles non encore INDEXED
    if len(docs) < 5:
        extra = (
            db.query(Document)
            .filter(
                Document.case_id == case.id,
                Document.cabinet_id == case.cabinet_id,
            )
            .order_by(Document.created_at.desc())
            .limit(25)
            .all()
        )
        seen = {d.id for d in docs}
        for d in extra:
            if d.id not in seen and (d.extracted_text or "").strip():
                docs.append(d)
                seen.add(d.id)

    parts: list[str] = []
    parties: list[str] = []
    if case.client_name:
        parties.append(case.client_name)
    if getattr(case, "opposing_name", None):
        parties.append(case.opposing_name or "")
    total = 0
    for d in docs:
        chunk = (d.extracted_text or "").strip()
        if not chunk:
            continue
        header = f"--- Pièce : {d.original_name or d.filename} ---\n"
        piece = header + chunk[:9000]
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
    language: str | None = None,
    skip_spend: bool = False,
) -> dict[str, Any]:
    if not skip_spend:
        assert_can_use_cle_de_barre(db, cabinet_id)

    case = (
        db.query(Case).filter(Case.id == case_id, Case.cabinet_id == cabinet_id).first()
    )
    if not case:
        raise HTTPException(status_code=404, detail="Dossier introuvable")

    locale = normalize_locale(language)
    raw_text, parties = _collect_case_text(db, case)
    if not raw_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Aucune pièce extractible dans ce dossier. Uploadez des documents d'abord.",
        )

    mapping: dict[str, str] = {}
    base_map = load_case_pii_mapping(case)
    masked = build_full_mask(
        raw_text, parties=parties, structured=True, base_mapping=base_map
    )
    dossier_for_llm = masked.text
    mapping = masked.mapping
    if mapping:
        save_case_pii_mapping(db, case, mapping)

    if locale == "ar":
        meta = (
            f"المرجع : {case.reference}\n"
            f"العنوان : {getattr(case, 'title', None) or '—'}\n"
            f"النوع : {case.case_type}\n"
            f"المحكمة / الغرفة : {getattr(case, 'tribunal', None) or '—'} / {getattr(case, 'chamber', None) or '—'}\n"
            f"رقم الملف : {getattr(case, 'court_file_number', None) or '—'}\n"
            f"الموكل : {'(مجهول)' if mapping else (case.client_name or '—')}\n"
            f"الخصم : {'(مجهول)' if mapping else (getattr(case, 'opposing_name', None) or '—')}\n"
        )
        prompt = (
            f"{meta}\n"
            f"وثائق الملف :\n{dossier_for_llm}\n\n"
            "اكتب مذكرة المرافعة الشفهية (clé de barre) كاملة ومنظمة بصيغة Markdown. "
            "استخدم كل الوثائق ذات الصلة. "
            "أجب بالعربية فقط حتى لو كانت الوثائق بالفرنسية."
        )
        if extra_instructions:
            prompt += f"\nتعليمات المحامي : {extra_instructions.strip()}\n"
    else:
        meta = (
            f"Référence : {case.reference}\n"
            f"Titre : {getattr(case, 'title', None) or '—'}\n"
            f"Type : {case.case_type}\n"
            f"Tribunal / chambre : {getattr(case, 'tribunal', None) or '—'} / {getattr(case, 'chamber', None) or '—'}\n"
            f"N° greffe : {getattr(case, 'court_file_number', None) or '—'}\n"
            f"Client : {'(anonymisé)' if mapping else (case.client_name or '—')}\n"
            f"Adverse : {'(anonymisé)' if mapping else (getattr(case, 'opposing_name', None) or '—')}\n"
        )
        prompt = (
            f"{meta}\n"
            f"Pièces du dossier :\n{dossier_for_llm}\n\n"
            "Rédige la clé de barre complète et structurée (Markdown). "
            "Utilise TOUTES les pièces pertinentes (contrat, licenciement, paie, PV, expertise…). "
            "Réponds UNIQUEMENT en français."
        )
        if extra_instructions:
            prompt += f"\nInstructions avocat : {extra_instructions.strip()}\n"

    text, provider = chat_free_tier(
        prompt,
        _system_cle(locale),
        preferred="openai",
        strict_preferred=True,
        allow_ollama=False,
        max_tokens=4000,
        temperature=0.25,
    )
    if not text:
        raise HTTPException(status_code=503, detail="IA indisponible pour la clé de barre.")

    content = text
    if mapping:
        content = unmask_text(content, mapping)

    if not skip_spend:
        increment_cle_usage(db, cabinet_id)

    return {
        "case_id": case.id,
        "reference": case.reference,
        "cle_de_barre": content,
        "pii_masked": bool(mapping),
        "parties_tokens": mapping,
        "provider": provider,
        "language": locale,
        "model_premium": True,
    }
