"""Vérification Cloudflare Turnstile (optionnelle si non configurée)."""

from __future__ import annotations

import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


async def verify_turnstile(token: str | None, remote_ip: str | None = None) -> bool:
    """True si captcha OK, ou si Turnstile n'est pas configuré (dev)."""
    if not settings.TURNSTILE_SECRET_KEY:
        return True
    if not token:
        return False
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(
                "https://challenges.cloudflare.com/turnstile/v0/siteverify",
                data={
                    "secret": settings.TURNSTILE_SECRET_KEY,
                    "response": token,
                    **({"remoteip": remote_ip} if remote_ip else {}),
                },
            )
            data = resp.json()
            return bool(data.get("success"))
    except Exception as exc:
        logger.warning("Turnstile verify failed: %s", exc)
        return False
