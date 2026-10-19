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
    build_full_mask,
    build_mask_from_parties,
    collect_all_party_names,
    unmask_text,
)
from app.services.pii_store import load_case_pii_mapping, save_case_pii_mapping

logger = logging.getLogger(__name__)

_SYSTEM = """Tu es l'assistant ChatGPT d'un avocat marocain sur une plaidoirie.

TU DOIS D'ABORD CLASSER LA CONSIGNE :

A) SALUTATION / BRUIT / INCOMPLET (hola, salut, hi, « Comment », « ok », test, un mot vague)
   → NE MODIFIE PAS le document. BODY = texte actuel IDENTIQUE.
   → ASSISTANT_REPLY : réponds poliment et demande clairement ce qu'il faut modifier
     (ex. « Que voulez-vous changer dans la plaidoirie ? Ex. allonge رابعاً »).

B) QUESTION SEULE (pourquoi / comment / explique / c'est quoi…) SANS demande d'édition
   → NE MODIFIE PAS le document. BODY identique.
   → ASSISTANT_REPLY : réponds utilement en français (2–8 phrases).

C) VRAIE MODIFICATION (allonge, rends plus longue, ajoute, supprime, corrige, change les noms,
   remplis خامساً, reformule, etc.)
   → Applique EXACTEMENT la demande dans le BODY (fautes OK, FR/AR mélangés).
   → Si un titre est cité (أولاً…خامساً / لهذه الأسباب), modifie surtout ce passage.
   → « plus longue / developpe / allonge » = enrichir nettement (≈ double sous le titre).
   → Ne détourne pas vers d'autres sections non demandées.
   → Ne pas inventer de faits. Conserver PARTIE_A/B sauf si on demande les noms en clair/arabe.
   → BODY en arabe fusḥā. ASSISTANT_REPLY : confirme brièvement ce qui a changé.

INTERDIT
- Prétendre avoir « appliqué » hola / Comment en réécrivant la plaidoirie.
- Ajouter des « commentaires » dans le BODY si on n'a pas demandé d'éditer.
- Menu d'actions préprogrammées : suis la consigne libre comme ChatGPT.

SORTIE OBLIGATOIRE (sans markdown)
ASSISTANT_REPLY: …
TITLE: …
BODY:
…texte complet (identique si A/B, révisé si C)…
"""


def _is_chat_noise(s: str) -> bool:
    """Salutation / bruit / consigne trop vague → ne pas toucher au document."""
    t = (s or "").strip()
    if len(t) < 2:
        return True
    low = t.lower().strip(" !.?;،؟\t\n")
    if re.fullmatch(
        r"hola|hi|hello|hey|salut|bonjour|bonsoir|yo|coucou|"
        r"ok|oui|non|merci|thanks|thx|lol|test|wtf|ah|euh|hmm|hein|"
        r"comment|pourquoi|quoi|yes|no|bonne?|d['’]?accord|"
        r"سلام|مرحبا|أهلا|شكرا|تمام|واخا|لا|نعم",
        low,
    ):
        return True
    # Un seul mot très court sans consigne d'édition
    if len(low.split()) <= 2 and len(low) <= 12 and not re.search(
        r"allong|plus|ajoute|change|ecris|écrit|dévelop|modif|corrige|"
        r"رابعا|ثالثا|ثانيا|أولا|خامسا|ملتمس|مقدمة",
        low,
    ):
        if not re.search(r"[\u0600-\u06FF]{4,}", t):
            return True
    return False


def _is_question_only(s: str) -> bool:
    """Question sans verbe d'édition → répondre sans toucher au BODY."""
    if _is_chat_noise(s):
        return False
    t = (s or "").lower()
    has_edit = bool(
        re.search(
            r"allong|plus\s+long|rends?\b|ajoute|supprime|efface|enl[eè]ve|"
            r"change|remplace|modifie|corrige|reformul|d[ée]velop|enrich|"
            r"remplir|compl[eè]te|[eé]cri[rs]|mets?\b|mettre|passe\b|"
            r"introduc|noms?\s+.*arabe|en\s+arabe|"
            r"وسّع|وسع|أضف|احذف|غيّر|غير|استبدل|صحّح|طوّل|اكتب",
            t,
        )
    )
    if has_edit:
        return False
    return bool(
        re.search(
            r"\?|comment\b|pourquoi|expliq|c['’]?est\s+quoi|que\s+veut|"
            r"d['’]?\s*o[uù]\s+vient|clarif|peux[- ]tu|peux\s+tu|"
            r"اشرح|وضح|لماذا|شنو|ما\s*معنى|من\s+أين",
            t,
        )
    )


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
            r"d[ée]vel+o*p|eplsu|"
            r"plus\s+(cette|ce|la|le|long|longue|grande|d[ée]taill)|"
            r"rends?\s+.+\s+plus|"
            r"faire\s+plus\s+long|plus\s+long|"
            r"élargir|enrichir|d[ée]taill|allong|"
            r"وسّع|وسع|طور|أطل|فصل|طوّل|المزيد|أطلها|طول",
            t,
        )
    ) or bool(
        re.search(r"رابعاً?|ثالثاً?|ثانياً?|أولاً?|خامساً?", s or "")
        and re.search(r"plus\s+long|allong|d[ée]velop|rends?|enrich|طول|وسع", t)
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


def _wants_arabic_party_names(s: str) -> bool:
    """Écrire / afficher les noms des parties en alphabet arabe (fautes OK)."""
    t = (s or "").lower()
    fr = bool(
        re.search(
            r"(noms?|parties?|pr[eé]noms?).{0,48}arabe|"
            r"arabe.{0,48}(noms?|parties?)|"
            r"[eé]cri[rs].{0,40}(noms?|parties?).{0,28}arabe|"
            r"(mets?|mettre|passe[rz]?|change[rz]?).{0,24}(noms?|parties?).{0,24}arabe|"
            r"noms?\s+des?\s+parties?|"
            r"parties?\s+en\s+arabe|"
            r"en\s+arabe\s+(les?\s+)?(noms?|parties?)",
            t,
        )
    )
    ar = bool(
        re.search(
            r"أسماء.{0,20}(أطراف|طرف)|أطراف.{0,20}(عربي|عربية)|"
            r"بالعربية.{0,20}(أسماء|أطراف)|"
            r"اكتب.{0,30}(الأسماء|أسماء|الأطراف).{0,20}عربي|"
            r"أسماء\s*الأطراف",
            s or "",
        )
    )
    return fr or ar


def _wants_targeted_light_edit(s: str) -> bool:
    """Petites edits (noms, dates, montants, orthographe) — ne pas exiger +40 chars."""
    if _wants_arabic_party_names(s):
        return True
    t = (s or "").lower()
    return bool(
        re.search(
            r"\bnoms?\b|\bparties?\b|pr[eé]nom|orthographe|corrige\s+le\s+nom|"
            r"remplace|en\s+arabe|en\s+fran[cç]ais|latin|"
            r"date|montant|cin\b|t[eé]l[eé]phone|email|"
            r"غيّر|غير|استبدل|بالعربية|الاسم",
            t,
        )
    )


def _arabic_char_ratio(s: str) -> float:
    letters = [c for c in (s or "") if c.isalpha()]
    if not letters:
        return 0.0
    ar = sum(1 for c in letters if "\u0600" <= c <= "\u06FF")
    return ar / max(len(letters), 1)


def _party_glossary_lines(mapping: dict[str, str], parties: list[str]) -> list[str]:
    """Lignes glossaire PARTIE_* → nom réel (pour forcer l'arabe)."""
    lines: list[str] = []
    seen_tok: set[str] = set()
    # mapping côté mask : souvent {original: token} — normaliser
    tok_to_name: dict[str, str] = {}
    for k, v in (mapping or {}).items():
        ks, vs = (k or "").strip(), (v or "").strip()
        if not ks or not vs:
            continue
        if ks.startswith("PARTIE_") and not vs.startswith("PARTIE_"):
            tok_to_name[ks] = vs
        elif vs.startswith("PARTIE_") and not ks.startswith("PARTIE_"):
            tok_to_name[vs] = ks
    for tok in sorted(tok_to_name.keys()):
        if tok in seen_tok:
            continue
        seen_tok.add(tok)
        lines.append(f"{tok} → « {tok_to_name[tok]} »")
    # Parties fiche sans jeton encore listé
    for i, name in enumerate(parties or []):
        n = (name or "").strip()
        if not n or len(n) < 2:
            continue
        if any(n == x or n in x for x in tok_to_name.values()):
            continue
        letter = chr(ord("A") + i) if i < 26 else str(i + 1)
        lines.append(f"(partie {letter}) → « {n} »")
    return lines


def _wants_fill_gaps(s: str) -> bool:
    """Intention « remplir / il n'y a rien » — fautes et formulations orales OK."""
    if _wants_arabic_party_names(s):
        return False
    if _wants_intro(s) and not re.search(
        r"خامساً?|لهذه\s*الأسباب|فارغ|vide|rien\s+[eé]crit|املأ|أكمل|raison|ملتمسات",
        s or "",
        re.I,
    ):
        return False
    t = (s or "").lower()
    # « ecris les noms… » ≠ remplir une section vide
    if re.search(r"[eé]cri[rs].{0,40}(noms?|parties?|pr[eé]nom)", t):
        if not re.search(r"vide|فارغ|خامسا|لهذه|ملتمسات|sous\s+(ce|le)\s+titre|ici\b", t):
            return False
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


def _changed_enough(before: str, after: str, *, min_diffs: int | None = None) -> bool:
    a, b = _norm_cmp(before), _norm_cmp(after)
    if not b or len(b) < 20:
        return False
    if a == b:
        return False
    floor = 12 if min_diffs is None else max(4, int(min_diffs))
    # Longueur qui bouge nettement
    if abs(len(a) - len(b)) >= floor:
        return True
    # Jetons PARTIE_* remplacés par du texte (ex. noms en arabe)
    tok_b = len(re.findall(r"PARTIE_[A-Z0-9]+", before or "", flags=re.I))
    tok_a = len(re.findall(r"PARTIE_[A-Z0-9]+", after or "", flags=re.I))
    if tok_b > 0 and tok_a < tok_b:
        return True
    # Plus d'arabe = souvent translittération des noms
    if _arabic_char_ratio(after) >= _arabic_char_ratio(before) + 0.02 and abs(
        len(re.findall(r"[\u0600-\u06FF]", after or ""))
        - len(re.findall(r"[\u0600-\u06FF]", before or ""))
    ) >= 4:
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
    # Sinon exiger une différence globale (seuil assoupli pour petites edits)
    shorter = min(len(a), len(b))
    diffs = sum(1 for i in range(shorter) if a[i] != b[i]) + abs(len(a) - len(b))
    need = max(floor, int(0.008 * max(len(a), 1)))
    return diffs >= need


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
    case = None
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
    base_map = load_case_pii_mapping(case) if case else {}
    m_body = build_full_mask(body_in, parties=parties, structured=True, base_mapping=base_map)
    m_instr = build_full_mask(instr_in, parties=parties, structured=True, base_mapping=m_body.mapping)
    m_title = build_full_mask(title_in, parties=parties, structured=True, base_mapping=m_instr.mapping)
    body_in, instr_in, title_in = m_body.text, m_instr.text, m_title.text
    mapping = m_title.mapping
    if case and mapping:
        save_case_pii_mapping(db, case, mapping)

    lang_label = "arabe fusḥā" if language == "ar" else "français juridique"
    chat_noise = _is_chat_noise(instr)
    question_only = _is_question_only(instr)
    preserve_body = chat_noise or question_only

    # Salutation / bruit : répondre sans appeler OpenAI ni toucher au texte
    if chat_noise:
        reply_local = (
            "Bonjour. Que voulez-vous modifier dans la plaidoirie ? "
            "Exemples : « rends رابعاً plus longue », « ajoute une introduction », "
            "« ecris les noms des parties en arabe », « remplis لهذه الأسباب »."
        )
        logger.info("revise chat_noise skip-llm case=%s instr=%r", case_id or "-", instr[:40])
        return (title or "").strip() or "مرافعة", text, "local", reply_local

    focus = _longest_arabic_span(instr)
    expand = _wants_expand(instr) and not preserve_body
    wants_intro = _wants_intro(instr) and not preserve_body
    wants_explain = _wants_explain(instr) or question_only
    wants_meta = _wants_meta_pipeline(instr)
    wants_ar_names = _wants_arabic_party_names(instr) and not preserve_body
    if wants_meta:
        wants_explain = True
    mentioned = _markers_mentioned(instr)
    cited_sections = [
        mk
        for mk in ("أولاً", "ثانياً", "ثالثاً", "رابعاً", "خامساً", "سادساً", "لهذه الأسباب", "الملتمسات")
        if re.search(rf"{re.escape(mk.rstrip('ً'))}ً?", instr or "")
    ]
    if preserve_body:
        cited_sections = []
    thin_before = _thin_sections_in(body_in)
    thin_closing = [m for m in thin_before if m in _CLOSING_MARKERS]

    fill_gaps = (
        (not preserve_body)
        and (not wants_ar_names)
        and (not expand)
        and (not cited_sections)
        and _wants_fill_gaps(instr)
    )
    smart_fill = bool(
        fill_gaps
        and (not wants_intro)
        and (thin_closing or thin_before or mentioned)
    )
    targets = [m for m in mentioned if m in thin_before or _is_section_thin(body_in, m)]
    if smart_fill and not targets:
        targets = list(thin_closing) or list(thin_before) or list(mentioned)

    extra_intent = ""
    if question_only or preserve_body:
        extra_intent = (
            "\n=== MODE QUESTION (obligatoire) ===\n"
            "NE MODIFIE PAS le BODY : recopie le texte actuel à l'identique.\n"
            "Réponds seulement dans ASSISTANT_REPLY (français, clair, utile).\n"
            "Si la question est incomplète, demande ce qu'il faut changer concrètement.\n"
        )
    elif wants_ar_names:
        gloss = _party_glossary_lines(mapping, parties)
        gloss_block = "\n".join(f"- {g}" for g in gloss) if gloss else "- (noms déjà présents → alphabet arabe)"
        extra_intent = (
            "\n=== MODE ÉDITION — NOMS EN ARABE ===\n"
            f"{gloss_block}\n"
            "Remplace PARTIE_* et formes latines par ces noms en alphabet arabe partout.\n"
        )
    elif expand or cited_sections:
        label = " · ".join(cited_sections) if cited_sections else (focus[:120] if focus else "le passage cité")
        extra_intent = (
            "\n=== MODE ÉDITION — ALLONGER / MODIFIER ===\n"
            f"Cible : {label}\n"
            + (f"Passage cité : « {focus} »\n" if focus else "")
            + "Enrichis nettement sous ce(s) titre(s) (≈ double si « plus longue »). "
            "Garde le reste. Ne touche pas aux autres sections sans demande.\n"
        )
    elif wants_intro:
        extra_intent = (
            "\n=== MODE ÉDITION — INTRODUCTION ===\n"
            "Ajoute en tête (avant أولاً) une intro pro 4–8 phrases ; garde le reste.\n"
        )
    elif smart_fill and targets:
        labels = " · ".join(targets)
        extra_intent = (
            f"\n=== MODE ÉDITION — SECTIONS VIDES ===\nRemplir : {labels}\n"
            "Corps réel 3–6 phrases (ملتمسات sous لهذه الأسباب).\n"
        )
    else:
        extra_intent = (
            "\n=== MODE ÉDITION LIBRE (comme ChatGPT) ===\n"
            "Applique la consigne telle quelle (fautes OK). "
            "Si ce n'est PAS une demande d'édition, garde le BODY identique "
            "et réponds seulement en ASSISTANT_REPLY.\n"
        )

    base_prompt = (
        f"Langue du document : {lang_label}\n"
        f"Titre actuel : {title_in or '—'}\n\n"
        "=== Consigne de l'avocat ===\n"
        f"{instr_in}\n"
        f"{extra_intent}"
        + (
            "BODY = texte actuel inchangé. ASSISTANT_REPLY obligatoire.\n"
            if preserve_body
            else "Si édition : modifications VISIBLES dans BODY. Si question : BODY inchangé.\n"
        )
        + f"=== Plaidoirie actuelle ===\n{body_in[:28000]}\n"
    )

    from app.services.billing import openai_model_for_plan, get_entitlements

    plan_slug = "free"
    try:
        plan_slug = get_entitlements(db, cabinet_id).plan.slug
    except Exception:
        pass
    model = openai_model_for_plan(plan_slug, "revise")
    need_fill = bool(smart_fill and targets)

    raw, provider = chat_free_tier(
        base_prompt,
        _SYSTEM,
        preferred="openai",
        strict_preferred=True,
        allow_ollama=False,
        model_override=model,
        max_tokens=8000 if not preserve_body else 1200,
        temperature=0.35 if preserve_body else (0.7 if (expand or cited_sections or wants_intro or wants_ar_names) else 0.55),
    )
    if not raw:
        raise HTTPException(
            status_code=503,
            detail="ChatGPT (OpenAI) indisponible — réessayez dans un instant.",
        )

    title_out, body_out, reply_out = _parse_title_body(
        raw, title_in or (title or "مرافعة"), body_in
    )

    # Garde-fou : question / bruit → document intouché
    if preserve_body:
        body_out = body_in
        title_out = title_in or title_out
        if not reply_out or len(reply_out) < 8:
            reply_out = (
                "Précisez ce que vous voulez modifier dans la plaidoirie "
                "(ex. « allonge رابعاً », « ajoute une intro »)."
            )
        if mapping:
            title_out = unmask_text(title_out, mapping)
            body_out = unmask_text(body_out, mapping)
            reply_out = unmask_text(reply_out, mapping)
        logger.info("revise Q&A preserve_body case=%s", case_id or "-")
        return title_out, body_out, provider, reply_out

    def _ok_change(after: str) -> bool:
        return _changed_enough(body_in, after, min_diffs=6)

    def _section_grew(after: str) -> bool:
        for mk in cited_sections or ([] if not expand else list(mentioned)):
            before_p = _section_payload(body_in, mk)
            after_p = _section_payload(after, mk)
            if len(re.sub(r"\s+", "", after_p)) >= len(re.sub(r"\s+", "", before_p)) + 40:
                return True
        if expand and len(_norm_cmp(after)) >= len(_norm_cmp(body_in)) + 40:
            return True
        return False

    identical = _norm_cmp(body_in) == _norm_cmp(body_out)
    weak = identical or (not _ok_change(body_out) and not _section_grew(body_out))
    if wants_explain and reply_out and len(reply_out) >= 30 and not (expand or cited_sections or need_fill or wants_ar_names or wants_intro):
        # Question + éventuelle micro-édition : on accepte
        weak = False
        body_out = body_in  # pas de réécriture fantôme
    if wants_ar_names:
        tok_b = len(re.findall(r"PARTIE_[A-Z0-9]+", body_in or "", flags=re.I))
        tok_a = len(re.findall(r"PARTIE_[A-Z0-9]+", body_out or "", flags=re.I))
        if tok_b > tok_a or _ok_change(body_out):
            weak = False

    if weak and (expand or cited_sections or need_fill or wants_intro or wants_ar_names):
        logger.warning(
            "revise weak edit — one free retry case=%s expand=%s cited=%s",
            case_id or "-",
            expand,
            cited_sections,
        )
        retry_prompt = (
            base_prompt
            + "\n\n=== ALERTE ===\n"
            "Ta réponse précédente était trop proche de l'original.\n"
            "Réécris le BODY avec la modification DEMANDÉE clairement visible.\n"
            "Si « plus longue » / section citée : double au minimum le corps sous ce titre.\n"
            "Sortie ASSISTANT_REPLY + TITLE + BODY uniquement.\n"
        )
        raw2, provider2 = chat_free_tier(
            retry_prompt,
            _SYSTEM,
            preferred="openai",
            strict_preferred=True,
            allow_ollama=False,
            model_override=model,
            max_tokens=8000,
            temperature=0.75,
        )
        if raw2:
            t2, b2, r2 = _parse_title_body(
                raw2, title_out or title_in or (title or "مرافعة"), body_in
            )
            if _ok_change(b2) or _section_grew(b2) or len(b2) > len(body_out):
                title_out, body_out = t2, b2
            if r2:
                reply_out = r2
            provider = provider2 or provider

        if wants_ar_names and not _ok_change(body_out):
            local = body_out or body_in
            for tok, original in (mapping or {}).items():
                if not tok.startswith("PARTIE_"):
                    continue
                name = (original or "").strip()
                if not name:
                    continue
                for alt in (tok, tok.replace("_", "-"), tok.replace("_", " ")):
                    if alt in local:
                        local = local.replace(alt, name)
            body_out = local
            if not reply_out:
                reply_out = "Noms des parties remis en clair (formes du dossier)."

        if _norm_cmp(body_in) == _norm_cmp(body_out) and not (reply_out and len(reply_out) >= 20):
            reply_out = (
                reply_out
                or "J’ai relu la demande. Reformulez en une phrase simple "
                "(ex. « allonge رابعاً » ou « ajoute une intro ») et renvoyez."
            )
        elif not reply_out:
            reply_out = "Modification appliquée selon votre consigne."
    elif weak and reply_out and len(reply_out) >= 20:
        # Réponse utile sans édition réelle → ne pas écraser le document
        body_out = body_in
    elif weak:
        body_out = body_in
        reply_out = (
            reply_out
            or "Je n’ai pas modifié le document. Précisez la modification voulue "
            "(ex. « allonge رابعاً »)."
        )
    elif not reply_out:
        reply_out = "Modification appliquée selon votre consigne."

    if mapping:
        title_out = unmask_text(title_out, mapping)
        body_out = unmask_text(body_out, mapping)
        if reply_out:
            reply_out = unmask_text(reply_out, mapping)

    if wants_ar_names and not reply_out:
        reply_out = "Les noms des parties sont écrits en arabe dans la plaidoirie."

    if wants_explain and not reply_out:
        if wants_meta:
            reply_out = (
                "Pas à pas : 1) dossier + dictée anonymisés, 2) ChatGPT prépare 0–5 QCM, "
                "3) vous répondez, 4) rédaction, 5) titres أولاً…خامساً / لهذه الأسباب (ملتمسات)."
            )
        else:
            reply_out = (
                "« لهذه الأسباب » est la clôture : les الملتمسات (demandes concrètes) "
                "se rédigent sous ce titre."
            )

    logger.info(
        "revise via %s case=%s expand=%s cited=%s preserve=%s",
        provider,
        case_id or "-",
        expand,
        cited_sections or "-",
        preserve_body,
    )
    return title_out, body_out, provider, reply_out or ""
