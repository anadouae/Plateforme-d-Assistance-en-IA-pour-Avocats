import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


async def verify_google_id_token(id_token: str) -> dict | None:
    """Verify Google ID token and return user info."""
    if not settings.GOOGLE_CLIENT_ID:
        return None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"id_token": id_token},
            )
            if res.status_code != 200:
                return None
            data = res.json()
            if data.get("aud") != settings.GOOGLE_CLIENT_ID:
                return None
            if not data.get("email_verified", "false") in (True, "true"):
                return None
            return {
                "google_id": data["sub"],
                "email": data["email"].lower(),
                "full_name": data.get("name", data["email"].split("@")[0]),
            }
    except Exception as exc:
        logger.warning("Google token verification failed: %s", exc)
        return None
