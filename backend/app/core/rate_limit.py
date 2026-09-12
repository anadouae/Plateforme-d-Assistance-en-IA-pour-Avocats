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
    """IP client — en prod derrière Caddy, prendre le DERNIER hop XFF de confiance, pas le spoofable premier."""
    direct = request.client.host if request.client else "unknown"
    env = (settings.ENVIRONMENT or "").lower()
    forwarded = request.headers.get("x-forwarded-for")
    if not forwarded:
        return direct
    parts = [p.strip() for p in forwarded.split(",") if p.strip()]
    if not parts:
        return direct
    # Dev : premier hop OK. Prod : dernier hop (ajouté par le reverse-proxy de confiance).
    if env in {"production", "prod"}:
        return parts[-1]
    return parts[0]


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


def check_named_rate_limit(
    *,
    name: str,
    limit: int,
    window_sec: int = 60,
) -> None:
    """Rate-limit sur une clé nommée (ex. code d'invitation), indépendante de l'IP."""
    limit = _effective_limit(limit)
    bucket_key = f"named:{name}"
    if not _check_redis(bucket_key, limit, window_sec):
        _check_memory(bucket_key, limit, window_sec)


def get_cabinet_ai_daily_used(cabinet_id: str) -> int:
    """Crédits IA déjà consommés aujourd’hui (UTC) — lecture seule."""
    from datetime import datetime, timezone

    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    key = f"ai:day:{cabinet_id}:{day}"
    client = _get_redis()
    if client is not None:
        try:
            return int(client.get(key) or 0)
        except Exception:
            return 0
    with _lock:
        bucket = _buckets.get(f"daily:{key}")
        if not bucket:
            return 0
        now = time.time()
        while bucket and now - bucket[0] > 86400:
            bucket.popleft()
        return len(bucket)


def check_cabinet_ai_daily(
    cabinet_id: str,
    cost: int,
    daily_cap: int,
    *,
    acknowledge_overage: bool = False,
) -> None:
    """
    Incrémente le compteur journalier.
    Au-delà du plafond : 429 structuré DAILY_CAP_CHOICE (choix client),
    sauf si acknowledge_overage=True → on laisse continuer (crédits mois restent).
    """
    if daily_cap < 0 or cost <= 0:
        return
    from datetime import datetime, timezone

    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    key = f"ai:day:{cabinet_id}:{day}"

    def _choice_exc(used_now: int) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "DAILY_CAP_CHOICE",
                "message": (
                    "Vous avez beaucoup utilisé l’IA aujourd’hui "
                    f"({daily_cap} crédits indicatifs / jour). "
                    "Ce n’est pas un problème de paiement. "
                    "Choisissez : attendre demain, ou continuer "
                    "(les crédits du mois seront débités)."
                ),
                "daily_limit": int(daily_cap),
                "daily_used": int(max(0, used_now)),
                "choices": ["wait_tomorrow", "continue"],
            },
            headers={"Retry-After": "60"},
        )

    client = _get_redis()
    if client is not None:
        try:
            pipe = client.pipeline()
            pipe.incrby(key, cost)
            pipe.expire(key, 36 * 3600)
            used = int(pipe.execute()[0])
            if used > daily_cap and not acknowledge_overage:
                client.decrby(key, cost)
                raise _choice_exc(used - cost)
            return
        except HTTPException:
            raise
        except Exception as exc:
            logger.warning("daily AI cap redis failed: %s", exc)

    used_now = get_cabinet_ai_daily_used(cabinet_id)
    if used_now + cost > daily_cap and not acknowledge_overage:
        raise _choice_exc(used_now)

    bucket_key = f"daily:{key}"
    with _lock:
        bucket = _buckets.setdefault(bucket_key, deque())
        now = time.time()
        while bucket and now - bucket[0] > 86400:
            bucket.popleft()
        for _ in range(max(1, min(cost, 20))):
            bucket.append(now)


def acquire_cabinet_ai_slot(cabinet_id: str, slots: int, *, ttl_sec: int = 180) -> str:
    """Réserve un slot concurrent. Retourne token à liberer. 429 si saturé."""
    import uuid as _uuid

    token = str(_uuid.uuid4())
    client = _get_redis()
    if client is None or slots < 1:
        return token
    try:
        key = f"ai:slots:{cabinet_id}"
        now = time.time()
        client.zremrangebyscore(key, 0, now - ttl_sec)
        n = int(client.zcard(key) or 0)
        if n >= slots:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    "Trop de traitements IA en parallèle pour ce cabinet. "
                    "Attendez la fin d'une rédaction / analyse."
                ),
                headers={"Retry-After": "30"},
            )
        client.zadd(key, {token: now})
        client.expire(key, ttl_sec + 5)
        return token
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("AI slot acquire failed: %s", exc)
        return token


def release_cabinet_ai_slot(cabinet_id: str, token: str | None) -> None:
    if not token:
        return
    client = _get_redis()
    if client is None:
        return
    try:
        client.zrem(f"ai:slots:{cabinet_id}", token)
    except Exception:
        pass


def refund_cabinet_ai_daily(cabinet_id: str, cost: int) -> None:
    if cost <= 0:
        return
    from datetime import datetime, timezone

    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    key = f"ai:day:{cabinet_id}:{day}"
    client = _get_redis()
    if client is None:
        return
    try:
        client.decrby(key, cost)
    except Exception:
        pass


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
