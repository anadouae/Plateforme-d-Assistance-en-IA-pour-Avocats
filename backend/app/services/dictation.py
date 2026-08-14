"""Dictée vocale → correction (AR/FR) → document officiel marocain."""

from __future__ import annotations

import logging
import re

from app.core.config import settings
from app.services.arabic_text_fix import repair_arabic_stt, strip_markdown_noise
from app.services.free_llm_router import chat_free_tier
from app.services.plaidoirie_prompt import (
    PLAIDOIRIE_TYPES,
    build_plaidoirie_system,
    compose_fallback_system,
)

logger = logging.getLogger(__name__)

DOC_TYPES = {
    "plaidoirie": "مرافعة (Plaidoirie)",
    "general": "وثيقة قانونية عامة",
    "petition": "مقال افتتاحي / عريضة",
    "memo": "مذكرة دفاع",
    "letter": "رسالة رسمية",
    "minutes": "عرض حال / محضر",
}

DOC_TYPES_FR = {
    "plaidoirie": "Plaidoirie",
    "general": "Document juridique",
    "petition": "Requête / assignation",
    "memo": "Mémoire en défense",
    "letter": "Courrier officiel",
    "minutes": "Procès-verbal",
}

POLISH_SYSTEM_AR = """أنت مراجع لغوي قانوني مغربي متخصص في اللغة العربية الفصحى.
مهمتك: تحويل نص مُملى شفهيًا (أخطاء تعرف صوتي، دارجة، تكرار، غياب ترقيم، حرف ة المكتوب ه خطأً)
إلى نص عربي فصيح، واضح، مهني.

قواعد صارمة:
1. احذف التكرارات واحتفظ بالمعنى مرة واحدة.
2. صحّح الإملاء — خاصة التاء المربوطة (ة) لا الهاء (ه) في نهايات مثل: محكمة، مرافعة، جلسة، نفقة، شركة، مذكرة.
3. أضف علامات الترقيم العربية.
4. نظّم الفقرات (سطر فارغ بينها).
5. حوّل الدارجة الواضحة إلى فصحى قانونية دون تغيير المعنى.
6. لا تختلق وقائعًا ولا أرقامًا ولا فصول قانون. إن غاب شيء: [À VÉRIFIER : ...].
7. أعد النص المصحح فقط — ممنوع Markdown، ممنوع **نجمات**، ممنوع # عناوين، ممنوع شرح.
8. إن كان النص فارغًا بلا معنى: جملة واحدة تطلب إعادة الإملاء."""

POLISH_SYSTEM_FR = """Tu es un réviseur juridique marocain, expert en français professionnel.
Ta mission : transformer un texte dicté oralement (erreurs STT, répétitions, ponctuation absente)
en français juridique clair et soigné.

Règles strictes :
1. Supprime les répétitions, garde le sens une seule fois.
2. Corrige orthographe et grammaire.
3. Ajoute la ponctuation française.
4. Structure en paragraphes (ligne vide entre eux).
5. Style professionnel de barreau, sans changer le fond.
6. N'invente jamais de faits, montants ou articles de loi. Si manque : [À VÉRIFIER : ...].
7. Renvoie UNIQUEMENT le texte corrigé — pas de Markdown, pas d'explication.
8. Si le texte est vide / sans sens : une seule phrase demandant de redicter."""

COMPOSE_SYSTEM_FR = """Tu es un assistant de rédaction juridique marocain (français).
À partir du texte source, produis un document structuré pour le tribunal.

Format de sortie OBLIGATOIRE :
TITLE: <titre court>
BODY:
<corps structuré avec points numérotés si pertinent>
CHECKS:
- <points à vérifier, ou « aucun »>
"""


def _normalize_lang(language: str | None) -> str:
    lang = (language or "ar").strip().lower()
    if lang.startswith("fr"):
        return "fr"
    return "ar"


def _local_only() -> bool:
    return bool(getattr(settings, "DICTATION_LOCAL_ONLY", False))


def _llm(prompt: str, system: str, preferred: str = "mistral") -> tuple[str | None, str]:
    return chat_free_tier(
        prompt,
        system,
        preferred=preferred,
        local_only=_local_only(),
    )


def _strip_fences(text: str) -> str:
    return strip_markdown_noise(text or "")


def _collapse_repeats(text: str) -> str:
    """Réduit les phrases répétées en boucle (artefact Web Speech)."""
    t = re.sub(r"\s+", " ", text).strip()
    parts = re.split(r"(?<=[.。؟!?])\s+", t)
    out: list[str] = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if p in out[-4:]:
            continue
        out.append(p)
    t = " ".join(out)
    for _ in range(5):
        nxt = re.sub(r"(.{20,}?)(?:\s+\1){1,}", r"\1", t)
        if nxt == t:
            break
        t = nxt
    return t.strip()


def polish_arabic_dictation(raw: str) -> tuple[str, str]:
    """Rétrocompat : polish arabe."""
    return polish_dictation(raw, language="ar")


def polish_dictation(raw: str, language: str = "ar") -> tuple[str, str]:
    """Corrige et ponctue une dictée AR ou FR. Retourne (texte, provider)."""
    lang = _normalize_lang(language)
    raw = (raw or "").strip()
    if not raw:
        return "", "none"
    raw = _collapse_repeats(raw)
    if lang == "ar":
        raw = repair_arabic_stt(raw)
    if len(raw) < 8:
        return raw, "passthrough"

    if lang == "fr":
        system = POLISH_SYSTEM_FR
        prompt = (
            "Texte dicté (supprime répétitions, corrige, ponctue — sans Markdown) :\n\n"
            f"{raw}"
        )
    else:
        system = POLISH_SYSTEM_AR
        prompt = (
            "النص المُملى (أزل التكرار، أصلح حرف ة، صحّح ونقّط — بدون Markdown):\n\n"
            f"{raw}"
        )

    text, provider = _llm(prompt, system)
    if not text:
        logger.warning("Dictation polish LLM unavailable — returning cleaned raw")
        return raw, "none"
    cleaned = strip_markdown_noise(_strip_fences(text))
    if lang == "ar":
        cleaned = repair_arabic_stt(cleaned)
    return cleaned, provider


def _parse_compose_output(cleaned: str, hint_title: str) -> tuple[str, str, list[str]]:
    title_out = hint_title
    body_out = cleaned
    checks: list[str] = []

    if "TITLE:" in cleaned and "BODY:" in cleaned:
        try:
            after_title = cleaned.split("TITLE:", 1)[1]
            if "BODY:" in after_title:
                title_part, rest = after_title.split("BODY:", 1)
                title_out = title_part.strip().splitlines()[0].strip() or hint_title
                if "CHECKS:" in rest:
                    body_part, checks_part = rest.split("CHECKS:", 1)
                    body_out = body_part.strip()
                    for line in checks_part.strip().splitlines():
                        item = line.strip().lstrip("-•*").strip()
                        if item and item not in {"لا شيء", "aucun", "none", "—"}:
                            checks.append(item)
                else:
                    body_out = rest.strip()
        except Exception:
            body_out = cleaned
    return title_out, body_out, checks


def compose_official_document(
    body: str,
    *,
    doc_type: str = "plaidoirie",
    title: str | None = None,
    city: str | None = None,
    cabinet_name: str | None = None,
    plaidoirie_type: str | None = None,
    language: str = "ar",
) -> tuple[str, str, str, list[str]]:
    """
    Rédige le corps du document officiel.
    Retourne (title, body, provider, checks).
    """
    lang = _normalize_lang(language)
    body = (body or "").strip()
    if not body:
        return "", "", "none", []

    if lang == "fr":
        kind = DOC_TYPES_FR.get(doc_type, DOC_TYPES_FR["general"])
        hint_title = title.strip() if title else kind
        extras = []
        if city:
            extras.append(f"Ville proposée : {city}")
        if cabinet_name:
            extras.append(f"Cabinet : {cabinet_name}")
        system = COMPOSE_SYSTEM_FR
        prompt = (
            f"Type de document : {kind}\n"
            f"Titre suggéré : {hint_title}\n"
            + ("\n".join(extras) + "\n" if extras else "")
            + "\nTexte source :\n\n"
            f"{body}\n\n"
            "Réponds au format TITLE / BODY / CHECKS."
        )
        text, provider = _llm(prompt, system)
        if not text:
            return hint_title, body, "none", []
        cleaned = strip_markdown_noise(_strip_fences(text))
        title_out, body_out, checks = _parse_compose_output(cleaned, hint_title)
        return strip_markdown_noise(title_out), strip_markdown_noise(body_out), provider, checks

    kind = DOC_TYPES.get(doc_type, DOC_TYPES["general"])
    hint_title = title.strip() if title else kind
    extras = []
    if city:
        extras.append(f"المدينة المقترحة للتذييل: {city}")
    if cabinet_name:
        extras.append(f"اسم المكتب: {cabinet_name}")

    type_id = (plaidoirie_type or "").strip()
    if doc_type == "plaidoirie":
        if type_id not in PLAIDOIRIE_TYPES:
            type_id = "civil-general"
        system = build_plaidoirie_system(type_id)
        type_line = f"نوع المرافعة المفروض: {PLAIDOIRIE_TYPES[type_id]} (id={type_id})\n"
    else:
        system = compose_fallback_system()
        type_line = f"نوع الوثيقة: {kind}\n"

    prompt = (
        type_line
        + f"عنوان مقترح: {hint_title}\n"
        + ("\n".join(extras) + "\n" if extras else "")
        + "\nالنص المصدر (بعد التصحيح أو النموذج):\n\n"
        f"{body}\n\n"
        "أرجع النتيجة بالشكل المطلوب (TITLE / BODY / CHECKS)."
    )
    text, provider = _llm(prompt, system)
    if not text:
        return hint_title, body, "none", []

    cleaned = strip_markdown_noise(_strip_fences(text))
    title_out, body_out, checks = _parse_compose_output(cleaned, hint_title)
    body_out = strip_markdown_noise(repair_arabic_stt(body_out))
    title_out = strip_markdown_noise(title_out)
    return title_out, body_out, provider, checks
