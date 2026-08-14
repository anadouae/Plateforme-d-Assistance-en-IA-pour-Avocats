"""Notes / résumé de chunks pour synthèse intelligente (map-reduce)."""

from __future__ import annotations

import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# Phase map : notes denses (pas un résumé figé de 150 mots)
SYSTEM_PROMPTS = {
    "fr": (
        "Tu es un analyste juridique de cabinet. "
        "Pour CE MORCEAU de document, extrais des NOTES UTILES et fidèles "
        "(faits, parties, dates, montants, demandes, décisions, risques, obligations). "
        "Markdown court, puces. N'invente rien. "
        "Si le morceau est peu informatif, dis-le en une ligne. "
        "UNIQUEMENT en français. Pas de disclaimer."
    ),
    "ar": (
        "أنت محلل قانوني. من هذا الجزء من الوثيقة، استخرج ملاحظات مفيدة ودقيقة "
        "(وقائع، أطراف، تواريخ، مبالغ، طلبات، قرارات، مخاطر، التزامات). "
        "Markdown مختصر. لا تختلق. بالعربية فقط."
    ),
    "en": (
        "You are a legal analyst. From THIS chunk, extract faithful useful notes "
        "(facts, parties, dates, amounts, claims, decisions, risks). "
        "Short Markdown bullets. Do not invent. English only."
    ),
}

USER_PROMPTS = {
    "fr": "Notes juridiques utiles pour ce morceau :\n\n",
    "ar": "ملاحظات قانونية مفيدة لهذا الجزء:\n\n",
    "en": "Useful legal notes for this chunk:\n\n",
}

MERGE_PROMPTS = {
    "fr": (
        "Fusionne ces notes de morceaux en un dossier de notes cohérent "
        "(sans doublons, sans invention), Markdown structuré :\n\n"
    ),
    "ar": "ادمج هذه الملاحظات في ملف ملاحظات متسق دون تكرار ودون اختلاق:\n\n",
    "en": "Merge these chunk notes into one coherent note file without invention:\n\n",
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
    payload_text = (text or "").strip()[:10000]
    if len(payload_text) < 20:
        return None
    base = settings.MISTRAL_BASE_URL.rstrip("/")
    model = settings.MISTRAL_MODEL or "mistral-medium-latest"
    try:
        with httpx.Client(timeout=float(settings.LLM_HTTP_TIMEOUT_SEC or 45)) as client:
            r = client.post(
                f"{base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.MISTRAL_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "temperature": 0.25,
                    "max_tokens": 1200,
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
    text: str, max_chars: int = 4500, language: str | None = None
) -> str | None:
    locale = _locale(language)
    payload_text = (text or "").strip()[:max_chars]
    if len(payload_text) < 20:
        return None
    timeout = min(float(settings.OLLAMA_CHAT_TIMEOUT or 120), 120.0)
    body = {
        "model": _ollama_model(),
        "stream": False,
        "keep_alive": "10m",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPTS[locale]},
            {"role": "user", "content": f"{USER_PROMPTS[locale]}{payload_text}"},
        ],
        "options": {
            "temperature": 0.2,
            "num_predict": max(512, min(900, int(settings.OLLAMA_NUM_PREDICT or 512))),
            "num_ctx": 4096,
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
    text: str, max_chars: int = 10000, language: str | None = None
) -> tuple[str | None, str, str]:
    """Retourne (notes, provider, model). Cloud Mistral d'abord."""
    cleaned = (text or "").strip()[:max_chars]
    if len(cleaned) < 20:
        return None, "none", ""

    cloud = _summarize_mistral_cloud(cleaned, language=language)
    if cloud:
        return cloud, "mistral-cloud", settings.MISTRAL_MODEL or "mistral-medium-latest"

    if ollama_available():
        local = _summarize_ollama_local(
            cleaned, max_chars=min(max_chars, 4500), language=language
        )
        if local:
            return local, "ollama", _ollama_model()

    return None, "none", ""


def summarize_long(
    text: str,
    chunk_size: int = 7000,
    max_chunks: int = 6,
    language: str | None = None,
) -> tuple[str | None, str, str]:
    """Map-reduce : notes par morceau → notes fusionnées (pour synthèse finale)."""
    cleaned = (text or "").strip()
    if len(cleaned) < 20:
        return None, "none", ""
    if len(cleaned) <= chunk_size:
        return summarize_text(cleaned, max_chars=chunk_size, language=language)

    locale = _locale(language)
    chunks = [cleaned[i : i + chunk_size] for i in range(0, len(cleaned), chunk_size)]
    # Priorise début + fin (souvent en-tête / dispositif) + milieu
    if len(chunks) > max_chunks:
        head_n = max(2, max_chunks // 2)
        tail_n = max(1, max_chunks - head_n - 1)
        mid_idx = len(chunks) // 2
        selected = chunks[:head_n]
        if 0 < mid_idx < len(chunks) - 1 and chunks[mid_idx] not in selected:
            selected.append(chunks[mid_idx])
        selected.extend(chunks[-tail_n:])
        # dédoublonnage en gardant l'ordre
        seen: set[int] = set()
        ordered: list[str] = []
        for c in selected:
            h = hash(c[:80])
            if h in seen:
                continue
            seen.add(h)
            ordered.append(c)
        chunks = ordered[:max_chunks]

    partials: list[str] = []
    provider, model = "none", ""
    for chunk in chunks:
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
        max_chars=12000,
        language=language,
    )


def _model() -> str:
    return _ollama_model()
