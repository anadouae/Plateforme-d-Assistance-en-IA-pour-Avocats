from pathlib import Path

path = Path(r"C:\Users\daurinia\Desktop\Avocat-AI-Assistance\backend\app\core\rate_limit.py")
text = path.read_text(encoding="utf-8")
needle = '''def count_failures(request: Request, *, key: str, window_sec: int = 900) -> int:
    """Nombre d'échecs récents (IP) — pour déclencher CAPTCHA."""
'''
insert = '''def check_cabinet_ai_daily(cabinet_id: str, cost: int, daily_cap: int) -> None:
    """Incrémente le compteur journalier Redis ; 429 si dépassement soft-cap."""
    if daily_cap < 0 or cost <= 0:
        return
    from datetime import datetime, timezone

    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    key = f"ai:day:{cabinet_id}:{day}"
    client = _get_redis()
    if client is not None:
        try:
            pipe = client.pipeline()
            pipe.incrby(key, cost)
            pipe.expire(key, 36 * 3600)
            used = int(pipe.execute()[0])
            if used > daily_cap:
                client.decrby(key, cost)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=(
                        f"Plafond IA journalier atteint ({daily_cap} crédits/jour). "
                        "Réessayez demain ou passez à un plan supérieur."
                    ),
                    headers={"Retry-After": "3600"},
                )
            return
        except HTTPException:
            raise
        except Exception as exc:
            logger.warning("daily AI cap redis failed: %s", exc)
    bucket_key = f"daily:{key}"
    for _ in range(max(1, min(cost, 20))):
        _check_memory(bucket_key, limit=max(daily_cap, 1), window_sec=86400)


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


'''
if "check_cabinet_ai_daily" not in text:
    if needle not in text:
        raise SystemExit("needle missing")
    text = text.replace(needle, insert + needle, 1)
    path.write_text(text, encoding="utf-8")
    print("rate_limit patched")
else:
    print("already patched")
