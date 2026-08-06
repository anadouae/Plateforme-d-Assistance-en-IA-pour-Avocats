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
    cases,
    corpus,
    dictation,
    documents,
    plaidoirie_templates,
    summarize,
    team,
    workspace,
)
from app.api import settings as settings_api
from app.core.config import settings
from app.core.migrations import run_migrations
from app.services.rag import ensure_legal_corpus, get_corpus_stats, warmup_embeddings
from app.services.groq_llm import llm_health

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
        # CSP API : pas de contenu HTML — politique restrictive par défaut
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
        )
        if request.url.path.startswith("/api/auth"):
            response.headers["Cache-Control"] = "no-store"
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains; preload"
            )
        return response


def _init_rag() -> None:
    try:
        warmup_embeddings()
        ensure_legal_corpus()
        logger.info("ChromaDB corpus ready")
    except Exception as exc:
        logger.warning("ChromaDB init deferred: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        run_migrations()
        logger.info("Database migrations applied")
    except Exception as exc:
        logger.exception("Migrations failed at startup: %s", exc)

    from app.core.security import is_weak_secret_key

    if settings.ENVIRONMENT == "production":
        if not settings.ENCRYPTION_KEY:
            raise RuntimeError("ENCRYPTION_KEY is required in production")
        if is_weak_secret_key(settings.SECRET_KEY):
            raise RuntimeError("SECRET_KEY is weak or default — refuse to start in production")
    elif not settings.ENCRYPTION_KEY:
        logger.warning("ENCRYPTION_KEY not set — files stored unencrypted")
    if is_weak_secret_key(settings.SECRET_KEY):
        logger.warning("SECRET_KEY is weak/default — change it before production")

    async def _delayed_rag() -> None:
        await asyncio.sleep(3)
        await asyncio.to_thread(_init_rag)

    rag_task = asyncio.create_task(_delayed_rag())

    yield

    rag_task.cancel()
    try:
        await rag_task
    except asyncio.CancelledError:
        pass


_docs_url = None if settings.ENVIRONMENT == "production" else "/docs"
_redoc_url = None if settings.ENVIRONMENT == "production" else "/redoc"

app = FastAPI(
    title=settings.APP_NAME,
    description="API Sanad – Avocat AI Assistance",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    openapi_url=None if settings.ENVIRONMENT == "production" else "/openapi.json",
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
app.include_router(corpus.router)


@app.get("/")
def root():
    return {
        "service": "sanad-api",
        "status": "running",
        "docs": "/docs" if _docs_url else None,
        "health": "/health",
        "frontend": settings.FRONTEND_URL,
        "message": "Utilisez /health pour vérifier l'API, ou ouvrez le frontend sur http://localhost:3000",
    }


@app.get("/health")
def health():
    llm = {"status": "skipped"}
    corpus = {}
    try:
        llm = llm_health()
    except Exception:
        llm = {"status": "unavailable"}
    try:
        corpus = get_corpus_stats()
    except Exception:
        pass
    return {
        "status": "ok",
        "service": "sanad-api",
        "version": "2.0.0",
        "environment": settings.ENVIRONMENT,
        "encryption": bool(settings.ENCRYPTION_KEY),
        "minio": settings.USE_MINIO,
        "llm": llm,
        "cloud_fallback_enabled": settings.LLM_ALLOW_CLOUD_FALLBACK and bool(settings.GROQ_API_KEY),
        "corpus": {
            "total_entries": corpus.get("total_entries", 0),
            "target": corpus.get("target_adala", 130000),
            "collections": list(corpus.get("collections", {}).keys()),
        },
        "web_search": settings.WEB_SEARCH_PROVIDER,
    }


@app.get("/health/live")
def health_live():
    """Healthcheck rapide — ne touche ni LLM ni Chroma."""
    return {"status": "ok"}


@app.get("/health/stt")
def health_stt():
    from app.services.whisper_stt import whisper_status

    return whisper_status()
