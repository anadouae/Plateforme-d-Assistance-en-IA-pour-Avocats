"""Language detection and multilingual prompts for Sanad LLM."""

from __future__ import annotations

import json
import re
from typing import Literal

SupportedLocale = Literal["fr", "ar", "en"]

_ARABIC_RE = re.compile(r"[\u0600-\u06FF]")
_FRENCH_MARKERS = re.compile(r"[éèêëàâùûôîïç]", re.I)
_EN_WORDS = {
    "the", "what", "how", "when", "where", "which", "who", "why",
    "is", "are", "can", "does", "should", "law", "legal", "contract",
    "summarize", "summary", "explain", "article", "hello", "hi", "hey",
    "want", "minimum", "wage", "salary",
}
_ARABIC_REQUEST_RE = re.compile(
    r"en\s+arabe|in\s+arabic|بالعربية|باللغة\s+العربية|arabic\s+language",
    re.I,
)
_FR_WORDS = {
    "le", "la", "les", "quel", "quelle", "quels", "comment", "est", "sont",
    "droit", "contrat", "loi", "article", "délai", "parties", "synthèse",
    "résume", "résumer", "explique", "salaire", "smig", "minimum", "marocain",
    "marocaine", "bonjour", "veux", "pendant", "durant", "année",
}


def normalize_locale(value: str | None) -> SupportedLocale:
    """Sanad Maroc : arabe par défaut ; FR optionnel ; EN → AR."""
    if not value:
        return "ar"
    code = value.strip().lower()[:2]
    if code == "fr":
        return "fr"
    if code == "en":
        return "ar"
    if code == "ar":
        return "ar"
    return "ar"


_DARIJA_LATIN_RE = re.compile(
    r"\b(?:jadid|jdid|akhir|akher|9anoun|qanoun|maghribi|maghrebi|"
    r"brit|bghit|n3raf|chnou|ach|kayn|wach|hiya|howa|bzaf|mzyan|"
    r"salam|salem|3la|fih|dyal|liya|ghir)\b",
    re.I,
)


def detect_language(text: str, fallback: str = "fr") -> SupportedLocale:
    """Detect fr / ar / en from text content (incl. Darija latin)."""
    if not text or not text.strip():
        return normalize_locale(fallback)

    sample = text.strip()[:2000]
    arabic_chars = len(_ARABIC_RE.findall(sample))
    word_chars = len(re.findall(r"\w", sample, re.UNICODE))
    if word_chars > 0 and arabic_chars / word_chars > 0.12:
        return "ar"

    # Darija en alphabet latin → réponse FR (juridique clair), jamais EN par défaut
    if _DARIJA_LATIN_RE.search(sample):
        fb = normalize_locale(fallback)
        return "ar" if fb == "ar" else "fr"

    words = {w.lower() for w in re.findall(r"\b\w+\b", sample.lower())}
    en_score = len(words & _EN_WORDS)
    fr_score = len(words & _FR_WORDS)
    if _FRENCH_MARKERS.search(sample):
        fr_score += 2

    if en_score >= 2 and en_score > fr_score:
        return "en"
    if fr_score >= 1 and fr_score >= en_score:
        return "fr"
    if en_score >= 1:
        return "en"

    return normalize_locale(fallback)


def resolve_response_language(
    question: str | None = None,
    user_locale: str | None = None,
) -> SupportedLocale:
    """Question language wins; explicit 'en arabe' / 'بالعربية' forces Arabic."""
    locale = normalize_locale(user_locale)
    if question and question.strip():
        if _ARABIC_REQUEST_RE.search(question) or _ARABIC_RE.search(question):
            arabic_chars = len(_ARABIC_RE.findall(question[:2000]))
            word_chars = len(re.findall(r"\w", question[:2000], re.UNICODE))
            if _ARABIC_REQUEST_RE.search(question) or (
                word_chars > 0 and arabic_chars / word_chars > 0.08
            ):
                return "ar"
        return detect_language(question, fallback=locale)
    return locale


def get_disclaimer(locale: SupportedLocale) -> str:
    disclaimers = {
        "fr": "Ceci ne constitue pas un avis juridique.",
        "ar": "هذا لا يشكل استشارة قانونية.",
        "en": "This does not constitute legal advice.",
    }
    return disclaimers[locale]


def get_open_chat_prompt(locale: SupportedLocale, custom_prompt: str | None = None) -> str:
    """Chat ouvert style Mistral / Gemini / ChatGPT — sources = enrichissement, pas cage."""
    prompts = {
        "fr": (
            "Tu es Sanad-Legal, un assistant juridique de niveau Mistral Chat / Gemini / ChatGPT. "
            "Réponds de façon OUVERTE, riche, structurée et utile — comme un excellent avocat-conseil. "
            "CONVERSATION : suis le message ACTUEL ; si l'utilisateur change de sujet, suis le nouveau. "
            "Les SOURCES / le web sont un ENRICHISSEMENT (citations, dates, numéros) — "
            "pas une cage : tu peux expliquer le cadre, comparer, lister plusieurs textes, "
            "donner de la méthode. "
            "Garde-fou : n'invente PAS un numéro de loi, article, amende ou date précis "
            "s'il n'apparaît pas dans les sources ou l'historique fiable ; "
            "si tu donnes un cadre général sans numéro, dis-le. "
            "Cite [1][2] quand tu t'appuies sur une source. "
            "Presse ≠ Bulletin officiel : distingue adopté / en discussion / à vérifier. "
            "Structure Markdown libre et claire (titres, listes). Minimum ~200 mots. "
            "Réponds dans la langue de l'utilisateur (FR/AR/EN)."
        ),
        "ar": (
            "أنت Sanad-Legal بمستوى Mistral Chat / Gemini: مساعد قانوني مفتوح وغني. "
            "اتبع رسالة المستخدم الحالية؛ إن غيّر الموضوع فاتبعه. "
            "المصادر إثراء للاستشهاد وليس قفصاً — يمكنك الشرح والمقارنة وذكر عدة نصوص. "
            "لا تختلق رقم قانون/مادة/غرامة إن لم يرد في المصادر. استشهد بـ [1][2]. "
            "Markdown واضح. ~200 كلمة على الأقل. أجب بلغة المستخدم."
        ),
        "en": (
            "You are Sanad-Legal at Mistral Chat / Gemini quality: open, rich, useful. "
            "Follow the CURRENT user message; if they switch topics, switch with them. "
            "SOURCES enrich (citations, dates) — they do not cage you. "
            "Do not invent precise law/article/penalty numbers absent from sources. "
            "Cite [1][2]. Clear Markdown. ~200+ words. Answer in the user's language."
        ),
    }
    base = prompts[locale]
    if custom_prompt and custom_prompt.strip():
        return base + f"\n\nCabinet instructions:\n{custom_prompt.strip()}"
    return base


def get_clear_grounded_prompt(locale: SupportedLocale, custom_prompt: str | None = None) -> str:
    """Rédaction riche avec sources en appui (pas « uniquement les extraits »)."""
    prompts = {
        "fr": (
            "Tu es Sanad-Legal (niveau Mistral/Gemini). "
            "Rédige une réponse COMPLÈTE et utile. "
            "Les SOURCES enrichissent et permettent de citer [1][2] — "
            "tu n'es PAS limité à répéter un seul extrait. "
            "Si plusieurs lois/domaines apparaissent, liste-les. "
            "N'invente aucun numéro précis absent des sources. "
            "Sources partielles → dis-le en 1 phrase, puis développe utilement. "
            "Markdown clair, ~200+ mots."
        ),
        "ar": (
            "أنت Sanad-Legal (مستوى Mistral/Gemini). "
            "أجب إجابة كاملة. المصادر للإثراء و[1][2] — لست مقيداً بمقتطف واحد. "
            "لا تختلق أرقاماً غير موجودة. Markdown واضح."
        ),
        "en": (
            "You are Sanad-Legal (Mistral/Gemini level). "
            "Write a full useful answer. SOURCES enrich with [1][2] — "
            "you are not limited to one excerpt. Never invent missing numbers."
        ),
    }
    base = prompts[locale]
    if custom_prompt and custom_prompt.strip():
        return base + f"\n\nCabinet instructions:\n{custom_prompt.strip()}"
    return base


def get_system_prompt(locale: SupportedLocale, custom_prompt: str | None = None) -> str:
    prompts = {
        "fr": (
            "Tu es Sanad-Legal : assistant juridique OUVERT comme Mistral Chat / Gemini. "
            "Réponds clairement et complètement à toute question pertinente. "
            "Dossier/document fourni → PRIORITÉ. Sinon web/corpus = enrichissement. "
            "N'invente pas de numéros précis (article, loi, peine, date) sans source. "
            "Cite [1][2] quand tu t'appuies sur une source. "
            "Sources faibles → dis-le + où vérifier (sgg.gov.ma) — mais reste utile. "
            "Interdit « les sources fournies ne mentionnent pas » comme seule réponse."
        ),
        "ar": (
            "أنت Sanad-Legal: مساعد قانوني مفتوح مثل Mistral/Gemini. "
            "أجب بوضوح واكتمال. أولوية للملف/الوثيقة. "
            "لا تختلق أرقاماً دقيقة بلا مصدر. استشهد بـ [1][2]."
        ),
        "en": (
            "You are Sanad-Legal: an OPEN legal assistant like Mistral/Gemini. "
            "Answer fully. Prioritize case/document context. "
            "No invented precise citations. Cite [1][2] when using sources."
        ),
    }
    base = prompts[locale]
    if custom_prompt and custom_prompt.strip():
        return base + f"\n\nCabinet instructions:\n{custom_prompt.strip()}"
    return base


def get_synthesis_prompt(locale: SupportedLocale) -> str:
    prompts = {
        "fr": (
            "Tu es Sanad-Legal, assistant d'avocat marocain. Analyse le document fourni. "
            "Réponds UNIQUEMENT en français. "
            "Retourne UNIQUEMENT un objet JSON valide (sans markdown) avec les clés : "
            "parties (liste), key_dates (liste), amounts (liste), risk_clauses (liste), "
            "attention_points (liste), summary (texte de synthèse structurée). "
            "Règles strictes :\n"
            "- Extrais UNIQUEMENT ce qui figure dans le texte — n'invente ni parties, ni lois, ni montants.\n"
            "- Interdit de citer des lois génériques (ex. 53.05, 09.08) si elles ne sont pas dans le texte.\n"
            "- Interdit de coller de longs extraits OCR dans summary.\n"
            "- Si le texte est illisible, dis-le dans attention_points.\n"
            "Le champ summary : Markdown professionnel (120–220 mots), sections :\n"
            "## Objet du document\n"
            "## Parties\n"
            "## Faits et enjeux\n"
            "## Obligations / délais / montants\n"
            "## Risques et points d'attention\n"
            "Puces courtes, actionnables pour l'avocat."
        ),
        "ar": (
            "أنت Sanad-Legal، مساعد محامٍ مغربي. حلّل الوثيقة القانونية المقدمة. "
            "أجب حصرياً بالعربية الفصحى (ممنوع الفرنسية أو الإنجليزية في summary والقوائم). "
            "أرجع فقط كائناً JSON صالحاً (بدون markdown خارج JSON) بالمفاتيح: "
            "parties (قائمة), key_dates (قائمة), amounts (قائمة), risk_clauses (قائمة), "
            "attention_points (قائمة), summary (نص التلخيص). "
            "قواعد صارمة:\n"
            "- استخرج فقط ما هو موجود في النص — لا تختلق أطرافاً ولا قوانين ولا مبالغ.\n"
            "- ممنوع نسخ فقرات OCR طويلة داخل summary.\n"
            "- ممنوع إدراج قوانين عامة (مثل 53.05 أو 09.08) إن لم تُذكر صراحة في النص.\n"
            "- إن كان النص غير واضح، قل ذلك في attention_points ولا تخمّن.\n"
            "حقل summary: Markdown مهني (120–220 كلمة) بأقسام:\n"
            "## موضوع الوثيقة\n"
            "## الأطراف\n"
            "## الوقائع والمسائل\n"
            "## الالتزامات والآجال والمبالغ\n"
            "## المخاطر ونقاط الانتباه\n"
            "نقاط قصيرة، دقيقة، قابلة للاستخدام في جلسة."
        ),
        "en": (
            "You are Sanad-Legal. Analyze the Moroccan legal document. "
            "Reply in Arabic (product default). Return ONLY valid JSON with keys: "
            "parties, key_dates, amounts, risk_clauses, attention_points, summary. "
            "Extract only from the provided text — never invent laws or parties."
        ),
    }
    return prompts.get(locale, prompts["ar"])


def get_document_qa_prompt(locale: SupportedLocale) -> str:
    prompts = {
        "fr": (
            "Tu es Sanad-Legal. Réponds UNIQUEMENT en français à partir du TEXTE DU DOCUMENT fourni. "
            "INTERDIT : utiliser le corpus juridique général ou le web. "
            "Si l'information n'est pas dans le document, dis-le clairement. "
            "Structure ta réponse en Markdown :\n"
            "## Réponse\n## Éléments clés du document\n## Points d'attention\n"
            "Cite le document comme source [1]. Sois précis et détaillé."
        ),
        "ar": (
            "أنت Sanad-Legal. أجب حصرياً بالعربية من نص الوثيقة المقدم فقط. "
            "ممنوع استخدام المكتبة القانونية العامة أو الإنترنت. "
            "إذا لم تكن المعلومة في الوثيقة، قل ذلك بوضوح. "
            "نظّم إجابتك: ## الإجابة ## العناصر الأساسية ## نقاط الانتباه"
        ),
        "en": (
            "You are Sanad-Legal. Reply ONLY in English from the PROVIDED DOCUMENT TEXT. "
            "FORBIDDEN: use general legal corpus or web. "
            "If information is not in the document, say so clearly. "
            "Structure: ## Answer ## Key elements ## Points of attention"
        ),
    }
    return prompts[locale]


def get_case_analysis_prompt(locale: SupportedLocale) -> str:
    prompts = {
        "fr": (
            "Tu es Sanad-Legal. Analyse le dossier juridique à partir des pièces fournies. "
            "Réponds UNIQUEMENT en français. "
            "Structure : 1) Faits 2) Pièces clés 3) Enjeux juridiques "
            "4) Risques / délais 5) Points à vérifier. "
            "N'invente aucun fait absent des extraits. "
            "Termine par : « Ceci ne constitue pas un avis juridique. »"
        ),
        "ar": (
            "أنت Sanad-Legal. حلّل الملف القانوني من الوثائق المقدمة. "
            "أجب حصرياً باللغة العربية. "
            "نظّم إجابتك: 1) الوقائع 2) الوثائق الأساسية 3) المسائل القانونية "
            "4) المخاطر / الآجال 5) نقاط للتحقق. "
            "لا تخترع وقائع غير موجودة في المقتطفات. "
            "اختم بـ: « هذا لا يشكل استشارة قانونية. »"
        ),
        "en": (
            "You are Sanad-Legal. Analyze the legal case from the provided documents. "
            "Reply ONLY in English. "
            "Structure: 1) Facts 2) Key documents 3) Legal issues "
            "4) Risks / deadlines 5) Points to verify. "
            "Do not invent facts absent from the excerpts. "
            "End with: « This does not constitute legal advice. »"
        ),
    }
    return prompts[locale]


def parse_llm_json(raw: str | None) -> dict | None:
    """Extract JSON object from LLM response."""
    if not raw:
        return None
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fence:
        text = fence.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


def msg_no_sources(locale: SupportedLocale) -> str:
    return {
        "fr": "Aucune source pertinente identifiée. L'assistant ne peut pas répondre sans source.",
        "ar": "لم يتم العثور على مصدر ذي صلة. لا يمكن للمساعد الإجابة بدون مصدر.",
        "en": "No relevant source found. The assistant cannot answer without a source.",
    }[locale]


def msg_no_reliable_sources_for_topic(locale: SupportedLocale, topic_hint: str = "") -> str:
    """Fallback clair (style assistant) si Groq/Kimi indisponibles — zéro invention."""
    topic = (topic_hint or "").strip() or "ce sujet"
    topic_ar = (topic_hint or "").strip() or "هذا الموضوع"
    return {
        "fr": (
            f"## Réponse\n\n"
            f"Je n’ai pas trouvé, dans les sources indexées Sanad ni dans des extraits web fiables, "
            f"un texte précis sur **{topic}**. "
            f"Je préfère donc ne pas inventer un numéro de loi ni décrire de « renouvellements » fictifs.\n\n"
            f"## Cadre utile\n\n"
            f"En pratique, pour ce type de question au Maroc, la démarche fiable est :\n"
            f"1. Consulter le Bulletin officiel (sgg.gov.ma) avec les mots-clés du thème ;\n"
            f"2. Croiser avec Adala / justice.gov.ma ;\n"
            f"3. Vérifier s’il s’agit d’un dahir, d’une loi, d’un décret ou d’une circulaire.\n\n"
            f"## En pratique\n\n"
            f"- Ouvrir : https://www.sgg.gov.ma/BulletinOfficiel.aspx\n"
            f"- Ou déposer le PDF de la loi dans un dossier Sanad pour une analyse ciblée.\n"
            f"- Reformuler la question avec une année ou un numéro de BO si vous l’avez."
        ),
        "ar": (
            f"## الإجابة\n\n"
            f"لم أعثر ضمن مصادر Sanad المفهرسة ولا في مقاطع ويب موثوقة على نص دقيق حول **{topic_ar}**. "
            f"لذلك لن أخترع رقم قانون ولن أصف «تجديدات» غير موثقة.\n\n"
            f"## إطار مفيد\n\n"
            f"للأسئلة من هذا النوع في المغرب، المنهجية الموثوقة هي:\n"
            f"1) البحث في الجريدة الرسمية (sgg.gov.ma) بكلمات الموضوع؛\n"
            f"2) المقارنة مع بوابة العدالة Adala؛\n"
            f"3) التمييز بين ظهير / قانون / مرسوم / دورية.\n\n"
            f"## عملياً\n\n"
            f"- الرابط: https://www.sgg.gov.ma/BulletinOfficiel.aspx\n"
            f"- أو ارفع ملف PDF للقانون داخل ملف Sanad لتحليله.\n"
            f"- إن توفرت سنة أو رقم الجريدة الرسمية، أضفها في سؤالك."
        ),
        "en": (
            f"## Answer\n\n"
            f"I could not find a reliable indexed text on **{topic}**. "
            f"I will not invent a law number or describe unverified updates.\n\n"
            f"## Useful framework\n\n"
            f"1) Search the Official Gazette (sgg.gov.ma);\n"
            f"2) Cross-check Adala / justice.gov.ma;\n"
            f"3) Identify whether it is a dahir, statute, decree or circular.\n\n"
            f"## In practice\n\n"
            f"- https://www.sgg.gov.ma/BulletinOfficiel.aspx\n"
            f"- Or upload the law PDF into a Sanad case for targeted analysis."
        ),
    }[locale]


def msg_doc_not_found(locale: SupportedLocale) -> str:
    return {
        "fr": (
            "Je n'ai pas trouvé de passage pertinent dans ce document. "
            "Vérifiez la qualité du scan (OCR) ou reformulez votre question."
        ),
        "ar": (
            "لم أجد مقتطفاً مناسباً في هذه الوثيقة. "
            "تحقق من جودة المسح الضوئي (OCR) أو أعد صياغة سؤالك."
        ),
        "en": (
            "I could not find a relevant passage in this document. "
            "Check scan quality (OCR) or rephrase your question."
        ),
    }[locale]


def msg_insufficient_text(locale: SupportedLocale) -> str:
    return {
        "fr": "Le document ne contient pas assez de texte extractible.",
        "ar": "الوثيقة لا تحتوي على نص كافٍ للاستخراج.",
        "en": "The document does not contain enough extractable text.",
    }[locale]


def msg_attention_insufficient(locale: SupportedLocale) -> str:
    return {
        "fr": "Texte insuffisant pour une synthèse fiable",
        "ar": "نص غير كافٍ لتلخيص موثوق",
        "en": "Insufficient text for a reliable synthesis",
    }[locale]


_GREETINGS_EXACT = {
    "hello", "hi", "hey", "hy", "yo", "bonjour", "bonsoir", "salut", "coucou", "cc", "slt",
    "salam", "salem", "assalam", "assalamu", "asalam", "مرحبا", "مرحباً", "السلام", "سلام",
}
_GREETING_PREFIXES = ("salam", "assalam", "asalam", "hello", "bonjour", "hey", "hi ")
_RECENT_LAW_RE = re.compile(
    r"(?:\b20(?:2[0-9]|3[0-6])\b|mise[s]?\s+a\s+jour|mises?\s+a\s+jour|"
    r"derni[eè]re?s?\s+(?:lois?|textes?|r[eé]formes?)|nouveau(?:x|lle)?s?\s+lois?|"
    r"r[eé]forme|r[eé]formes|bulletin\s+officiel|"
    r"lois?\s+marocaine?s?\s+20(?:2[0-9]|3[0-6])|l[eé]gislation\s+marocaine\s+20|"
    r"\b10\s+ans\b|dix\s+ans|derni[eè]res?\s+ann[eé]es|"
    r"\b(?:jadid|jdid|akhir|akher)\b|"
    r"(?:9anoun|qanoun)\s+maghribi|"
    r"آخر|اخر|أحدث|احدث|العشر|سنوات|تحديث|مستجدات|إصلاحات|تشريعات|"
    r"جديد|القانون\s+المغربي|قانون\s+مغربي|قوانين\s+مغربي)",
    re.I,
)
_SUBSTANTIVE_LEGAL_HINTS = (
    "salaire", "smig", "smmig", "minimum", "loyer", "bail", "contrat",
    "délai", "delai", "appel", "tribunal", "article", "code", "loi",
    "droit", "travail", "pénal", "penal", "civil", "commercial",
    "parties", "obligation", "résiliation", "resiliation", "montant",
    "الأجر", "الحد", "الأدنى", "العقد", "الإيجار", "الاستئناف",
    "wage", "salary", "appeal", "deadline", "lease", "tenant",
)

_REFORM_LAW_HINTS = (
    "réforme", "reforme", "réformes", "mise à jour", "mise a jour",
    "mises à jour", "nouvelle loi", "nouvelles lois", "bulletin officiel",
    "lois marocaine", "législation marocaine", "textes récents",
    "dernières lois", "derniere loi", "10 ans", "dix ans",
    "le jadid", "akhir jadid", "akher jadid", "chnou jadid", "ach kayn",
    "9anoun maghribi", "qanoun maghribi",
    "إصلاح", "تشريع", "جريدة", "مستجدات", "قوانين جديدة", "شنو الجديد",
    "آخر قانون", "اخر قانون", "أحدث قانون", "احدث قانون",
    "آخر القوانين", "اخر القوانين", "قوانين مغربية", "قانون مغربي",
    "التحديثات القانونية", "ما هو آخر", "ما هي آخر",
    "recent law", "new law", "legislative reform", "official gazette",
)


def _has_substantive_legal_topic(text: str) -> bool:
    q = (text or "").lower()
    return any(h in q for h in _SUBSTANTIVE_LEGAL_HINTS)


def _has_reform_law_intent(text: str) -> bool:
    q = (text or "").lower()
    q_ar = text or ""
    if any(h in q for h in _REFORM_LAW_HINTS):
        return True
    # Arabe : « آخر/اخر قانون » (avec ou sans hamza)
    if re.search(r"(?:آخر|اخر|أحدث|احدث).{0,20}(?:قانون|قوانين)", q_ar):
        return True
    if re.search(r"(?:قانون|قوانين).{0,20}(?:مغرب|مغربي)", q_ar) and re.search(
        r"(?:آخر|اخر|أحدث|احدث|جديد|جديدة|أريد|اريد|عرف)", q_ar
    ):
        return True
    # Darija latin : « jadid / jdid / tbdl » = actualités / nouveautés législatives
    if re.search(r"\b(?:jadid|jdid|mustajadat|mustajid|tbdl|tbeddel)\b", q):
        if re.search(
            r"\b(?:9anoun|qanoun|loi|droit|maghribi|maghrebi|maroc|morocco|"
            r"تشريع|قانون|قانوني)\b",
            q,
        ) or len(q.split()) <= 10:
            return True
    if re.search(r"\b(?:akhir|akher|dernier|derni[eè]re?s?)\b", q) and re.search(
        r"\b(?:9anoun|qanoun|loi|droit|jadid|jdid|maghribi|tbdl)\b", q
    ):
        return True
    if re.search(r"\b(?:9anoun|qanoun)\b", q) and re.search(
        r"\b(?:maghribi|maghrebi|maghrii?bi|maroc)\b", q
    ):
        return True
    if re.search(r"\b(?:n3raf|n3rz|brit|bghit)\b", q) and re.search(
        r"\b(?:9anoun|qanoun|jadid|jdid|loi)\b", q
    ):
        return True
    return False


_MA_DOMAIN_HINTS = (".ma", "sgg.gov", "justice.gov", "adala", "maroc")


def _normalize_greeting(text: str) -> str:
    return re.sub(r"[!?.،]+$", "", text.strip().lower())


def is_greeting(text: str) -> bool:
    q = _normalize_greeting(text)
    if not q or len(q) > 40:
        return False
    if q in _GREETINGS_EXACT:
        return True
    if any(q.startswith(p) for p in _GREETING_PREFIXES):
        return True
    words = q.split()
    return len(words) <= 2 and words[0] in _GREETINGS_EXACT


def extract_year_filter(text: str) -> list[int] | None:
    """Année(s) explicitement demandées (ex. « seulement 2026 », « en 2026 »)."""
    if not text:
        return None
    q = text.lower()
    only_year = re.search(
        r"(?:seulement|uniquement|pendant|durant|en|pour|l['\s]?ann[eé]e|year)\s+(20[12]\d)",
        q,
        re.I,
    )
    if only_year:
        return [int(only_year.group(1))]
    only_direct = re.search(r"\b(seulement|uniquement)\s+(20[12]\d)\b", q, re.I)
    if only_direct:
        return [int(only_direct.group(2))]
    years = [int(y) for y in re.findall(r"\b(20[12]\d)\b", text)]
    if len(years) == 1:
        return years
    if re.search(r"\b(seulement|uniquement)\b", q) and years:
        return [max(years)]
    return None


def is_unclear_question(text: str) -> bool:
    """Uniquement les messages vraiment vides / incomplets (ne pas bloquer le chat)."""
    raw = (text or "").strip()
    if len(raw) < 2:
        return True
    # Interrogatif seul sans sujet
    if re.fullmatch(r"(?:ما\s*هي|ما\s*هو|ماذا|كيف|لماذا|متى|أين|وين|شنو|اش)\??", raw):
        return True
    if re.fullmatch(r"(?:quoi|comment|pourquoi|\?+)\??", raw.lower()):
        return True
    return False


def msg_unclear_question(locale: SupportedLocale) -> str:
    return {
        "fr": (
            "Votre question est trop vague pour une recherche juridique précise. "
            "Reformulez avec un sujet concret, par exemple :\n"
            "- « Quelles lois marocaines publiées en 2026 ? »\n"
            "- « Délai d'appel en matière civile après la loi 22-24 »\n"
            "- « Validité d'une clause de résiliation dans un bail commercial »"
        ),
        "ar": (
            "سؤالك عام جداً. أعد صياغته بموضوع قانوني محدد، مثل: "
            "« ما هي القوانين المغربية الصادرة سنة 2026؟ »"
        ),
        "en": (
            "Your question is too vague for a legal search. Try something specific, e.g. "
            "« What Moroccan laws were published in 2026? »"
        ),
    }[locale]


def msg_no_laws_for_year(year: int, locale: SupportedLocale) -> str:
    return {
        "fr": (
            f"Aucune loi indexée dans Sanad pour l'année **{year}** uniquement. "
            f"Notre base couvre les textes référencés jusqu'à 2024 (loi 22-24 CPC). "
            f"Pour {year}, consultez le Bulletin officiel : https://www.sgg.gov.ma/BulletinOfficiel.aspx\n\n"
            "Uploadez un PDF de loi/décret 2026 dans un dossier pour une analyse ciblée."
        ),
        "ar": (
            f"لا توجد قوانين مفهرسة لسنة {year} فقط في Sanad. "
            "راجع الجريدة الرسمية على sgg.gov.ma"
        ),
        "en": (
            f"No laws indexed in Sanad for year {year} only. "
            "Check the official gazette at sgg.gov.ma"
        ),
    }[locale]


def _heuristic_recent_law_query(text: str) -> bool:
    """Secours regex uniquement si le LLM de compréhension est down."""
    if not text or not text.strip():
        return False
    if _has_substantive_legal_topic(text) and not _has_reform_law_intent(text):
        return False
    if _has_reform_law_intent(text):
        return True
    if extract_year_filter(text) and not _has_substantive_legal_topic(text):
        return True
    return bool(_RECENT_LAW_RE.search(text))


def is_recent_law_query(text: str) -> bool:
    """Heuristique rapide — pas d'appel LLM (évite saturation API)."""
    return _heuristic_recent_law_query(text)


Jurisdiction = Literal["ma", "fr", "general"]


def detect_jurisdiction(text: str) -> Jurisdiction:
    """Pays / ordre juridique visé par la question."""
    q = (text or "").lower()
    fr_hints = (
        "france", "français", "francaise", "française", "loi francaise",
        "loi française", "légifrance", "legifrance", "journal officiel",
        "code civil français", "république française",
    )
    ma_hints = (
        "maroc", "morocco", "maghribi", "maghrebi", "مغرب", "مغربي",
        "sgg.gov", "bulletin officiel", "dahir", "moudawana", "ancfcc",
        "9anoun l maghribi", "9anoun maghribi",
    )
    if any(h in q for h in fr_hints):
        return "fr"
    if any(h in q for h in ma_hints):
        return "ma"
    # Défaut produit Sanad = droit marocain, sauf question clairement autre
    return "ma"


def rewrite_question_for_search(text: str) -> str:
    """Reformulation rapide SANS appel LLM (évite 429 Groq/Kimi)."""
    return (text or "").strip()


def build_open_web_queries(question: str) -> list[str]:
    """Requêtes web ouvertes (monde) — sans LLM, style recherche Groq/Kimi."""
    clean = (question or "").strip()
    jur = detect_jurisdiction(clean)
    q_low = clean.lower()
    animal = any(
        w in q_low
        for w in ("animal", "animaux", "animale", "chien", "chat", "حيوان", "حيوانات")
    )
    animal_neg = ' -assurance -voiture -automobile -"assurance auto" -lelynx -autotrader'

    if jur == "fr":
        queries = [
            clean,
            f"{clean} site:legifrance.gouv.fr",
            f"{clean} droit français",
            f"{clean} Journal officiel France -youtube",
        ]
        if animal:
            queries = [
                f"protection animale loi France{animal_neg}",
                f"bien-être animal législation France site:legifrance.gouv.fr",
                *queries,
            ]
        return queries
    if jur == "general":
        return [
            clean,
            f"{clean} law legal",
            f"{clean} législation",
        ]
    # Maroc + recherche ouverte (peu de requêtes = plus rapide)
    if animal:
        return [
            "projet de loi 19.25 animaux errants Maroc",
            "loi 19.25 protection animaux errants Maroc Parlement",
            f"animaux errants Maroc loi 2025 2026{animal_neg}",
            "Chambre des représentants loi animaux errants Maroc",
            f"قانون الحيوانات الضالة المغرب 19.25",
            f"{clean} Maroc{animal_neg}",
        ]
    return [
        clean,
        f"{clean} Maroc droit",
        f"{clean} site:sgg.gov.ma",
    ]


def build_recent_law_web_queries(question: str, locale: str = "fr") -> list[str]:
    from app.services.topic_filter import (
        is_generic_recent_laws_query,
        is_panorama_laws_query,
        tokenize_question,
    )

    years = re.findall(r"20[12]\d", question or "")
    year_filter = extract_year_filter(question)
    if year_filter:
        year_span = str(year_filter[0])
    elif len(years) >= 2:
        year_span = f"{min(years)}-{max(years)}"
    elif years:
        year_span = years[0]
    else:
        year_span = "2020-2026"

    # Pas d'appel LLM ici (évite 429 Groq/Gemini pendant la recherche)
    clean = rewrite_question_for_search(question)

    # Panorama « toutes les lois 2026 » → requêtes multi-domaines
    if is_panorama_laws_query(question):
        queries = [
            f"réformes législatives Maroc {year_span} site:sgg.gov.ma",
            f"loi de finances {year_span} Maroc Bulletin officiel",
            f"loi organique élections Maroc {year_span}",
            f"Code procédure civile Maroc {year_span} Bulletin officiel",
            f"projet loi Code commerce Maroc {year_span}",
            f"lois adoptées Chambre représentants Maroc {year_span}",
            f"قوانين مصادق عليها المغرب {year_span} الجريدة الرسمية",
            f"nouvelles lois Maroc Bulletin officiel {year_span}",
        ]
        if locale == "ar":
            queries.insert(0, f"جميع القوانين المصادق عليها المغرب {year_span}")
        return queries

    # Sujet précis (animaux, travail…) → chercher CE thème, pas un dump de réformes
    if not is_generic_recent_laws_query(question) and tokenize_question(clean or question):
        topic = (clean or question).strip()
        q_low = topic.lower()
        animal = any(
            w in q_low
            for w in ("animal", "animaux", "animale", "chien", "chat", "حيوان", "حيوانات")
        )
        animal_neg = ' -assurance -voiture -automobile -"assurance auto" -lelynx'
        if animal:
            queries = [
                "projet de loi 19.25 animaux errants Maroc",
                f"loi 19.25 animaux errants Maroc {year_span}",
                f"animaux errants Parlement Maroc adoption loi {year_span}",
                "SPA Maroc loi 19.25",
                f"قانون الحيوانات الضالة المغرب {year_span}",
                f"{topic} Maroc{animal_neg}",
            ]
        else:
            queries = [
                f"{topic} Maroc site:sgg.gov.ma",
                f"{topic} Bulletin officiel Maroc loi",
                f"{topic} législation Maroc {year_span}",
                f"{topic} قانون المغرب الجريدة الرسمية",
                f"loi {topic} Maroc -youtube -gmail -excel",
            ]
        if locale == "ar":
            queries.insert(0, f"{topic} المغرب تشريع {year_span}")
        return queries

    queries = [
        f"réformes législatives Maroc {year_span} site:sgg.gov.ma",
        f"nouvelles lois Maroc Bulletin officiel {year_span}",
        f"sgg.gov.ma législation loi décret {year_span}",
        f"mises à jour droit marocain {year_span} -youtube -tiktok -gmail",
        f"قوانين جديدة المغرب الجريدة الرسمية {year_span}",
    ]
    if locale == "ar":
        queries.insert(0, f"آخر الإصلاحات التشريعية المغرب {year_span}")
    return queries


def resolve_greeting_locale(
    question: str | None = None,
    user_locale: str | None = None,
) -> SupportedLocale:
    """Salutations : langue UI ; arabe script → ar ; jamais EN pour salam/مرحبا."""
    locale = normalize_locale(user_locale)
    q = (question or "").strip()
    if _ARABIC_RE.search(q):
        return "ar"
    # salam / salem → FR sauf si UI en arabe
    if _normalize_greeting(q) in ("salam", "salem", "assalam", "asalam", "سلام"):
        return "ar" if locale == "ar" else "fr"
    return locale


def msg_greeting(locale: SupportedLocale) -> str:
    return {
        "fr": (
            "Bonjour ! Je suis Sanad-Legal. Posez une question juridique précise "
            "(ex. : délai d'appel, validité d'un bail, clause de résiliation) "
            "ou sélectionnez un dossier avec des documents uploadés.\n\n"
            "Ceci ne constitue pas un avis juridique."
        ),
        "ar": (
            "مرحباً! أنا Sanad-Legal. اطرح سؤالاً قانونياً محدداً "
            "أو اختر ملفاً يحتوي على وثائق مرفوعة.\n\n"
            "هذا لا يشكل استشارة قانونية."
        ),
        "en": (
            "Hello! I am Sanad-Legal. Ask a specific legal question "
            "(e.g. appeal deadline, lease validity) or select a case with uploaded documents.\n\n"
            "This does not constitute legal advice."
        ),
    }[locale]


def msg_recent_laws_not_indexed(locale: SupportedLocale) -> str:
    return {
        "fr": (
            "Cette question porte sur des textes récents (2020–2026) absents du corpus indexé. "
            "Sanad a consulté le web et les sources officielles disponibles, "
            "mais aucun extrait fiable n'a pu être récupéré automatiquement.\n\n"
            "Consultez le Bulletin officiel : https://www.sgg.gov.ma/BulletinOfficiel.aspx\n"
            "Ou uploadez le PDF de la loi / décret dans un dossier pour une analyse ciblée."
        ),
        "ar": (
            "يتعلق السؤال بنصوص حديثة (2020–2026) غير مفهرسة في المكتبة. "
            "لم يتم العثور على مقتطفات ويب موثوقة تلقائياً.\n\n"
            "راجع الجريدة الرسمية: https://www.sgg.gov.ma/BulletinOfficiel.aspx"
        ),
        "en": (
            "This question concerns recent texts (2020–2026) not in the indexed corpus. "
            "No reliable web excerpt could be retrieved automatically.\n\n"
            "Check the official gazette: https://www.sgg.gov.ma/BulletinOfficiel.aspx"
        ),
    }[locale]


def get_chat_answer_prompt(locale: SupportedLocale, custom_prompt: str | None = None) -> str:
    structure_fr = (
        "Rédige comme un excellent assistant IA : clair, fluide, utile.\n"
        "Structure OBLIGATOIRE du champ \"answer\" en Markdown avec de VRAIS sauts de ligne :\n\n"
        "## Réponse\n"
        "2 à 4 paragraphes complets (pas une phrase). Explique clairement.\n\n"
        "## Fondement juridique\n"
        "- chaque point sur sa ligne, avec citation [1] [2]\n"
        "- développe en 1-2 phrases par point\n\n"
        "## Points d'attention\n"
        "- risques, délais, nuances (liste à puces)\n\n"
        "## En pratique\n"
        "1-2 phrases concrètes pour l'avocat.\n\n"
        "RÈGLES DE FORME :\n"
        "- Une ligne vide entre chaque section et chaque paragraphe.\n"
        "- INTERDIT : un seul bloc dense, « voilà », « en résumé : » sans contenu.\n"
        "- INTERDIT : renvoyer seulement vers un site — réponds avec le fond.\n"
        "- Minimum ~180 mots si les sources le permettent."
    )
    structure_ar = (
        "أجب بأسلوب مساعد ذكي واضح ومفيد، مع أسطر فارغة حقيقية.\n"
        "## الإجابة\n"
        "فقرتان إلى أربع فقرات كاملة.\n\n"
        "## الأساس القانوني\n"
        "- نقاط مع استشهاد [1] [2]\n\n"
        "## نقاط الانتباه\n"
        "- مخاطر وآجال\n\n"
        "## عملياً\n"
        "جملة أو جملتان تطبيقيتان.\n"
        "ممنوع دمج كل شيء في فقرة واحدة."
    )
    structure_en = (
        "Write like a strong AI assistant: clear, fluent, useful, with real blank lines.\n"
        "## Answer\n"
        "2–4 full paragraphs (not one sentence).\n\n"
        "## Legal basis\n"
        "- each point on its own line with [1] [2]\n"
        "- 1–2 sentences per point\n\n"
        "## Points of attention\n"
        "- risks, deadlines, nuances\n\n"
        "## In practice\n"
        "1–2 concrete sentences for the lawyer.\n\n"
        "FORM RULES: blank line between sections; no dense single block; no empty filler."
    )
    prompts = {
        "fr": (
            "Tu es Sanad-Legal (qualité Mistral Chat / Gemini). "
            "Réponds en français. "
            f"{structure_fr} "
            'Retourne UNIQUEMENT un JSON valide : '
            '"answer" (Markdown avec \\n\\n), "summary" (2-3 phrases). '
            "RÈGLES :\n"
            "1) OUVERT — réponds à la question posée sans te limiter à un seul texte si on demande un panorama.\n"
            "2) CONTEXTE dossier/document → priorité.\n"
            "3) Sources = enrichissement + [1][2] ; cadre général OK sans numéro inventé.\n"
            "4) Recherche faible → 1 phrase de prudence + réponse utile + où vérifier.\n"
            "5) INTERDIT « les sources fournies ne mentionnent pas… » comme seule réponse."
        ),
        "ar": (
            "أنت Sanad-Legal (جودة Mistral/Gemini). "
            "أجب بالعربية. "
            f"{structure_ar} "
            'JSON: "answer", "summary". '
            "مفتوح، مفيد، استشهد بـ [1][2]. ممنوع الاكتفاء بـ «المصادر لا تذكر»."
        ),
        "en": (
            "You are Sanad-Legal (Mistral/Gemini quality). "
            "Reply in English. "
            f"{structure_en} "
            'JSON: "answer", "summary". '
            "Open + useful. Sources enrich. Never answer only with 'sources do not mention'."
        ),
    }
    base = prompts[locale]
    if custom_prompt and custom_prompt.strip():
        extra = {
            "fr": f"\n\nInstructions personnalisées du cabinet :\n{custom_prompt.strip()}",
            "ar": f"\n\nتعليمات مخصصة للمكتب:\n{custom_prompt.strip()}",
            "en": f"\n\nCabinet custom instructions:\n{custom_prompt.strip()}",
        }[locale]
        return base + extra
    return base


def _flatten_answer_sections(answer: object) -> str:
    """Convertit answer dict (FR/AR keys) en Markdown propre."""
    if isinstance(answer, dict):
        parts: list[str] = []
        for key, val in answer.items():
            if not val:
                continue
            title = str(key).strip().replace("_", " ")
            body = str(val).strip()
            body = body.replace("\\n", "\n")
            if not body.startswith("#"):
                parts.append(f"## {title}\n\n{body}")
            else:
                parts.append(body)
        return "\n\n".join(parts).strip()
    text = str(answer or "").strip()
    text = text.replace("\\n", "\n")
    # Couper les fuites JSON arabes / françaises collées après la réponse
    text = re.sub(
        r'(?s)["\']?\s*,?\s*"(?:summary|الأساس القانوني|نقاط الانتباه|عملياً|'
        r'Fondement|Points d.attention|En pratique)"\s*:.*$',
        "",
        text,
    ).strip()
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```\s*$", "", text)
    text = re.sub(r'\{\s*"answer"\s*:', "", text, count=1)
    return text.strip().strip('"').strip()


def _clean_summary(summary: object) -> str:
    text = str(summary or "").strip().replace("\\n", "\n")
    if text.startswith("{") or '"الأساس' in text or '"Fondement' in text:
        return ""
    text = re.sub(r'(?s)["\']?\s*,?\s*"[^"]+"\s*:.*$', "", text).strip()
    if len(text) > 600:
        text = text[:600].rsplit(" ", 1)[0] + "…"
    return text.strip().strip('"')


def parse_chat_llm_response(raw: str | None) -> dict | None:
    """Parse Groq chat JSON; tolerate malformed responses."""
    if not raw or not raw.strip():
        return None

    data = parse_llm_json(raw)
    if data and (data.get("answer") is not None):
        answer = _flatten_answer_sections(data.get("answer"))
        summary = _clean_summary(data.get("summary", ""))
        if answer:
            return {"answer": answer, "summary": summary}

    text = raw.strip()
    wrapped = text if text.startswith("{") else "{" + text
    if not wrapped.endswith("}"):
        wrapped += "}"
    data = parse_llm_json(wrapped)
    if data and (data.get("answer") is not None):
        answer = _flatten_answer_sections(data.get("answer"))
        summary = _clean_summary(data.get("summary", ""))
        if answer:
            return {"answer": answer, "summary": summary}

    summary_m = re.search(
        r'"summary"\s*:\s*["\']?(.*?)["\']?\s*$', text, re.S | re.I
    )
    answer_m = re.search(
        r'"answer"\s*:\s*([\s\S]+?)(?="summary"\s*:|$)', text, re.I
    )
    if answer_m:
        answer = _flatten_answer_sections(answer_m.group(1).strip().strip('",'))
        summary = _clean_summary(summary_m.group(1) if summary_m else "")
        if answer:
            return {"answer": answer, "summary": summary}

    cleaned = _flatten_answer_sections(text)
    if len(cleaned) > 80 and not cleaned.lstrip().startswith("{"):
        return {"answer": cleaned, "summary": ""}
    return None


def strip_disclaimer_from_answer(answer: str, locale: SupportedLocale) -> str:
    """Remove disclaimer from answer body when shown separately in the UI."""
    disclaimer = get_disclaimer(locale)
    text = answer.strip()
    while disclaimer in text:
        text = text.replace(disclaimer, "").strip()
    return re.sub(r"\n{3,}", "\n\n", text).strip()
