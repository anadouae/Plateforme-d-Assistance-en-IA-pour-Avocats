"""Révision ciblée d'une plaidoirie déjà rédigée (instruction avocat + PII)."""

from __future__ import annotations

import logging
import re
import unicodedata

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Case
from app.services.billing import assert_can_use_ai_action
from app.services.free_llm_router import chat_free_tier
from app.services.pii_mask import (
    build_mask_from_parties,
    collect_all_party_names,
    unmask_text,
)

logger = logging.getLogger(__name__)

_SYSTEM = """Tu es un avocat plaidant marocain. Tu révises une plaidoirie déjà rédigée.

COMPRÉHENSION INTELLIGENTE (priorité absolue)
- L'avocat écrit souvent vite, avec fautes, sans accents, en majuscules, ou en mélange FR/AR.
  Tu DOIS comprendre l'intention comme un collègue humain — PAS exiger une phrase « correcte ».
  Exemples d'équivalence :
  • « mais tu n a s rien ecrit ici خامساً / لهذه الأسباب » = Rédige le corps sous ces titres vides.
  • « developpe eplsu » / « plus cette partie » = Allonge / enrichis le passage.
  • « ici » + un titre arabe = travailler CE titre.
  • Une plainte (« toujours vide », « pourquoi rien ») = corriger vraiment le document.
- Si le système te donne une « INTENTION INTERPRÉTÉE », suis-la même si la consigne brute est mal orthographiée.
- Interdit de répondre « c'est fait » sans modifier réellement le BODY.

MISSION
- Appliquer des modifications VISIBLES et concrètes. Interdit de renvoyer le texte quasi identique.
- Sections vides (خامساً، لهذه الأسباب، الملتمسات, etc.) : RÉDIGER un vrai corps
  (3–6 phrases ou points) en arabe fusḥā, UNIQUEMENT à partir des faits déjà présents.
  Interdit de laisser le titre seul.
- Introduction pro, paraphrase juridique, traduction FR→AR : selon la consigne.
- Ne pas inventer de faits absents. Conserver PARTIE_A, PARTIE_B…
- BODY en arabe fusḥā (noms propres latins OK).

FORME BARREAU MAROC
- « سيدي الرئيس » / « حضرة المحكمة الموقرة » selon le contexte.
- Structure أولاً / ثانياً / … sauf consigne contraire.
- Sous « لهذه الأسباب » : ملتمسات concrets déjà déductibles du dossier.

SORTIE OBLIGATOIRE (sans markdown)
TITLE: …
BODY:
…texte complet révisé (modifications réellement appliquées)…
"""


_SECTION_MARKERS = (
    "أولاً",
    "ثانياً",
    "ثالثاً",
    "رابعاً",
    "خامساً",
    "سادساً",
    "سابعاً",
    "لهذه الأسباب",
    "وبناء عليه",
    "الملتمسات",
)


def _longest_arabic_span(s: str) -> str:
    spans = re.findall(r"[\u0600-\u06FF][\u0600-\u06FF0-9\s،,:؛.()/«»\"'\-]{18,}", s or "")
    if not spans:
        return ""
    return max(spans, key=len).strip(" «»\"'")


def _wants_expand(s: str) -> bool:
    t = (s or "").lower()
    return bool(
        re.search(
            r"d[ée]vel+o*p|eplsu|plus\s+(cette|ce|la|le)|"
            r"élargir|enrichir|d[ée]taill|allong|"
            r"وسّع|وسع|طور|أطل|فصل|طوّل|المزيد",
            t,
        )
    )


_CLOSING_MARKERS = (
    "خامساً",
    "سادساً",
    "سابعاً",
    "لهذه الأسباب",
    "وبناء عليه",
    "الملتمسات",
)


def _wants_fill_gaps(s: str) -> bool:
    """Intention « remplir / il n'y a rien » — fautes et formulations orales OK."""
    t = (s or "").lower()
    fr = bool(
        re.search(
            r"rien\s+[eé]crit|n['’ ]?a\s*s?\s+rien|pas\s+[eé]crit|y\s*a\s*rien|"
            r"est\s+vide|tjs\s+vide|toujours\s+vide|encore\s+vide|"
            r"compl[eè]t|remplir|rempli|écris|ecris|ajoute\s+(ici|là|la|ca|ça)|"
            r"manquant|incomplet|vide\s+ici|sous\s+(ce|le)\s+titre|"
            r"pourquoi\s+(rien|vide|pas)|mais\s+tu|t['’]?as\s+rien|"
            r"il\s+manque|faut\s+[eé]crire|r[eé]dig",
            t,
        )
    )
    ar = bool(
        re.search(
            r"فارغ|أكتب|اكتب|أكمل|املأ|لا\s*يوجد|ما\s*كتبت|ما\s*كتبتش|فين\s*النص|وين\s*النص",
            s or "",
        )
    )
    named = bool(
        re.search(
            r"خامساً?|لهذه\s*الأسباب|الملتمسات|وبناءً?\s*عليه",
            s or "",
        )
    )
    points = "/" in t or "ici" in t or "هنا" in (s or "") or "là" in t or "la :" in t
    return fr or ar or (named and (fr or points or ar))


def _looks_like_complaint_or_point(s: str) -> bool:
    """Plainte / pointage oral (« mais… », « ici », titres cités)."""
    t = (s or "").lower()
    return bool(
        re.search(
            r"\bmais\b|\bici\b|\bl[aà]\b|toujours|encore|pourquoi|"
            r"rien|vide|manque|n['’ ]?a\s*s?\s+rien|/",
            t,
        )
    ) or bool(re.search(r"خامساً?|لهذه\s*الأسباب|هنا|فارغ", s or ""))


def _norm_cmp(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


def _section_payload(text: str, marker: str) -> str:
    """Texte entre un titre de section et le titre suivant (ou fin)."""
    t = text or ""
    # Accepter خامسا / خامساً
    base = marker.rstrip("ً")
    m = re.search(rf"{re.escape(base)}ً?\s*[:：]?\s*", t)
    if not m:
        return ""
    rest = t[m.end() :]
    nxt = re.search(
        r"(?:أولاً?|ثانياً?|ثالثاً?|رابعاً?|خامساً?|سادساً?|سابعاً?|"
        r"لهذه\s*الأسباب|وبناءً?\s*عليه|الملتمسات)\s*[:：]?",
        rest,
    )
    chunk = rest[: nxt.start()] if nxt else rest
    return re.sub(r"\s+", " ", chunk).strip(" :：\n\t")


def _is_section_thin(text: str, marker: str, *, min_chars: int = 48) -> bool:
    payload = _section_payload(text, marker)
    compact = re.sub(r"[\s:：.،؛\-–—]", "", payload)
    return len(compact) < min_chars


def _thin_sections_in(text: str, markers: tuple[str, ...] | None = None) -> list[str]:
    out: list[str] = []
    for mk in markers or _SECTION_MARKERS:
        if mk in ("أولاً", "ثانياً", "ثالثاً", "رابعاً") and mk not in (text or ""):
            continue
        if re.search(rf"{re.escape(mk.rstrip('ً'))}ً?", text or ""):
            if _is_section_thin(text, mk):
                out.append(mk)
    return out


def _markers_mentioned(instr: str) -> list[str]:
    found: list[str] = []
    for mk in ("خامساً", "لهذه الأسباب", "الملتمسات", "وبناء عليه", "رابعاً", "ثالثاً"):
        base = mk.rstrip("ً")
        if re.search(rf"{re.escape(base)}ً?", instr or ""):
            found.append(mk)
    return found


def _parse_title_body(raw: str, fallback_title: str, fallback_body: str) -> tuple[str, str]:
    title_out = fallback_title
    body_out = (raw or "").strip() or fallback_body
    if not raw:
        return title_out, body_out
    tm = re.search(r"(?im)^\s*TITLE\s*[:：]\s*(.+)$", raw)
    if tm:
        title_out = tm.group(1).strip()
    bm = re.search(r"(?is)BODY\s*[:：]\s*(.+)$", raw)
    if bm:
        body_out = bm.group(1).strip()
    if body_out.upper().startswith("TITLE"):
        lines = body_out.split("\n", 1)
        body_out = lines[1].strip() if len(lines) > 1 else body_out
    # Retirer un éventuel préambule hors BODY
    if "TITLE:" in body_out[:80].upper() and "BODY:" in body_out.upper():
        bm2 = re.search(r"(?is)BODY\s*[:：]\s*(.+)$", body_out)
        if bm2:
            body_out = bm2.group(1).strip()
    return title_out or fallback_title, body_out or fallback_body


def _changed_enough(before: str, after: str) -> bool:
    a, b = _norm_cmp(before), _norm_cmp(after)
    if not b or len(b) < 40:
        return False
    if a == b:
        return False
    # Au moins ~2 % de divergence ou 40 caractères différents (approx)
    if abs(len(a) - len(b)) >= 40:
        return True
    # distance grossière : préfixe commun
    common = 0
    for x, y in zip(a, b):
        if x == y:
            common += 1
        else:
            break
    # Si le début change (souvent la مقدمة), OK
    if common < min(120, len(a) // 3):
        return True
    # Sinon exiger une différence globale
    shorter = min(len(a), len(b))
    diffs = sum(1 for i in range(shorter) if a[i] != b[i]) + abs(len(a) - len(b))
    return diffs >= max(40, int(0.02 * max(len(a), 1)))


def revise_plaidoirie_body(
    db: Session,
    *,
    cabinet_id: str,
    case_id: str | None,
    title: str,
    body: str,
    instruction: str,
    language: str = "ar",
    skip_quota_assert: bool = False,
) -> tuple[str, str, str]:
    """
    Applique une consigne avocat sur le texte existant.
    Retourne (title, body, provider).
    """
    if not skip_quota_assert:
        assert_can_use_ai_action(db, cabinet_id, "revise")
    instr = (instruction or "").strip()
    text = (body or "").strip()
    if len(instr) < 3:
        raise HTTPException(status_code=400, detail="Indiquez une modification (ex. ajouter un montant).")
    if len(text) < 40:
        raise HTTPException(status_code=400, detail="Plaidoirie trop courte à réviser.")

    parties: list[str] = []
    if case_id:
        case = db.query(Case).filter(Case.id == case_id, Case.cabinet_id == cabinet_id).first()
        if case:
            parties = collect_all_party_names(
                known_parties=[case.client_name or "", getattr(case, "opposing_name", None) or ""],
                texts=[text, instr],
            )

    mapping: dict[str, str] = {}
    body_in = text
    instr_in = instr
    title_in = (title or "").strip()
    if parties:
        m_body = build_mask_from_parties(body_in, parties=parties)
        m_instr = build_mask_from_parties(instr_in, parties=parties)
        m_title = build_mask_from_parties(title_in, parties=parties)
        body_in, instr_in, title_in = m_body.text, m_instr.text, m_title.text
        mapping = {**m_body.mapping, **m_instr.mapping, **m_title.mapping}

    lang_label = "arabe fusḥā" if language == "ar" else "français juridique"
    focus = _longest_arabic_span(instr)
    expand = _wants_expand(instr)
    fill_gaps = _wants_fill_gaps(instr)
    mentioned = _markers_mentioned(instr)
    thin_before = _thin_sections_in(body_in)
    thin_closing = [m for m in thin_before if m in _CLOSING_MARKERS]
    # Compréhension intelligente : on regarde AUSSI le document (titres vides),
    # pas seulement une phrase « parfaite » de l'avocat.
    smart_fill = bool(
        fill_gaps
        or mentioned
        or (_looks_like_complaint_or_point(instr) and thin_closing)
        or (len((instr or "").strip()) <= 160 and thin_closing and _looks_like_complaint_or_point(instr))
    )
    targets = [m for m in mentioned if m in thin_before or _is_section_thin(body_in, m)]
    if smart_fill and not targets:
        targets = list(thin_closing) or list(thin_before) or list(mentioned)
    for m in mentioned:
        if m not in targets and _is_section_thin(body_in, m):
            targets.append(m)
    # Si l'avocat cite des titres et le doc a d'autres clôtures vides → les remplir aussi
    if mentioned and thin_closing:
        for m in thin_closing:
            if m not in targets:
                targets.append(m)

    extra_intent = ""
    intent_human = ""
    if targets or (smart_fill and thin_before):
        labels = " · ".join(targets or thin_closing or thin_before)
        intent_human = (
            f"Remplir / rédiger le corps sous les titres encore vides : {labels}."
        )
        extra_intent = (
            "\n=== INTENTION INTERPRÉTÉE (obligatoire — ne pas demander de reformulation) ===\n"
            f"{intent_human}\n"
            "La consigne brute peut être fautive ; cette intention fait foi.\n"
            "\n=== SECTIONS VIDES À RÉDIGER (OBLIGATOIRE) ===\n"
            f"Titres concernés : {labels}\n"
            "Sous CHAQUE titre ci-dessus, écris un corps réel (au moins 3–6 phrases ou points numérotés) "
            "en arabe juridique, à partir des faits DÉJÀ présents dans la plaidoirie "
            "(نفقة، حضانة، تواريخ، أطراف، طلبات). "
            "Interdit de laisser « خامساً : » ou « لهذه الأسباب: » sans texte après. "
            "Pour « لهذه الأسباب » : formuler les الملتمسات concrets. "
            "Garde le reste de la plaidoirie et sors TITLE/BODY complets.\n"
        )
    elif expand and focus:
        intent_human = f"Développer / allonger nettement le passage : « {focus[:120]} »."
        extra_intent = (
            "\n=== INTENTION INTERPRÉTÉE (obligatoire) ===\n"
            f"{intent_human}\n"
            "\n=== PASSAGE À DÉVELOPPER (OBLIGATOIRE) ===\n"
            f"« {focus} »\n"
            "Réécris CE paragraphe pour qu'il fasse AU MOINS le double de longueur : "
            "motifs juridiques (مدونة الأسرة, مصلحة المحضون, نفقة), en restant sur les faits déjà présents. "
            "Ne te contente pas de paraphraser une phrase. "
            "Garde le reste de la plaidoirie (أولاً / ثانياً / …) et TITLE/BODY complets.\n"
        )
    elif expand:
        intent_human = "Allonger / enrichir le passage visé par l'avocat."
        extra_intent = (
            "\n=== INTENTION INTERPRÉTÉE ===\n"
            f"{intent_human}\n"
            "Ajoute des développements juridiques concrets (au moins +120 caractères nets).\n"
        )
    base_prompt = (
        f"Langue du document : {lang_label}\n"
        f"Titre actuel : {title_in or '—'}\n\n"
        "=== Consigne brute de l'avocat (fautes possibles — comprends l'intention) ===\n"
        f"{instr_in}\n"
        f"{extra_intent}"
        "Comprends intelligemment, puis APPLIQUE dans BODY des changements visibles "
        "(surtout sections vides ou passage cité). Ne dis jamais que c'est fait sans écrire le texte.\n"
        f"=== Plaidoirie actuelle ===\n{body_in[:28000]}\n"
    )

    from app.services.billing import openai_model_for_plan, get_entitlements

    plan_slug = "free"
    try:
        plan_slug = get_entitlements(db, cabinet_id).plan.slug
    except Exception:
        pass
    model = openai_model_for_plan(plan_slug, "revise")
    need_fill = bool(targets or (smart_fill and (thin_closing or thin_before)))

    raw, provider = chat_free_tier(
        base_prompt,
        _SYSTEM,
        preferred="openai",
        strict_preferred=True,
        allow_ollama=False,
        model_override=model,
        max_tokens=8000,
        temperature=0.62 if (expand or need_fill) else 0.5,
    )
    if not raw:
        raise HTTPException(
            status_code=503,
            detail="ChatGPT (OpenAI) indisponible — réessayez dans un instant.",
        )

    title_out, body_out = _parse_title_body(raw, title_in or (title or "مرافعة"), body_in)

    def _still_thin(after: str) -> bool:
        if not need_fill:
            return False
        check = targets or thin_before
        return any(_is_section_thin(after, mk) for mk in check)

    too_shy = (
        not _changed_enough(body_in, body_out)
        or (expand and len(_norm_cmp(body_out)) < len(_norm_cmp(body_in)) + 80)
        or _still_thin(body_out)
    )
    if too_shy:
        logger.warning(
            "revise no-op detected — retry harder case=%s fill=%s",
            case_id or "-",
            need_fill,
        )
        retry_prompt = (
            base_prompt
            + "\n\n=== ALERTE ===\n"
            "Ta réponse précédente était trop proche de l'original OU laissait des titres vides — INTERDIT.\n"
            "Tu DOIS remplir concrètement les sections visées (corps sous خامساً / لهذه الأسباب si demandés).\n"
            "Si DÉVELOPPER : allonge nettement le passage.\n"
            "Sortie TITLE / BODY uniquement.\n"
        )
        raw2, provider2 = chat_free_tier(
            retry_prompt,
            _SYSTEM,
            preferred="openai",
            strict_preferred=True,
            allow_ollama=False,
            model_override=model,
            max_tokens=8000,
            temperature=0.65,
        )
        if raw2:
            title_out, body_out = _parse_title_body(
                raw2, title_out or title_in or (title or "مرافعة"), body_in
            )
            provider = provider2 or provider
        still_shy = (
            not _changed_enough(body_in, body_out)
            or (expand and len(_norm_cmp(body_out)) < len(_norm_cmp(body_in)) + 80)
            or _still_thin(body_out)
        )
        if still_shy:
            raise HTTPException(
                status_code=502,
                detail=(
                    "L'IA n'a pas réussi à appliquer la modification (sections encore vides "
                    "ou texte trop peu changé). Renvoyez la même demande une fois — "
                    "le langage naturel / avec fautes est accepté."
                ),
            )

    if mapping:
        title_out = unmask_text(title_out, mapping)
        body_out = unmask_text(body_out, mapping)

    logger.info("revise via %s case=%s changed=1 fill=%s", provider, case_id or "-", need_fill)
    return title_out, body_out, provider
