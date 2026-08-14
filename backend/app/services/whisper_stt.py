"""Speech-to-text local via faster-whisper (prêt VPS / offline)."""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from app.core.config import settings
from app.core.timeouts import OperationTimeout, run_with_timeout
from app.services.arabic_text_fix import repair_arabic_stt

logger = logging.getLogger(__name__)

_model = None
_model_name: str | None = None

_AR_PROMPT = (
    "مرافعة قانونية بالعربية الفصحى. "
    "محكمة، مرافعة، جلسة، المدعية، المدعى عليها، النفقة، الحضانة، "
    "شركة، هيئة المحامين، لهذه الأسباب."
)

_FR_PROMPT = (
    "Plaidoirie juridique en français. "
    "Tribunal, plaidoirie, audience, demandeur, défendeur, pension alimentaire, "
    "garde d'enfants, société, barreau, pour ces motifs."
)


def whisper_status() -> dict:
    return {
        "enabled": bool(settings.WHISPER_ENABLED),
        "model": settings.WHISPER_MODEL,
        "device": settings.WHISPER_DEVICE,
        "loaded": _model is not None,
        "timeout_sec": settings.WHISPER_TIMEOUT_SEC,
    }


def _get_model():
    global _model, _model_name
    if not settings.WHISPER_ENABLED:
        return None
    name = (settings.WHISPER_MODEL or "small").strip()
    if _model is not None and _model_name == name:
        return _model
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        logger.warning("faster-whisper non installé")
        return None

    device = (settings.WHISPER_DEVICE or "cpu").strip()
    compute = (settings.WHISPER_COMPUTE_TYPE or "int8").strip()
    logger.info("Loading Whisper model=%s device=%s compute=%s", name, device, compute)
    _model = WhisperModel(name, device=device, compute_type=compute)
    _model_name = name
    return _model


def _normalize_lang(language: str | None) -> str | None:
    if not language or language == "auto":
        return None
    lang = language.strip().lower()[:8]
    if lang.startswith("ar"):
        return "ar"
    if lang.startswith("fr"):
        return "fr"
    if lang.startswith("en"):
        return "en"
    return lang


def _transcribe_once(tmp_path: str, lang: str | None, *, vad_filter: bool) -> tuple[str, str]:
    model = _get_model()
    if model is None:
        return "", "none"

    kwargs: dict = {
        "task": "transcribe",
        "beam_size": 2 if lang in {"ar", "fr"} else 1,
        "best_of": 2 if lang in {"ar", "fr"} else 1,
        "temperature": 0.0,
        "condition_on_previous_text": False,
        "vad_filter": vad_filter,
        "word_timestamps": False,
    }
    if vad_filter:
        # Moins agressif : les courts clips / micro faible passaient pour du silence
        kwargs["vad_parameters"] = dict(
            min_silence_duration_ms=800,
            speech_pad_ms=400,
            threshold=0.35,
        )
    if lang:
        kwargs["language"] = lang
    if lang == "ar":
        kwargs["initial_prompt"] = _AR_PROMPT
    elif lang == "fr":
        kwargs["initial_prompt"] = _FR_PROMPT

    segments, info = model.transcribe(tmp_path, **kwargs)
    parts = [seg.text.strip() for seg in segments if seg.text and seg.text.strip()]
    text = " ".join(parts).strip()
    detected = getattr(info, "language", lang or "?")
    if detected == "ar" or lang == "ar":
        text = repair_arabic_stt(text)
    provider = f"whisper:{_model_name or settings.WHISPER_MODEL}:{detected}"
    return text, provider


def _transcribe_file(tmp_path: str, lang: str | None) -> tuple[str, str]:
    text, provider = _transcribe_once(tmp_path, lang, vad_filter=True)
    if text.strip():
        return text, provider
    # VAD trop strict (fixture courte / parole faible) → 2e passe sans filtre
    logger.info("Whisper empty with VAD — retry without VAD filter")
    return _transcribe_once(tmp_path, lang, vad_filter=False)


def transcribe_audio_bytes(
    data: bytes,
    filename: str = "audio.webm",
    language: str | None = "ar",
) -> tuple[str | None, str]:
    """
    Retourne (texte, provider).
    provider = whisper:<model> | none | whisper:timeout
    """
    if not data or len(data) < 64:
        return None, "none"

    model = _get_model()
    if model is None:
        return None, "none"

    suffix = Path(filename).suffix.lower() or ".webm"
    if suffix not in {".webm", ".wav", ".mp3", ".m4a", ".ogg", ".mp4", ".mpeg", ".mpga"}:
        suffix = ".webm"

    lang = _normalize_lang(language)
    # Défaut arabe pour Sanad (évite le français si auto hésite)
    if lang is None and (language or "ar").startswith("ar"):
        lang = "ar"

    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name

        timeout = float(settings.WHISPER_TIMEOUT_SEC or 600)

        def _run():
            return _transcribe_file(tmp_path, lang)

        text, provider = run_with_timeout(_run, timeout, label="whisper")
        return (text or None), provider
    except OperationTimeout:
        logger.error("Whisper timeout after %.0fs file=%s", settings.WHISPER_TIMEOUT_SEC, filename)
        return None, "whisper:timeout"
    except Exception as exc:
        logger.warning("Whisper transcription failed: %s", exc)
        return None, "none"
    finally:
        if tmp_path:
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except OSError:
                pass
