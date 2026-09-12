"""Routeur multi free-tiers (Mistral → Groq → Gemini → DeepSeek → Together → SambaNova → Kimi → Ollama).

Objectif : éviter le « cerveau coupé » quand un seul provider est en 429.
Compatible OpenAI Chat Completions via httpx (sync, comme le reste de LexHub).
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class _Bucket:
    name: str
    base_url: str
    api_key: str
    model: str
    rpm: int = 20
    cooldown_until: float = 0.0
    recent_calls: list[float] = field(default_factory=list)
    fail_streak: int = 0

    def available(self) -> bool:
        if not self.api_key:
            return False
        now = time.time()
        if now < self.cooldown_until:
            return False
        self.recent_calls = [t for t in self.recent_calls if now - t < 60]
        return len(self.recent_calls) < self.rpm

    def mark_ok(self) -> None:
        self.recent_calls.append(time.time())
        self.fail_streak = 0

    def mark_fail(self, status_code: int | None = None) -> None:
        self.fail_streak += 1
        # 429 / quota → cooldown 2–5 min
        if status_code == 429 or self.fail_streak >= 2:
            wait = 180 if status_code == 429 else 120
            self.cooldown_until = time.time() + wait
            logger.warning("LLM provider %s cooling down %ss", self.name, wait)


def _providers() -> list[_Bucket]:
    """Ordre : débit / fiabilité pour un chat juridique FR/AR.

    OpenAI n'est pas dans la rotation free par défaut (coût) — on le priorise
    uniquement si preferred=\"openai\" (plans Pro+ / clé de barre).
    """
    return [
        _Bucket(
            name="mistral",
            base_url=(settings.MISTRAL_BASE_URL or "https://api.mistral.ai/v1").rstrip("/"),
            api_key=settings.MISTRAL_API_KEY,
            model=settings.MISTRAL_MODEL or "mistral-small-latest",
            rpm=20,
        ),
        _Bucket(
            name="groq",
            base_url="https://api.groq.com/openai/v1",
            api_key=settings.GROQ_API_KEY,
            model=settings.GROQ_MODEL or "llama-3.1-8b-instant",
            rpm=20,
        ),
        _Bucket(
            name="gemini",
            base_url="https://generativelanguage.googleapis.com/v1beta/openai",
            api_key=settings.GEMINI_API_KEY,
            model=settings.GEMINI_MODEL or "gemini-2.5-flash",
            rpm=15,
        ),
        _Bucket(
            name="deepseek",
            base_url="https://api.deepseek.com",
            api_key=settings.DEEPSEEK_API_KEY,
            model=settings.DEEPSEEK_MODEL or "deepseek-chat",
            rpm=30,
        ),
        _Bucket(
            name="together",
            base_url="https://api.together.xyz/v1",
            api_key=settings.TOGETHER_API_KEY,
            model=settings.TOGETHER_MODEL or "meta-llama/Llama-3.3-70B-Instruct-Turbo",
            rpm=40,
        ),
        _Bucket(
            name="sambanova",
            base_url="https://api.sambanova.ai/v1",
            api_key=settings.SAMBANOVA_API_KEY,
            model=settings.SAMBANOVA_MODEL or "Meta-Llama-3.3-70B-Instruct",
            rpm=30,
        ),
        _Bucket(
            name="kimi",
            base_url=settings.KIMI_BASE_URL.rstrip("/"),
            api_key=settings.KIMI_API_KEY,
            model=settings.KIMI_MODEL or "kimi-k2.6",
            rpm=10,
        ),
        _Bucket(
            name="openai",
            base_url=(settings.OPENAI_BASE_URL or "https://api.openai.com/v1").rstrip("/"),
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL or "gpt-4o-mini",
            rpm=60,
        ),
    ]


_STATE: dict[str, _Bucket] = {}


def _get_bucket(name: str, template: _Bucket) -> _Bucket:
    if name not in _STATE:
        _STATE[name] = template
    else:
        # Refresh keys/models from settings without losing cooldown
        b = _STATE[name]
        b.api_key = template.api_key
        b.base_url = template.base_url
        b.model = template.model
        b.rpm = template.rpm
    return _STATE[name]


def _openai_chat(
    bucket: _Bucket,
    system: str,
    prompt: str,
    max_tokens: int = 4096,
    temperature: float = 0.55,
    prior_messages: list[dict[str, str]] | None = None,
    model_override: str | None = None,
) -> str | None:
    url = f"{bucket.base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {bucket.api_key}",
        "Content-Type": "application/json",
    }
    messages: list[dict[str, str]] = [{"role": "system", "content": system}]
    if prior_messages:
        for m in prior_messages[-12:]:
            role = (m.get("role") or "").strip()
            content = (m.get("content") or "").strip()
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": prompt})
    payload = {
        "model": (model_override or bucket.model).strip() or bucket.model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    try:
        with httpx.Client(timeout=float(settings.LLM_HTTP_TIMEOUT_SEC or 30)) as client:
            r = client.post(url, headers=headers, json=payload)
        if r.status_code >= 400:
            bucket.mark_fail(r.status_code)
            logger.warning("%s failed HTTP %s: %s", bucket.name, r.status_code, r.text[:160])
            return None
        data = r.json()
        content = data["choices"][0]["message"]["content"]
        text = (content or "").strip()
        if text:
            bucket.mark_ok()
            return text
        bucket.mark_fail()
        return None
    except Exception as exc:
        bucket.mark_fail()
        logger.warning("%s exception: %s", bucket.name, exc)
        return None


def _call_ollama_local(
    system: str,
    prompt: str,
    *,
    max_tokens: int | None = None,
) -> str | None:
    try:
        predict = max(512, int(max_tokens or settings.OLLAMA_NUM_PREDICT or 512))
        with httpx.Client(timeout=min(float(settings.OLLAMA_CHAT_TIMEOUT or 90), 120.0)) as client:
            r = client.post(
                f"{settings.OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                    "stream": False,
                    "options": {
                        "temperature": 0.15,
                        "num_predict": predict,
                    },
                },
            )
        r.raise_for_status()
        return (r.json().get("message") or {}).get("content", "").strip() or None
    except Exception as exc:
        logger.warning("Ollama local fallback failed: %s", exc)
        return None


def chat_free_tier(
    prompt: str,
    system: str,
    preferred: str | None = None,
    *,
    allow_ollama: bool = True,
    local_only: bool = False,
    prior_messages: list[dict[str, str]] | None = None,
    max_tokens: int = 4096,
    temperature: float = 0.55,
    model_override: str | None = None,
    strict_preferred: bool = False,
) -> tuple[str | None, str]:
    """
    Essaie les providers free dans l'ordre.
    Retourne (texte, nom_provider).
    local_only=True → Ollama uniquement.
    strict_preferred=True → uniquement le provider demandé (pas de fallback faible).
    model_override → modèle ponctuel (ex. gpt-4o pour révision ChatGPT-like).
    Note: DICTATION_LOCAL_ONLY ne s'applique qu'au STT (Whisper), pas au polish LLM.
    """
    if local_only:
        text = _call_ollama_local(system, prompt, max_tokens=max_tokens)
        if text:
            return text, "ollama"
        return None, "none"

    preferred = (preferred or "auto").strip().lower()
    buckets = [_get_bucket(p.name, p) for p in _providers()]

    ordered: list[_Bucket] = []
    openai_bucket = next((b for b in buckets if b.name == "openai"), None)
    force_openai = bool(getattr(settings, "LLM_FORCE_OPENAI", True)) and bool(
        openai_bucket and openai_bucket.api_key
    )
    strict_openai = bool(getattr(settings, "LLM_OPENAI_STRICT", True))
    if force_openai:
        # LexHub : toute génération texte = ChatGPT si la clé est là
        preferred = "openai"
        if strict_openai:
            strict_preferred = True
            allow_ollama = False
    elif preferred in ("auto", "", "none") and openai_bucket and openai_bucket.api_key:
        preferred = "openai"
    if preferred in (
        "mistral",
        "groq",
        "gemini",
        "deepseek",
        "together",
        "sambanova",
        "kimi",
        "openai",
    ):
        ordered.extend([b for b in buckets if b.name == preferred])
        # Strict OpenAI : jamais de rotation free-tier
        if not strict_preferred and not (force_openai and strict_openai):
            # Ne pas faire basculer OpenAI dans la rotation free si non demandé
            rest = [b for b in buckets if b.name != preferred and b.name != "openai"]
            if preferred == "openai":
                ordered.extend(rest)
            else:
                ordered.extend(rest)
    else:
        if force_openai and openai_bucket:
            ordered = [openai_bucket]
        else:
            ordered = [b for b in buckets if b.name != "openai"]

    for bucket in ordered:
        if force_openai and strict_openai and bucket.name != "openai":
            continue
        if not bucket.available():
            continue
        text = _openai_chat(
            bucket,
            system,
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            prior_messages=prior_messages,
            model_override=model_override if bucket.name == "openai" else None,
        )
        if text:
            label = bucket.name
            if bucket.name == "openai" and model_override:
                label = f"openai:{model_override}"
            logger.info("LLM reply via %s", label)
            return text, label

    if allow_ollama and not strict_preferred:
        text = _call_ollama_local(system, prompt, max_tokens=max_tokens)
        if text:
            return text, "ollama"

    return None, "none"


def router_status() -> dict:
    """État des free tiers (pour /health)."""
    now = time.time()
    out = {}
    for p in _providers():
        b = _get_bucket(p.name, p)
        b.recent_calls = [t for t in b.recent_calls if now - t < 60]
        out[b.name] = {
            "configured": bool(b.api_key),
            "available": b.available(),
            "cooldown_sec": max(0, int(b.cooldown_until - now)),
            "rpm_used": len(b.recent_calls),
            "rpm_limit": b.rpm,
            "model": b.model,
        }
    out["ollama"] = {
        "configured": True,
        "base_url": settings.OLLAMA_BASE_URL,
        "model": settings.OLLAMA_MODEL,
    }
    return out
