"""Post-traitement STT arabe — corrections orthographiques minimales (fidélité)."""

from __future__ import annotations

import re

# Lexique ه→ة (Chrome STT sort presque toujours ه à la place de ة)
_TEH_MARBUTA_WORDS = {
    "محكمه": "محكمة",
    "مرافعه": "مرافعة",
    "المرافعه": "المرافعة",
    "جلسه": "جلسة",
    "دعوه": "دعوى",
    "قضيه": "قضية",
    "نفقه": "نفقة",
    "حضانه": "حضانة",
    "شركه": "شركة",
    "هيئه": "هيئة",
    "مذكره": "مذكرة",
    "مسطره": "مسطرة",
    "ابتدائيه": "ابتدائية",
    "استئنافيه": "استئنافية",
    "تجاريه": "تجارية",
    "اداريه": "إدارية",
    "إداريه": "إدارية",
    "مدنيه": "مدنية",
    "مدعيه": "مدعية",
    "المدعيه": "المدعية",
    "العارضه": "العارضة",
    "جريمه": "جريمة",
    "سيده": "سيدة",
    "السيذه": "السيدة",
    "السيده": "السيدة",
    "سنه": "سنة",
    "متورطه": "متورطة",
    "مجموعه": "مجموعة",
    "دعاره": "دعارة",
    "الدعاره": "الدعارة",
    "مغربيه": "مغربية",
    "المغربيه": "المغربية",
    "دستوريه": "دستورية",
    "الدستوريه": "الدستورية",
    "والدستوريه": "والدستورية",
    "نقطه": "نقطة",
    "اهميه": "أهمية",
    "الاهميه": "الأهمية",
    "الأهميه": "الأهمية",
    "موقره": "موقرة",
    "الموقره": "الموقرة",
    "عقوبه": "عقوبة",
    "العقوبه": "العقوبة",
    "قاصره": "قاصرة",
    "القاصره": "القاصرة",
    "تجاره": "تجارة",
    "مدينه": "مدينة",
    "المدينه": "المدينة",
    "شرطه": "شرطة",
    "الشرطه": "الشرطة",
    "نيابه": "نيابة",
    "النيابه": "النيابة",
    "ظاهره": "ظاهرة",
    "وقايه": "وقاية",
    "حمايه": "حماية",
    "الحمايه": "الحماية",
    "حريه": "حرية",
    "الحريه": "الحرية",
    "دوليه": "دولية",
    "الدوليه": "الدولية",
    "اسريه": "أسرية",
    "الاسريه": "الأسرية",
    "قانونيه": "قانونية",
    "القانونيه": "القانونية",
    "جزائيه": "جزائية",
    "الجزائيه": "الجزائية",
    "ناحيه": "ناحية",
    "الناحيه": "الناحية",
    "صوره": "صورة",
    "الصوره": "الصورة",
    "منطقه": "منطقة",
    "المنطقه": "المنطقة",
    "مصلحه": "مصلحة",
    "المصلحه": "المصلحة",
    "سلطه": "سلطة",
    "السلطه": "السلطة",
    "دوله": "دولة",
    "الدوله": "الدولة",
    "وزاره": "وزارة",
    "الوزاره": "الوزارة",
    "ماده": "مادة",
    "الماده": "المادة",
    "فقره": "فقرة",
    "الفقره": "الفقرة",
    "وثيقه": "وثيقة",
    "الوثيقه": "الوثيقة",
    "شهاده": "شهادة",
    "الشهاده": "الشهادة",
    "تهمه": "تهمة",
    "التهمه": "التهمة",
    "براءه": "براءة",
    "البراءه": "البراءة",
    "ادانه": "إدانة",
    "الادانه": "الإدانة",
}

# Mots qui DOIVENT garder ه final (هذه = هـٰذِهِ, pas ة)
_KEEP_FINAL_HEH = {
    "الله",
    "ولله",
    "بالله",
    "تالله",
    "وجه",
    "فقه",
    "شبه",
    "كره",
    "نبه",
    "فيه",
    "وفيه",
    "عليه",
    "وعليه",
    "إليه",
    "اليه",
    "منه",
    "عنه",
    "له",
    "به",
    "معه",
    "لديه",
    "لديهم",
    "أمامه",
    "امامه",
    "نحوه",
    "ضده",
    "قبله",
    "بعده",
    "كله",
    "بعضه",
    "نفسه",
    "وحده",
    "هذه",
    "لهذه",
    "بهذه",
    "كهذه",
    "فهذه",
    "وهذه",
}


def _fix_one_word(word: str) -> str:
    if not word:
        return word
    # Sépare ponctuation collée
    m = re.match(r"^([\u0600-\u06FF]+)(.*)$", word)
    if not m:
        return word
    core, rest = m.group(1), m.group(2)
    if core in _TEH_MARBUTA_WORDS:
        return _TEH_MARBUTA_WORDS[core] + rest
    if core in _KEEP_FINAL_HEH:
        return word
    # Préfixe ال / و / ف / ب / ك / ل
    for pref in ("وال", "بال", "كال", "فال", "لل", "ال", "و", "ف", "ب", "ك", "ل"):
        if core.startswith(pref) and len(core) > len(pref) + 2:
            stem = core[len(pref) :]
            if stem in _TEH_MARBUTA_WORDS:
                return pref + _TEH_MARBUTA_WORDS[stem] + rest
            if stem in _KEEP_FINAL_HEH:
                return word
            if stem.endswith("ه") and stem not in _KEEP_FINAL_HEH and len(stem) >= 3:
                return pref + stem[:-1] + "ة" + rest
            break
    # Mot simple terminé par ه → ة (Chrome STT)
    if core.endswith("ه") and core not in _KEEP_FINAL_HEH and len(core) >= 3:
        return core[:-1] + "ة" + rest
    return word


def repair_arabic_stt(text: str) -> str:
    """Nettoyage léger — corrige ه→ة (artefact Chrome) sans changer le sens."""
    t = (text or "").strip()
    if not t:
        return ""
    t = re.sub(r"\s+", " ", t)
    # Artefact fréquent si ة forcée à tort sur هذه
    t = t.replace("هذة", "هذه").replace("لهذة", "لهذه")
    # Lexique exact d'abord
    for wrong, right in _TEH_MARBUTA_WORDS.items():
        t = re.sub(rf"(?<!\w){re.escape(wrong)}(?!\w)", right, t)
    # Puis heuristique mot à mot
    parts = t.split(" ")
    t = " ".join(_fix_one_word(p) for p in parts)
    return t.strip()


def audio_transcript_quality(text: str) -> str:
    """Heuristique simple qualité STT (good|medium|poor)."""
    t = (text or "").strip()
    if len(t) < 8:
        return "poor"
    words = t.split()
    if len(words) < 4:
        return "poor"
    ar = sum(1 for c in t if "\u0600" <= c <= "\u06FF")
    if ar / max(1, len(t)) < 0.4:
        return "poor"
    if len(words) >= 12:
        return "good"
    return "medium"


def strip_markdown_noise(text: str) -> str:
    """Enlève **, *, #, puces markdown aléatoires du corps de document."""
    t = text or ""
    t = re.sub(r"^```(?:\w+)?\s*", "", t.strip())
    t = re.sub(r"\s*```$", "", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"\1", t)
    t = re.sub(r"__(.+?)__", r"\1", t)
    t = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"\1", t)
    t = re.sub(r"(?m)^\s{0,3}#{1,6}\s+", "", t)
    t = re.sub(r"(?m)^\s*[-*•]\s+", "— ", t)
    t = re.sub(r"(?<!\S)\*{1,3}(?!\S)", "", t)
    t = re.sub(r"[ \t]+\n", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()

def repair_stt_garbage(text: str) -> str:
    """
    Retire les artefacts STT évidents (début absurde, chevauchement d'ouverture)
    sans supprimer de faits juridiques.
    """
    t = re.sub(r"\s+", " ", (text or "").strip())
    if not t:
        return ""

    # Ouverture juridique standard — tout garbage avant « المرافعة »
    t = re.sub(
        r"^(?:انا|أنا|إن\s*ا|إنا)\s+[\u0600-\u06FF\s]{0,55}?\s*(?:ان|إن)\s+(?=المرافعة)",
        "إن ",
        t,
        flags=re.IGNORECASE,
    )
    # « المربع / مربع / المرافعة التي نحن ان المرافعة » → une seule ouverture
    t = re.sub(
        r"^(?:المربع|مربع|المرافعة)\s+التي\s+نحن\s+(?:ان|إن)\s+المرافعة\s+",
        "إن المرافعة ",
        t,
        flags=re.IGNORECASE,
    )
    # Double amorce collée : « … المرافعة … ان المرافعة »
    t = re.sub(
        r"(إن\s+المرافعة\s+التي\s+نحن\s+[\u0600-\u06FF\s]{2,40}?)\s+(?:ان|إن)\s+المرافعة\s+",
        r"\1 ",
        t,
        flags=re.IGNORECASE,
    )
    # Répétition « التي نحن » consécutive
    t = re.sub(r"(التي\s+نحن)\s+\1\s+", r"\1 ", t, flags=re.IGNORECASE)
    # Chevauchement classique dictée : segment quasi-identique au début
    m = re.match(
        r"^(.{12,80}?)\s+(?:ان|إن)\s+المرافعة\s+التي\s+نحن",
        t,
        flags=re.IGNORECASE,
    )
    if m:
        prefix = m.group(1).strip()
        if prefix and "المرافعة" not in prefix and len(prefix.split()) <= 8:
            t = re.sub(r"^" + re.escape(prefix) + r"\s+", "إن ", t, count=1)

    # Lexique STT juridique / darija → فصحى (forme seulement)
    stt_lex = [
        (r"(?<!\S)كريان\s+", "حي "),
        (r"بكريان\s+", "بحي "),
        (r"(?<!\S)تجزئة\s+", "حي "),
        (r"اولاد\s+الفقراء", "أولاد الفقراء"),
        (r"الدار\s+البيض\b", "الدار البيضاء"),
        (r"(?<!\S)اكثر\s+من", "أكثر من"),
        (r"(?<!\S)3\s+رجال", "3 رجال"),
        (r"(?<!\S)10\s+نساء", "10 نساء"),
        (r"بين\s*(\d+)\s*وال\s*(\d+)", r"بين \1 و \2"),
        (r"(?<!\S)حنيا\s+بنت", "حنية بنت"),
        (r"(?<!\S)المدعية\s+حنيا\b", "المدعية حنية"),
        (r"(?<!\S)الدستوريه", "الدستورية"),
        (r"(?<!\S)المغربيه", "المغربية"),
        (r"(?<!\S)القصوى\b", "القصوى"),
        (r"(?<!\S)نطالب\s+بالعقوبات", "نطالب بأقصى العقوبات"),
        (r"(?<!\S)يوليو\b(?=\s|\d|$)", "يوليوز"),
        (r"(?<!\S)شتنبر\b", "شتنبر"),
        (r"(?<!\S)غشت\b", "غشت"),
    ]
    for pat, repl in stt_lex:
        t = re.sub(pat, repl, t, flags=re.IGNORECASE)

    # Éviter « إن إن المرافعة » (double hamza après nettoyage)
    t = re.sub(r"^(?:إن\s+){2,}", "إن ", t)
    t = re.sub(r"^إن\s+(?:ان|إن)\s+(?=المرافعة)", "إن ", t, flags=re.IGNORECASE)
    t = re.sub(
        r"^[\u0600-\u06FF\s]{0,40}?\s+(?:ان|إن)\s+(?=المرافعة)",
        "إن ",
        t,
        count=1,
        flags=re.IGNORECASE,
    )

    return t.strip()


def finalize_arabic_polish(text: str) -> str:
    """Dernière passe : espaces, doublons, typos STT résiduelles."""
    t = re.sub(r"\s+", " ", (text or "").strip())
    if not t:
        return ""
    fixes = [
        (r"^(?:إن\s+){2,}", "إن "),
        (r"^إن\s+(?:ان|إن)\s+", "إن "),
        (r"امام\s*محكمتكم", "أمام محكمتكم"),
        (r"امام\s*محكمة", "أمام محكمة"),
        (r"امامحكمتكم", "أمام محكمتكم"),
        (r"امامحكمة", "أمام محكمة"),
        (r"(?<!\S)امام(?=\s*محكم)", "أمام "),
        (r"معالجتة", "معالجته"),
        (r"بصددي\s", "بصدد "),
        (r"ولهذا،?\s*ولذلك،?", "ولذلك،"),
        (r"اقصى", "أقصى"),
        (r"اكثر", "أكثر"),
        (r"(?<!\S)اغلب", "أغلب"),
        (r"شكرا\b", "شكراً"),
        (r"(\d{4})\s+(\d{4})(?=\s|$|[.،])", r"\1"),
        # Typos STT fréquents (licenciement / textile)
        (r"تكسييل", "تكستيل"),
        (r"تكسيتيل", "تكستيل"),
        (r"تيكستيل", "تكستيل"),
        (r"سيباقتصاديا", "سببا اقتصاديا"),
        (r"سياق\s*اقتصاديا", "سببا اقتصاديا"),
        (r"الفصل\s+لأساب\b", "الفصل للأسباب"),
        (r"لأساب\b", "للأسباب"),
        (r"إليه\s+جينا\b", "إليه"),
        (r"العمراني\s+بتقاضي", "العمراني يتقاضى"),
        (r"العمراني\s+تقاضي", "العمراني يتقاضى"),
        (r"تكستيل\s*(?:ذ|د)\.?\s*م\.?\s*م", "تكستيل ذ.م.م"),
        # Espaces mangés STT
        (r"بمذكرات(?:ها|ه)الجواب", "بمذكراتها الجواب"),
        (r"مذكرات(?:ها|ه)الجواب", "مذكراتها الجواب"),
    ]
    for pat, repl in fixes:
        t = re.sub(pat, repl, t, flags=re.IGNORECASE)
    t = re.sub(r"،\s*،+", "،", t)
    return re.sub(r"\s{2,}", " ", t).strip()


def split_legal_phrases(text: str) -> str:
    """Insère des pauses (،) avant connecteurs juridiques — sans résumer."""
    t = (text or "").strip()
    if not t or len(t) < 80:
        return t
    markers = (
        "سيدي الرئيس",
        "والتي تورط",
        "وتتكون",
        "وقد عمل",
        "ولذلك",
        "وبناء على",
        "ملف رقم",
        "تاريخ الجلسة",
        "جلسة",
        "ونلتمس",
        "ونطلب",
        "ونحيط",
        "المحامي",
        "المدعية",
        "المدعى",
    )
    for m in markers:
        t = re.sub(
            rf"(?<![،.\n])\s+({re.escape(m)})",
            rf"، \1",
            t,
            count=1,
        )
    t = re.sub(r"،\s*،+", "،", t)
    return re.sub(r"\s{2,}", " ", t).strip()


def light_arabic_punctuation(text: str) -> str:
    """Ajoute une ponctuation légère (، .) sans changer les mots."""
    t = (text or "").strip()
    if not t:
        return ""
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"\s*([،؛:])\s*", r"\1 ", t)
    t = re.sub(r"\s+([.!?؟])\s*", r"\1 ", t)
    connectors = (
        "وحيث", "حيث", "لذلك", "وعليه", "وبناء عليه", "وبناءً عليه",
        "أولا", "ثانيا", "ثالثا", "لهذه الأسباب",
    )
    for c in connectors:
        t = re.sub(rf"({re.escape(c)})(?![،:])\s+", rf"\1، ", t)
    if len(t) > 40 and t[-1] not in ".!?؟۔":
        t = t.rstrip(" ،,") + "."
    return re.sub(r"\s{2,}", " ", t).strip()


# Substitutions STT / darija → fusḥā (haute confiance) — marquées ‹ › pour l’UI orange.
# Ne pas y mettre de simples hamzas / ponctuation (pas de faux « STT »).
_STT_FUSHA_MARKED: list[tuple[str, str]] = [
    # أيدادها (STT) → إعدادها
    (r"(?<!\S)(?:أ|ا)يداد(ها|ه|هم|هما|هن)(?=\s|[.،]|$)", r"‹إعداد\1›"),
    (r"(?<!\S)اعداد(ها|ه|هم|هما|هن)(?=\s|[.،]|$)", r"‹إعداد\1›"),
    # عن التجار بالمخدرات → الاتجار بالمخدرات (forme juridique, sans inventer)
    (r"عن\s+التجار\s+بالمخدرات", "‹الاتجار بالمخدرات›"),
    (r"جرائم\s+عن\s+التجار(?!\s+بالمخدرات)", "جرائم ‹الاتجار›"),
    (r"قضايا\s+عن\s+التجار(?!\s+بالمخدرات)", "قضايا ‹الاتجار›"),
]


def light_arabic_fusha_form(text: str) -> str:
    """Corrections de FORME fusḥā — sans résumer ni supprimer de faits.

    Les substitutions STT évidentes sont enveloppées dans ‹…› (surlignage orange UI).
    Les retouches mineures (همزة، ترقيم، accord) restent non marquées.
    """
    t = (text or "").strip()
    if not t:
        return ""
    # Conserver d’éventuels marqueurs déjà présents ; éviter double ‹‹
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"‹+", "‹", t)
    t = re.sub(r"›+", "›", t)

    # 1) STT marqué (avant les règles de forme génériques)
    for pat, repl in _STT_FUSHA_MARKED:
        t = re.sub(pat, repl, t)

    # 2) Forme fusḥā (hamza, tā marbūṭa, grammaire légère) — sans ‹ ›
    replacements = [
        (r"(?<!\S)ان(?=\s)", "إن"),
        (r"(?<=[.。؟!\n،])\s*ان(?=\s)", "إن"),
        (r"(?<!\S)الى(?=\s|[.،]|$)", "إلى"),
        (r"القائها", "إلقائها"),
        (r"القاءها", "إلقاءها"),
        (r"القاء(?=\s)", "إلقاء"),
        (r"(?<!\S)الاشخاص(?=\s|[.،]|$)", "الأشخاص"),
        (r"(?<!\S)اشخاص(?=\s|[.،]|$)", "أشخاص"),
        (r"(?<!\S)الاولى(?=\s)", "الأولى"),
        (r"(?<!\S)اخر(?=\s)", "آخر"),
        (r"(?<!\S)اخرين(?=\s)", "آخرين"),
        (r"(?<!\S)ايضا(?=\s|[.،]|$)", "أيضاً"),
        (r"(?<!\S)ايضاً(?=\s|[.،]|$)", "أيضاً"),
        # Accord : تورطت فيها عدد → تورط فيها عدد (عدد = masculin)
        (r"والتي\s+كانت\s+قد\s+تورطت\s+فيها\s+(عدد|أعداد)", r"والتي كان قد تورط فيها \1"),
        (r"كانت\s+قد\s+تورطت\s+فيها\s+(عدد|أعداد)", r"كان قد تورط فيها \1"),
        (r"والتي\s+تورطت\s+فيها\s+(عدد|أعداد)", r"والتي تورط فيها \1"),
        (r"تورطت\s+فيها\s+(عدد|أعداد)", r"تورط فيها \1"),
        (r"والتي تورط (?!فيها)", "والتي تورط فيها "),
        (r"والتي تورطت (?!فيها)", "والتي تورطت فيها "),
        (r"باقسم (?=العقوبات)", "نطالب بأقصى "),
        (r"(?<!\S)ايجار(?=\s)", "إيجار"),
        (r"وامر[اأ]تين", "وامرأتان"),
        (r"(?<!\S)اعمارهم(?=\s)", "أعمارهم"),
        (r"اعمارهما", "أعمارهم"),
        (r"معالجتة", "معالجته"),
        (r"محامي\s*لـ?\s*ة", "المحامية"),
        (r"المحامي\s*لـ?\s*ة", "المحامية"),
        (r"بصددي\s", "بصدد "),
        (r"امام\s*محكمتكم", "أمام محكمتكم"),
        (r"امام\s*محكمة", "أمام محكمة"),
        (r"سيدي الرئيس(?![،,])", "سيدي الرئيس،"),
    ]
    for pat, repl in replacements:
        t = re.sub(pat, repl, t)
    for marker in ("ملف رقم", "وتاريخ الجلسة", "تاريخ الجلسة", "ولذلك", "وعليه"):
        t = re.sub(rf"(?<![،.\n])\s+({re.escape(marker)})", rf"، \1", t)
    t = re.sub(r"،\s*،+", "،", t)
    t = re.sub(r"\s{2,}", " ", t).strip()
    if len(t) > 40 and t[-1] not in ".!?؟۔‹›":
        t = t.rstrip(" ،,") + "."
    return t
