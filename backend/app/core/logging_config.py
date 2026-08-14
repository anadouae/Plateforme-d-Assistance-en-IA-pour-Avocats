"""Logs structurés JSON + correlation ID + Sentry optionnel."""

from __future__ import annotations

import json
import logging
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings

correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="")


def get_correlation_id() -> str:
    return correlation_id_ctx.get() or ""


def set_correlation_id(value: str | None = None) -> str:
    cid = (value or "").strip() or str(uuid.uuid4())
    correlation_id_ctx.set(cid)
    return cid


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", None) or get_correlation_id(),
        }
        for key in ("user_id", "cabinet_id", "task", "endpoint", "document_id", "status_code"):
            val = getattr(record, key, None)
            if val is not None:
                payload[key] = val
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


class CorrelationFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not getattr(record, "correlation_id", None):
            record.correlation_id = get_correlation_id()
        return True


def configure_logging() -> None:
    level = getattr(logging, (settings.LOG_LEVEL or "INFO").upper(), logging.INFO)
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(CorrelationFilter())
    if settings.LOG_JSON and (settings.ENVIRONMENT or "").lower() != "test":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s [%(correlation_id)s] %(name)s: %(message)s")
        )
    root.addHandler(handler)

    # Réduire le bruit des libs
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)

    if settings.SENTRY_DSN:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.celery import CeleryIntegration
            from sentry_sdk.integrations.fastapi import FastApiIntegration

            sentry_sdk.init(
                dsn=settings.SENTRY_DSN,
                integrations=[FastApiIntegration(), CeleryIntegration()],
                traces_sample_rate=0.05,
                environment=settings.ENVIRONMENT,
            )
            logging.getLogger(__name__).info("Sentry initialized")
        except Exception as exc:
            logging.getLogger(__name__).warning("Sentry init failed: %s", exc)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        incoming = request.headers.get("x-request-id") or request.headers.get("x-correlation-id")
        cid = set_correlation_id(incoming)
        request.state.correlation_id = cid
        try:
            response = await call_next(request)
        finally:
            # ne pas laisser fuiter vers une autre requête async
            correlation_id_ctx.set("")
        response.headers["X-Request-ID"] = cid
        return response


def log_extra(**kwargs) -> dict:
    """Helper pour logger.info(..., extra=log_extra(user_id=...))."""
    return {k: v for k, v in kwargs.items() if v is not None}
