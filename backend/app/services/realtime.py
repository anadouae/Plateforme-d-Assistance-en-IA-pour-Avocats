"""Pub/sub temps réel cabinet — Redis + WebSocket FastAPI."""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def _channel(cabinet_id: str) -> str:
    return f"lexhub:cabinet:{cabinet_id}"


def publish_cabinet_event(cabinet_id: str, event: str, payload: dict[str, Any] | None = None) -> None:
    """Publie un événement pour tous les onglets/navigateurs du cabinet."""
    if not cabinet_id:
        return
    try:
        import redis

        from app.core.config import settings

        r = redis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=1.5)
        msg = json.dumps({"event": event, "payload": payload or {}}, default=str)
        r.publish(_channel(cabinet_id), msg)
    except Exception as exc:
        logger.debug("realtime publish skipped: %s", exc)


async def subscribe_cabinet(cabinet_id: str):
    """Async generator d’événements Redis pour un cabinet."""
    import asyncio

    import redis.asyncio as aioredis

    from app.core.config import settings

    client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    pubsub = client.pubsub()
    await pubsub.subscribe(_channel(cabinet_id))
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message.get("type") == "message":
                data = message.get("data")
                if isinstance(data, str):
                    yield data
            else:
                await asyncio.sleep(0.05)
    finally:
        try:
            await pubsub.unsubscribe(_channel(cabinet_id))
            await pubsub.close()
            await client.close()
        except Exception:
            pass
