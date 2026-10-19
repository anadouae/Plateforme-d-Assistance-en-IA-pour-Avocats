"""Plaidoirie : dossier + pièces + dictée → rédaction IA (PII masqué avant envoi).

Confidentialité cabinet (toujours) :
1) Collecte identité juridique + pièces + dictée
2) Remplace les vrais noms par PARTIE_A / PARTIE_B…
3) Envoie à l'IA (OpenAI prioritaire si clé)
4) Restaure les noms dans le document final
"""

from __future__ import annotations

import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Case
from app.services.cle_de_barre import _collect_case_text
from app.services.free_llm_router import chat_free_tier
from app.services.pii_mask import (
    build_full_mask,
    build_mask_from_parties,
    collect_all_party_names,
    party_tokens_legend,
    unmask_text,
)
from app.services.pii_store import load_case_pii_mapping, save_case_pii_mapping
from app.services.plaidoirie_postprocess import postprocess_plaidoirie_body
from app.services.plaidoirie_prompt import PLAIDOIRIE_AGENT_SYSTEM, PLAIDOIRIE_TYPES

logger = logging.getLogger(__name__)

_QUALITY_FR = {
    "personne_physique": "personne physique (individu)",
    "personne_morale": "personne morale (société / association)",
    "administration": "administration / État",
}

_DEGREE_FR = {
    "premiere_instance": "première instance",
    "appel": "appel",
    "cassation": "cassation",
    "refere": "référé (urgence)",
}

_TRIBUNAL_FR = {
    "tpi": "Tribunal de première instance",
    "commerce": "Tribunal de commerce",
    "admin": "Tribunal administratif",
    "social": "Tribunal social",
    "appel": "Cour d'appel",
    "cassation": "Cour de cassation",
}

_ROLE_FR = {
    "demandeur": "demandeur",
    "defendeur": "défendeur",
    "partie_civile": "partie civile (victime)",
    "prevenu": "prévenu / accusé",
    "requerant": "requérant",
    "salarie": "salarié demandeur",
    "employeur": "employeur défendeur",
}


def _parse_title_body_checks(raw: str, fallback_title: str) -> tuple[str, str, list[str]]:
    title = fallback_title
    body = raw.strip()
    checks: list[str] = []
    if "TITLE:" in raw and "BODY:" in raw:
        try:
            after_title = raw.split("TITLE:", 1)[1]
            title_part, rest = after_title.split("BODY:", 1)
            title = title_part.strip().split("\n")[0].strip() or fallback_title
            if "CHECKS:" in rest:
                body_part, checks_part = rest.split("CHECKS:", 1)
                body = body_part.strip()
                checks = [
                    ln.strip().lstrip("-•").strip()
                    for ln in checks_part.strip().splitlines()
                    if ln.strip() and ln.strip() not in ("-", "•")
                ]
            else:
                body = rest.strip()
        except Exception:
            body = raw.strip()
    return title, body, checks


def _case_parties(case: Case) -> list[str]:
    """Noms à masquer : client + adverse (+ éventuels aliases)."""
    parties: list[str] = []
    for n in (case.client_name, getattr(case, "opposing_name", None)):
        name = (n or "").strip()
        if name and name not in parties:
            parties.append(name)
    return parties


def _legal_identity_block(case: Case, *, masked: bool) -> str:
    """Contexte juridique structuré pour l'IA (sans renvoyer les vrais noms si masked)."""
    client_label = "PARTIE_A (client du cabinet)" if masked else (case.client_name or "—")
    adverse_label = "PARTIE_B (partie adverse)" if masked and (case.opposing_name or "").strip() else (
        (case.opposing_name or "").strip() or "—"
    )
    degree = _DEGREE_FR.get(case.jurisdiction_degree or "", case.jurisdiction_degree or "—")
    tribunal = _TRIBUNAL_FR.get(case.tribunal or "", case.tribunal or "—")
    role = _ROLE_FR.get(case.client_role or "", case.client_role or "—")
    cq = _QUALITY_FR.get(case.client_quality or "", case.client_quality or "—")
    oq = _QUALITY_FR.get(case.opposing_quality or "", case.opposing_quality or "—")
    lines = [
        "=== Identité juridique du dossier ===",
        f"Référence cabinet : {case.reference}",
        f"Matière : {case.case_type or '—'}",
        f"Degré de juridiction : {degree}",
        f"Tribunal compétent : {tribunal}",
    ]
    city = (getattr(case, "court_city", None) or "").strip()
    if city:
        lines.append(f"Ville du tribunal : {city}")
    rg = (getattr(case, "court_file_number", None) or "").strip()
    if rg:
        lines.append(f"N° de rôle / RG : {rg}")
    chamber = (getattr(case, "chamber", None) or "").strip()
    if chamber:
        lines.append(f"Chambre : {chamber}")
    greffe = (getattr(case, "greffe", None) or "").strip()
    if greffe:
        lines.append(f"Greffe : {greffe}")
    judge = (getattr(case, "judge_name", None) or "").strip()
    if judge:
        lines.append(f"Juge / magistrat : {judge}")
    proc = (getattr(case, "procedure_status", None) or "").strip()
    if proc:
        lines.append(f"Statut procédural : {proc}")
    lines.extend(
        [
            f"Client du cabinet : {client_label}",
            f"  — Rôle procédural : {role}",
            f"  — Nature juridique : {cq}",
        ]
    )
    if (case.client_domicile or "").strip() and not masked:
        lines.append(f"  — Domicile / siège : {case.client_domicile.strip()}")
    elif (case.client_domicile or "").strip() and masked:
        lines.append("  — Domicile / siège : (fourni, conservé hors prompt nominatif)")
    lines.append(f"Partie adverse : {adverse_label}")
    lines.append(f"  — Nature juridique : {oq}")
    if case.description:
        lines.append(f"Notes dossier : {(case.description or '')[:800]}")
    return "\n".join(lines)


def compose_plaidoirie_from_case(
    db: Session,
    *,
    cabinet_id: str,
    case_id: str,
    dictation_text: str,
    plaidoirie_type: str | None,
    title: str | None,
    language: str = "ar",
    brief_posture: str | None = None,
    brief_jurisdiction: str | None = None,
    clarifications: list[dict] | None = None,
) -> tuple[str, str, str, list[str], bool]:
    """
    Analyse dossier + pièces + identité juridique + dictée avocat → plaidoirie.
    Retourne (title, body, provider, checks, pii_masked).
    """
    case = db.query(Case).filter(Case.id == case_id, Case.cabinet_id == cabinet_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Dossier introuvable")

    raw_docs, _ = _collect_case_text(db, case)
    known = _case_parties(case)
    parties = collect_all_party_names(
        known_parties=known,
        texts=[raw_docs, dictation_text or ""],
    )

    # Confidentialité produit : toujours pseudonymiser avant IA cloud
    base_map = load_case_pii_mapping(case)
    mapping: dict[str, str] = {}
    dossier_block = raw_docs
    dictation_block = (dictation_text or "").strip()
    use_pii = True

    masked_docs = build_full_mask(
        dossier_block, parties=parties, structured=True, base_mapping=base_map
    )
    masked_dict = build_full_mask(
        dictation_block, parties=parties, structured=True, base_mapping=masked_docs.mapping
    )
    dossier_block = masked_docs.text
    dictation_block = masked_dict.text
    mapping = masked_dict.mapping
    if mapping:
        save_case_pii_mapping(db, case, mapping)
        logger.info(
            "PII mask case=%s tokens=%s parties=%d",
            case.reference,
            list(mapping.keys()),
            len(parties),
        )

    type_id = (plaidoirie_type or "libre").strip()
    if type_id not in PLAIDOIRIE_TYPES:
        type_id = "libre"
    type_label = PLAIDOIRIE_TYPES[type_id]
    hint_title = (title or "").strip() or f"مرافعة — {case.reference}"

    system = PLAIDOIRIE_AGENT_SYSTEM.format(type_label=type_label, type_id=type_id)
    system += (
        "\n\n=== Confidentialité ===\n"
        "Les parties apparaissent comme PARTIE_A, PARTIE_B… "
        "CIN_* = carte nationale, TEL_* = téléphone, EMAIL_* = e-mail. "
        "Conserve ces jetons tels quels dans BODY. N'invente aucun nom propre ni numéro réel.\n"
        "Utilise l'identité juridique (degré, tribunal, N° RG, greffe, chambre, rôles, "
        "nature personne physique/morale) pour cadrer l'acte — sans inventer de faits "
        "absents de la dictée ou des pièces.\n"
        "Cite OBLIGATOIREMENT dans le corps : tribunal compétent, N° RG (s'il est fourni), "
        "référence dossier, et les parties (via jetons).\n"
        "Si des clarifications avocat sont fournies : respecte-les strictement.\n"
        "Mode rédaction pro : arabe fusḥā uniquement dans BODY/TITLE ; "
        "rephrase professionnel autorisé ; interdiction de laisser des phrases françaises "
        "au milieu du texte arabe (sauf noms propres latins).\n"
        "Rédige une plaidoirie EXHAUSTIVE de niveau barreau (أطراف، وقائع مفصّلة، مناقشة قانونية "
        "مع حجج ومواد عند توفرها، ملتمسات مفصّلة).\n"
        "INTERDIT : résumé de 3–10 lignes ; INTERDIT : sections vides ou génériques ; "
        "INTERDIT : redondance (même idée répétée).\n"
        "Même si la dictée est courte : développe à partir des pièces (montants, dates, "
        "qualités, demandes) pour produire une مرافعة complète digne d'audience.\n"
        "Forme barreau marocain : titres numérotés (أولاً / ثانياً…), citations d'articles "
        "uniquement si présentes ou clairement déductibles des pièces (sinon CHECKS).\n"
        "Longueur cible BODY : au moins 1200–2500 mots si les pièces le permettent ; "
        "minimum 600 mots même avec dictée courte.\n"
    )

    dictation_len = len(dictation_block.strip())
    short_dictation = dictation_len < 280

    prompt_parts = [
        _legal_identity_block(case, masked=use_pii),
        "Langue cible OBLIGATOIRE : arabe fusḥā juridique uniquement (TITLE + BODY).",
        "Si le titre / client / objet du dossier est en français : reformule-le en arabe dans TITLE et dans le corps.",
    ]
    if mapping:
        prompt_parts.append(party_tokens_legend(mapping))
    if brief_posture:
        prompt_parts.append(f"Rôle de l'avocat à l'audience : {brief_posture}")
    if brief_jurisdiction:
        prompt_parts.append(f"Juridiction (rappel) : {brief_jurisdiction}")
    if clarifications:
        from app.services.plaidoirie_clarify import format_clarifications_block

        block = format_clarifications_block(clarifications)
        if block:
            prompt_parts.append(block)
    if dossier_block.strip():
        prompt_parts.append(
            f"\n=== Pièces du dossier (OCR / texte indexé — anonymisées) ===\n{dossier_block[:28000]}"
        )
    else:
        prompt_parts.append("\n(Pas de pièce indexée — base-toi sur la dictée + fiche dossier.)")

    prompt_parts.append(f"\n=== Dictée de l'avocat (source principale des faits) ===\n{dictation_block}\n")
    if short_dictation:
        prompt_parts.append(
            "\n=== Mode dictée courte ===\n"
            "La dictée est brève : tu dois quand même produire une plaidoirie complète "
            "en exploitant au maximum les pièces et la fiche juridique. "
            "Ne te limite pas à paraphraser la phrase dictée.\n"
        )
    prompt_parts.append(
        "Produis une plaidoirie professionnelle marocaine au format TITLE / BODY / CHECKS.\n"
        "Sources autorisées UNIQUEMENT : dictée + pièces + fiche juridique + clarifications.\n"
        "Ne résume pas la dictée : conserve tous les faits, montants, dates et demandes.\n"
        "Sois exhaustif : structure type مذكرة دفاع (شكل، موضوع، مناقشة، ملتمسات).\n"
        "Dans BODY, mentionne explicitement le tribunal et le N° RG s'ils figurent dans la fiche.\n"
        "Si les pièces contiennent un argument oublié par l'avocat : intègre-le clairement.\n"
        "Si un élément obligatoire (identité, domicile…) manque : note-le dans CHECKS seulement."
    )

    # Qualité ChatGPT : modèle selon plan (free→mini, lourds→gpt-4o)
    from app.services.billing import get_entitlements, openai_model_for_plan

    preferred = "openai"
    model = openai_model_for_plan(get_entitlements(db, cabinet_id).plan.slug, "compose")
    user_prompt = "\n".join(prompt_parts)
    text, provider = chat_free_tier(
        user_prompt,
        system,
        preferred=preferred,
        model_override=model,
        max_tokens=8000,
        temperature=0.45,
    )
    # Relance si sortie trop courte (modèle free trop laconique).
    if text and len(text) < 900:
        retry_prompt = (
            user_prompt
            + "\n\nREPRISE OBLIGATOIRE : ta réponse précédente était trop courte. "
            "Rédige une plaidoirie complète (minimum 800 mots dans BODY), "
            "avec faits détaillés tirés des pièces, discussion juridique et ملتمسات précis. "
            "Arabe fusḥā uniquement — aucun paragraphe français."
        )
        text2, provider2 = chat_free_tier(
            retry_prompt,
            system,
            preferred=preferred,
            model_override=model,
            max_tokens=8000,
            temperature=0.5,
        )
        if text2 and len(text2) > len(text):
            text, provider = text2, provider2
    if not text:
        raise HTTPException(
            status_code=503,
            detail="IA indisponible — réessayez dans un instant.",
        )

    title_out, body_out, checks = _parse_title_body_checks(text, hint_title)
    if use_pii and mapping:
        title_out = unmask_text(title_out, mapping)
        body_out = unmask_text(body_out, mapping)
        checks = [unmask_text(c, mapping) for c in checks]

    body_out, section_warnings = postprocess_plaidoirie_body(
        body_out,
        source_text=dictation_text,
        plaidoirie_type=type_id,
        for_export=False,
    )
    if use_pii and mapping:
        body_out = unmask_text(body_out, mapping)

    checks = checks + section_warnings
    if use_pii:
        checks.insert(
            0,
            f"Confidentialité : {len(mapping)} nom(s) masqué(s) (PARTIE_…) avant l'IA, puis restaurés.",
        )
    if clarifications:
        checks.insert(0, f"Clarifications avocat prises en compte ({len(clarifications)}).")
    if raw_docs.strip():
        n_pieces = raw_docs.count("--- Pièce")
        checks.insert(0, f"Pièces du dossier intégrées à l'analyse ({n_pieces}).")
    checks.insert(
        0,
        f"Fiche juridique : {case.case_type or '—'} · {_DEGREE_FR.get(case.jurisdiction_degree or '', '—')} · "
        f"{_ROLE_FR.get(case.client_role or '', '—')}.",
    )

    return title_out, body_out, provider, checks, use_pii and bool(mapping)
