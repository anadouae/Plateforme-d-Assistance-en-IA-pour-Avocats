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

_SYSTEM = """Tu es un avocat plaidant marocain. Tu révises une plaidoirie déjà rédigée ET tu peux répondre à l'avocat.

COMPRÉHENSION INTELLIGENTE (priorité absolue)
- L'avocat écrit souvent vite, avec fautes, sans accents, ou en mélange FR/AR.
  Tu DOIS comprendre l'intention comme un collègue humain.
  Exemples :
  • « pourquoi pour ces raisons mais tu ecris pas les raisons » / « explique خامساً / لهذه الأسباب »
    = Expliquer ET rédiger le corps sous ces titres (الملتمسات concrets).
  • « developpe eplsu » = Allonge le passage.
  • « ajoute une introduction » = Intro pro en tête.
- Si « INTENTION INTERPRÉTÉE » est fournie, suis-la.

MISSION
- Modifications VISIBLES dans le BODY. Interdit de renvoyer le texte quasi identique.
- Sections vides (خامساً، لهذه الأسباب، الملتمسات) : RÉDIGER un vrai corps (3–6 phrases/points)
  à partir des faits déjà présents. Interdit de laisser le titre seul.
- Ne pas inventer de faits absents. Conserver PARTIE_A, PARTIE_B…
- BODY en arabe fusḥā.

RÉPONSE À L'AVOCAT (si question / pourquoi / explique / comprends / d'où vient / formulaire)
- Ajoute aussi une ligne claire :
ASSISTANT_REPLY: <2 à 8 phrases en français, pédagogiques, pas à pas>
- Si on demande d'où vient le formulaire de questions : expliquer que LexHub lit d'abord
  le dossier anonymisé + la dictée, puis ChatGPT prépare 0–5 QCM avant rédaction ;
  l'avocat confirme ; ensuite la rédaction utilise ces réponses.
- Si on demande pourquoi « لهذه الأسباب » : c'est le titre de clôture ; les الملتمسات
  (demandes concrètes) doivent être écrits SOUS ce titre — puis les écrire dans le BODY.

SORTIE OBLIGATOIRE (sans markdown)
ASSISTANT_REPLY: … (recommandé dès qu'il y a une question)
TITLE: …
BODY:
…texte complet révisé…
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


def _wants_intro(s: str) -> bool:
    """Ajouter / rédiger une introduction ou adresse au tribunal."""
    t = (s or "").lower()
    fr = bool(
        re.search(
            r"introduc|pr[eé]ambule|preambule|ouverture|"
            r"ajoute[rz]?\s+(une?\s+)?intro|ajou?te[rz]?\s+l['’]?intro|"
            r"mettre\s+(une?\s+)?intro|ajouter\s+au\s+d[eé]but|"
            r"au\s+d[eé]but\s+(de\s+)?(la\s+)?plaid|"
            r"sidi\s*pr[eé]sident|adresse\s+(au|à\s+la)\s+(tribunal|cour|pr[eé]sident)",
            t,
        )
    )
    ar = bool(
        re.search(
            r"مقدمة|تقديم|استهلال|سيدي\s*الرئيس|حضرة\s*المحكمة|أضف\s*(?:لي\s*)?(?:مقدمة|تقديم)",
            s or "",
        )
    )
    return fr or ar


_CLOSING_MARKERS = (
    "خامساً",
    "سادساً",
    "سابعاً",
    "لهذه الأسباب",
    "وبناء عليه",
    "الملتمسات",
)


def _wants_explain(s: str) -> bool:
    """Question / explication (pas seulement une édition silencieuse)."""
    t = (s or "").lower()
    return bool(
        re.search(
            r"expliq|pourquoi|comprend|c['’]?est\s+quoi|d['’]?\s*o[uù]\s+vient|"
            r"comment\s+(ça|ca|se)|que\s+veut\s+dire|clarif|"
            r"formulaire|questionnaire|\bqcm\b|ces\s+questions|"
            r"qui\s+(les?\s+)?pr[eé]pare|comment\s+.{0,20}pr[eé]pare|"
            r"pas\s+[àa]\s+pas|étape\s+par\s+étape|"
            r"اشرح|وضح|لماذا|فين|شنو|ما\s*معنى|من\s+أين|كيف\s+تُ?عد",
            t,
        )
    ) or bool(re.search(r"raison|ملتمسات|لهذه\s*الأسباب", s or "", re.I))


def _wants_meta_pipeline(s: str) -> bool:
    """Demande sur l'origine du QCM / des titres (pas seulement le fond juridique)."""
    t = (s or "").lower()
    return bool(
        re.search(
            r"formulaire|questionnaire|\bqcm\b|ces\s+questions|"
            r"d['’]?\s*o[uù]\s+vient|d['’]?\s*o[uù]\s+viennent|"
            r"qui\s+(les?\s+)?pr[eé]pare|comment\s+.{0,24}pr[eé]pare|"
            r"pas\s+[àa]\s+pas|étape|pipeline|d['’]?\s*où|"
            r"من\s+أين|كيف\s+تُ?عد|من\s+يحضر",
            t,
        )
    )


def _wants_fill_gaps(s: str) -> bool:
    """Intention « remplir / il n'y a rien » — fautes et formulations orales OK."""
    if _wants_intro(s) and not re.search(
        r"خامساً?|لهذه\s*الأسباب|فارغ|vide|rien\s+[eé]crit|املأ|أكمل|raison|ملتمسات",
        s or "",
        re.I,
    ):
        return False
    t = (s or "").lower()
    fr = bool(
        re.search(
            r"rien\s+[eé]crit|n['’ ]?a\s*s?\s+rien|pas\s+[eé]crit|y\s*a\s*rien|"
            r"est\s+vide|tjs\s+vide|toujours\s+vide|encore\s+vide|"
            r"compl[eè]te[rz]?|remplir|rempli|"
            r"\b[eé]cris\b|\becris\b|ajoute\s+(ici|l[aà]|ca|ça)\b|"
            r"manquant|incomplet|vide\s+ici|sous\s+(ce|le)\s+titre|"
            r"pourquoi\s+(rien|vide|pas)|mais\s+tu|t['’]?as\s+rien|"
            r"il\s+manque|faut\s+[eé]crire|r[eé]dig(?:e|er)?\s+(ici|sous|le|la)|"
            r"pas\s+le\s*s?\s*raison|les\s+raisons|pour\s+ces\s+raisons|"
            r"tu\s+ecris\s+pas|vous\s+ecrivez",
            t,
        )
    )
    ar = bool(
        re.search(
            r"فارغ|أكتب|اكتب|أكمل|املأ|لا\s*يوجد|ما\s*كتبت|ما\s*كتبتش|فين\s*النص|وين\s*النص|"
            r"الأسباب|الملتمسات",
            s or "",
        )
    )
    named = bool(
        re.search(
            r"خامساً?|لهذه\s*الأسباب|الملتمسات|وبناءً?\s*عليه",
            s or "",
        )
    )
    points = "/" in t or re.search(r"\bici\b|\blà\b|هنا", t) is not None
    return fr or ar or (named and (fr or points or ar or _wants_explain(s)))


def _looks_like_complaint_or_point(s: str) -> bool:
    """Plainte / pointage oral (« mais… », « ici », titres cités)."""
    if _wants_intro(s):
        return False
    t = (s or "").lower()
    return bool(
        re.search(
            r"\bmais\b|\bici\b|toujours|encore|pourquoi|"
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


def _parse_title_body(raw: str, fallback_title: str, fallback_body: str) -> tuple[str, str, str]:
    title_out = fallback_title
    body_out = (raw or "").strip() or fallback_body
    reply = ""
    if not raw:
        return title_out, body_out, reply
    rm = re.search(
        r"(?is)ASSISTANT_REPLY\s*[:：]\s*(.+?)(?=\n\s*TITLE\s*[:：]|\n\s*BODY\s*[:：]|$)",
        raw,
    )
    if rm:
        reply = re.sub(r"\s+", " ", rm.group(1)).strip()
    tm = re.search(r"(?im)^\s*TITLE\s*[:：]\s*(.+)$", raw)
    if tm:
        title_out = tm.group(1).strip()
    bm = re.search(r"(?is)BODY\s*[:：]\s*(.+)$", raw)
    if bm:
        body_out = bm.group(1).strip()
    # Nettoyer fuites de balises
    body_out = re.sub(r"(?is)\n?\s*ASSISTANT_REPLY\s*[:：].*$", "", body_out).strip()
    if body_out.upper().startswith("TITLE"):
        lines = body_out.split("\n", 1)
        body_out = lines[1].strip() if len(lines) > 1 else body_out
    if "TITLE:" in body_out[:80].upper() and "BODY:" in body_out.upper():
        bm2 = re.search(r"(?is)BODY\s*[:：]\s*(.+)$", body_out)
        if bm2:
            body_out = bm2.group(1).strip()
    return title_out or fallback_title, body_out or fallback_body, reply


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
) -> tuple[str, str, str, str]:
    """
    Applique une consigne avocat sur le texte existant.
    Retourne (title, body, provider, assistant_reply).
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
    wants_intro = _wants_intro(instr)
    wants_explain = _wants_explain(instr)
    wants_meta = _wants_meta_pipeline(instr)
    if wants_meta:
        wants_explain = True
    fill_gaps = _wants_fill_gaps(instr) or (
        wants_explain and bool(_thin_sections_in(body_in, _CLOSING_MARKERS))
    )
    mentioned = _markers_mentioned(instr)
    thin_before = _thin_sections_in(body_in)
    thin_closing = [m for m in thin_before if m in _CLOSING_MARKERS]
    # Compréhension intelligente : on regarde AUSSI le document (titres vides),
    # pas seulement une phrase « parfaite » de l'avocat.
    # Ne pas détourner une demande d'introduction vers « remplir خامساً ».
    smart_fill = bool(
        (not wants_intro)
        and (
            fill_gaps
            or mentioned
            or (_looks_like_complaint_or_point(instr) and thin_closing)
            or (len((instr or "").strip()) <= 160 and thin_closing and _looks_like_complaint_or_point(instr))
        )
    )
    targets = [m for m in mentioned if m in thin_before or _is_section_thin(body_in, m)]
    if smart_fill and not targets:
        targets = list(thin_closing) or list(thin_before) or list(mentioned)
    for m in mentioned:
        if m not in targets and _is_section_thin(body_in, m):
            targets.append(m)
    # Si l'avocat cite des titres et le doc a d'autres clôtures vides → les remplir aussi
    if mentioned and thin_closing and not wants_intro:
        for m in thin_closing:
            if m not in targets:
                targets.append(m)

    extra_intent = ""
    intent_human = ""
    if wants_intro and not (targets and fill_gaps):
        intent_human = "Ajouter une introduction professionnelle en tête de plaidoirie."
        extra_intent = (
            "\n=== INTENTION INTERPRÉTÉE (obligatoire) ===\n"
            f"{intent_human}\n"
            "La consigne peut contenir des fautes ; cette intention fait foi.\n"
            "\n=== INTRODUCTION À AJOUTER (OBLIGATOIRE) ===\n"
            "Place en TOUTE PREMIÈRE partie du BODY (avant أولاً / ثانياً) une introduction "
            "d'au moins 4–8 phrases : adresse au tribunal (سيدي الرئيس / حضرة المحكمة الموقرة), "
            "présentation brève des parties et de l'objet, puis transition vers les moyens. "
            "Conserve TOUT le reste de la plaidoirie inchangé (sauf transition). "
            "Ne te plains pas des sections vides non demandées — ne les remplis que si la consigne le demande.\n"
        )
    elif targets or (smart_fill and thin_before):
        labels = " · ".join(targets or thin_closing or thin_before)
        intent_human = (
            f"Remplir / rédiger le corps sous les titres encore vides : {labels}."
        )
        if wants_explain:
            intent_human += (
                " Expliquer aussi à l'avocat (ASSISTANT_REPLY) pourquoi le titre « لهذه الأسباب » "
                "existe et quelles demandes concrètes (ملتمسات) doivent y figurer."
            )
            if wants_meta:
                intent_human += (
                    " Expliquer PAS À PAS d'où vient le formulaire de questions : "
                    "1) lecture anonymisée du dossier + dictée, 2) ChatGPT prépare 0–5 QCM, "
                    "3) l'avocat répond, 4) rédaction avec ces clarifications, "
                    "5) les titres أولاً…خامساً / لهذه الأسباب viennent du modèle de plaidoirie."
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
            + (
                "Ajoute aussi ASSISTANT_REPLY: explication claire en français (2–8 phrases).\n"
                if wants_explain
                else ""
            )
        )
    elif wants_explain or wants_meta:
        intent_human = (
            "Répondre clairement à la question de l'avocat (ASSISTANT_REPLY), "
            "et appliquer toute modification utile au document."
        )
        if wants_meta:
            intent_human += (
                " Expliquer PAS À PAS : formulaire QCM (dossier anonymisé → ChatGPT → 0–5 questions → "
                "réponses avocat → rédaction) + structure أولاً…خامساً / لهذه الأسباب / الملتمسات."
            )
        extra_intent = (
            "\n=== INTENTION INTERPRÉTÉE (obligatoire) ===\n"
            f"{intent_human}\n"
            "La consigne peut contenir des fautes ; cette intention fait foi.\n"
            "ASSISTANT_REPLY obligatoire (français, pédagogique, 3–8 phrases).\n"
            "Si des sections de clôture sont vides, remplis-les aussi dans le BODY.\n"
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
    need_fill = bool(
        (not wants_intro)
        and (targets or (smart_fill and (thin_closing or thin_before)))
    )

    raw, provider = chat_free_tier(
        base_prompt,
        _SYSTEM,
        preferred="openai",
        strict_preferred=True,
        allow_ollama=False,
        model_override=model,
        max_tokens=8000,
        temperature=0.62 if (expand or need_fill or wants_intro) else 0.5,
    )
    if not raw:
        raise HTTPException(
            status_code=503,
            detail="ChatGPT (OpenAI) indisponible — réessayez dans un instant.",
        )

    title_out, body_out, reply_out = _parse_title_body(
        raw, title_in or (title or "مرافعة"), body_in
    )

    def _still_thin(after: str) -> bool:
        if not need_fill:
            return False
        check = targets or thin_before
        return any(_is_section_thin(after, mk) for mk in check)

    def _intro_ok(after: str) -> bool:
        if not wants_intro:
            return True
        a, b = _norm_cmp(body_in), _norm_cmp(after)
        if len(b) >= len(a) + 60:
            return True
        common = 0
        for x, y in zip(a, b):
            if x == y:
                common += 1
            else:
                break
        return common < min(80, max(20, len(a) // 5)) or _changed_enough(body_in, after)

    too_shy = (
        not _changed_enough(body_in, body_out)
        or (expand and len(_norm_cmp(body_out)) < len(_norm_cmp(body_in)) + 80)
        or _still_thin(body_out)
        or (wants_intro and not _intro_ok(body_out))
    )
    if wants_intro and _intro_ok(body_out) and not need_fill:
        too_shy = False
    if need_fill and not _still_thin(body_out):
        too_shy = False
    if wants_explain and reply_out and _changed_enough(body_in, body_out):
        too_shy = False
    if wants_explain and reply_out and len(reply_out) >= 40 and not need_fill:
        too_shy = False
    if too_shy:
        logger.warning(
            "revise no-op detected — retry harder case=%s fill=%s intro=%s",
            case_id or "-",
            need_fill,
            wants_intro,
        )
        retry_hint = (
            "Tu DOIS ajouter une INTRODUCTION réelle en tête du BODY (4–8 phrases), "
            "puis garder le reste. N'exige pas de remplir خامساً sauf si demandé.\n"
            if wants_intro
            else (
                "Tu DOIS remplir concrètement les sections visées "
                "(corps sous خامساً / لهذه الأسباب si demandés).\n"
                "Si DÉVELOPPER : allonge nettement le passage.\n"
                "Si QUESTION : ajoute aussi ASSISTANT_REPLY en français.\n"
            )
        )
        retry_prompt = (
            base_prompt
            + "\n\n=== ALERTE ===\n"
            "Ta réponse précédente était trop proche de l'original — INTERDIT.\n"
            + retry_hint
            + "Sortie ASSISTANT_REPLY (si question) + TITLE / BODY uniquement.\n"
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
            title_out, body_out, reply2 = _parse_title_body(
                raw2, title_out or title_in or (title or "مرافعة"), body_in
            )
            if reply2:
                reply_out = reply2
            provider = provider2 or provider
        still_shy = (
            not _changed_enough(body_in, body_out)
            or (expand and len(_norm_cmp(body_out)) < len(_norm_cmp(body_in)) + 80)
            or _still_thin(body_out)
            or (wants_intro and not _intro_ok(body_out))
        )
        if wants_intro and _intro_ok(body_out) and not need_fill:
            still_shy = False
        if need_fill and not _still_thin(body_out):
            still_shy = False
        if wants_explain and reply_out and len(reply_out) >= 40:
            if (
                not need_fill
                or _changed_enough(body_in, body_out)
                or abs(len(body_out) - len(body_in)) >= 30
            ):
                still_shy = False
        if still_shy and wants_explain and reply_out and len(reply_out) >= 60:
            # Question pédagogique : on accepte la réponse même si le corps a peu bougé
            still_shy = False
        if still_shy:
            detail = (
                "L'IA n'a pas encore ajouté l'introduction demandée. "
                "Renvoyez simplement « ajoute une introduction » — les fautes sont acceptées."
                if wants_intro
                else (
                    "L'IA n'a pas réussi à appliquer la modification (sections encore vides "
                    "ou texte trop peu changé). Renvoyez la même demande une fois — "
                    "le langage naturel / avec fautes est accepté."
                )
            )
            raise HTTPException(status_code=502, detail=detail)

    if mapping:
        title_out = unmask_text(title_out, mapping)
        body_out = unmask_text(body_out, mapping)
        if reply_out:
            reply_out = unmask_text(reply_out, mapping)

    if wants_explain and not reply_out:
        if wants_meta:
            reply_out = (
                "Pas à pas — d’où viennent les questions et les titres : "
                "1) LexHub lit votre dossier et votre dictée en les anonymisant (PARTIE_A…). "
                "2) ChatGPT prépare 0 à 5 questions à choix (formulaire QCM) pour lever les ambiguïtés. "
                "3) Vous répondez ; 4) la rédaction utilise ces réponses. "
                "5) Les titres أولاً…خامساً puis « لهذه الأسباب » viennent du modèle de plaidoirie : "
                "sous « لهذه الأسباب » il faut écrire les الملتمسات (demandes concrètes). "
                "J’ai aussi mis à jour le document si des passages étaient vides."
            )
        else:
            reply_out = (
                "« لهذه الأسباب » (pour ces motifs) est le titre de clôture de la plaidoirie : "
                "sous ce titre, l’avocat doit écrire les الملتمسات — les demandes concrètes "
                "(ex. النفقة، الحضانة، التعويض) déduites des faits déjà exposés. "
                "J’ai complété / mis à jour le corps sous ce titre dans le document."
            )

    logger.info("revise via %s case=%s changed=1 fill=%s", provider, case_id or "-", need_fill)
    return title_out, body_out, provider, reply_out or ""
