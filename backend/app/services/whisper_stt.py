"""Speech-to-text local via faster-whisper (prêt VPS / offline)."""

from __future__ import annotations

import logging
import tempfile
import threading
import time
from pathlib import Path

from app.core.config import settings
from app.core.timeouts import OperationTimeout, run_with_timeout
from app.services.arabic_text_fix import repair_arabic_stt

logger = logging.getLogger(__name__)

_model = None
_model_name: str | None = None
_stt_lock = threading.Lock()

_AR_PROMPT = ""  # vide = fidélité max (le prompt inventait des mots juridiques)

_FR_PROMPT = ""


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


def _wav_duration_sec(path: str) -> float:
    import wave

    try:
        with wave.open(path, "rb") as w:
            rate = w.getframerate() or 16000
            return w.getnframes() / float(rate)
    except Exception:
        return 0.0


def _ensure_wav_16k(src_path: str) -> str:
    import subprocess

    out = Path(src_path).with_suffix(".wav")
    if out.resolve() == Path(src_path).resolve():
        out = Path(src_path).with_name(Path(src_path).stem + "_16k.wav")
    # Band-pass voix + gain doux. PAS de dynaudnorm (crée des hallucinations).
    filters = ["highpass=f=80", "lowpass=f=7600"]
    gain_db = float(getattr(settings, "WHISPER_GAIN_DB", 6.0) or 0.0)
    if gain_db > 0.1:
        filters.append(f"volume={gain_db}dB")
    if bool(getattr(settings, "WHISPER_DENOISE", False)):
        # Soft only — jamais dynaudnorm agressif
        filters.append("afftdn=nf=-25")
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", src_path,
                "-ac", "1", "-ar", "16000",
                "-af", ",".join(filters),
                "-c:a", "pcm_s16le", str(out),
            ],
            check=True,
            capture_output=True,
            timeout=180,
        )
        if out.is_file() and out.stat().st_size > 64:
            return str(out)
    except Exception as exc:
        logger.warning("ffmpeg wav convert failed (%s) — keep original", exc)
    return src_path


def _split_long_wav(wav_path: str, chunk_sec: float) -> list[str]:
    """Découpe interne ~2 min pour dictées longues — pas de fenêtres 15 s."""
    import subprocess

    duration = _wav_duration_sec(wav_path)
    if duration <= 0 or duration <= float(getattr(settings, "WHISPER_CHUNK_MIN_SEC", 180) or 180):
        return [wav_path]
    step = max(60.0, float(chunk_sec or 120))
    paths: list[str] = []
    start = 0.0
    idx = 0
    while start < duration - 0.4:
        dest = Path(wav_path).with_name(f"{Path(wav_path).stem}_p{idx}.wav")
        try:
            subprocess.run(
                [
                    "ffmpeg", "-y", "-i", wav_path,
                    "-ss", f"{start:.2f}", "-t", f"{step:.2f}",
                    "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(dest),
                ],
                check=True,
                capture_output=True,
                timeout=90,
            )
            if dest.is_file() and dest.stat().st_size > 64:
                paths.append(str(dest))
        except Exception as exc:
            logger.warning("ffmpeg split failed at %.1fs: %s", start, exc)
            break
        start += step
        idx += 1
        if idx > 40:
            break
    return paths or [wav_path]


def _transcribe_once(tmp_path: str, lang: str | None, *, vad_filter: bool) -> tuple[str, str]:
    from app.services.stt_quality import drop_bad_segments, strip_prompt_leak

    model = _get_model()
    if model is None:
        return "", "none"

    audio_path = tmp_path
    # Anti-hallucination : seuil silence plus strict, pas de prompt, pas de contexte précédent
    kwargs: dict = {
        "task": "transcribe",
        "beam_size": 3 if lang == "ar" else 2,
        "best_of": 1,
        "temperature": 0.0,
        "condition_on_previous_text": False,
        "vad_filter": vad_filter,
        "word_timestamps": False,
        "no_speech_threshold": 0.55 if lang == "ar" else 0.6,
        "compression_ratio_threshold": 2.2,
        "log_prob_threshold": -1.0,
    }
    if vad_filter:
        kwargs["vad_parameters"] = dict(
            min_silence_duration_ms=500,
            speech_pad_ms=400,
            threshold=0.35,
        )
    if lang:
        kwargs["language"] = lang
    # Pas d'initial_prompt : il biaise Whisper et invente des formules non dictées

    segments, info = model.transcribe(audio_path, **kwargs)
    segs = list(segments)
    segs = drop_bad_segments(segs)
    parts = [seg.text.strip() for seg in segs if seg.text and seg.text.strip()]
    text = " ".join(parts).strip()
    text = strip_prompt_leak(text, _AR_PROMPT if lang == "ar" else _FR_PROMPT)
    detected = getattr(info, "language", lang or "?")
    if detected == "ar" or lang == "ar":
        text = _strip_arabic_hallucinations(repair_arabic_stt(text))
    provider = f"whisper:{_model_name or settings.WHISPER_MODEL}:{detected}"
    return text, provider


def _transcribe_file(tmp_path: str, lang: str | None) -> tuple[str, str]:
    # VAD d'abord : le silence sans VAD = source n°1 des mots inventés
    text, provider = _transcribe_once(tmp_path, lang, vad_filter=True)
    if text.strip():
        return text, provider
    logger.info("Whisper empty with VAD — retry without VAD (micro très faible)")
    return _transcribe_once(tmp_path, lang, vad_filter=False)


def _strip_arabic_hallucinations(text: str) -> str:
    """Retire formules Whisper souvent inventées hors dictée réelle."""
    import re

    t = (text or "").strip()
    if not t:
        return ""
    # Boucles typiques
    t = re.sub(r"(شكرا(?:ً)?(?:\s+لكم)?)(?:\s+\1){2,}", r"\1", t)
    t = re.sub(r"(والسلام عليكم(?: ورحمة الله(?: وبركاته)?)?)(?:\s+\1)+", r"\1", t)
    t = re.sub(r"(بسم الله الرحمن الرحيم)(?:\s+\1)+", r"\1", t)
    # Si le texte entier est une formule courte seule → souvent hallucination sur silence
    alone = {
        "شكرا",
        "شكرا لكم",
        "شكراً",
        "والسلام عليكم",
        "السلام عليكم",
        "بسم الله الرحمن الرحيم",
        "ترجمة نانسي قنقر",
        "اشتركوا في القناة",
        "ترجمة",
    }
    compact = re.sub(r"\s+", " ", t).strip()
    if compact in alone or len(compact.split()) <= 2 and any(x in compact for x in alone):
        return ""
    return t.strip()


def _transcribe_openai(data: bytes, filename: str, lang: str | None) -> tuple[str | None, str]:
    """STT via API OpenAI (même clé ChatGPT) — pas de modèle local / Groq."""
    key = (settings.OPENAI_API_KEY or "").strip()
    if not key:
        return None, "none"
    try:
        import httpx
    except ImportError:
        return None, "none"
    base = (settings.OPENAI_BASE_URL or "https://api.openai.com/v1").rstrip("/")
    model = (getattr(settings, "OPENAI_WHISPER_MODEL", None) or "whisper-1").strip()
    mime = "audio/webm"
    lower = (filename or "").lower()
    if lower.endswith(".wav"):
        mime = "audio/wav"
    elif lower.endswith(".mp3"):
        mime = "audio/mpeg"
    elif lower.endswith(".ogg"):
        mime = "audio/ogg"
    elif lower.endswith(".m4a"):
        mime = "audio/mp4"
    try:
        with httpx.Client(timeout=180.0) as client:
            res = client.post(
                f"{base}/audio/transcriptions",
                headers={"Authorization": f"Bearer {key}"},
                files={"file": (filename or "audio.webm", data, mime)},
                data={
                    "model": model,
                    "response_format": "json",
                    **({"language": lang} if lang in ("ar", "fr", "en") else {}),
                },
            )
        if res.status_code >= 400:
            logger.warning("OpenAI STT HTTP %s: %s", res.status_code, res.text[:240])
            return None, "none"
        text = (res.json().get("text") or "").strip()
        if lang == "ar":
            text = _strip_arabic_hallucinations(repair_arabic_stt(text))
        if not text:
            return None, "none"
        return text, f"openai:{model}"
    except Exception as exc:
        logger.warning("OpenAI STT failed: %s", exc)
        return None, "none"


def _transcribe_groq(data: bytes, filename: str, lang: str | None) -> tuple[str | None, str]:
    if bool(getattr(settings, "DICTATION_OPENAI_ONLY", True)):
        return None, "none"
    key = (settings.GROQ_API_KEY or "").strip()
    if not key:
        return None, "none"
    try:
        import httpx
    except ImportError:
        return None, "none"
    model = (getattr(settings, "GROQ_WHISPER_MODEL", None) or "whisper-large-v3").strip()
    mime = "audio/webm"
    lower = (filename or "").lower()
    if lower.endswith(".wav"):
        mime = "audio/wav"
    elif lower.endswith(".mp3"):
        mime = "audio/mpeg"
    elif lower.endswith(".ogg"):
        mime = "audio/ogg"
    try:
        with httpx.Client(timeout=120.0) as client:
            res = client.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {key}"},
                files={"file": (filename or "audio.webm", data, mime)},
                data={
                    "model": model,
                    "response_format": "json",
                    "temperature": "0",
                    **({"language": lang} if lang in ("ar", "fr", "en") else {}),
                },
            )
        if res.status_code >= 400:
            logger.warning("Groq Whisper HTTP %s: %s", res.status_code, res.text[:200])
            return None, "none"
        text = (res.json().get("text") or "").strip()
        if lang == "ar":
            text = _strip_arabic_hallucinations(repair_arabic_stt(text))
        if not text:
            return None, "none"
        return text, f"groq:{model}"
    except Exception as exc:
        logger.warning("Groq Whisper failed: %s", exc)
        return None, "none"


def transcribe_audio_bytes(
    data: bytes,
    filename: str = "audio.webm",
    language: str | None = "ar",
) -> tuple[str | None, str]:
    """Retourne (texte, provider)."""
    if not data or len(data) < 64:
        return None, "none"

    lang = _normalize_lang(language)
    if lang is None and (language or "ar").startswith("ar"):
        lang = "ar"

    local_only = bool(getattr(settings, "DICTATION_LOCAL_ONLY", False))
    openai_only = bool(getattr(settings, "DICTATION_OPENAI_ONLY", True))
    prefer_groq = bool(getattr(settings, "DICTATION_STT_PREFER_GROQ", False)) and not openai_only

    if not _stt_lock.acquire(blocking=False):
        logger.warning("[STT] busy — refuse second concurrent transcription")
        return None, "whisper:busy"

    t0 = time.monotonic()
    try:
        # LexHub : dictée audio = API OpenAI uniquement (clé ChatGPT payante)
        if not local_only:
            oa_text, oa_provider = _transcribe_openai(data, filename, lang)
            if oa_text:
                logger.info(
                    "[STT] openai-primary lang=%s chars=%d provider=%s elapsed=%.1fs",
                    lang,
                    len(oa_text),
                    oa_provider,
                    time.monotonic() - t0,
                )
                return oa_text, oa_provider
            if openai_only:
                logger.warning("[STT] OpenAI-only mode — transcription failed")
                return None, "openai:failed"

        # Arabe : Groq large-v3 (désactivé si DICTATION_OPENAI_ONLY)
        if not local_only and prefer_groq and lang in ("ar", "fr"):
            groq_text, groq_provider = _transcribe_groq(data, filename, lang)
            if groq_text:
                preview = groq_text[:120].replace("\n", " ")
                logger.info(
                    "[STT] groq-primary lang=%s chars=%d provider=%s elapsed=%.1fs preview=%r",
                    lang,
                    len(groq_text),
                    groq_provider,
                    time.monotonic() - t0,
                    preview,
                )
                return groq_text, groq_provider

        if openai_only:
            return None, "openai:failed"

        model = _get_model()
        if model is not None:
            suffix = Path(filename).suffix.lower() or ".webm"
            if suffix not in {".webm", ".wav", ".mp3", ".m4a", ".ogg", ".mp4", ".mpeg", ".mpga"}:
                suffix = ".webm"

            tmp_path: str | None = None
            wav_path: str | None = None
            extra_parts: list[str] = []
            try:
                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                    tmp.write(data)
                    tmp_path = tmp.name

                wav_path = _ensure_wav_16k(tmp_path)
                duration = _wav_duration_sec(wav_path)
                timeout = max(float(settings.WHISPER_TIMEOUT_SEC or 1800), duration * 8.0 + 90.0)
                chunk_on = bool(getattr(settings, "WHISPER_CHUNK_ENABLED", False))
                chunk_sec = float(getattr(settings, "WHISPER_CHUNK_SEC", 120) or 120)
                min_sec = float(getattr(settings, "WHISPER_CHUNK_MIN_SEC", 180) or 180)

                def _run():
                    if chunk_on and duration > min_sec:
                        parts = _split_long_wav(wav_path, chunk_sec)
                        extra_parts.extend(p for p in parts if p != wav_path)
                        texts: list[str] = []
                        provider = f"whisper:{_model_name or settings.WHISPER_MODEL}:{lang or '?'}"
                        logger.info("[STT] long dictation duration=%.1fs parts=%d", duration, len(parts))
                        for part in parts:
                            piece, provider = _transcribe_file(part, lang)
                            if piece.strip():
                                texts.append(piece.strip())
                        return " ".join(texts).strip(), provider
                    return _transcribe_file(wav_path, lang)

                text, provider = run_with_timeout(_run, timeout, label="whisper")
                if lang == "ar" and text:
                    text = _strip_arabic_hallucinations(text)
                elapsed = time.monotonic() - t0
                rtf = (elapsed / duration) if duration > 0 else 0.0
                logger.info(
                    "[STT] success model=%s device=cpu compute=int8 lang=%s "
                    "audio_duration=%.1fs transcription_duration=%.1fs rtf=%.2f chars=%d",
                    settings.WHISPER_MODEL,
                    lang,
                    duration,
                    elapsed,
                    rtf,
                    len(text or ""),
                )
                if text:
                    return text, provider
            except OperationTimeout:
                logger.error("[STT] timeout after %.0fs file=%s", settings.WHISPER_TIMEOUT_SEC, filename)
                return None, "whisper:timeout"
            except Exception as exc:
                logger.warning("[STT] transcription failed: %s", exc)
            finally:
                for p in [tmp_path, wav_path, *extra_parts]:
                    if not p:
                        continue
                    try:
                        Path(p).unlink(missing_ok=True)
                    except OSError:
                        pass

        if local_only:
            return None, "none"

        groq_text, groq_provider = _transcribe_groq(data, filename, lang)
        if groq_text:
            return groq_text, groq_provider

        if model is None:
            return None, "none"
        return None, "none"
    finally:
        _stt_lock.release()
