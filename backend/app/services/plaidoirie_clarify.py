"""Clarification QCM avant rédaction — questions ciblées après analyse anonymisée."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Case
from app.services.cle_de_barre import _collect_case_text
from app.services.free_llm_router import chat_free_tier
from app.services.pii_mask import (
    collect_all_party_names,
    mask_corpus,
    party_tokens_legend,
)
from app.services.plaidoirie_prompt import PLAIDOIRIE_TYPES

logger = logging.getLogger(__name__)

CLARIFY_SYSTEM = """Tu es un assistant juridique marocain. Tu as lu un dossier ANOYME (PARTIE_A…).
Ta mission : poser au maximum 5 questions à choix multiples pour lever les ambiguïtés
avant de rédiger la plaidoirie. Ne répète pas ce qui est déjà clair.

Règles :
- Questions courtes, concrètes, basées UNIQUEMENT sur le dossier / pièces / dictée.
- Chaque question a 2 à 4 options tirées du contenu (pas inventées hors contexte).
- Toujours permettre une option « autre » côté client (allow_other=true).
- Conserve les jetons PARTIE_* tels quels — n'invente aucun nom propre.
- Si tout est clair : retourne {"questions": []}.

Réponds UNIQUEMENT en JSON valide :
{
  "questions": [
    {
      "id": "q1",
      "prompt_ar": "...",
      "prompt_fr": "...",
      "options": [
        {"id": "a", "label_ar": "...", "label_fr": "..."},
        {"id": "b", "label_ar": "...", "label_fr": "..."}
      ],
      "allow_other": true
    }
  ],
  "summary_ar": "جملة قصيرة عما فهمته",
  "summary_fr": "Une phrase sur ce que tu as compris",
  "pieces_noted": 0
}
"""


def _strip_json_fence(raw: str) -> str:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _parse_clarify_json(raw: str) -> dict[str, Any]:
    text = _strip_json_fence(raw)
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    # Tentative extraction du premier objet {…}
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try:
            data = json.loads(m.group(0))
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
    return {"questions": [], "summary_fr": "", "summary_ar": "", "pieces_noted": 0}


def prepare_masked_case_context(
    db: Session,
    *,
    cabinet_id: str,
    case_id: str,
    dictation_text: str,
) -> tuple[Case, str, str, dict[str, str], int]:
    """
    Retourne (case, dossier_masked, dictation_masked, mapping, n_pieces).
    """
    # Import local pour éviter le cycle compose ↔ clarify
    from app.services.plaidoirie_case_compose import _case_parties

    case = db.query(Case).filter(Case.id == case_id, Case.cabinet_id == cabinet_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Dossier introuvable")

    raw_docs, _ = _collect_case_text(db, case)
    known = _case_parties(case)
    parties = collect_all_party_names(
        known_parties=known,
        texts=[raw_docs, dictation_text or ""],
    )
    n_pieces = raw_docs.count("--- Pièce") if raw_docs else 0
    from app.services.pii_store import load_case_pii_mapping, save_case_pii_mapping

    base_map = load_case_pii_mapping(case)
    masked_list, mapping = mask_corpus(
        raw_docs,
        (dictation_text or "").strip(),
        parties=parties,
        structured=True,
        base_mapping=base_map,
    )
    if mapping:
        save_case_pii_mapping(db, case, mapping)
    return case, masked_list[0], masked_list[1], mapping, n_pieces


def clarify_plaidoirie_from_case(
    db: Session,
    *,
    cabinet_id: str,
    case_id: str,
    dictation_text: str,
    plaidoirie_type: str | None = None,
    language: str = "ar",
    brief_posture: str | None = None,
    brief_jurisdiction: str | None = None,
) -> dict[str, Any]:
    """Analyse anonymisée → questions QCM (max 5)."""
    from app.services.plaidoirie_case_compose import _legal_identity_block

    case, dossier_block, dictation_block, mapping, n_pieces = prepare_masked_case_context(
        db,
        cabinet_id=cabinet_id,
        case_id=case_id,
        dictation_text=dictation_text,
    )

    type_id = (plaidoirie_type or "libre").strip()
    if type_id not in PLAIDOIRIE_TYPES:
        type_id = "libre"

    prompt_parts = [
        _legal_identity_block(case, masked=bool(mapping)),
        f"Type d'acte / plaidoirie : {PLAIDOIRIE_TYPES[type_id]} ({type_id})",
        f"Langue UI : {'arabe' if language == 'ar' else 'français'}",
    ]
    if mapping:
        prompt_parts.append(party_tokens_legend(mapping))
    if brief_posture:
        prompt_parts.append(f"Rôle avocat : {brief_posture}")
    if brief_jurisdiction:
        prompt_parts.append(f"Juridiction : {brief_jurisdiction}")
    if dossier_block.strip():
        prompt_parts.append(f"\n=== Pièces (anonymisées) ===\n{dossier_block[:14000]}")
    else:
        prompt_parts.append("\n(Pas de pièce indexée.)")
    prompt_parts.append(f"\n=== Dictée (anonymisée) ===\n{dictation_block[:8000]}\n")
    prompt_parts.append(
        "Génère le JSON de clarification (0 à 5 questions). "
        f"pieces_noted doit être environ {n_pieces}."
    )

    preferred = "openai"
    raw, provider = chat_free_tier(
        "\n".join(prompt_parts),
        CLARIFY_SYSTEM,
        preferred=preferred,
        max_tokens=1800,
        temperature=0.2,
    )
    if not raw:
        # Pas bloquant : rédaction possible sans QCM
        return {
            "questions": [],
            "summary_fr": "Analyse indisponible — vous pouvez rédiger directement.",
            "summary_ar": "التحليل غير متاح — يمكنكم الصياغة مباشرة.",
            "pieces_noted": n_pieces,
            "pii_tokens": list(mapping.keys()),
            "provider": "none",
        }

    data = _parse_clarify_json(raw)
    questions_raw = data.get("questions") or []
    questions: list[dict[str, Any]] = []
    for i, q in enumerate(questions_raw[:5]):
        if not isinstance(q, dict):
            continue
        opts = q.get("options") or []
        clean_opts = []
        for j, o in enumerate(opts[:4]):
            if not isinstance(o, dict):
                continue
            oid = str(o.get("id") or chr(ord("a") + j))
            clean_opts.append(
                {
                    "id": oid,
                    "label_ar": str(o.get("label_ar") or o.get("label_fr") or oid)[:200],
                    "label_fr": str(o.get("label_fr") or o.get("label_ar") or oid)[:200],
                }
            )
        if len(clean_opts) < 2:
            continue
        questions.append(
            {
                "id": str(q.get("id") or f"q{i + 1}")[:40],
                "prompt_ar": str(q.get("prompt_ar") or q.get("prompt_fr") or "")[:400],
                "prompt_fr": str(q.get("prompt_fr") or q.get("prompt_ar") or "")[:400],
                "options": clean_opts,
                "allow_other": bool(q.get("allow_other", True)),
            }
        )

    return {
        "questions": questions,
        "summary_fr": str(data.get("summary_fr") or "")[:400],
        "summary_ar": str(data.get("summary_ar") or "")[:400],
        "pieces_noted": int(data.get("pieces_noted") or n_pieces),
        "pii_tokens": list(mapping.keys()),
        "provider": provider,
    }


def format_clarifications_block(
    clarifications: list[dict[str, Any]] | None,
) -> str:
    if not clarifications:
        return ""
    lines = ["=== Clarifications confirmées par l'avocat ==="]
    for c in clarifications:
        qid = str(c.get("id") or "")
        choice = str(c.get("choice") or c.get("label") or "").strip()
        other = str(c.get("other") or "").strip()
        if other:
            lines.append(f"- {qid}: Autre — {other}")
        elif choice:
            lines.append(f"- {qid}: {choice}")
    return "\n".join(lines) if len(lines) > 1 else ""
