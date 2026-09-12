"""Découpe audio pour Whisper long — VAD énergie + fenêtres ~15 s (léger RAM)."""

from __future__ import annotations

import logging
import struct
import wave
from pathlib import Path

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16_000
# Fenêtre d’analyse (ms) pour RMS
_FRAME_MS = 30
_HOP_MS = 15


def wav_duration_sec(path: str) -> float:
    try:
        with wave.open(path, "rb") as w:
            frames = w.getnframes()
            rate = w.getframerate() or SAMPLE_RATE
            return frames / float(rate)
    except Exception as exc:
        logger.warning("wav_duration_sec failed: %s", exc)
        return 0.0


def _read_pcm16_mono(path: str) -> tuple[list[int], int]:
    with wave.open(path, "rb") as w:
        rate = w.getframerate()
        nch = w.getnchannels()
        sw = w.getsampwidth()
        nframes = w.getnframes()
        raw = w.readframes(nframes)
    if sw != 2:
        raise ValueError(f"expected 16-bit PCM, got sampwidth={sw}")
    samples = list(struct.unpack("<" + "h" * (len(raw) // 2), raw))
    if nch == 2:
        samples = samples[0::2]
    elif nch != 1:
        # downmix naïf
        out: list[int] = []
        for i in range(0, len(samples), nch):
            chunk = samples[i : i + nch]
            out.append(int(sum(chunk) / max(1, len(chunk))))
        samples = out
    return samples, rate


def _write_pcm16_mono(path: str, samples: list[int], rate: int = SAMPLE_RATE) -> None:
    clipped = [max(-32768, min(32767, int(s))) for s in samples]
    raw = struct.pack("<" + "h" * len(clipped), *clipped)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(raw)


def _rms_frames(samples: list[int], rate: int) -> list[float]:
    frame = max(1, int(rate * _FRAME_MS / 1000))
    hop = max(1, int(rate * _HOP_MS / 1000))
    out: list[float] = []
    for i in range(0, max(0, len(samples) - frame + 1), hop):
        window = samples[i : i + frame]
        if not window:
            break
        acc = sum(s * s for s in window) / len(window)
        out.append(acc ** 0.5)
    return out


def _speech_regions(
    samples: list[int],
    rate: int,
    *,
    min_speech_ms: int = 250,
    pad_ms: int = 280,
) -> list[tuple[int, int]]:
    """Retourne des plages (start_sample, end_sample) de parole (VAD énergie)."""
    if len(samples) < rate // 10:
        return [(0, len(samples))]

    rms = _rms_frames(samples, rate)
    if not rms:
        return [(0, len(samples))]

    sorted_r = sorted(rms)
    baseline = sorted_r[max(0, int(len(sorted_r) * 0.35))]
    peak = sorted_r[min(len(sorted_r) - 1, int(len(sorted_r) * 0.90))]
    thr = max(120.0, baseline * 1.8, (baseline + peak) * 0.28)

    hop = max(1, int(rate * _HOP_MS / 1000))
    speech_flags = [v >= thr for v in rms]

    # Lissage: combler trous < 180 ms
    fill = max(1, int(0.18 / (_HOP_MS / 1000)))
    flags = speech_flags[:]
    i = 0
    while i < len(flags):
        if flags[i]:
            i += 1
            continue
        j = i
        while j < len(flags) and not flags[j]:
            j += 1
        if j - i <= fill and i > 0 and j < len(flags):
            for k in range(i, j):
                flags[k] = True
        i = j

    regions: list[tuple[int, int]] = []
    i = 0
    while i < len(flags):
        if not flags[i]:
            i += 1
            continue
        j = i
        while j < len(flags) and flags[j]:
            j += 1
        start = i * hop
        end = min(len(samples), j * hop + hop)
        if (end - start) * 1000 / rate >= min_speech_ms:
            regions.append((start, end))
        i = j

    if not regions:
        return [(0, len(samples))]

    pad = int(rate * pad_ms / 1000)
    padded: list[tuple[int, int]] = []
    for s, e in regions:
        padded.append((max(0, s - pad), min(len(samples), e + pad)))

    # Fusion régions qui se chevauchent
    merged: list[tuple[int, int]] = [padded[0]]
    for s, e in padded[1:]:
        ps, pe = merged[-1]
        if s <= pe + int(rate * 0.12):
            merged[-1] = (ps, max(pe, e))
        else:
            merged.append((s, e))
    return merged


def _split_long_region(
    start: int,
    end: int,
    samples: list[int],
    rate: int,
    max_sec: float,
) -> list[tuple[int, int]]:
    max_len = int(rate * max_sec)
    length = end - start
    if length <= max_len:
        return [(start, end)]

    # Couper aux minima d’énergie tous les ~max_sec
    frame = max(1, int(rate * 0.05))
    cuts: list[int] = [start]
    pos = start + max_len
    while pos < end - int(rate * 0.8):
        window_start = max(start, pos - int(rate * 0.6))
        window_end = min(end, pos + int(rate * 0.6))
        best = pos
        best_e = float("inf")
        for i in range(window_start, window_end - frame, frame):
            chunk = samples[i : i + frame]
            e = sum(abs(x) for x in chunk) / len(chunk)
            if e < best_e:
                best_e = e
                best = i
        cuts.append(best)
        pos = best + max_len
    cuts.append(end)

    out: list[tuple[int, int]] = []
    for a, b in zip(cuts, cuts[1:]):
        if b - a >= int(rate * 0.35):
            out.append((a, b))
    return out or [(start, end)]


def plan_speech_chunks(
    wav_path: str,
    *,
    max_chunk_sec: float = 15.0,
    min_total_sec: float = 22.0,
) -> list[tuple[float, float]]:
    """
    Planifie des chunks (start_sec, end_sec).
    Si audio court (< min_total_sec) → un seul chunk (fichier entier).
    """
    dur = wav_duration_sec(wav_path)
    if dur <= 0:
        return [(0.0, 0.0)]
    if dur < min_total_sec:
        return [(0.0, dur)]

    try:
        samples, rate = _read_pcm16_mono(wav_path)
    except Exception as exc:
        logger.warning("plan_speech_chunks read failed (%s) — fixed windows", exc)
        chunks: list[tuple[float, float]] = []
        t = 0.0
        while t < dur:
            chunks.append((t, min(dur, t + max_chunk_sec)))
            t += max_chunk_sec
        return chunks

    regions = _speech_regions(samples, rate)
    spans: list[tuple[int, int]] = []
    for s, e in regions:
        spans.extend(_split_long_region(s, e, samples, rate, max_chunk_sec))

    if not spans:
        return [(0.0, dur)]

    return [(a / rate, b / rate) for a, b in spans]


def extract_chunk_wav(
    src_wav: str,
    dest_wav: str,
    start_sec: float,
    end_sec: float,
) -> str:
    """Extrait [start,end] vers un nouveau WAV 16 kHz mono."""
    samples, rate = _read_pcm16_mono(src_wav)
    a = max(0, int(start_sec * rate))
    b = min(len(samples), int(end_sec * rate))
    if b <= a:
        b = min(len(samples), a + int(rate * 0.5))
    _write_pcm16_mono(dest_wav, samples[a:b], rate)
    return dest_wav


def soft_denoise_wav(src_path: str, dest_path: str | None = None) -> str:
    """Léger nettoyage ffmpeg — optionnel. Pas de dynaudnorm (hallucinations)."""
    import subprocess

    out = dest_path or str(Path(src_path).with_name(Path(src_path).stem + "_dn.wav"))
    filters = [
        "highpass=f=80,lowpass=f=7600,volume=6dB",
        "highpass=f=80,lowpass=f=7600,afftdn=nf=-25",
        "highpass=f=80,lowpass=f=7600",
    ]
    for af in filters:
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    src_path,
                    "-af",
                    af,
                    "-ac",
                    "1",
                    "-ar",
                    "16000",
                    "-c:a",
                    "pcm_s16le",
                    out,
                ],
                check=True,
                capture_output=True,
                timeout=90,
            )
            if Path(out).is_file() and Path(out).stat().st_size > 64:
                return out
        except Exception:
            continue
    logger.info("soft_denoise skipped — keep original wav")
    return src_path


def merge_chunk_texts(parts: list[str]) -> str:
    """Fusionne les textes de chunks en évitant doublons de bord."""
    out = ""
    for raw in parts:
        p = " ".join((raw or "").split()).strip()
        if not p:
            continue
        if not out:
            out = p
            continue
        # Chevauchement: si le début du chunk est déjà en fin de out
        words_out = out.split()
        words_p = p.split()
        max_k = min(8, len(words_out), len(words_p))
        best = 0
        for k in range(max_k, 0, -1):
            if words_out[-k:] == words_p[:k]:
                best = k
                break
        rest = " ".join(words_p[best:])
        if rest:
            out = f"{out} {rest}".strip()
    return out


def merge_confidence(metas: list[dict]) -> dict:
    if not metas:
        return {"confidence": 0, "needs_review": True, "avg_logprob": None, "chunks": 0}
    confs = [int(m.get("confidence") or 0) for m in metas]
    reviews = [bool(m.get("needs_review")) for m in metas]
    lps = [m.get("avg_logprob") for m in metas if m.get("avg_logprob") is not None]
    avg_conf = int(round(sum(confs) / len(confs)))
    avg_lp = (sum(float(x) for x in lps) / len(lps)) if lps else None
    return {
        "confidence": avg_conf,
        "needs_review": any(reviews) or avg_conf < 58,
        "avg_logprob": avg_lp,
        "chunks": len(metas),
    }
