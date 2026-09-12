"""Assistance non-destructive à la plaidoirie (forme / structure / variables / suggestions).

Jamais d'insertion automatique d'arguments ou de fond juridique.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from app.services.dictation_contradictions import (
    _extract_age_ranges,
    _extract_amounts,
    _extract_bint_names,
    _extract_case_numbers,
    _extract_dates,
    _extract_person_names,
    _uniq_keep_order,
)


@dataclass
class FormEdit:
    id: str
    original: str
    proposed: str
    kind: str = "form"  # form | stt


@dataclass
class PleaVariable:
    kind: str
    value: str
    label_ar: str
    label_fr: str


@dataclass
class StructureHint:
    section_ar: str
    section_fr: str
    excerpt: str
    message_ar: str
    message_fr: str


@dataclass
class LawSuggestion:
    code_ar: str
    code_fr: str
    article: str
    reason_ar: str
    reason_fr: str
    insert_ar: str


# Suggestions purement indicatives — l'avocat décide d'insérer ou non
_LAW_RULES: list[tuple[re.Pattern[str], LawSuggestion]] = [
    (
        re.compile(r"طلاق|نفقة|حضانة|مدونة\s*الأسرة|زوج"),
        LawSuggestion(
            code_ar="مدونة الأسرة",
            code_fr="Code de la famille",
            article="(حسب الواقعة — يراجع النص)",
            reason_ar="النص يشير إلى نزاع أسري؛ يمكن للمحامي التحقق من المقتضى المناسب في مدونة الأسرة.",
            reason_fr="Le texte évoque un litige familial ; vérifier l’article pertinent du Code de la famille.",
            insert_ar="[اقتراح مراجعة: مدونة الأسرة — المقتضى المناسب حسب الوقائع — يقرر المحامي الإدراج]",
        ),
    ),
    (
        re.compile(r"عقد|التزام|فسخ|تعويض|ضرر|قانون\s*الالتزامات"),
        LawSuggestion(
            code_ar="قانون الالتزامات والعقود",
            code_fr="D.O.C.",
            article="(مثال شائع: 230–231 — للتأكيد فقط)",
            reason_ar="إشارة إلى التزام/عقد؛ اقتراح التحقق من ق.ل.ع. دون إدراج تلقائي.",
            reason_fr="Mention d’obligation/contrat ; suggestion de vérifier le D.O.C. (pas d’insertion auto).",
            insert_ar="[اقتراح مراجعة: قانون الالتزامات والعقود — فصل يحدده المحامي]",
        ),
    ),
    (
        re.compile(r"اختصاص|قبول|آجال|مسطرة\s*مدنية|شكل"),
        LawSuggestion(
            code_ar="قانون المسطرة المدنية",
            code_fr="Code de procédure civile",
            article="(مثال شائع: 1 وما يليه / 41 — للتأكيد)",
            reason_ar="إشارة إلى الشكل/الاختصاص؛ اقتراح مراجعة ق.م.م.",
            reason_fr="Mention de forme/compétence ; suggestion CPC marocain.",
            insert_ar="[اقتراح مراجعة: قانون المسطرة المدنية — المقتضى الشكلي الذي يختاره المحامي]",
        ),
    ),
    (
        re.compile(r"اتجار|مخدرات|سرقة|ضرب|جناية|جنحة|متهم"),
        LawSuggestion(
            code_ar="القانون الجنائي",
            code_fr="Code pénal",
            article="(حسب التهمة — يراجع النص)",
            reason_ar="إطار زجري محتمل؛ لا يُدرج أي فصل إلا بموافقة المحامي.",
            reason_fr="Cadre pénal possible ; aucun article n’est ajouté sans l’avocat.",
            insert_ar="[اقتراح مراجعة: القانون الجنائي — الفصل المطابق للتهمة كما يحددها المحامي]",
        ),
    ),
    (
        re.compile(r"شغل|أجير|فصل|تعويض.*فصل|CNSS|ضمان\s*اجتماعي"),
        LawSuggestion(
            code_ar="مدونة الشغل",
            code_fr="Code du travail",
            article="(حسب النزاع)",
            reason_ar="نزاع شغل محتمل؛ اقتراح مراجعة مدونة الشغل.",
            reason_fr="Litige du travail possible ; suggestion Code du travail.",
            insert_ar="[اقتراح مراجعة: مدونة الشغل — المقتضى الذي يختاره المحامي]",
        ),
    ),
    (
        re.compile(r"قرار\s*إداري|إلغاء|تجاوز\s*السلطة|محكمة\s*إدارية"),
        LawSuggestion(
            code_ar="المسطرة الإدارية / القانون الإداري",
            code_fr="Contentieux administratif",
            article="(حسب القرار المطعون فيه)",
            reason_ar="طعن إداري محتمل؛ اقتراح التحقق من المسطرة الإدارية.",
            reason_fr="Contentieux admin. possible ; vérifier la procédure administrative.",
            insert_ar="[اقتراح مراجعة: المسطرة الإدارية — وسيلة المشروعية التي يحددها المحامي]",
        ),
    ),
    (
        re.compile(r"سير|حادثة|مركبة|رخصة\s*السياقة"),
        LawSuggestion(
            code_ar="مدونة السير",
            code_fr="Code de la route",
            article="(حسب المخالفة)",
            reason_ar="حادثة/مخالفة سير محتملة.",
            reason_fr="Accident / infractions routières possibles.",
            insert_ar="[اقتراح مراجعة: مدونة السير — المخالفة كما يكيّفها المحامي]",
        ),
    ),
]


# Corrections STT à haute confiance uniquement (jamais un diff libre « qui invente »)
_SMART_STT_FIXES: list[tuple[str, str]] = [
    (r"تكسييل", "تكستيل"),
    (r"تكسيتيل", "تكستيل"),
    (r"تيكستيل", "تكستيل"),
    (r"سيباقتصاديا", "سببا اقتصاديا"),
    (r"سياق\s*اقتصاديا", "سببا اقتصاديا"),
    (r"الفصل\s+لأساب\b", "الفصل للأسباب"),
    (r"(?<!\S)لأساب\b", "للأسباب"),
    (r"العمراني\s+تقاضي", "العمراني يتقاضى"),
    (r"العمراني\s+بتقاضي", "العمراني يتقاضى"),
    (r"محامي\s*لـ?\s*ة", "المحامية"),
    (r"المحامي\s*لـ?\s*ة", "المحامية"),
    (r"امامحكمتكم", "أمام محكمتكم"),
    (r"امام\s*محكمتكم", "أمام محكمتكم"),
    (r"اعمارهما", "أعمارهم"),
    (r"معالجتة", "معالجته"),
    (r"اقصى", "أقصى"),
    (r"اكثر", "أكثر"),
    # STT fréquent : الدين دينا (créance) mal entendu « الذين دينا »
    (r"الذين\s+دينا", "الدين دينا"),
    (r"الدينا\b", "الدين دينا"),
    (r"(?<!\S)(?:أ|ا)يداد(ها|ه|هم|هما|هن)(?=\s|[.،]|$)", r"إعداد\1"),
    (r"عن\s+التجار\s+بالمخدرات", "الاتجار بالمخدرات"),
]


def _norm_ar_cmp(s: str) -> str:
    """Normalise pour comparer deux suggestions (évite faux « a → a »)."""
    t = (s or "").strip()
    t = re.sub(r"[‹›«»\"'…] ", "", t)
    t = re.sub(r"[‹›«»\"'…]", "", t)
    # Diacritiques arabes + tatweel + ponctuation attachée
    t = re.sub(r"[\u064B-\u065F\u0670\u0640]", "", t)
    t = re.sub(r"[،,.;:؟!?()\[\]\-–—/]", "", t)
    t = t.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ة", "ه")
    t = re.sub(r"\s+", "", t)
    return t


def build_form_edits(source: str, polished: str, *, limit: int = 25) -> list[FormEdit]:
    """
    Panneau de revue : presque toujours vide.

    Les corrections STT fiables sont déjà appliquées dans le texte corrigé.
    On ne propose une ligne que si une faute STT connue reste ENCORE dans le
    corrigé (l'avocat peut alors accepter). Jamais de fuzzy / SequenceMatcher.
    """
    plain = re.sub(r"[‹›]", "", polished or "")
    edits: list[FormEdit] = []
    seen: set[tuple[str, str]] = set()
    n = 0

    def _add(orig: str, prop: str, kind: str = "stt") -> None:
        nonlocal n
        o = re.sub(r"\s+", " ", (orig or "").strip())
        p = re.sub(r"\s+", " ", (prop or "").strip())
        if not o or not p or o == p:
            return
        if _norm_ar_cmp(o) == _norm_ar_cmp(p):
            return
        # Différence trop faible (1 caractère de ponctuation / alef)
        if abs(len(o) - len(p)) <= 1 and _norm_ar_cmp(o) == _norm_ar_cmp(p):
            return
        key = (o, p)
        if key in seen:
            return
        seen.add(key)
        n += 1
        edits.append(FormEdit(id=f"e{n}", original=o, proposed=p, kind=kind))

    # Uniquement si la faute est encore visible dans le texte corrigé
    for pat, repl in _SMART_STT_FIXES:
        for m in re.finditer(pat, plain, flags=re.IGNORECASE):
            raw = m.group(0)
            fixed = re.sub(pat, repl, raw, flags=re.IGNORECASE)
            if raw != fixed:
                _add(raw, fixed, "stt")
            if len(edits) >= limit:
                return edits

    return edits


def extract_plea_variables(text: str) -> list[PleaVariable]:
    t = text or ""
    out: list[PleaVariable] = []
    for c in _extract_case_numbers(t):
        out.append(
            PleaVariable("case_number", c, "رقم الملف", "N° de dossier")
        )
    for d in _extract_dates(t):
        out.append(PleaVariable("date", d, "تاريخ", "Date"))
    for a in _extract_amounts(t):
        out.append(PleaVariable("amount", a, "مبلغ", "Montant"))
    for a in _extract_age_ranges(t):
        out.append(PleaVariable("age", a, "سن / أعمار", "Âge"))
    for n in _uniq_keep_order(_extract_person_names(t) + _extract_bint_names(t)):
        out.append(PleaVariable("person_name", n, "اسم", "Nom"))
    # Dédup valeurs
    seen: set[str] = set()
    uniq: list[PleaVariable] = []
    for v in out:
        if v.value in seen:
            continue
        seen.add(v.value)
        uniq.append(v)
    return uniq


_SECTION_PATTERNS: list[tuple[re.Pattern[str], str, str, str, str]] = [
    (
        re.compile(r"ملف\s*رقم|تاريخ\s*الجلسة|طرف|مدعي|مدعى|متهم"),
        "تحديد الأطراف / هوية الملف",
        "Parties / identification du dossier",
        "يبدو أن هذه الفقرة تخص الأطراف أو رقم الملف — يمكن وضعها في ترويسة الأطراف.",
        "Ce passage semble concerner les parties ou le n° de dossier — à placer en en-tête.",
    ),
    (
        re.compile(r"حيث إن|وقعت|بتاريخ|في يوم|سرد|الوقائع"),
        "ثانياً — في الوقائع",
        "II. Rappel des faits",
        "فقرة وقائع محتملة — دون تعديل النص، اقترح نقلها إلى قسم الوقائع.",
        "Faits possibles — suggestion de placement en section Faits (sans modifier les mots).",
    ),
    (
        re.compile(r"في الشكل|اختصاص|قبول|آجال|صفة"),
        "أولاً — في الشكل",
        "I. En la forme",
        "دفوع شكلية محتملة — قسم الشكل.",
        "Moyens de forme possibles — section En la forme.",
    ),
    (
        re.compile(r"مناقشة|قانون|فصل|يدفع|تفنيد|موضوع"),
        "ثالثاً — في المناقشة",
        "III. Au fond",
        "حجاج موضوعي محتمل — قسم المناقشة (يبقى نص المحامي كما هو).",
        "Discussion au fond — section Discussion (texte inchangé).",
    ),
    (
        re.compile(r"لهذه الأسباب|يلتمس|نطالب|نحكم|الصائر|تعويض"),
        "لهذه الأسباب / الملتمسات",
        "IV. Par ces motifs",
        "ملتمسات محتملة — قسم لهذه الأسباب.",
        "Conclusions possibles — section Par ces motifs.",
    ),
]


def suggest_structure(text: str, *, max_hints: int = 5) -> list[StructureHint]:
    t = (text or "").strip()
    if len(t) < 40:
        return []
    # Découper en phrases / blocs
    parts = re.split(r"(?<=[.。؟!\n])\s+", t)
    parts = [p.strip() for p in parts if len(p.strip()) >= 24]
    hints: list[StructureHint] = []
    used_sections: set[str] = set()
    for p in parts:
        for pat, sec_ar, sec_fr, msg_ar, msg_fr in _SECTION_PATTERNS:
            if sec_ar in used_sections:
                continue
            if pat.search(p):
                used_sections.add(sec_ar)
                excerpt = p[:120] + ("…" if len(p) > 120 else "")
                hints.append(
                    StructureHint(
                        section_ar=sec_ar,
                        section_fr=sec_fr,
                        excerpt=excerpt,
                        message_ar=msg_ar,
                        message_fr=msg_fr,
                    )
                )
                break
        if len(hints) >= max_hints:
            break
    return hints


def suggest_law_articles(text: str, *, max_n: int = 4) -> list[LawSuggestion]:
    t = text or ""
    out: list[LawSuggestion] = []
    seen: set[str] = set()
    for pat, sug in _LAW_RULES:
        if pat.search(t) and sug.code_ar not in seen:
            seen.add(sug.code_ar)
            out.append(sug)
        if len(out) >= max_n:
            break
    return out


def build_assist_payload(source: str, polished: str) -> dict:
    """Payload JSON-ready pour l'API polish."""
    body = polished or source or ""
    edits = build_form_edits(source or "", body)
    variables = extract_plea_variables(source or body)
    structure = suggest_structure(source or body)
    laws = suggest_law_articles(source or body)
    return {
        "edits": [asdict(e) for e in edits],
        "variables": [asdict(v) for v in variables],
        "structure_hints": [asdict(h) for h in structure],
        "law_suggestions": [asdict(s) for s in laws],
    }
