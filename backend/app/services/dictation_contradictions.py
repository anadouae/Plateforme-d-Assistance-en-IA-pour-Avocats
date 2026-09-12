"""Post-correction : faits source, marquage STT, contradictions déterministes."""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher


@dataclass
class ContradictionAlert:
    kind: str  # case_number | date | amount | person_name
    values: list[str]
    message_ar: str
    message_fr: str


_STOP_AR = {
    "في", "من", "إلى", "على", "عن", "مع", "هذا", "هذه", "ذلك", "تلك",
    "التي", "الذي", "والتي", "والذي", "أن", "إن", "كان", "كانت", "قد",
    "ثم", "أو", "و", "لا", "ما", "لم", "لن", "كل", "بعد", "قبل", "بين",
    "حسب", "حيث", "إذ", "إذا", "أما", "كما", "حتى", "أيضا", "أيضاً",
}


def _uniq_keep_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in items:
        key = re.sub(r"\s+", " ", (x or "").strip())
        if not key:
            continue
        norm = _norm_fact(key)
        if norm in seen:
            continue
        seen.add(norm)
        out.append(key)
    return out


def _norm_fact(s: str) -> str:
    t = re.sub(r"\s+", "", (s or "").strip().lower())
    return t.replace("على", "/").replace("ـ", "")


def _case_match_is_external_ref(text: str, start: int) -> bool:
    """Ignore jurisprudence / loi / articles — pas le n° du dossier en cours."""
    window = (text or "")[max(0, start - 80) : start + 20]
    skip = (
        r"محكمة\s*النقض|قرار\s*(?:الغرفة|محكمة)|ملف\s*اجتماعي|"
        r"القانون\s*رقم|مدونة\s*الشغل|المادة\s*\d|"
        r"الفصل\s*\d|الجريدة\s*الرسمية"
    )
    return bool(re.search(skip, window, flags=re.IGNORECASE))


def _extract_case_numbers(text: str) -> list[str]:
    """
    Uniquement le n° de dossier de L'AFFAIRE EN COURS.
    Exclut : arrêts (ملف اجتماعي عدد…), lois (القانون رقم 65.99), articles (المادة 62).
    """
    t = text or ""
    pats = [
        # Explicit : رقم الملف / ملف رقم / ملف عدد (pas « ملف اجتماعي »)
        r"(?<!اجتماعي\s)(?:رقم\s*الملف|ملف\s*(?:رقم|عدد)|الملف\s*(?:رقم|عدد)|"
        r"القضية\s*(?:رقم|عدد)|الدعوى\s*(?:رقم|عدد))"
        r"\s*[:：]?\s*"
        r"([0-9٠-٩]+(?:\s*(?:/|على|-)\s*[0-9٠-٩]+){0,3})",
    ]
    found: list[str] = []
    for p in pats:
        for m in re.finditer(p, t, flags=re.IGNORECASE):
            if _case_match_is_external_ref(t, m.start()):
                continue
            # « ملف اجتماعي عدد 2245/… » — le lookbehind peut manquer si espaces
            pre = t[max(0, m.start() - 24) : m.start()]
            if re.search(r"اجتماعي|النقض|قرار", pre):
                continue
            raw = m.group(1)
            val = re.sub(r"\s+", " ", raw.strip())
            val = re.sub(r"\s*على\s*", "/", val)
            val = re.sub(r"\s*/\s*", "/", val)
            # Refs cassation type 2245/5/1/2020 (≥3 segments) → ignorer
            if val.count("/") >= 3:
                continue
            # Année seule
            if re.fullmatch(r"(?:19|20)\d{2}", val):
                continue
            found.append(val)

    uniq = _uniq_keep_order(found)
    filtered: list[str] = []
    for v in uniq:
        if any(v != w and v in w for w in uniq):
            continue
        filtered.append(v)
    return filtered


_AMOUNT_NUM = (
    r"[0-9٠-٩]+"
    r"(?:[,.\u00a0\u202f٬'\u2019]\d{3})*"  # milliers : 180,484 / 180.484 / 180 484
    r"(?:[.,]\d{1,2})?"  # décimales optionnelles
)


def _normalize_amount_display(raw: str) -> str:
    """Recompose un montant ; virgule+3 chiffres = milliers (pas un split)."""
    t = re.sub(r"\s+", " ", (raw or "").strip())
    t = t.replace("\u00a0", "").replace("\u202f", "").replace("٬", ",").replace("'", "").replace("\u2019", "")
    # 180,484 ou 180.484 (groupes de 3) → garder tel quel pour affichage
    # Extraire la partie numérique pure pour dédup
    m = re.match(rf"^({_AMOUNT_NUM})", t)
    if not m:
        return t
    num = m.group(1)
    # Normaliser espaces/apostrophes dans le nombre
    num_clean = re.sub(r"[\u00a0\u202f'\u2019]", "", num)
    # Si point utilisé comme milliers (20.604) et exactement 3 digits après → comma style
    if re.fullmatch(r"[0-9٠-٩]{1,3}(?:\.[0-9٠-٩]{3})+", num_clean) and not re.search(
        r"\.\d{1,2}$", num_clean
    ):
        num_clean = num_clean.replace(".", ",")
    currency = ""
    rest = t[m.end() :].strip()
    if re.search(r"درهم|د\.?\s*م\.?|DH|MAD", rest, re.I):
        currency = " درهم"
    return f"{num_clean}{currency}".strip()


def _amount_key(raw: str) -> str:
    """Clé numérique sans séparateurs (180484)."""
    t = _normalize_amount_display(raw)
    digits = re.sub(r"[^\d٠-٩]", "", t)
    # arab digits → western
    trans = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
    return digits.translate(trans)


def _extract_amounts(text: str) -> list[str]:
    """Montants complets — jamais de fragments coupés à la virgule des milliers."""
    t = text or ""
    found: list[str] = []
    pats = [
        rf"(?:مبلغ|قدره|قدرهً|بمبلغ|مجموعة|مجموع(?:ه|ها)?|أجرة|تعويض)\s*[:：]?\s*"
        rf"({_AMOUNT_NUM})\s*(?:درهم|د\.?\s*م\.?|DH|MAD)",
        rf"({_AMOUNT_NUM})\s*(?:درهم|د\.?\s*م\.?|DH|MAD)",
        rf"=\s*({_AMOUNT_NUM})(?=\s*(?:درهم|د\.?\s*م\.?|DH|MAD|\s|$))",
    ]
    for p in pats:
        for m in re.finditer(p, t, flags=re.IGNORECASE):
            found.append(_normalize_amount_display(m.group(1) + " درهم"))
    # Dédup par valeur numérique
    seen: set[str] = set()
    out: list[str] = []
    for a in found:
        k = _amount_key(a)
        if not k or k in seen:
            continue
        # Ignorer fragments absurdes < 3 chiffres sauf montants explicites petits déjà OK
        if len(k) < 3:
            continue
        seen.add(k)
        out.append(a)
    return out


def _label_before(text: str, pos: int, *, max_chars: int = 60) -> str:
    chunk = (text or "")[max(0, pos - max_chars) : pos]
    chunk = re.sub(r"\s+", " ", chunk).strip()
    # Couper après le montant précédent pour ne pas hériter de son libellé
    parts = re.split(r"(?:درهم|DH|MAD)\s*[.。؟!\n؛,]?", chunk, flags=re.I)
    chunk = (parts[-1] if parts else chunk).strip(" :：-–—،,")
    # « تعويض الإخطار ← 13,600 » : garder le libellé avant la flèche
    chunk = re.sub(r"\s*[←→]\s*[0-9٠-٩][0-9٠-٩,.\s]*$", "", chunk).strip()
    chunk = re.sub(r"\s*[←→]\s*$", "", chunk).strip()
    words = chunk.split()
    return " ".join(words[-10:]) if words else ""


def _normalize_event_label(label: str) -> str:
    t = re.sub(r"\s+", " ", (label or "").strip())
    # Ordre : du plus spécifique au plus général (éviter que « فصل » mange tout)
    rules = [
        (r"ضرر\s*معنوي|معنوي", "ضرر_معنوي"),
        (r"عطلة|أيام\s*(?:غير\s*)?مستوفاة", "عطلة"),
        (r"إخطار|المادة\s*51", "تعويض_إخطار"),
        (r"تعويض\s*(?:الفصل\s*)?(?:ال)?قانوني|المادة\s*53", "تعويض_قانوني"),
        (r"تعويض\s*عن\s*الفصل|أجرة\s*شهر\s*ونصف|×\s*1\.5", "تعويض_فصل"),
        (r"غرامة|تهديدية|كل\s*يوم\s*تأخير", "غرامة_يومية"),
        (r"مجموعة|مجموع(?:ه|ها)?|المفصل\s*أعلاه", "مجموع"),
        (r"أجرة\s*شهرية|راتب|يتقاضى", "أجرة_شهرية"),
        (r"قرار|نقض|غرفة\s*اجتماعية|ملف\s*اجتماعي", "اجتهاد"),
        (r"إنذار|توصل|إشعار\s*التوصل", "إنذار"),
        # Distinguer les types de mémoires (pas le même document)
        (r"مذكرة\s*جوابية", "مذكرة_جوابية"),
        (r"مذكرة\s*كتابية|مذكرتنا\s*الكتابية", "مذكرة_كتابية"),
        (r"مذكرة\s*(?:افتتاحية|تعقيبية|ختامية)", "مذكرة_أخرى"),
        # « مؤرخة في » seul ≠ regrouper toutes les dates de documents
        (r"جلسة|مرافعة", "جلسة"),
        (r"أعفي|مُنع|منع\s*(?:من)?\s*ولوج|فصل\s*تعسفي|تاريخ\s*الفصل", "فصل"),
        (r"التحاق|اشتغل|أقدمية|إحدى\s*عشرة\s*سنة", "التحاق"),
    ]
    for pat, key in rules:
        if re.search(pat, t, flags=re.IGNORECASE):
            return key
    return ""


def _extract_labeled_dates(text: str) -> list[tuple[str, str]]:
    """(label_event, date) — dates de jurisprudence exclues des contradictions."""
    months = (
        r"(?:يناير|فبراير|مارس|أبريل|ابريل|مايو|يونيو|يوليو|يوليوز|يونيه|"
        r"أغسطس|اغسطس|غشت|سبتمبر|شتنبر|أكتوبر|نوفمبر|ديسمبر)"
    )
    date_tok = rf"[0-9٠-٩]{{1,2}}\s+{months}\s+[0-9٠-٩]{{4}}"
    t = text or ""
    out: list[tuple[str, str]] = []
    occupied: set[int] = set()

    # « من DATE إلى DATE » = début / fin de relation (pas la même date d'événement)
    for m in re.finditer(
        rf"من\s+({date_tok})\s+إلى\s+({date_tok})",
        t,
        flags=re.IGNORECASE,
    ):
        out.append(("التحاق", re.sub(r"\s+", " ", m.group(1).strip())))
        out.append(("نهاية_العلاقة", re.sub(r"\s+", " ", m.group(2).strip())))
        occupied.update(range(m.start(1), m.end(1)))
        occupied.update(range(m.start(2), m.end(2)))

    pats = [
        rf"({date_tok})",
        r"(?<![0-9٠-٩/])([0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4})(?![0-9٠-٩/])",
    ]
    for p in pats:
        for m in re.finditer(p, t, flags=re.IGNORECASE):
            if any(i in occupied for i in range(m.start(1), m.end(1))):
                continue
            date = re.sub(r"\s+", " ", m.group(1).strip())
            pre = t[max(0, m.start() - 48) : m.start()]
            if re.search(r"نقض|اجتماعي|قرار\s*(?:الغرفة|محكمة)|ملف\s*اجتماعي", pre):
                continue
            # Fenêtre courte pour éviter de réutiliser le libellé d'une date précédente
            label = _normalize_event_label(_label_before(t, m.start(), max_chars=48))
            if label == "اجتهاد":
                continue
            if not label:
                continue  # sans référent → pas de contradiction croisée
            out.append((label, date))
    return out


def _extract_labeled_amounts(text: str) -> list[tuple[str, str]]:
    """(poste/libellé, montant) pour ne comparer que le même poste."""
    t = text or ""
    out: list[tuple[str, str]] = []
    for m in re.finditer(
        rf"({_AMOUNT_NUM})\s*(?:درهم|د\.?\s*م\.?|DH|MAD)",
        t,
        flags=re.IGNORECASE,
    ):
        amount = _normalize_amount_display(m.group(1) + " درهم")
        # Fenêtre courte : ne pas avaler le montant précédent (ex. 112,200)
        label = _normalize_event_label(_label_before(t, m.start(), max_chars=40))
        if not label:
            after = t[m.end() : m.end() + 48]
            label = _normalize_event_label(after)
        if not label:
            continue
        out.append((label, amount))
    return out


def _extract_dates(text: str) -> list[str]:
    """Liste plate (variables UI) — hors jurisprudence / sans libellé orphelin."""
    months = (
        r"(?:يناير|فبراير|مارس|أبريل|ابريل|مايو|يونيو|يوليو|يوليوز|يونيه|"
        r"أغسطس|اغسطس|غشت|سبتمبر|شتنبر|أكتوبر|نوفمبر|ديسمبر)"
    )
    found: list[str] = []
    t = text or ""
    for m in re.finditer(rf"([0-9٠-٩]{{1,2}}\s+{months}\s+[0-9٠-٩]{{4}})", t, flags=re.I):
        if _normalize_event_label(_label_before(t, m.start(), max_chars=40)) == "اجتهاد":
            continue
        found.append(re.sub(r"\s+", " ", m.group(1).strip()))
    # JJ/MM/AAAA : seulement si pas un fragment d'arrêt (…/5/1/2020)
    for m in re.finditer(r"(?<![0-9٠-٩/])([0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4})(?![0-9٠-٩/])", t):
        pre = t[max(0, m.start() - 40) : m.start()]
        if re.search(r"نقض|اجتماعي|قرار|ملف\s*اجتماعي", pre):
            continue
        found.append(m.group(1))
    return _uniq_keep_order(found)


def _extract_age_ranges(text: str) -> list[str]:
    """Ex. « بين 15 وال 25 سنة » / « بين 15 و 25 سنة »."""
    found: list[str] = []
    for m in re.finditer(
        r"بين\s*([0-9٠-٩]{1,3})\s*(?:و|وال)\s*(?:ال)?([0-9٠-٩]{1,3})\s*(?:سنة|عام|سنوات)?",
        text or "",
    ):
        a, b = m.group(1), m.group(2)
        found.append(f"بين {a} و {b} سنة")
    for m in re.finditer(
        r"(?:سن\s*(?:الضحية|المتهم(?:ة)?)|عمر(?:ها|ه)?)\s*[:：]?\s*([0-9٠-٩]{1,3})\s*(?:سنة|عام)?",
        text or "",
    ):
        found.append(f"{m.group(1)} سنة")
    return _uniq_keep_order(found)


def _extract_bint_names(text: str) -> list[str]:
    found: list[str] = []
    for m in re.finditer(
        r"([\u0600-\u06FF]{2,}\s+بن(?:ت)?\s+(?:ال)?[\u0600-\u06FF]{2,})",
        text or "",
    ):
        name = re.sub(r"\s+", " ", m.group(1).strip())
        if name.split()[0] not in _STOP_AR:
            found.append(name)
    return _uniq_keep_order(found)


def _extract_person_names(text: str) -> list[str]:
    role = (
        r"(?:المتهم(?:ة)?|المدعى\s*عليه(?:ا)?|المدعية?|الطرف\s*المدني|"
        r"الضحية|الضحيّة|السيد(?:ة)?|ذ\.|الأستاذ(?:ة)?|المدعوة?)"
    )
    # Nom : prénom + بن/بنت + patronyme (pas de mots libres du type « بين »)
    pat = rf"{role}\s+([\u0600-\u06FF]{{2,}}\s+بن(?:ت)?\s+(?:ال)?[\u0600-\u06FF]{{2,}})"
    skip_first = {
        "يتعلق",
        "يعترف",
        "اعترف",
        "اعترفوا",
        "في",
        "بـ",
        "بخصوص",
        "بشأن",
        "حسب",
        "كما",
        "الذي",
        "التي",
    }
    found: list[str] = []
    for m in re.finditer(pat, text):
        name = re.sub(r"\s+", " ", m.group(1).strip())
        name = re.split(
            r"[،,.]|\s+(?:الذي|التي|والتي|والذي|في|من|إلى|على|يتعلق)\s+",
            name,
        )[0].strip()
        parts = name.split()
        if not parts or parts[0] in skip_first:
            continue
        if len(name) < 4 or re.match(r"^(رقم|ملف|تاريخ)", name):
            continue
        # Exiger بن/بنت ou ≥ 2 tokens pour réduire le bruit
        if "بن" not in name and "بنت" not in name and len(parts) < 2:
            continue
        found.append(name)
    # Formes « فلان بنت/بن فلان » sans rôle (répétition contradictoire)
    for m in re.finditer(
        r"([\u0600-\u06FF]{2,}\s+بن(?:ت)?\s+(?:ال)?[\u0600-\u06FF]{2,})",
        text,
    ):
        name = re.sub(r"\s+", " ", m.group(1).strip())
        if not name or name.split()[0] in _STOP_AR:
            continue
        found.append(name)
    return _uniq_keep_order(found)


def _names_look_similar(a: str, b: str) -> bool:
    ta = set(re.findall(r"[\u0600-\u06FF]{2,}", a))
    tb = set(re.findall(r"[\u0600-\u06FF]{2,}", b))
    if not ta or not tb:
        return False
    inter = len(ta & tb)
    return inter >= max(1, min(len(ta), len(tb)) - 1) and a != b


def _fact_present(haystack: str, fact: str) -> bool:
    if not fact:
        return True
    h = haystack or ""
    variants = {
        fact,
        fact.replace("/", " على "),
        fact.replace(" على ", "/"),
        re.sub(r"\s+", "", fact),
        re.sub(r"\s+", "", fact.replace("على", "/")),
        re.sub(r"\s+", "", fact.replace("/", "على")),
        # Âges : « بين 15 وال 25 » ≈ « بين 15 و 25 »
        fact.replace(" وال ", " و "),
        fact.replace(" و ال ", " و "),
        re.sub(r"\s*وال\s*", " و ", fact),
        re.sub(r"\s+", "", re.sub(r"\s*وال\s*", "و", fact)),
    }
    h_compact = re.sub(r"\s+", "", h)
    h_norm = re.sub(r"\s*وال\s*", " و ", h)
    h_norm_c = re.sub(r"\s+", "", re.sub(r"\s*وال\s*", "و", h))
    for v in variants:
        if not v:
            continue
        if v in h or v in h_norm or re.sub(r"\s+", "", v) in h_compact or re.sub(r"\s+", "", v) in h_norm_c:
            return True
    return False


def restore_source_names(source: str, polished: str) -> str:
    """
    Empêche les hallucinations sur noms (ضحى بنت ليلى → ضحى بنت الليلة بنت ليلى).
    Restaure la forme exacte du source si le corrigé a expansé le nom.
    """
    out = polished or ""
    if not source or not out:
        return out
    names = _uniq_keep_order(_extract_person_names(source) + _extract_bint_names(source))
    for name in names:
        parts = name.split()
        if len(parts) < 2:
            continue
        if "بنت" not in name and "بن" not in name:
            continue
        first, last = parts[0], parts[-1]
        # « X بنت … بنت Y » → « X بنت Y »
        out = re.sub(
            rf"{re.escape(first)}\s+بن(?:ت)?(?:\s+[\u0600-\u06FF]{{2,}}){{1,4}}\s+بن(?:ت)?\s+{re.escape(last)}",
            name,
            out,
        )
        # « X بنت Z Y » (mot parasite entre بنت et le patronyme source)
        if "بنت" in name or "بن" in name:
            mid = "بنت" if "بنت" in name else "بن"
            out = re.sub(
                rf"{re.escape(first)}\s+{mid}\s+(?!{re.escape(last)}\b)[\u0600-\u06FF]{{2,}}\s+{re.escape(last)}",
                name,
                out,
            )
        # Si le nom source a disparu mais une variante proche existe, forcer la forme source
        if not _fact_present(out, name):
            out = re.sub(
                rf"{re.escape(first)}\s+بن(?:ت)?\s+(?:ال)?[\u0600-\u06FF]{{2,}}(?:\s+بن(?:ت)?\s+(?:ال)?[\u0600-\u06FF]{{2,}}){{0,2}}",
                name,
                out,
                count=1,
            )
    return out


def preserve_source_facts(source: str, polished: str) -> str:
    """
    Réinjecte dans le texte corrigé les faits présents dans la source
    mais absents après le LLM (ne jamais « trancher » / résumer en silence).
    """
    out = (polished or "").strip() or (source or "").strip()
    if not source:
        return out

    out = restore_source_names(source, out)

    missing_cases = [c for c in _extract_case_numbers(source) if not _fact_present(out, c)]
    if missing_cases:
        forms: list[str] = []
        for c in missing_cases:
            form = c.replace("/", " على ") if ("على" in source or "/" in c) else c
            forms.append(form)
        injection = " و".join(f"ملف رقم {f}" for f in forms)
        if re.search(r"ملف|الملف", out):
            new_out, n = re.subn(
                r"((?:الملف|ملف)\s*(?:رقم|عدد)?\s*[:：]?\s*[0-9٠-٩]+(?:\s*(?:/|على)\s*[0-9٠-٩]+)?)",
                r"\1 و" + injection,
                out,
                count=1,
            )
            out = new_out if n else out
        if not all(_fact_present(out, c) for c in missing_cases):
            out = out.rstrip() + f"\n\n(أرقام ملفات مذكورة أيضاً في الإملاء: {' و '.join(forms)})."

    extras: list[str] = []
    missing_dates = [d for d in _extract_dates(source) if not _fact_present(out, d)]
    missing_amounts = [a for a in _extract_amounts(source) if not _fact_present(out, a)]
    missing_ages = [a for a in _extract_age_ranges(source) if not _fact_present(out, a)]
    missing_names = [
        n
        for n in _uniq_keep_order(_extract_person_names(source) + _extract_bint_names(source))
        if not _fact_present(out, n)
    ]
    if missing_dates:
        # Réinjection inline si possible
        for d in missing_dates:
            if not _fact_present(out, d):
                extras.append(d)
        if extras:
            out = out.rstrip() + f"\n\n(تواريخ مذكورة أيضاً في الإملاء: {' و '.join(extras)})."
            extras = []
    if missing_ages:
        out = out.rstrip() + f"\n\n(أعمار مذكورة أيضاً في الإملاء: {' و '.join(missing_ages)})."
    if missing_amounts:
        extras.append("مبالغ مذكورة أيضاً في الإملاء: " + " و ".join(missing_amounts))
    if missing_names:
        extras.append("أسماء مذكورة أيضاً في الإملاء: " + " و ".join(missing_names))
    missing_ideas = [i for i in extract_idea_phrases(source) if not idea_present(out, i)]
    if missing_ideas:
        extras.append("عناصر مذكورة أيضاً في الإملاء: " + " و ".join(missing_ideas))
    if extras:
        out = out.rstrip() + "\n\n(" + " | ".join(extras) + ")."
    return out.strip()


def strip_reinjection_notes(text: str) -> str:
    """Retire les notes « مذكورة أيضاً في الإملاء » pour juger le corps seul."""
    body = re.sub(
        r"\n*\(\s*[^)]*مذكورة أيضاً في الإملاء[^)]*\)\.?\s*",
        "\n",
        text or "",
    )
    return re.sub(r"\n{3,}", "\n\n", body).strip()


def list_missing_source_facts(source: str, polished: str) -> list[tuple[str, str]]:
    """Liste (kind, value) des faits source absents du corrigé — pour alertes UI."""
    if not source:
        return []
    missing: list[tuple[str, str]] = []
    for c in _extract_case_numbers(source):
        if not _fact_present(polished, c):
            missing.append(("case_number", c))
    for d in _extract_dates(source):
        if not _fact_present(polished, d):
            missing.append(("date", d))
    for a in _extract_amounts(source):
        if not _fact_present(polished, a):
            missing.append(("amount", a))
    for a in _extract_age_ranges(source):
        if not _fact_present(polished, a):
            missing.append(("age", a))
    for n in _uniq_keep_order(_extract_person_names(source) + _extract_bint_names(source)):
        if not _fact_present(polished, n):
            missing.append(("person_name", n))
    for idea in extract_idea_phrases(source):
        if not idea_present(polished, idea):
            missing.append(("idea", idea))
    return missing


# Phrases / idées distinctes (fond) — au-delà des seuls chiffres
_IDEA_SPECS: list[tuple[str, str]] = [
    # (label canonique, regex source)
    ("رجل وامرأتان", r"رجل\s*و\s*امر[اأ]ت(?:ين|ان|ي?ن)"),
    ("ثمانية أشخاص", r"(?:ثماني[ةه]|8)\s*أشخاص"),
    ("إيجار البشر", r"ا?يجا?ر\s*البشر"),
    ("الاتجار بالبشر", r"(?:الاتجار|اتجار|تجارة)\s*(?:بال)?بشر"),
    ("بالمخدرات", r"بالمخدرات|المخدرات"),
    ("نطالب بأقصى العقوبات", r"(?:باقسم|نطالب|نلتمس|نقسم).{0,24}عقوب"),
    ("تعويض الضحايا", r"تعويض"),
    ("تشديد العقوبات", r"تشديد"),
]


def extract_idea_phrases(text: str) -> list[str]:
    found: list[str] = []
    t = text or ""
    for label, pat in _IDEA_SPECS:
        if re.search(pat, t, flags=re.IGNORECASE):
            found.append(label)
    return _uniq_keep_order(found)


def idea_present(haystack: str, idea_label: str) -> bool:
    """Présence souple d'une idée (variantes orthographiques)."""
    h = haystack or ""
    for label, pat in _IDEA_SPECS:
        if label == idea_label:
            return bool(re.search(pat, h, flags=re.IGNORECASE))
    return _fact_present(h, idea_label)


def content_word_coverage(source: str, polished: str) -> float:
    """Ratio de mots de contenu du source encore présents dans le corrigé (0–1)."""
    src = {
        t
        for t in _tokenize_words(re.sub(r"[‹›]", "", source or ""))
        if _is_content_word(t) and len(t) >= 3
    }
    if not src:
        return 1.0
    pol = {
        t
        for t in _tokenize_words(re.sub(r"[‹›]", "", polished or ""))
        if _is_content_word(t)
    }
    # Tolérer variantes très proches (1 caractère)
    hit = 0
    for w in src:
        if w in pol or any(
            abs(len(w) - len(p)) <= 1 and SequenceMatcher(None, w, p).ratio() >= 0.85
            for p in pol
            if abs(len(w) - len(p)) <= 2
        ):
            hit += 1
    return hit / len(src)


def _tokenize_words(text: str) -> list[str]:
    """Tokens mots (arabe/latin/chiffres) + espaces/ponctuation séparés."""
    return re.findall(
        r"[\u0600-\u06FF]{2,}|[0-9٠-٩]+(?:[./][0-9٠-٩]+)*|[A-Za-z0-9]+|[^\s]| +|\n+",
        text or "",
    )


def _is_content_word(tok: str) -> bool:
    if not tok or tok.isspace() or tok in "\n":
        return False
    if re.fullmatch(r"[،.;:؟!?()\[\]«»‹›\"'…\-–—/]+", tok):
        return False
    if tok in _STOP_AR:
        return False
    if re.fullmatch(r"[\u0600-\u06FF]{2,}", tok):
        return True
    if re.fullmatch(r"[0-9٠-٩]{2,}", tok):
        return False  # chiffres seuls = faits, pas « guess » lexical
    return False


def _looks_like_stt_sub(src_w: str, pol_w: str) -> bool:
    """Vrai si pol_w semble une correction phonétique de src_w (pas une reformulation libre)."""
    a = (src_w or "").strip()
    b = (pol_w or "").strip()
    if not a or not b or a == b:
        return False
    if abs(len(a) - len(b)) > max(4, len(a) // 2 + 1):
        return False
    return SequenceMatcher(None, a, b).ratio() >= 0.48


def annotate_stt_guesses(source: str, polished: str) -> tuple[str, list[str]]:
    """Marque les substitutions STT (‹…›) pour le surlignage orange.

    Conserve les marqueurs déjà posés (fusḥā / LLM) et ajoute un diff
    phonétique conservateur mot à mot — pas les retouches mineures
    (hamza, tā marbūṭa) ni les faits chiffrés.
    """
    src_plain = re.sub(r"[‹›]", "", source or "")
    pol = polished or ""
    guessed: list[str] = []

    for tok in re.findall(r"‹([^›]{1,80})›", pol):
        t = (tok or "").strip()
        if t and t not in guessed:
            guessed.append(t)

    src_words = [w for w in src_plain.split() if w]
    pol_words = [w for w in re.sub(r"[‹›]", "", pol).split() if w]
    if not src_words or not pol_words:
        return pol, guessed

    sm = SequenceMatcher(a=src_words, b=pol_words, autojunk=False)
    rebuilt: list[str] = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        chunk = pol_words[j1:j2]
        if tag == "replace" and (i2 - i1) == 1 and (j2 - j1) == 1:
            a, b = src_words[i1], pol_words[j1]
            if (
                _is_content_word(b)
                and _looks_like_stt_sub(a, b)
                and _norm_cmp_token(a) != _norm_cmp_token(b)
            ):
                if not (b.startswith("‹") and b.endswith("›")):
                    b = f"‹{b}›"
                inner = b.strip("‹›")
                if inner and inner not in guessed:
                    guessed.append(inner)
                rebuilt.append(b)
                continue
        rebuilt.extend(chunk)

    # Réinjecter les ‹ › déjà présents si le rebuild les a aplatis
    out = " ".join(rebuilt) if rebuilt else re.sub(r"[‹›]", "", pol)
    for tok in list(guessed):
        if f"‹{tok}›" not in out and tok in out:
            out = out.replace(tok, f"‹{tok}›", 1)
    return out, guessed


def _norm_cmp_token(s: str) -> str:
    t = re.sub(r"[\u064B-\u065F\u0670\u0640]", "", s or "")
    t = t.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ة", "ه")
    return t


def detect_dictation_contradictions(
    polished: str,
    *,
    source: str | None = None,
) -> list[ContradictionAlert]:
    """
    Analyse déterministe sur l'union source + corrigé
    (si le LLM a droppé un fait, on le voit encore via la source).
    """
    texts = [polished or ""]
    if source:
        texts.append(source)
    joined_for_extract = "\n".join(texts)

    alerts: list[ContradictionAlert] = []

    cases = _uniq_keep_order(
        _extract_case_numbers(polished or "") + _extract_case_numbers(source or "")
    )
    # Retirer préfixes inclus
    cases = [v for v in cases if not any(v != w and v in w for w in cases)]
    if len(cases) >= 2:
        alerts.append(
            ContradictionAlert(
                kind="case_number",
                values=cases,
                message_ar=f"تم رصد أكثر من رقم ملف في إملائكم: {' و '.join(cases)}. أيهما الصحيح؟",
                message_fr=f"Plusieurs numéros de dossier détectés : {' / '.join(cases)}. Lequel est le bon ?",
            )
        )

    dates_src = _extract_labeled_dates(source or "")
    # Contradiction date : uniquement 2+ dates DIFFÉRENTES pour le MÊME événement
    by_event: dict[str, list[str]] = {}
    for label, date in dates_src:
        if not label or label.startswith("date@"):
            continue  # pas de libellé → pas d'alerte (événements distincts)
        by_event.setdefault(label, [])
        if date not in by_event[label]:
            by_event[label].append(date)
    for label, vals in by_event.items():
        if len(vals) >= 2:
            alerts.append(
                ContradictionAlert(
                    kind="date",
                    values=vals,
                    message_ar=(
                        f"تم رصد تواريخ مختلفة لنفس الواقعة ({label}): "
                        f"{' و '.join(vals)}. أيها الصحيح؟"
                    ),
                    message_fr=(
                        f"Dates différentes pour le même événement ({label}) : "
                        f"{' / '.join(vals)}. Laquelle est la bonne ?"
                    ),
                )
            )

    labeled_amts = _extract_labeled_amounts(source or "") + _extract_labeled_amounts(
        polished or ""
    )
    by_poste: dict[str, list[str]] = {}
    for label, amount in labeled_amts:
        if not label or label.startswith("amt@"):
            continue
        key = _amount_key(amount)
        by_poste.setdefault(label, [])
        if not any(_amount_key(x) == key for x in by_poste[label]):
            by_poste[label].append(amount)
    for label, vals in by_poste.items():
        if len(vals) >= 2:
            alerts.append(
                ContradictionAlert(
                    kind="amount",
                    values=vals,
                    message_ar=(
                        f"تم رصد مبالغ مختلفة لنفس البند ({label}): "
                        f"{' و '.join(vals)}. أيها الصحيح؟"
                    ),
                    message_fr=(
                        f"Montants différents pour le même poste ({label}) : "
                        f"{' / '.join(vals)}. Lequel est le bon ?"
                    ),
                )
            )

    # Noms : ne comparer que les variantes présentes dans la SOURCE
    # (évite ضحى بنت ليلى vs ضحى بنت أيوب inventé par le LLM)
    names = _uniq_keep_order(
        _extract_person_names(source or "") + _extract_bint_names(source or "")
    )
    if len(names) >= 2:
        used: set[str] = set()
        for i, a in enumerate(names):
            if a in used:
                continue
            group = [a]
            for b in names[i + 1 :]:
                if b in used:
                    continue
                if _names_look_similar(a, b):
                    group.append(b)
                    used.add(b)
            if len(group) >= 2:
                used.add(a)
                alerts.append(
                    ContradictionAlert(
                        kind="person_name",
                        values=group,
                        message_ar=f"تم رصد صيغ مختلفة لاسم: {' و '.join(group)}. أيها الصحيح؟",
                        message_fr=f"Variantes du même nom : {' / '.join(group)}. Laquelle garder ?",
                    )
                )

    # Faits source absents du corps (hors notes de réinjection) → alerte critique
    body_only = strip_reinjection_notes(polished or "")
    missing = list_missing_source_facts(source or "", body_only)
    if missing:
        values = _uniq_keep_order([v for _, v in missing])
        alerts.append(
            ContradictionAlert(
                kind="missing_fact",
                values=values,
                message_ar=(
                    "⚠️ حُذفت من التصحيح وقائع كانت في الإملاء: "
                    + " و ".join(values)
                    + ". أُعيد إدراجها أسفل النص — راجعوا قبل الاعتماد."
                ),
                message_fr=(
                    "⚠️ Des faits de la dictée ont disparu à la correction : "
                    + " / ".join(values)
                    + ". Ils ont été réinjectés — vérifiez avant de valider."
                ),
            )
        )

    return alerts
