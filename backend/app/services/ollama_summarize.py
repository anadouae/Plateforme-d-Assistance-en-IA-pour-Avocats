"""Synthèse via Mistral — cloud rapide si clé dispo, sinon Ollama local."""

from __future__ import annotations

import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPTS = {
    "fr": (
        "Tu es un assistant juridique marocain. "
        "Résume le document de façon factuelle, UNIQUEMENT en français. "
        "N'invente rien. Structure Markdown claire :\n"
        "## Faits\n## Points clés\n## Risques\n"
        "Max 150 mots. Termine par : « Ceci ne constitue pas un avis juridique. »"
    ),
    "ar": (
        "أنت مساعد قانوني مغربي. "
        "لخّص الوثيقة بشكل واقعي ومنظّم، حصرياً باللغة العربية الفصحى. "
        "لا تختلق معلومات. استخدم Markdown بهذا الشكل:\n"
        "## الوقائع\n## النقاط الأساسية\n## المخاطر ونقاط الانتباه\n"
        "حد أقصى 150 كلمة. اختم بـ: «هذا لا يُعد استشارة قانونية.»"
    ),
    "en": (
        "You are a Moroccan legal assistant. "
        "Summarize the document factually, ONLY in English. "
        "Do not invent. Clear Markdown:\n"
        "## Facts\n## Key points\n## Risks\n"
        "Max 150 words. End with: “This does not constitute legal advice.”"
    ),
}

USER_PROMPTS = {
    "fr": "Résume ce document :\n\n",
    "ar": "لخّص هذه الوثيقة بالعربية المنظمة:\n\n",
    "en": "Summarize this document:\n\n",
}

MERGE_PROMPTS = {
    "fr": "Fusionne en un seul résumé court (max 120 mots), en français :\n\n",
    "ar": "ادمج في ملخص عربي واحد قصير ومنظم (حد أقصى 120 كلمة):\n\n",
    "en": "Merge into one short summary (max 120 words), in English:\n\n",
}


def _locale(language: str | None) -> str:
    lang = (language or "ar").strip().lower()[:2]
    return lang if lang in SYSTEM_PROMPTS else "ar"


def _ollama_model() -> str:
    return (settings.OLLAMA_SYNTHESIS_MODEL or settings.OLLAMA_MODEL or "mistral").strip()


def _base_url() -> str:
    return settings.OLLAMA_BASE_URL.rstrip("/")


def ollama_available(timeout: float = 3.0) -> bool:
    try:
        r = httpx.get(f"{_base_url()}/api/tags", timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False


def _summarize_mistral_cloud(text: str, language: str | None = None) -> str | None:
    if not settings.MISTRAL_API_KEY:
        return None
    locale = _locale(language)
    payload_text = (text or "").strip()[:8000]
    if len(payload_text) < 20:
        return None
    base = settings.MISTRAL_BASE_URL.rstrip("/")
    model = settings.MISTRAL_MODEL or "mistral-small-latest"
    try:
        with httpx.Client(timeout=60.0) as client:
            r = client.post(
                f"{base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.MISTRAL_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "temperature": 0.2,
                    "max_tokens": 512,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPTS[locale]},
                        {
                            "role": "user",
                            "content": f"{USER_PROMPTS[locale]}{payload_text}",
                        },
                    ],
                },
            )
            r.raise_for_status()
            content = r.json()["choices"][0]["message"]["content"]
            return (content or "").strip() or None
    except Exception as exc:
        logger.warning("Mistral cloud summarize failed: %s", exc)
        return None


def _summarize_ollama_local(
    text: str, max_chars: int = 3500, language: str | None = None
) -> str | None:
    locale = _locale(language)
    payload_text = (text or "").strip()[:max_chars]
    if len(payload_text) < 20:
        return None
    timeout = min(float(settings.OLLAMA_CHAT_TIMEOUT or 90), 90.0)
    body = {
        "model": _ollama_model(),
        "stream": False,
        "keep_alive": "10m",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPTS[locale]},
            {"role": "user", "content": f"{USER_PROMPTS[locale]}{payload_text}"},
        ],
        "options": {
            "temperature": 0.1,
            "num_predict": min(320, int(settings.OLLAMA_NUM_PREDICT or 320)),
            "num_ctx": 2048,
            "num_thread": 4,
        },
    }
    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.post(f"{_base_url()}/api/chat", json=body)
            r.raise_for_status()
            content = (r.json().get("message") or {}).get("content", "")
            return content.strip() or None
    except Exception as exc:
        logger.warning("Ollama local summarize failed (%s): %s", _ollama_model(), exc)
        return None


def summarize_text(
    text: str, max_chars: int = 8000, language: str | None = None
) -> tuple[str | None, str, str]:
    """Retourne (summary, provider, model). Cloud Mistral d'abord."""
    cleaned = (text or "").strip()[:max_chars]
    if len(cleaned) < 20:
        return None, "none", ""

    cloud = _summarize_mistral_cloud(cleaned, language=language)
    if cloud:
        return cloud, "mistral-cloud", settings.MISTRAL_MODEL or "mistral-small-latest"

    if ollama_available():
        local = _summarize_ollama_local(
            cleaned, max_chars=min(max_chars, 3500), language=language
        )
        if local:
            return local, "ollama", _ollama_model()

    return None, "none", ""


def summarize_long(
    text: str,
    chunk_size: int = 8000,
    max_chunks: int = 2,
    language: str | None = None,
) -> tuple[str | None, str, str]:
    cleaned = (text or "").strip()
    if len(cleaned) < 20:
        return None, "none", ""
    if len(cleaned) <= chunk_size:
        return summarize_text(cleaned, max_chars=chunk_size, language=language)

    locale = _locale(language)
    chunks = [cleaned[i : i + chunk_size] for i in range(0, len(cleaned), chunk_size)]
    partials: list[str] = []
    provider, model = "none", ""
    for chunk in chunks[:max_chunks]:
        part, prov, mod = summarize_text(chunk, max_chars=chunk_size, language=language)
        if part:
            partials.append(part)
            provider, model = prov, mod
    if not partials:
        return None, "none", ""
    if len(partials) == 1:
        return partials[0], provider, model
    return summarize_text(
        MERGE_PROMPTS[locale] + "\n\n---\n\n".join(partials),
        max_chars=8000,
        language=language,
    )


# compat anciens imports
def _model() -> str:
    return _ollama_model()
