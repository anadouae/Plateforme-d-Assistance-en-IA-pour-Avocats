"""Have I Been Pwned — API k-anonymity (range)."""

from __future__ import annotations

import hashlib
import logging

import httpx

logger = logging.getLogger(__name__)


async def is_password_breached(password: str) -> bool:
    """True si le mot de passe apparaît dans des fuites connues."""
    digest = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
    prefix, suffix = digest[:5], digest[5:]
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            resp = await client.get(
                f"https://api.pwnedpasswords.com/range/{prefix}",
                headers={"Add-Padding": "true", "User-Agent": "Sanad-Security"},
            )
            if resp.status_code != 200:
                logger.warning("HIBP status %s — skip check", resp.status_code)
                return False
            for line in resp.text.splitlines():
                parts = line.split(":")
                if parts and parts[0].strip().upper() == suffix:
                    return True
    except Exception as exc:
        logger.warning("HIBP check failed: %s", exc)
        return False
    return False
