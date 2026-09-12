from contextlib import asynccontextmanager
import asyncio
import logging
import threading

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.api import (
    admin,
    auth,
    billing,
    cases,
    corpus,
    dictation,
    documents,
    notifications,
    plaidoirie_templates,
    realtime_ws,
    summarize,
    team,
    workspace,
)
from app.api import settings as settings_api
from app.core.config import settings
from app.core.logging_config import CorrelationIdMiddleware, configure_logging
from app.core.migrations import run_migrations
from app.services.rag import get_corpus_stats
from app.services.groq_llm import llm_health

configure_logging()
logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(self), geolocation=(), payment=()"
        )
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        # CSP API : pas de contenu HTML — politique restrictive par défaut
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
        )
        if request.url.path.startswith("/api/auth"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains; preload"
            )
        return response


def _init_rag() -> None:
    """Ne pas charger BGE-M3 dans le process API (ça bloquait upload/suppression 40–90 s)."""
    logger.info("ChromaDB warmup skipped on API — handled by Celery")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        run_migrations()
        logger.info("Database migrations applied")
    except Exception as exc:
        logger.exception("Migrations failed at startup: %s", exc)

    try:
        from app.core.database import SessionLocal
        from app.services.billing import ensure_default_plans

        db = SessionLocal()
        try:
            ensure_default_plans(db)
            db.commit()
            logger.info("Billing default plans ensured")
        finally:
            db.close()
    except Exception as exc:
        logger.warning("Billing plan seed skipped: %s", exc)

    from app.core.security import is_weak_secret_key

    if settings.ENVIRONMENT == "production":
        if not settings.ENCRYPTION_KEY:
            raise RuntimeError("ENCRYPTION_KEY is required in production")
        if is_weak_secret_key(settings.SECRET_KEY):
            raise RuntimeError("SECRET_KEY is weak or default — refuse to start in production")
        # Turnstile obligatoire en prod (pas les clés de test Cloudflare)
        _cf_test_sites = {
            "1x00000000000000000000AA",
            "2x00000000000000000000AB",
            "3x00000000000000000000FF",
        }
        _cf_test_secrets = {
            "1x0000000000000000000000000000000AA",
            "2x0000000000000000000000000000000AA",
            "3x0000000000000000000000000000000AA",
        }
        if not settings.TURNSTILE_SITE_KEY or not settings.TURNSTILE_SECRET_KEY:
            raise RuntimeError(
                "TURNSTILE_SITE_KEY et TURNSTILE_SECRET_KEY sont obligatoires en production "
                "(Cloudflare Turnstile → https://dash.cloudflare.com → Turnstile)"
            )
        if (
            settings.TURNSTILE_SITE_KEY in _cf_test_sites
            or settings.TURNSTILE_SECRET_KEY in _cf_test_secrets
        ):
            raise RuntimeError(
                "Clés Turnstile de TEST Cloudflare interdites en production — "
                "créez un widget réel sur dash.cloudflare.com"
            )
    elif not settings.ENCRYPTION_KEY:
        logger.warning("ENCRYPTION_KEY not set — files stored unencrypted")
    if is_weak_secret_key(settings.SECRET_KEY):
        logger.warning("SECRET_KEY is weak/default — change it before production")

    async def _delayed_rag() -> None:
        await asyncio.sleep(3)
        await asyncio.to_thread(_init_rag)

    rag_task = asyncio.create_task(_delayed_rag())

    if settings.SEED_DEMO_DATA:
        try:
            from app.services.demo_seed import run_demo_seed

            await asyncio.to_thread(run_demo_seed, with_demo_data=True)
        except Exception as exc:
            logger.exception("SEED_DEMO_DATA failed: %s", exc)

    # Fallback rappels agenda 48 h si Celery beat est indisponible
    agenda_stop = threading.Event()

    def _agenda_reminder_loop() -> None:
        while not agenda_stop.wait(15 * 60):
            try:
                from app.core.database import SessionLocal
                from app.services.agenda_reminders import send_due_agenda_reminders

                db = SessionLocal()
                try:
                    send_due_agenda_reminders(db)
                finally:
                    db.close()
            except Exception as exc:
                logger.warning("Agenda reminder fallback failed: %s", exc)

    agenda_thread = threading.Thread(
        target=_agenda_reminder_loop,
        name="agenda-remind-48h",
        daemon=True,
    )
    agenda_thread.start()
    logger.info("Agenda 48h reminder fallback thread started")

    yield

    agenda_stop.set()
    rag_task.cancel()
    try:
        await rag_task
    except asyncio.CancelledError:
        pass


_docs_url = None if settings.ENVIRONMENT == "production" else "/docs"
_redoc_url = None if settings.ENVIRONMENT == "production" else "/redoc"

app = FastAPI(
    title=settings.APP_NAME,
    description="API LexHub — plateforme LegalTech marocaine",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    openapi_url=None if settings.ENVIRONMENT == "production" else "/openapi.json",
    # Évite les 307 /api/documents/ → /api/documents qui droppent parfois l'Authorization
    redirect_slashes=False,
)

origins = [o.strip() for o in settings.CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CorrelationIdMiddleware)

app.include_router(auth.router)
app.include_router(cases.router)
app.include_router(documents.router)
app.include_router(summarize.router)
app.include_router(workspace.router)
app.include_router(dictation.router)
app.include_router(plaidoirie_templates.router)
app.include_router(team.router)
app.include_router(settings_api.router)
app.include_router(admin.router)
app.include_router(billing.router)
app.include_router(billing.admin_router)
app.include_router(corpus.router)
app.include_router(notifications.router)
app.include_router(realtime_ws.router)


@app.get("/")
def root():
    return {
        "service": "lexhub-api",
        "status": "running",
        "docs": "/docs" if _docs_url else None,
        "health": "/health",
        "frontend": settings.FRONTEND_URL,
        "message": "Utilisez /health pour vérifier l'API, ou ouvrez le frontend sur http://localhost:3000",
    }


@app.get("/health")
@app.get("/api/health")
def health():
    """Healthcheck public minimal (pas d'infos internes)."""
    return {
        "status": "ok",
        "service": "lexhub-api",
        "version": "2.0.0",
    }


@app.get("/health/live")
@app.get("/api/health/live")
def health_live():
    """Healthcheck rapide — ne touche ni LLM ni Chroma."""
    return {"status": "ok"}


@app.get("/health/stt")
@app.get("/api/health/stt")
def health_stt():
    from app.services.whisper_stt import whisper_status

    return whisper_status()
