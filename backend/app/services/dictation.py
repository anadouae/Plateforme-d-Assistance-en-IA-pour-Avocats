"""Dictée vocale → correction arabe → document officiel marocain."""

from __future__ import annotations

import logging
import re

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

POLISH_SYSTEM = """أنت مراجع لغوي قانوني مغربي متخصص في اللغة العربية الفصحى.
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
    """Corrige et ponctue une dictée arabe. Retourne (texte, provider)."""
    raw = (raw or "").strip()
    if not raw:
        return "", "none"
    raw = repair_arabic_stt(_collapse_repeats(raw))
    if len(raw) < 8:
        return raw, "passthrough"

    prompt = (
        "النص المُملى (أزل التكرار، أصلح حرف ة، صحّح ونقّط — بدون Markdown):\n\n"
        f"{raw}"
    )
    text, provider = chat_free_tier(prompt, POLISH_SYSTEM, preferred="mistral")
    if not text:
        logger.warning("Dictation polish LLM unavailable — returning cleaned raw")
        return raw, "none"
    return strip_markdown_noise(repair_arabic_stt(_strip_fences(text))), provider


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
) -> tuple[str, str, str, list[str]]:
    """
    Rédige le corps du document officiel.
    Retourne (title_ar, body_ar, provider, checks).
    """
    body = (body or "").strip()
    if not body:
        return "", "", "none", []

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
    text, provider = chat_free_tier(prompt, system, preferred="mistral")
    if not text:
        return hint_title, body, "none", []

    cleaned = strip_markdown_noise(_strip_fences(text))
    title_out, body_out, checks = _parse_compose_output(cleaned, hint_title)
    body_out = strip_markdown_noise(repair_arabic_stt(body_out))
    title_out = strip_markdown_noise(title_out)
    return title_out, body_out, provider, checks
