"""Post-traitement plaidoirie : rôles procéduraux, numérotation, clôture, typos STT."""

from __future__ import annotations

import re

_ORDINALS = ("أولاً", "ثانياً", "ثالثاً", "رابعاً", "خامساً", "سادساً", "سابعاً")

_CRIMINAL_KW = re.compile(
    r"ضحا|جرائم|جنائ|زجر|متهم|ظنين|مخدر|اتجار\s*بالبشر|شبكة|عصاب",
    re.IGNORECASE,
)
_VICTIM_KW = re.compile(r"ضحا|طرف\s*مدني|مطالب\s*بالحق\s*المدني|فتيات|فتيان", re.IGNORECASE)
_ACCUSED_KW = re.compile(r"هنية|عصاب|متهم|ظنين|سيدات|رجال", re.IGNORECASE)

_CLOSING_POLITE = "واحسبكم على حسن استماعكم، وتقبلوا فائق الاحترام والتقدير."
_CLOSING_RESERVE = (
    "وذلك مع الاحتفاظ لموكلنا بكافة حقوقه القانونية الأخرى، "
    "تحت جميع التحفظات الشرعية والقانونية."
)

_SECTION_ORDINAL_RE = re.compile(
    r"(?m)(?:^|\n)\s*"
    r"(أولاً?|ثانياً?|ثالثاً?|رابعاً?|خامساً?|سادساً?|سابعاً?)"
    r"\s*[:：\-—]?\s*"
)

_ORDINAL_CANON = {
    "أولا": "أولاً",
    "أولاً": "أولاً",
    "ثانيا": "ثانياً",
    "ثانياً": "ثانياً",
    "ثالثا": "ثالثاً",
    "ثالثاً": "ثالثاً",
    "رابعا": "رابعاً",
    "رابعاً": "رابعاً",
    "خامسا": "خامساً",
    "خامساً": "خامساً",
    "سادسا": "سادساً",
    "سادساً": "سادساً",
    "سابعا": "سابعاً",
    "سابعاً": "سابعاً",
}

_EXPORT_HEADER_RE = re.compile(
    r"^(?:المملكة\s*المغربية|Royaume\s+du\s+Maroc|"
    r"المكتب\s*[:：]|المحامي\s*المعد\s*[:：]|تاريخ\s*التحرير\s*[:：])",
    re.IGNORECASE,
)

_PARTY_RULES: dict[str, dict[str, str]] = {
    "partie-civile": {
        "client": "الضحايا (الطرف المدني)",
        "opponent": "المتهم(ون) / الظنين(ون)",
    },
    "penal-defense": {
        "client": "المتهم / الظنين",
        "opponent": "النيابة العامة",
    },
    "penal-ordinaire": {
        "client": "المتهم / الظنين",
        "opponent": "النيابة العامة",
    },
    "civil-general": {
        "client": "المدعي(ة)",
        "opponent": "المدعى عليه(ا)",
    },
    "civil-defense": {
        "client": "المدعى عليه(ا)",
        "opponent": "المدعي(ة)",
    },
}


def count_dictation_sections(text: str) -> int:
    """Nombre d'ordinales (أولاً…خامساً) détectées dans la dictée."""
    return len(_SECTION_ORDINAL_RE.findall(text or ""))


def list_dictation_ordinals(text: str) -> list[str]:
    found: list[str] = []
    for raw in _SECTION_ORDINAL_RE.findall(text or ""):
        canon = _ORDINAL_CANON.get(raw, raw)
        if canon not in found:
            found.append(canon)
    return found


def fidelity_structure_plaidoirie(source: str) -> str:
    """
    Assemble le BODY depuis la dictée SANS réécriture LLM.
    Conserve chaque section (أولاً…خامساً) et son texte intégral.
    """
    src = (source or "").replace("\r\n", "\n").strip()
    if not src:
        return ""

    # Forcer les ordinales en début de ligne
    t = _SECTION_ORDINAL_RE.sub(
        lambda m: "\n\n" + _ORDINAL_CANON.get(m.group(1), m.group(1)) + " : ",
        src,
    )
    t = re.sub(r"\n{3,}", "\n\n", t).strip()

    # Intro → parties si on détecte مدعي / شركة
    parts = re.split(r"(?m)^(?=أولاً\s*[:：])", t, maxsplit=1)
    intro = parts[0].strip() if parts else ""
    rest = parts[1].strip() if len(parts) > 1 else t

    party_lines: list[str] = []
    plaintiff = ""
    defendant = ""
    pm = re.search(
        r"(?:موكلي|المدعي|السيد)\s*،?\s*(?:السيد\s+)?([^\n،,]{4,60}?)"
        r"(?=،\s*لمدة|،\s*من\s+\d|بمنصب|لمدة)",
        intro,
    )
    if pm:
        plaintiff = re.sub(r"\s+", " ", pm.group(1)).strip(" ،.")
    dm = re.search(
        r"بشركة\s+([^\n.،]{3,80}?)(?=\.|إحدى|يوم|$)",
        intro,
    )
    if not dm:
        dm = re.search(r"شركة\s+([^\n.،]{3,60}?(?:ذ\.?\s*م\.?\s*م)?)", intro)
    if dm:
        defendant = "شركة " + re.sub(r"\s+", " ", dm.group(1)).strip(" ،.")
        if not defendant.startswith("شركة شركة"):
            pass
        if defendant.startswith("شركة شركة"):
            defendant = defendant[len("شركة ") :]

    job = ""
    jm = re.search(r"بمنصب\s+([^\n.،]{3,80})", intro)
    if jm:
        job = re.sub(r"\s+", " ", jm.group(1)).strip(" ،.")

    if plaintiff or defendant:
        party_lines.append("تحديد الأطراف")
        party_lines.append("")
        if plaintiff:
            line = f"المدعي : {plaintiff}"
            if job:
                line += f" — {job}"
            party_lines.append(line)
            party_lines.append("")
        if defendant:
            party_lines.append(f"المدعى عليها : {defendant}")
            party_lines.append("")

    # Garder une intro courte (adresse au tribunal) si présente
    intro_keep = ""
    if re.search(r"السيد\s*الرئيس|السادة\s*المستشار", intro):
        first = intro.split("\n", 1)[0].strip()
        if len(first) < 120:
            intro_keep = first

    blocks: list[str] = []
    if party_lines:
        blocks.append("\n".join(party_lines).strip())
    if intro_keep:
        blocks.append(intro_keep)
    # Si pas d'ordinales dans rest, garder tout le texte source
    if not re.search(r"(?m)^أولاً\s*[:：]", rest) and count_dictation_sections(src) == 0:
        blocks.append(t)
    else:
        # Intro narrative avant أولاً (faits) — la garder après les parties
        if intro and not party_lines:
            blocks.append(intro)
        elif intro and party_lines:
            # Faits d'intro (sans la 1re ligne d'adresse déjà mise)
            narrative = intro
            if intro_keep and narrative.startswith(intro_keep):
                narrative = narrative[len(intro_keep) :].strip()
            if narrative and len(narrative) > 40:
                blocks.append(narrative)
        blocks.append(rest)

    out = "\n\n".join(b for b in blocks if b).strip()
    out = dedupe_consecutive_section_heads(out)
    out = repair_parties_parentheses(out)
    return re.sub(r"\n{3,}", "\n\n", out).strip()


def dedupe_consecutive_section_heads(text: str) -> str:
    """Supprime un titre de section répété deux fois de suite (bug assemblage)."""
    t = (text or "").replace("\r\n", "\n")
    t = re.sub(
        r"(?m)^(\s*(?:أولاً|ثانياً|ثالثاً|رابعاً|خامساً|سادساً)[^\n]*)\n+"
        r"\1\s*\n",
        r"\1\n",
        t,
    )
    # Même titre avec variation d'espaces
    lines = t.split("\n")
    out: list[str] = []
    prev_head = ""
    for line in lines:
        head_m = re.match(
            r"^\s*((?:أولاً|ثانياً|ثالثاً|رابعاً|خامساً|سادساً)\s*[:：\-—].*)$",
            line.strip(),
        )
        if head_m:
            key = re.sub(r"\s+", " ", head_m.group(1)).strip()
            if key == prev_head:
                continue
            prev_head = key
        else:
            if line.strip():
                prev_head = ""
        out.append(line)
    return "\n".join(out)


def repair_parties_parentheses(text: str) -> str:
    """Répare parenthèses cassées / mashup المدعي + المدعى عليها sur une ligne."""
    t = text or ""
    # Mashup LLM : المدعي : X (— titre (المدعى عليها) : Y
    t = re.sub(
        r"(المدعي(?:ة)?\s*[:：]\s*)([^\n(]+?)\s*\(\s*[—–\-]*\s*"
        r"([^\n(]+?)\s*\(\s*(المدعى\s*عليه(?:ا|م)?)\s*\)\s*[:：]\s*([^\n]+)",
        lambda m: (
            f"{m.group(1)}{m.group(2).strip()} — {m.group(3).strip()}\n"
            f"{m.group(4).strip()} : {m.group(5).strip()}"
        ),
        t,
        count=1,
        flags=re.I,
    )
    # Variante sans double paren
    t = re.sub(
        r"(المدعي(?:ة)?\s*[:：]\s*)([^\n]+?)\s*[—(]+\s*[—–\-]*\s*"
        r"([^\n]+?)\s+(المدعى\s*عليه(?:ا|م)?)\s*[:：]\s*([^\n]+)",
        lambda m: (
            f"{m.group(1)}{m.group(2).strip()} — {m.group(3).strip()}\n"
            f"{m.group(4).strip()} : {m.group(5).strip()}"
        ),
        t,
        count=1,
        flags=re.I,
    )
    # Orphelin « (— » ou « (– »
    t = re.sub(r"\(\s*[—–\-]+\s*", "— ", t)
    # Parenthèses non fermées en fin de ligne parties
    def _balance_line(line: str) -> str:
        if "المدع" not in line and "المتهم" not in line and "الضحايا" not in line:
            return line
        opens = line.count("(")
        closes = line.count(")")
        if opens > closes:
            return line + (")" * (opens - closes))
        if closes > opens:
            # Retirer fermetures en trop en fin
            extra = closes - opens
            out = line
            for _ in range(extra):
                out = re.sub(r"\)\s*$", "", out)
            return out
        return line

    t = "\n".join(_balance_line(ln) for ln in t.split("\n"))
    # Fragment export « (نا بكافة حقوقه) »
    t = re.sub(r"\(نا بكافة حقوقه(?:ا)?\)", "موكلنا بكافة حقوقه", t)
    t = re.sub(r"موكل\s*\(ي\)\s*نا", "موكلنا", t)
    t = re.sub(r"حقوقه\s*\(ا\)", "حقوقه", t)
    return t


def compose_completeness_check(source: str, body: str) -> tuple[bool, list[str]]:
    """
    Filet anti-troncature : compare sections / longueur dictée vs document.
    Retourne (ok, warnings).
    """
    warnings: list[str] = []
    src = source or ""
    out = body or ""
    src_secs = list_dictation_ordinals(src)
    out_secs = list_dictation_ordinals(out)
    missing = [s for s in src_secs if s not in out_secs]
    if missing:
        warnings.append(
            "⚠️ المستند المُولَّد يبدو ناقصاً مقارنة بإملائكم — أقسام مفقودة: "
            + "، ".join(missing)
            + ". يُرجى التحقق قبل المتابعة."
        )
        warnings.append(
            "⚠️ Le document généré semble incomplet par rapport à votre dictée "
            f"(sections manquantes : {', '.join(missing)}). Vérifiez avant de continuer."
        )

    # Longueur : ignorer espaces
    src_len = len(re.sub(r"\s+", "", src))
    out_len = len(re.sub(r"\s+", "", out))
    if src_len >= 400 and out_len < int(src_len * 0.55):
        warnings.append(
            "⚠️ Le document généré est nettement plus court que votre dictée "
            f"({out_len}/{src_len} car. utiles ≈ {int(100 * out_len / max(src_len, 1))}%). "
            "Vérifiez qu’aucune section n’a été tronquée."
        )

    # Séquence sans saut
    order = list(_ORDINALS)
    idxs = [order.index(s) for s in out_secs if s in order]
    for a, b in zip(idxs, idxs[1:]):
        if b > a + 1:
            skipped = order[a + 1 : b]
            warnings.append(
                "⚠️ Numérotation incomplète — saut détecté (manque : "
                + "، ".join(skipped)
                + ")."
            )
            break

    ok = not missing and not any("nettement plus court" in w or "ناقصاً" in w for w in warnings)
    return ok, warnings


def fix_lawyer_title_fragments(text: str) -> str:
    t = text or ""
    t = re.sub(r"المحامي\s*لـ?\s*ة\b", "المحامية", t)
    t = re.sub(r"محامي\s*لـ?\s*ة\b", "المحامية", t)
    t = re.sub(r"المحامي\s*ية\b", "المحامية", t)
    return t


def strip_export_duplicates(text: str) -> str:
    """Retire en-tête/pied/titre dupliqués (l'export Word les ajoute seul)."""
    t = (text or "").replace("\r\n", "\n").strip()
    if not t:
        return t
    t = re.sub(
        r"(?ms)^\s*المملكة\s*المغربية\s*\n\s*Royaume\s+du\s+Maroc\s*\n?",
        "",
        t,
    )
    lines: list[str] = []
    for raw in t.split("\n"):
        line = raw.strip()
        if _EXPORT_HEADER_RE.match(line):
            continue
        if re.match(r"^(?:حرر\s*ب|التوقيع|خاتم\s*المحامي)\b", line, re.IGNORECASE):
            continue
        lines.append(raw)
    t = "\n".join(lines).strip()
    t = re.sub(
        r"(?ms)(?:^|\n)\s*حرر\s*ب[^\n]*(?:\n\s*(?:التوقيع|خاتم)[^\n]*)*\s*$",
        "",
        t,
    ).strip()
    t = re.sub(r"(?m)^\s*خاتمة\s*[:：]\s*شكراً\.?\s*$", "", t)
    t = re.sub(r"\s*خاتمة\s*[:：]\s*شكراً\.?\s*", "\n\n", t)
    return t.strip()


def split_glued_sections(text: str) -> str:
    """Sépare titre, أطراف et sections collées sur une seule ligne."""
    t = (text or "").replace("\r\n", "\n").strip()
    if not t:
        return t
    # « مرافعة حرة المتهم(ة) » → titre + section
    t = re.sub(
        r"^(مرافعة\s+[^\n:：]{0,40}?)\s*(?=المتهم|الضحايا|تحديد\s*الأطراف|الأطراف)",
        r"\1\n\n",
        t,
        count=1,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"^(مرافعة\s+[^\n:：]{0,40}?)\s*(?:الأطراف|تحديد\s*الأطراف)\s*[:：]",
        r"\1\n\nتحديد الأطراف\n",
        t,
        count=1,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"(?<!\n)\s*(تحديد\s*الأطراف|الأطراف)\s*[:：]",
        r"\n\n\1 :",
        t,
    )
    t = re.sub(
        r"(?<!\n)\s*(أولاً|ثانياً|ثالثاً|رابعاً|خامساً|سادساً|لهذه\s*الأسباب|الملتمسات)\s*[:：]",
        r"\n\n\1 :",
        t,
    )
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def _wrap_parens(value: str) -> str:
    v = (value or "").strip()
    if not v:
        return v
    if v.startswith("(") and v.endswith(")"):
        inner = v[1:-1].strip()
        if inner.count("(") == inner.count(")"):
            return v
    return f"({v})"


def _format_party_value(text: str) -> str:
    """Nom + détails avec parenthèses équilibrées."""
    s = (text or "").strip()
    if not s:
        return s
    parts = [p.strip() for p in re.split(r"\s*[—–\-]\s*", s) if p.strip()]
    if len(parts) <= 1:
        return _wrap_parens(s)
    formatted = [_wrap_parens(parts[0])]
    for p in parts[1:]:
        if p.startswith("(") and p.endswith(")"):
            formatted.append(p)
        else:
            formatted.append(_wrap_parens(p))
    return " — ".join(formatted)


_PLACEHOLDER_LINE_RE = re.compile(
    r"^\s*(?:\[\s*يُستكمل[^\]]*\]|\(يُستكمل\)|\[\s*يُستكمل\s*\]|…{2,}|\.{4,})\s*$",
    re.I | re.M,
)
_PLACEHOLDER_INLINE_RE = re.compile(r"\[\s*يُستكمل[^\]]*\]|\(يُستكمل\)", re.I)

_INTERNAL_INSTRUCTION_RE = re.compile(
    r"(?m)^\s*(?:"
    r"خاتمة\s*قصيرة(?:\s*\+\s*تحفظات)?|"
    r"7\)\s*خاتمة[^\n]*|"
    r"خاتمة\s*\+\s*تحفظات"
    r")\s*[:：]?\s*$",
    re.I,
)


def strip_internal_instructions(text: str) -> str:
    t = (text or "").replace("\r\n", "\n")
    t = _INTERNAL_INSTRUCTION_RE.sub("", t)
    t = re.sub(r"(?<=\n)\s*خاتمة\s*قصيرة\s*\+\s*تحفظات\s*(?=\n)", "", t, flags=re.I)
    t = re.sub(r"(?<=[:\n])\s*خاتمة\s*قصيرة\s*\+\s*تحفظات\s*(?=\n|$)", "", t, flags=re.I)
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def _is_placeholder_content(content: str) -> bool:
    c = (content or "").strip()
    if not c:
        return True
    if _PLACEHOLDER_LINE_RE.match(c):
        return True
    if _PLACEHOLDER_INLINE_RE.fullmatch(c):
        return True
    if c in {"…", "......", "—", "-", "–"}:
        return True
    return False


def _default_form_paragraph(source: str, plaidoirie_type: str | None) -> str:
    if _CRIMINAL_KW.search(source or ""):
        return (
            "حيث إن الدعوى مقبولة للتداول شكلاً، وتتوفر المحكمة على الاختصاص "
            "والولاية القضائية، مما يتعين معه السير في المناقشة."
        )
    return (
        "حيث إن الدعوى مستوفية لكافة الشروط الشكلية المتطلبة قانوناً، "
        "مما يتعين معه التصريح بقبولها شكلاً."
    )


def _extract_discussion_from_source(source: str) -> str:
    src = (source or "").replace("\r\n", "\n")
    chunks: list[str] = []
    for pat in (
        r"[^.\n]{20,400}?(?:نطلب|نلتمس|يلتمس)[^.\n]{5,400}?[.؟]",
        r"[^.\n]{20,400}?(?:بتشديد|أقصى\s*العقوبات|حقوق\s*[^\s.\n]{2,30})[^.\n]{5,300}?[.؟]",
    ):
        for m in re.finditer(pat, src, flags=re.I):
            s = re.sub(r"\s+", " ", m.group(0)).strip()
            if s and s not in chunks and len(s) > 25:
                chunks.append(s)
    return " ".join(chunks[:2]).strip()


def _extract_facts_from_source(source: str) -> str:
    src = (source or "").replace("\r\n", "\n")
    for pat in (
        r"إن\s*المرافعة[^.\n]{20,800}[.؟]",
        r"[^.\n]{30,800}?(?:جرائم|تورط|عصاب)[^.\n]{10,800}[.؟]",
    ):
        m = re.search(pat, src, flags=re.I)
        if m:
            return re.sub(r"\s+", " ", m.group(0)).strip()
    return ""


def sanitize_sections_for_output(
    text: str,
    *,
    source: str = "",
    plaidoirie_type: str | None = None,
    for_export: bool = False,
) -> tuple[str, list[str]]:
    """
    Nettoie placeholders — SANS inventer de phrases ni supprimer de sections
    qui ont du contenu réel dans la source.
    """
    warnings: list[str] = []
    t = strip_internal_instructions(text)
    src = source or t

    # Remplacer placeholders vides par alerte — jamais de phrase inventée
    def _warn_placeholder(label: str) -> None:
        msg = (
            f"⚠️ القسم « {label} » ناقص في المستند — أكملوه يدوياً قبل التصدير "
            "(لا يُختلق أي نص)."
        )
        if msg not in warnings:
            warnings.append(msg)

    # Lignes placeholder seules sous un titre → retirer le marqueur, garder le titre
    t = re.sub(
        r"(?m)^(\s*(?:أولاً|ثانياً|ثالثاً|رابعاً|خامساً)[^\n]*\n)\s*\[\s*يُستكمل[^\]]*\]\s*\n?",
        r"\1",
        t,
    )
    if re.search(r"(?m)^\s*أولاً[^\n]*\[\s*يُستكمل", t, re.I):
        _warn_placeholder("أولاً")
        t = re.sub(r"(?m)^(\s*أولاً[^\n]*)\[\s*يُستكمل[^\]]*\]", r"\1", t)
    if re.search(r"(?m)^\s*ثانياً[^\n]*\[\s*يُستكمل", t, re.I):
        _warn_placeholder("ثانياً")
        t = re.sub(r"(?m)^(\s*ثانياً[^\n]*)\[\s*يُستكمل[^\]]*\]", r"\1", t)
    if re.search(r"(?m)^\s*ثالثاً[^\n]*\[\s*يُستكمل", t, re.I):
        _warn_placeholder("ثالثاً")
        t = re.sub(r"(?m)^(\s*ثالثاً[^\n]*)\[\s*يُستكمل[^\]]*\]", r"\1", t)

    # Sections vides (titre sans corps) : avertir, NE PAS supprimer ni remplir
    section_specs = (
        (
            r"(?m)^(\s*أولاً[^\n]*\n)"
            r"(.*?)(?=^\s*(?:ثانياً|ثالثاً|رابعاً|خامساً|لهذه\s*الأسباب|الملتمسات|\Z))",
            "أولاً",
        ),
        (
            r"(?m)^(\s*ثانياً[^\n]*\n)"
            r"(.*?)(?=^\s*(?:ثالثاً|رابعاً|خامساً|لهذه\s*الأسباب|الملتمسات|\Z))",
            "ثانياً",
        ),
        (
            r"(?m)^(\s*ثالثاً[^\n]*\n)"
            r"(.*?)(?=^\s*(?:رابعاً|خامساً|لهذه\s*الأسباب|الملتمسات|\Z))",
            "ثالثاً",
        ),
        (
            r"(?m)^(\s*رابعاً[^\n]*\n)"
            r"(.*?)(?=^\s*(?:خامساً|لهذه\s*الأسباب|الملتمسات|\Z))",
            "رابعاً",
        ),
    )
    for pat, label in section_specs:
        for m in re.finditer(pat, t, flags=re.S | re.I):
            body_part = m.group(2).strip()
            head = m.group(1)
            inline = re.sub(
                rf"^\s*{re.escape(label)}ً?\s*[:：\-—]?\s*",
                "",
                head.strip(),
                flags=re.I,
            ).strip()
            combined = f"{inline} {body_part}".strip()
            if _is_placeholder_content(combined):
                _warn_placeholder(label)
                # Si la source a du contenu pour cette section, le réinjecter
                src_chunk = _extract_section_from_source(src, label)
                if src_chunk and len(src_chunk) > 40:
                    t = t[: m.start()] + m.group(1) + src_chunk + "\n\n" + t[m.end() :]

    lines = []
    for line in t.split("\n"):
        if _PLACEHOLDER_LINE_RE.match(line.strip()):
            continue
        clean = _PLACEHOLDER_INLINE_RE.sub("", line).strip()
        if clean:
            lines.append(clean)
        elif not line.strip():
            lines.append("")
    t = "\n".join(lines)
    t = re.sub(r"\n{3,}", "\n\n", t).strip()
    t = dedupe_consecutive_section_heads(t)
    t = repair_parties_parentheses(t)

    if for_export and _PLACEHOLDER_INLINE_RE.search(t):
        t = _PLACEHOLDER_INLINE_RE.sub("", t)
        if not any("يُستكمل" in w for w in warnings):
            warnings.append(
                "⚠️ Des marqueurs internes [يُستكمل] ont été retirés du document exporté."
            )

    return t, warnings


def _extract_section_from_source(source: str, ordinal: str) -> str:
    """Extrait le corps d'une section (أولاً…) depuis la dictée source."""
    src = (source or "").replace("\r\n", "\n")
    # Accepter أولا / أولاً
    base = ordinal.rstrip("ً")
    pat = (
        rf"(?m)(?:^|\n)\s*{re.escape(base)}ً?\s*[:：\-—]?\s*"
        rf"([^\n]*)\n"
        rf"(.*?)(?=(?:^|\n)\s*(?:أولاً?|ثانياً?|ثالثاً?|رابعاً?|خامساً?|سادساً?|لهذه\s*الأسباب|الملتمسات)|\Z)"
    )
    m = re.search(pat, src, flags=re.S)
    if not m:
        return ""
    title_rest = (m.group(1) or "").strip()
    body = (m.group(2) or "").strip()
    if title_rest and not body.startswith(title_rest):
        # Titre sur la même ligne que l'ordinale
        return (title_rest + "\n\n" + body).strip() if body else title_rest
    return body


def format_parties_with_parentheses(text: str) -> str:
    """Met noms, dates et numéros de dossier entre parenthèses."""
    t = text or ""

    def _file_repl(m: re.Match) -> str:
        label = m.group(1)
        num = m.group(2).strip()
        return f"{label} : {_wrap_parens(num)}"

    t = re.sub(
        r"(?m)(رقم\s*(?:الملف|ملف\s*القضية|الملف))\s*[:：]\s*([^\n—]+?)(?=\s*—|\s*$|\s*تاريخ)",
        _file_repl,
        t,
    )
    t = re.sub(
        r"(?m)(تاريخ\s*الجلسة)\s*[:：]\s*([^\n—]+)",
        lambda m: f"{m.group(1)} : {_wrap_parens(m.group(2).strip())}",
        t,
    )
    # Nom propre après rôle
    for role in (
        r"المتهم(?:ة)?(?:\s*/\s*الظنين(?:ة)?)?(?:\s*/\s*المتهم(?:ون)?)?",
        r"الضحايا\s*\(الطرف\s*المدني\)",
        r"الطرف\s*المدني\s*\(الضحايا\)",
    ):
        t = re.sub(
            rf"(?m)({role})\s*[:：]\s*([^\n]+)",
            lambda m: f"{m.group(1)} : {_format_party_value(m.group(2).strip())}",
            t,
            count=1,
        )
    return t


def _infer_context(text: str, plaidoirie_type: str | None) -> str:
    tid = (plaidoirie_type or "").strip()
    if tid in ("partie-civile",):
        return "victim_criminal"
    if tid in ("penal-defense", "penal-ordinaire", "detention"):
        return "penal_defense"
    if tid in ("civil-defense",):
        return "civil_defense"
    if tid in ("civil-general", "commercial", "famille", "foncier", "social-travail"):
        return "civil_plaintiff"
    blob = text or ""
    if _VICTIM_KW.search(blob) and _CRIMINAL_KW.search(blob):
        return "victim_criminal"
    if _CRIMINAL_KW.search(blob):
        return "penal"
    return "civil"


def _split_dashed_parties_line(t: str) -> str:
    """Découpe ligne « مدعى عليه … — ضحايا … — ملف … — تاريخ … »."""

    def _process_line(line: str) -> str:
        s = line.strip()
        if not re.search(r"المدعى\s*عليه", s, re.I):
            return line
        if not re.search(r"الضحايا\s*[:：]", s, re.I):
            return line
        m = re.match(
            r"^(?:(?:الأطراف|تحديد\s*الأطراف)\s*[:：]\s*)?"
            r"المدعى\s*عليه(?:م|ا|ون)?\s*[:：]\s*"
            r"(.+?)\s*[—–\-]\s*الضحايا\s*[:：]\s*"
            r"(.+)$",
            s,
            re.I,
        )
        if not m:
            return line
        accused = m.group(1).strip()
        tail = m.group(2).strip()
        victims = tail
        file_no = ""
        session = ""
        chunks = re.split(r"\s*[—–\-]\s*(?=ملف|تاريخ\s*الجلسة)", tail, flags=re.I)
        if chunks:
            victims = chunks[0].strip()
        for chunk in chunks[1:]:
            if re.search(r"ملف", chunk, re.I):
                fm = re.search(r"(\d+)", chunk)
                if fm:
                    file_no = fm.group(1)
            if re.search(r"تاريخ\s*الجلسة", chunk, re.I):
                sm = re.search(r"[:：]\s*(.+)$", chunk)
                if sm:
                    session = sm.group(1).strip()
        lines = [
            "تحديد الأطراف",
            "",
            f"المتهم(ة) / المتهم(ون) : {_format_party_value(accused)}",
            "",
            f"الضحايا (الطرف المدني) : {_format_party_value(victims)}",
        ]
        if file_no:
            lines.extend(["", f"رقم الملف : {_wrap_parens(file_no)}"])
        if session:
            lines.extend(["", f"تاريخ الجلسة : {_wrap_parens(session)}"])
        return "\n".join(lines)

    out: list[str] = []
    parties_done = False
    for raw in t.split("\n"):
        if (
            not parties_done
            and re.search(r"المدعى\s*عليه", raw, re.I)
            and re.search(r"الضحايا\s*[:：]", raw, re.I)
        ):
            out.append(_process_line(raw))
            parties_done = True
        elif re.match(r"^\s*تحديد\s*الأطراف\s*[:：]?\s*$", raw) and parties_done:
            continue
        else:
            out.append(raw)
    return "\n".join(out)


def fix_party_roles(text: str, plaidoirie_type: str | None = None) -> str:
    """Corrige inversion victimes / accusés ; sépare ligne mashup."""
    t = split_glued_sections(text)
    t = _split_dashed_parties_line(t)
    ctx = _infer_context(t, plaidoirie_type)

    if ctx in ("victim_criminal", "penal") or _CRIMINAL_KW.search(t):
        t = re.sub(
            r"(?m)^(\s*)المدعى\s*عليه(?:م|ا|ون)?\s*[:：]\s*"
            r"(?=.*(?:هنية|عصاب|متهم|ظنين|سيدات\s*و))",
            r"\1المتهم(ة) / المتهم(ون) : ",
            t,
            flags=re.IGNORECASE,
        )
        t = re.sub(
            r"(?m)^(\s*)المدعى\s*عليه(?:م|ا|ون)?\s*[:：]\s*(?=.*(?:ضحا|فتيات|فتيان))",
            r"\1الضحايا (الطرف المدني) : ",
            t,
            flags=re.IGNORECASE,
        )
        t = re.sub(
            r"الطرف\s*المدني\s*\(الضحايا\)\s*المتهمة\s*[:：]",
            "المتهم(ة) :",
            t,
            flags=re.IGNORECASE,
        )
        t = re.sub(
            r"(?m)^(\s*)الأطراف\s*[:：]\s*$",
            r"\1تحديد الأطراف",
            t,
        )

    if ctx == "penal_defense":
        t = re.sub(
            r"(?m)^(\s*)المدعى\s*عليه(?:م|ا|ون)?\s*[:：]\s*(?=.*(?:متهم|ظنين))",
            r"\1المتهم / الظنين : ",
            t,
            flags=re.IGNORECASE,
        )

    return format_parties_with_parentheses(t)


def fix_form_vs_facts_sections(text: str, plaidoirie_type: str | None = None) -> str:
    """Si « أولاً — في الشكل » contient des faits, renommer en وقائع."""
    t = text or ""
    tid = (plaidoirie_type or "").strip()
    penal = tid in ("partie-civile", "penal-defense", "penal-ordinaire", "penal", "libre") or _CRIMINAL_KW.search(t)

    if re.search(r"(?m)^\s*أولاً\s*[-—]\s*في\s*الشكل\s*[:：]", t) and re.search(
        r"إن\s*المرافعة|جرائم|تورط|عصاب", t
    ):
        if penal:
            t = re.sub(
                r"(?m)^(\s*)أولاً\s*[-—]\s*في\s*الشكل\s*[:：]",
                r"\1أولاً — في الوقائع :",
                t,
                count=1,
            )
        else:
            # Garder الشكل court ; déplacer faits vers ثانياً si besoin
            pass
    return t


def ensure_section_numbering(text: str, plaidoirie_type: str | None = None) -> str:
    """Vérifie la séquence — n'invente JAMAIS de paragraphe de remplissage."""
    t = (text or "").replace("\r\n", "\n").strip()
    if not t:
        return t
    t = dedupe_consecutive_section_heads(t)
    # Ne plus injecter « حيث إن الملف مقبول… » ni renommer agressivement
    return fix_form_vs_facts_sections(t, plaidoirie_type)


def ensure_closing_formula(text: str) -> str:
    t = strip_export_duplicates(text)
    if not t:
        return t
    has_polite = bool(re.search(r"واحسبكم|حسن\s*استماع", t))
    has_reserve = bool(re.search(r"التحفظات|الاحتفاظ.*حقوق", t))
    parts = [t]
    if not has_polite:
        parts.append(_CLOSING_POLITE)
    if not has_reserve:
        parts.append(_CLOSING_RESERVE)
    return "\n\n".join(p for p in parts if p).strip()


def party_role_prompt_block(plaidoirie_type: str | None) -> str:
    tid = (plaidoirie_type or "libre").strip()
    ctx = _infer_context("", tid)
    lines = [
        "=== قواعد الأطراف (إلزامية — لا خلط الأدوار) ===",
        "ممنوع وضع المتهم(ين) تحت « المدعى عليه(م) » في القضايا الجنائية.",
        "ممنوع وضع الضحايا تحت « المدعى عليه(م) ».",
        "استعمل الأقواس () للأسماء والأرقام والتواريخ.",
        "مثال جنائي — طرف مدني:",
        "  المتهم(ة) : (هنية بنت محمد) — (حي أولاد الفقراء، الدار البيضاء)",
        "  الضحايا (الطرف المدني) : (فتيات وفتيان) — (16–25 سنة)",
        "  رقم الملف : (120) — تاريخ الجلسة : (16 يوليوز 2026)",
    ]
    rules = _PARTY_RULES.get(tid)
    if rules:
        lines.append(f"- موكل(ي) المحامي: {rules['client']}")
        lines.append(f"- الخصم: {rules['opponent']}")
    elif ctx == "victim_criminal":
        lines.extend(
            [
                "- الضحايا = الطرف المدني (بأقواس)",
                "- هنية / العصابة = المتهم(ون) (بأقواس) — وليس مدعى عليه",
            ]
        )
    lines.append("تحديد الأطراف على سطر مستقل — ثم أولاً، ثانياً، ثالثاً…")
    lines.append("لا تكرر المملكة/المكتب/التوقيع في BODY — يُضاف عند التصدير.")
    return "\n".join(lines)


def strip_invented_boilerplate(body: str, source: str) -> str:
    """Retire phrases inventées connues absentes de la dictée."""
    t = body or ""
    src = source or ""
    fillers = (
        "حيث إن الدعوى مستوفية لكافة الشروط الشكلية المتطلبة قانوناً، مما يتعين معه التصريح بقبولها شكلاً.",
        "حيث إن الدعوى مستوفية لكافة الشروط الشكلية المتطلبة قانوناً.",
        "حيث إن الملف مقبول للتداول.",
        "حيث إن الدعوى مقبولة للتداول شكلاً، وتتوفر المحكمة على الاختصاص والولاية القضائية، مما يتعين معه السير في المناقشة.",
        "حيث إن المرافق مسؤولة لكافة الفروض النظامية لمقاولة قانونا، بما يعني مع الصريح بشرط شكلاً.",
    )
    for f in fillers:
        if f in t and f not in src:
            t = t.replace(f, "")
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def postprocess_plaidoirie_body(
    body: str,
    *,
    source_text: str | None = None,
    plaidoirie_type: str | None = None,
    for_export: bool = False,
) -> tuple[str, list[str]]:
    src = source_text or body or ""
    t = fix_lawyer_title_fragments(body or "")
    t = strip_export_duplicates(t)
    t = strip_internal_instructions(t)
    t = strip_invented_boilerplate(t, src)
    t = split_glued_sections(t)
    t = repair_parties_parentheses(t)
    t = fix_party_roles(t, plaidoirie_type)
    t = ensure_section_numbering(t, plaidoirie_type)
    t = dedupe_consecutive_section_heads(t)
    t = re.sub(r"(?m)(?:^تحديد\s*الأطراف\s*[:：]?\s*\n\s*){2,}", "تحديد الأطراف\n\n", t)
    t = re.sub(r"(?m)^مرافعة\s+[^\n]{0,50}\s*\n+(?=تحديد\s*الأطراف)", "", t)
    if for_export:
        t = ensure_closing_formula(t)
        t = repair_parties_parentheses(t)
        t = strip_invented_boilerplate(t, src)
    else:
        t = strip_export_duplicates(t)
    t, warnings = sanitize_sections_for_output(
        t,
        source=src,
        plaidoirie_type=plaidoirie_type,
        for_export=for_export,
    )
    return t.strip(), warnings
