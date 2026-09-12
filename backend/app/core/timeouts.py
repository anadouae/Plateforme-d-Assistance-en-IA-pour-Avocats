"""Exécution avec timeout explicite (threads — pour OCR / Whisper sync)."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="lexhub-timeout")


class OperationTimeout(TimeoutError):
    """Timeout métier (Whisper / OCR / externe)."""


def run_with_timeout(fn: Callable[[], T], timeout_sec: float, *, label: str = "operation") -> T:
    """
    Exécute fn dans un thread et lève OperationTimeout si dépasse timeout_sec.
    Note: le thread peut continuer en arrière-plan (limitation Python) ;
    Celery soft_time_limit reste la barrière hard pour les workers.
    """
    if timeout_sec <= 0:
        return fn()
    future = _executor.submit(fn)
    try:
        return future.result(timeout=timeout_sec)
    except FuturesTimeout as exc:
        future.cancel()
        logger.error("Timeout %s after %.0fs", label, timeout_sec)
        raise OperationTimeout(f"{label} timeout after {timeout_sec:.0f}s") from exc
