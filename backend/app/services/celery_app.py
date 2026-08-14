import logging
import threading

from celery import Celery
from celery.signals import worker_process_init

from app.core.config import settings

logger = logging.getLogger(__name__)

celery_app = Celery(
    "sanad",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Africa/Casablanca",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
)

celery_app.autodiscover_tasks(["app.services"])


def _warmup_models_sync() -> None:
    """Charge BGE-M3 + Whisper (peut prendre 1–3 min la 1re fois)."""
    try:
        from app.services.rag import warmup_embeddings

        warmup_embeddings()
    except Exception as exc:
        logger.warning("Celery embedding warmup skipped: %s", exc)
    if settings.WHISPER_ENABLED:
        try:
            from app.services.whisper_stt import _get_model

            _get_model()
            logger.info("Celery Whisper model warmed")
        except Exception as exc:
            logger.warning("Celery Whisper warmup skipped: %s", exc)


@worker_process_init.connect
def _warmup_worker_models(**_kwargs) -> None:
    """Warm-up en arrière-plan : n'bloque PAS l'acceptation des tâches (extraction PDF)."""
    threading.Thread(
        target=_warmup_models_sync,
        name="sanad-model-warmup",
        daemon=True,
    ).start()
    logger.info("Celery model warmup started in background")
