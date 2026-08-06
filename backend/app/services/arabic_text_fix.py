"""Post-traitement STT arabe (Whisper / Chrome) — lettre ة, nettoyage Markdown."""

from __future__ import annotations

import re

# Mots juridiques / courants où la finale est ة (pas ه)
_TEH_MARBUTA_WORDS = {
    "محكمه": "محكمة",
    "مرافعه": "مرافعة",
    "جلسه": "جلسة",
    "دعوه": "دعوى",
    "قضيـه": "قضية",
    "قضيه": "قضية",
    "نفقه": "نفقة",
    "حضانه": "حضانة",
    "شركه": "شركة",
    "هيئه": "هيئة",
    "مذكره": "مذكرة",
    "مسطره": "مسطرة",
    "وقايع": "وقائع",
    "مناقشه": "مناقشة",
    "ملتمسات": "ملتمسات",
    "ابتدائيه": "ابتدائية",
    "استئنافيه": "استئنافية",
    "تجاريه": "تجارية",
    "اداريه": "إدارية",
    "إداريه": "إدارية",
    "مدنيه": "مدنية",
    "زجريه": "زجرية",
    "عائليه": "عائلية",
    "اجريه": "أجيرة",
    "أجيره": "أجيرة",
    "مدعيه": "مدعية",
    "مدعى عليها": "مدعى عليها",
    "المدعیه": "المدعية",
    "المدعيه": "المدعية",
    "الظنينه": "الظنينة",
    "الظنينه": "الظنينة",
    "العارضه": "العارضة",
    "المستأنفه": "المستأنفة",
    "المستأنفه": "المستأنفة",
}


def repair_arabic_stt(text: str) -> str:
    """Corrige artefacts fréquents de la dictée arabe (ة manquante, espaces)."""
    t = (text or "").strip()
    if not t:
        return ""
    t = re.sub(r"\s+", " ", t)
    # Remplacements lexicaux (ه finale → ة)
    for wrong, right in _TEH_MARBUTA_WORDS.items():
        t = re.sub(rf"(?<!\w){re.escape(wrong)}(?!\w)", right, t)
    # Patterns génériques courants en fin de mot juridique : ه → ة
    # (uniquement si le mot se termine par ه précédé d'une lettre arabe)
    def _teh(m: re.Match[str]) -> str:
        word = m.group(1)
        if word in {"فيه", "عليه", "إليه", "منه", "عنه", "له", "به", "هذه", "تلك"}:
            return word
        if len(word) >= 4 and word.endswith("ه"):
            return word[:-1] + "ة"
        return word

    t = re.sub(r"(?<![\u0600-\u06FF])([\u0600-\u06FF]{3,}ه)(?![\u0600-\u06FF])", _teh, t)
    return t.strip()


def strip_markdown_noise(text: str) -> str:
    """Enlève **, *, #, puces markdown aléatoires du corps de document."""
    t = text or ""
    t = re.sub(r"^```(?:\w+)?\s*", "", t.strip())
    t = re.sub(r"\s*```$", "", t)
    # Gras / italique markdown
    t = re.sub(r"\*\*(.+?)\*\*", r"\1", t)
    t = re.sub(r"__(.+?)__", r"\1", t)
    t = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"\1", t)
    # Titres markdown
    t = re.sub(r"(?m)^\s{0,3}#{1,6}\s+", "", t)
    # Puces markdown en début de ligne → tiret simple
    t = re.sub(r"(?m)^\s*[-*•]\s+", "— ", t)
    # Étoiles isolées restantes
    t = re.sub(r"(?<!\S)\*{1,3}(?!\S)", "", t)
    t = re.sub(r"[ \t]+\n", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()
