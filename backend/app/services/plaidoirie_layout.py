"""Découpage / nettoyage du corps de plaidoirie — partagé Word + PDF."""

from __future__ import annotations

import re

_AR_MONTHS = (
    "يناير|فبراير|مارس|أبريل|ماي|يونيو|يوليوز|غشت|شتنبر|أكتوبر|نوفمبر|ديسمبر"
)

# Mots / passages mis en gras à l'export (mise en page uniquement — texte inchangé)
_EMPHASIS_RE = re.compile(
    rf"((?:^|\n)\s*(?:أولاً?|ثانياً?|ثالثاً?|رابعاً?|خامساً?|سادساً?|سابعاً?)\s*[:：\-—]?"
    rf"|\d{{1,2}}/\d{{1,2}}/\d{{4}}"
    rf"|\d{{1,2}}\s+(?:{_AR_MONTHS})\s+\d{{4}}"
    rf"|المادة\s+\d+"
    rf"|القانون\s+رقم\s+[\d.]+"
    rf"|مدونة\s+الشغل"
    rf"|قانون\s+المسطرة\s+المدنية"
    rf"|(?:الحجة|حجة\s+الخصم|الحجج)\s+عدد\s+[\d\sو]+"
    rf"|قرار\s+[^،.\n]{{0,120}}?\(\s*ملف\s+اجتماعي\s+عدد\s+[\d/]+\s*\)"
    rf"|ملف\s+اجتماعي\s+عدد\s+[\d/]+"
    rf"|\d{{1,3}}(?:,\d{{3}})+\s*درهم"
    rf"|\d+(?:\.\d+)?\s*درهم"
    rf"|←\s*[\d,]+(?:\s*درهم)?"
    rf"|=\s*[\d,]+\s*درهم"
    rf"|ذ\.?\s*م\.?\s*م\.?"
    rf"|السيد\s+[\u0600-\u06FF]{{2,18}}(?:\s+[\u0600-\u06FF]{{2,18}})?(?=\s*[،,؛]|$|\s+من|\s+لم|\s+ب)"
    rf"|شركة\s+[\u0600-\u06FF]{{2,18}}(?:\s+[\u0600-\u06FF]{{2,18}}){{1,2}}(?:\s+ذ\.?\s*م\.?\s*م\.?)?"
    rf"|\d+\s*×\s*[\d.]+\s*×\s*\d+\s*=\s*[\d,]+\s*درهم"
    rf"|\d+\s*×\s*[\d.]+\s*=\s*[\d,]+\s*درهم"
    rf")",
    re.UNICODE,
)

_LTR_CHUNK_RE = re.compile(
    rf"(\d{{1,2}}/\d{{1,2}}/\d{{4}}"
    rf"|\d{{1,2}}\s+(?:{_AR_MONTHS})\s+\d{{4}}"
    rf"|\d+\.\d+"
    rf"|\d{{1,3}}(?:,\d{{3}})+"
    rf"|\d+\s*×\s*[\d.]+\s*×\s*\d+\s*=\s*[\d,]+(?:\s*درهم)?"
    rf"|\d+\s*×\s*[\d.]+\s*=\s*[\d,]+(?:\s*درهم)?"
    rf"|\d+(?:\.\d+)?\s*درهم"
    rf"|[A-Za-z][A-Za-z0-9\s\-'\.&éèêàâùûôîçÉÈÊÀÂÙÛÔÎÇ]+"
    rf"|\(\s*[\d،,\s]+\s*\))",
)

_RLM = "\u200F"

_SECTION_SPLIT_RE = re.compile(
    r"(?=(?:^|\n)\s*(?:"
    r"أولاً|ثانياً|ثالثاً|رابعاً|خامساً|سادساً|سابعاً|"
    r"لهذه\s*الأسباب|وبناءً?\s*عليه|الوقائع|المناقشة|الطلبات|الملتمسات|"
    r"تحديد\s*الأطراف|صيغة|"
    r"First|Second|Third|Par ces motifs"
    r")\s*[:：.\-–—]?)",
    re.MULTILINE | re.IGNORECASE,
)

_SECTION_HEAD_RE = re.compile(
    r"^(?:"
    r"أولاً|ثانياً|ثالثاً|رابعاً|خامساً|سادساً|سابعاً|"
    r"لهذه\s*الأسباب|الوقائع|المناقشة|الطلبات|الملتمسات|"
    r"تحديد\s*الأطراف|الأطراف|صيغة|"
    r"أولاً\s*[-—]\s*في|ثانياً\s*[-—]\s*في|ثالثاً\s*[-—]\s*في|"
    r"رابعاً\s*[-—]\s*في|في\s*الشكل|في\s*الوقائع|في\s*المناقشة|"
    r"في\s*المناقشة\s*القانونية|في\s*المسؤولية|"
    r"المتهم|الضحايا|رقم\s*الملف|تاريخ\s*الجلسة"
    r")",
    re.IGNORECASE,
)

_FOOTER_LINE_RE = re.compile(
    r"^(?:حرر\s*ب|التوقيع|خاتم\s*المحامي|ذ\.?\s*$|الأستاذ\s*$)",
    re.IGNORECASE,
)

_HEADER_LINE_RE = re.compile(
    r"^(?:المملكة\s*المغربية|Royaume\s+du\s+Maroc|المكتب\s*:|المحامي\s*[:：]|"
    r"المحامي\s*المعد|تاريخ\s*التحرير|الدار\s*البيضاء\s*،?\s*في)",
    re.IGNORECASE,
)


def normalize_arabic_commas(text: str) -> str:
    """Virgules arabes (،) — sans toucher aux milliers (112,200)."""
    t = text or ""
    if not t:
        return t
    slots: dict[str, str] = {}

    def _stash(m: re.Match[str]) -> str:
        key = f"\x00N{len(slots)}\x00"
        slots[key] = m.group(0)
        return key

    t = re.sub(r"\d{1,3}(?:,\d{3})+", _stash, t)
    t = t.replace(",", "،")
    for key, val in slots.items():
        t = t.replace(key, val)
    return t


def sanitize_export_text(text: str) -> str:
    """Retire caractères de remplacement / contrôles qui cassent PDF/Word."""
    if not text:
        return ""
    t = text.replace("\ufeff", "").replace("\u00ad", "").replace("\ufffd", "")
    t = t.replace("\u2028", "\n").replace("\u2029", "\n")
    t = re.sub(r"[\u0000-\u0008\u000b\u000c\u000e-\u001f]", "", t)
    t = re.sub(r"[\ue000-\uf8ff]", "", t)  # private use
    t = re.sub(r"[\u2060\u2066-\u2069]", "", t)  # isolates parasites
    # Carrés / cases à cocher / puces symboliques → tiret simple (évite tofu [] en PDF)
    t = re.sub(r"[\u25a0-\u25ff\u2610\u2611\u2612\u2b1a-\u2b1c\ufffc\ufffd□■◻◼▪▫●○•‣⁃∙]", "", t)
    t = re.sub(r"\[\s*\]", "", t)
    # Puces / tirets en tête de ligne → en-dash ASCII-safe pour Noto
    t = re.sub(
        r"(?m)^[\s]*(?:[-*–—•▪▫●○□■◦‣⁃]|\[[\sxX]?\])\s+",
        "– ",
        t,
    )
    return t


def fix_word_export_bidi(text: str) -> str:
    """RLM après ponctuation arabe (pas les blocs chiffres — gérés en runs LTR Word)."""
    if not text:
        return text
    t = text.replace("\r\n", "\n")
    return re.sub(
        r"([\u0600-\u06FF])([.،:؛!?])(?=\s|$|\n)(?!\u200F)",
        rf"\1\2{_RLM}",
        t,
    )


def split_typography_runs(text: str) -> list[tuple[str, bool, bool]]:
    """
    Découpe un paragraphe en runs (texte, gras?, ltr?).
    Les îlots LTR (65.99, dates, montants) sont isolés AVANT le gras typographique.
    """
    t = fix_word_export_bidi(normalize_arabic_commas(text or ""))
    if not t:
        return []

    runs: list[tuple[str, bool, bool]] = []
    pos = 0
    while pos < len(t):
        m = _LTR_CHUNK_RE.search(t, pos)
        if not m or m.start() > pos:
            rtl_end = m.start() if m else len(t)
            runs.extend(_emphasis_runs(t[pos:rtl_end], force_ltr=False))
            if not m:
                break
        chunk = m.group(0)
        end = m.end()
        # Ponctuation finale collée au bloc chiffres/date → même run LTR (évite « . » orphelin)
        while end < len(t) and t[end] in ".،:؛!?":
            chunk += t[end]
            end += 1
        runs.extend(_emphasis_runs(chunk, force_ltr=True))
        pos = end
    if runs:
        return runs
    return [(t, False, False)]


def _emphasis_runs(segment: str, *, force_ltr: bool) -> list[tuple[str, bool, bool]]:
    if force_ltr:
        emph = bool(_EMPHASIS_RE.search(re.sub(r"[\u200F\u200E]", "", segment)))
        return [(segment, emph, True)]
    parts = _EMPHASIS_RE.split(segment)
    out: list[tuple[str, bool, bool]] = []
    for i, part in enumerate(parts):
        if not part:
            continue
        out.append((part, i % 2 == 1, force_ltr))
    return out or [(segment, False, force_ltr)]


def is_section_heading(text: str) -> bool:
    t = (text or "").strip()
    if not t or "\n" in t:
        return False
    if len(t) > 60:
        return False
    if re.match(
        r"^(?:القول|الحكم|الأمر|وشكرا|حيث|بما\s*أن|وحيث|تطالب|نلتمس|يلتمس|انعقد|رزق|توقف|وفقاً|إن|تأسيساً)",
        t,
    ):
        return False
    # Phrase d'intro aux ملتمسات — corps regular, pas titre bleu
    if re.match(r"^لهذه\s*الأسباب", t) and (len(t) > 55 or re.search(r"يلتمس|نطلب|نحكم", t)):
        return False
    # Ordinal seul ou avec texte factuel : si c'est du texte narratif, pas un titre
    if re.match(r"^(?:أولاً?|ثانياً?|ثالثاً?|رابعاً?|خامساً?|سادساً?|سابعاً?)\s*[:：\-—]?\s*", t):
        if re.search(r"في\s+(?:الشكل|الوقائع|الموضوع|المناقشة|المسؤولية|الطلبات)|الدفوع|الطلبات|الملتمسات", t):
            return True
        if len(t) > 20:
            return False
    return bool(_SECTION_HEAD_RE.match(t))


_ORDINAL_HEAD_RE = re.compile(
    r"^(أولاً?|ثانياً?|ثالثاً?|رابعاً?|خامساً?|سادساً?|سابعاً?)"
    r"(?:\s*[:：]?\s*(?:في\s+[\u0600-\u06FF]{2,24}(?:\s+[\u0600-\u06FF]{2,24}){0,4})?)?"
    r"\s*[:：]?\s*",
)


def _split_ordinal_heading(text: str) -> list[str]:
    """Sépare un vrai sous-titre de section (ex: « أولاً — في الشكل ») du texte suivant."""
    t = (text or "").strip()
    m = _ORDINAL_HEAD_RE.match(t)
    if not m:
        return [t]
    head = m.group(0).strip().rstrip(" :：")
    rest = t[m.end() :].strip(" :：")
    if rest and rest != head:
        # Ne séparer que si head est un vrai titre procédural (ex: "أولاً : في الشكل")
        if re.search(r"في\s+(?:الشكل|الوقائع|الموضوع|المناقشة|المسؤولية|الطلبات|الدعوى)|الدفوع", head) and len(head) < 45:
            return [f"{head} :", rest]
        # Sinon, pour les faits ou arguments (ex: "أولاً : انعقد زواج..."), garder le paragraphe uni !
        return [t]
    return [t if t.endswith((":", "：")) else f"{head} :"]


def _flatten_lines(text: str) -> list[str]:
    """Découpe les retours ligne simples puis listes numérotées inline."""
    t = (text or "").strip()
    if not t:
        return []
    if "\n" not in t:
        out: list[str] = []
        for part in _split_ordinal_heading(t):
            out.extend(_split_numbered_inline(part))
        return out
    out: list[str] = []
    for line in t.split("\n"):
        line = line.strip()
        if not line:
            continue
        for part in _split_ordinal_heading(line):
            out.extend(_split_numbered_inline(part))
    return out


def _split_numbered_inline(text: str) -> list[str]:
    """Découpe « 1. … 2. … 3. … » collés sur une ligne en paragraphes."""
    t = (text or "").strip()
    if not t:
        return []
    # Au moins deux items numérotés
    if len(re.findall(r"(?:^|\s)\d{1,2}\s*[.)]\s+\S", t)) < 2:
        return [t]
    parts = re.split(r"(?=(?:^|\s)\d{1,2}\s*[.)]\s+)", t)
    out = [p.strip() for p in parts if p and p.strip()]
    return out if len(out) > 1 else [t]


def prepare_plaidoirie_blocks(body: str) -> list[str]:
    """
    Corps normalisé pour Word et PDF (même découpage).
    Retire en-tête/pied dupliqués ; découpe sections et listes numérotées.
    """
    text = (body or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return []
    text = sanitize_export_text(text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Nettoyage artefacts avant découpage
    text = re.sub(r"\[\s*\]", "", text)
    text = re.sub(r"([:：])\s*[—\-–]+\s*", r"\1 ", text)
    text = re.sub(r"([:：])\s*/\s*", r"\1 ", text)
    text = re.sub(r"صيغة\s*الختام\s*[:：]?\s*", "", text)
    text = re.sub(r"\bCasablanca\b", "الدار البيضاء", text, flags=re.IGNORECASE)

    # Séparer "تحديد الأطراف :" sur sa propre ligne de titre
    text = re.sub(r"(?m)^(تحديد\s*الأطراف\s*[:：]?)\s*([^\n]+)$", r"\1\n\2", text)

    # Fusionner les ordinaux orphelins (ex: "أولاً :" seul sur sa ligne) avec la ligne suivante
    text = re.sub(
        r"(?m)^((?:أولاً?|ثانياً?|ثالثاً?|رابعاً?|خامساً?|سادساً?|سابعاً?)\s*[:：\-—]?)\s*\n+\s*(?!\n)",
        r"\1 ",
        text,
    )
    # Supprimer les numéros orphelins isolés sur une ligne (ex: "5)" ou "(5")
    text = re.sub(r"(?m)^\s*(?:\(?\d{1,2}\)?|\d{1,2}[.)])\s*(?=\n|$)", "", text)
    # Nettoyer les puces numérotées avant les titres de section (ex: "2) في الشكل:" -> "في الشكل:")
    text = re.sub(
        r"(?m)^\s*\d{1,2}\s*[.)]\s*(في\s+الشكل|في\s+الوقائع|في\s+المناقشة|في\s+الموضوع|لهذه\s+الأسباب|الوقائع|المناقشة|الملتمسات)",
        r"\1",
        text,
    )
    # Nettoyer les tirets/puces parasites devant les rôles des parties (ex: "— المدعى عليه:" -> "المدعى عليه:")
    text = re.sub(
        r"(?m)^[\s]*[—–-]\s*(المدعي|المدعية|المدعى|المتهم|الظنين|الضح|المطالب|السيد|السيدة|شركة)",
        r"\1",
        text,
    )

    blocks: list[str] = []
    for chunk in re.split(r"\n\s*\n", text):
        chunk = chunk.strip()
        if not chunk:
            continue
        # Toujours découper si sections collées (même ligne courte)
        inline_parts = _SECTION_SPLIT_RE.split(chunk)
        inline_parts = [p.strip() for p in inline_parts if p and p.strip()]
        if len(inline_parts) > 1:
            for p in inline_parts:
                blocks.extend(_flatten_lines(p))
            continue
        if "\n" not in chunk and len(chunk) > 280:
            parts = _SECTION_SPLIT_RE.split(chunk)
            parts = [p.strip() for p in parts if p and p.strip()]
            if len(parts) > 1:
                for p in parts:
                    blocks.extend(_flatten_lines(p))
                continue
        blocks.extend(_flatten_lines(chunk))

    cleaned: list[str] = []
    for b in blocks:
        b = re.sub(r"\[\s*\]", "", b).strip()
        b = re.sub(r"\s{2,}", " ", b)
        if not b:
            continue
        if _HEADER_LINE_RE.match(b):
            continue
        if _FOOTER_LINE_RE.match(b):
            continue
        if re.search(r"حرر\s*ب.+(?:التوقيع|خاتم|بتاريخ)", b) and len(b) < 240:
            continue
        b = re.sub(r"\[\s*\]", "", b).strip()
        b = re.sub(r"[\u25a0-\u25ff\u2610\u2611\u2612\u2b1a-\u2b1c\ufffc\ufffd□■◻◼▪▫●○•]", "", b).strip()
        b = re.sub(r"(?m)^[\s]*(?:[-*–—]|\[[\sxX]?\])\s+", "– ", b).strip()
        if not b:
            continue
        if re.match(r"^تحت\s*جميع\s*التحفظات", b) and "ملتمس" not in b:
            cleaned.append(b)
            continue
        if re.match(r"^(?:واحسبكم|وذلك\s*مع\s*الاحتفاظ)", b):
            cleaned.append(b)
            continue
        fold = re.sub(r"\s+", "", b)
        if len(fold) > 48:
            dup = False
            for prev in cleaned[-3:]:
                pf = re.sub(r"\s+", "", prev)
                if fold == pf or (len(fold) > 60 and fold in pf) or (len(pf) > 60 and pf in fold):
                    dup = True
                    break
            if dup:
                continue
        cleaned.append(b)

    while cleaned and _FOOTER_LINE_RE.match(cleaned[-1]):
        cleaned.pop()

    return cleaned
