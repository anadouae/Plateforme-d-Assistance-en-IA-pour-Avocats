"""Rate limiting Redis (avec fallback mémoire si Redis indisponible)."""

from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, Request, status

from app.core.config import settings

logger = logging.getLogger(__name__)

_lock = Lock()
_buckets: dict[str, deque[float]] = defaultdict(deque)
_redis = None
_redis_failed = False


def _get_redis():
    global _redis, _redis_failed
    if _redis_failed:
        return None
    if _redis is not None:
        return _redis
    try:
        import redis

        client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        client.ping()
        _redis = client
        return _redis
    except Exception as exc:
        logger.warning("Redis rate-limit unavailable, using memory: %s", exc)
        _redis_failed = True
        return None


def _raise_429(bucket_key: str, limit: int, window_sec: int) -> None:
    logger.warning(
        "Rate limit exceeded",
        extra={
            "endpoint": bucket_key,
            "status_code": 429,
            "task": "rate_limit",
        },
    )
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Trop de requêtes. Réessayez dans quelques instants.",
        headers={"Retry-After": str(window_sec)},
    )


def _check_memory(bucket_key: str, limit: int, window_sec: int) -> None:
    now = time.monotonic()
    cutoff = now - window_sec
    with _lock:
        q = _buckets[bucket_key]
        while q and q[0] < cutoff:
            q.popleft()
        if len(q) >= limit:
            _raise_429(bucket_key, limit, window_sec)
        q.append(now)


def _check_redis(bucket_key: str, limit: int, window_sec: int) -> bool:
    """True si limité via Redis ; False pour fallback mémoire."""
    client = _get_redis()
    if client is None:
        return False
    try:
        key = f"rl:{bucket_key}"
        pipe = client.pipeline()
        now = time.time()
        pipe.zremrangebyscore(key, 0, now - window_sec)
        pipe.zadd(key, {f"{now}:{time.time_ns()}": now})
        pipe.zcard(key)
        pipe.expire(key, window_sec + 1)
        results = pipe.execute()
        count = int(results[2])
        if count > limit:
            _raise_429(bucket_key, limit, window_sec)
        return True
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Redis rate-limit error, fallback memory: %s", exc)
        return False


def _effective_limit(limit: int) -> int:
    """En local/Docker, toutes les requêtes partagent souvent la même IP."""
    env = (settings.ENVIRONMENT or "").lower()
    if settings.DEBUG or env in {"development", "dev", "local"}:
        return max(limit * 8, 80)
    return limit


def _client_ip(request: Request) -> str:
    ip = request.client.host if request.client else "unknown"
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        ip = forwarded.split(",")[0].strip() or ip
    return ip


def check_rate_limit(
    request: Request,
    *,
    key: str,
    limit: int,
    window_sec: int = 60,
    subject: str | None = None,
) -> None:
    """
    Lève 429 si trop de requêtes pour (IP[, subject], key) dans la fenêtre.
    `subject` = user_id pour limiter par compte (uploads).
    """
    limit = _effective_limit(limit)
    ip = _client_ip(request)
    bucket_key = f"{key}:{ip}"
    if subject:
        bucket_key = f"{key}:u:{subject}:{ip}"
    if not _check_redis(bucket_key, limit, window_sec):
        _check_memory(bucket_key, limit, window_sec)


def count_failures(request: Request, *, key: str, window_sec: int = 900) -> int:
    """Nombre d'échecs récents (IP) — pour déclencher CAPTCHA."""
    ip = _client_ip(request)
    bucket_key = f"{key}:{ip}"
    client = _get_redis()
    if client is not None:
        try:
            redis_key = f"rl:{bucket_key}"
            now = time.time()
            client.zremrangebyscore(redis_key, 0, now - window_sec)
            return int(client.zcard(redis_key))
        except Exception:
            pass
    now = time.monotonic()
    cutoff = now - window_sec
    with _lock:
        q = _buckets[bucket_key]
        while q and q[0] < cutoff:
            q.popleft()
        return len(q)


def record_failure(request: Request, *, key: str, window_sec: int = 900) -> int:
    """Enregistre un échec et retourne le total dans la fenêtre."""
    ip = _client_ip(request)
    bucket_key = f"{key}:{ip}"
    client = _get_redis()
    if client is not None:
        try:
            redis_key = f"rl:{bucket_key}"
            now = time.time()
            pipe = client.pipeline()
            pipe.zremrangebyscore(redis_key, 0, now - window_sec)
            pipe.zadd(redis_key, {f"{now}:{time.time_ns()}": now})
            pipe.zcard(redis_key)
            pipe.expire(redis_key, window_sec + 1)
            results = pipe.execute()
            return int(results[2])
        except Exception:
            pass
    _check_memory(bucket_key, limit=10_000, window_sec=window_sec)
    return count_failures(request, key=key, window_sec=window_sec)
