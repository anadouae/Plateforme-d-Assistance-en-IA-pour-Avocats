"""Tests Phase 1–2 pipeline dictée (lexique, chunks, confiance)."""

from __future__ import annotations

import math
import struct
import tempfile
import wave
from pathlib import Path

from app.services.arabic_text_fix import audio_transcript_quality, light_arabic_fusha_form, repair_arabic_stt
from app.services.audio_chunks import (
    extract_chunk_wav,
    merge_chunk_texts,
    merge_confidence,
    plan_speech_chunks,
    wav_duration_sec,
)
from app.services.dictation import looks_like_nonsense, polish_dictation


def test_looks_like_nonsense_keyboard_mash():
    assert looks_like_nonsense("k;k;l;") is True
    assert looks_like_nonsense("asdf") is True
    assert looks_like_nonsense(";;;") is True
    assert looks_like_nonsense("ك ك ك ك") is True
    # Fautes / mots cassés → PAS nonsense (ChatGPT doit approximer)
    assert looks_like_nonsense("السلا ن م السيد الؤيس") is False
    assert looks_like_nonsense("السيد الرئيس المحكمة الابتدائية") is False
    assert looks_like_nonsense("Monsieur le président, nous demandons") is False
from app.services.stt_quality import _confidence_from_segments, pick_best_transcript


def test_fusha_form_drug_trafficking_sentence():
    """Exemple utilisateur : forme réelle, faits conservés, STT orange."""
    raw = (
        "إن المرافعة التي نحن بصدد إلقائها تخص قضية من قضايا عن التجار بالمخدرات "
        "والتي كانت قد تورطت فيها عدد من الأشخاص"
    )
    fixed = light_arabic_fusha_form(raw)
    plain = fixed.replace("‹", "").replace("›", "")
    assert "الاتجار بالمخدرات" in plain
    assert "عن التجار بالمخدرات" not in plain
    assert "تورط فيها عدد" in plain
    assert "تورطت فيها عدد" not in plain
    assert "‹الاتجار بالمخدرات›" in fixed
    assert "أشخاص" in plain or "الأشخاص" in plain


def test_fusha_stt_idaduha_to_idadaha():
    assert "‹إعدادها›" in light_arabic_fusha_form("نحن بصدد أيدادها اليوم أمام المحكمة الموقرة")
    assert "‹إعدادها›" in light_arabic_fusha_form("نحن بصدد ايدادها اليوم أمام المحكمة الموقرة")


def test_polish_dictation_preserves_stt_marks():
    raw = (
        "إن المرافعة التي نحن بصدد إلقائها تخص قضية من قضايا عن التجار بالمخدرات "
        "والتي كانت قد تورطت فيها عدد من الأشخاص"
    )
    pol, prov = polish_dictation(raw, language="ar", source="audio")
    assert prov == "fidelity"
    assert "‹الاتجار بالمخدرات›" in pol
    assert "تورط فيها عدد" in pol.replace("‹", "").replace("›", "")
    assert "عدد من الأشخاص" in pol or "عدد من أشخاص" in pol


def _write_tone_wav(path: Path, seconds: float, *, freq: float = 220.0, amp: int = 8000) -> None:
    rate = 16_000
    n = int(rate * seconds)
    samples = []
    for i in range(n):
        # Alternance parole / silence pour tester le VAD
        t = i / rate
        in_speech = (int(t) % 3) != 2  # 2s speech, 1s silence
        if in_speech:
            val = int(amp * math.sin(2 * math.pi * freq * t))
        else:
            val = 0
        samples.append(val)
    raw = struct.pack("<" + "h" * len(samples), *samples)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(raw)


def test_repair_arabic_legal_lexicon():
    raw = "السيد ريس امام محكمتكم الموقرة لهده الاسباب يلتمس العارد فتح اجل"
    fixed = repair_arabic_stt(raw)
    assert "السيد الرئيس" in fixed
    assert "أمام محكمتكم الموقرة" in fixed
    # لهذه avec teh marbuta (ة) — pas ه final
    assert "لهذ\u0629" in fixed
    assert "الأسباب" in fixed
    assert "يلتمس العارض" in fixed
    assert "فتح أجل" in fixed


def test_repair_casablanca_phonetic():
    assert "الدار البيضاء" in repair_arabic_stt("بمديمة دعوة بيضاء")


def test_audio_quality_heuristic():
    good = (
        "أمام محكمة الابتدائية السيد الرئيس المرافعة في القضية "
        "المدعى عليه والمتهم بخصوص النفقة والحضانة"
    )
    assert audio_transcript_quality(good) in {"good", "medium"}
    assert audio_transcript_quality("hi") == "poor"


def test_confidence_from_segments():
    class Seg:
        def __init__(self, lp, ns=0.1):
            self.avg_logprob = lp
            self.no_speech_prob = ns

    score, needs, avg = _confidence_from_segments([Seg(-0.2), Seg(-0.25)])
    assert 50 <= score <= 100
    assert avg is not None
    assert needs is False or score < 58

    low, needs_low, _ = _confidence_from_segments([Seg(-1.1, 0.8)])
    assert needs_low is True
    assert low < 58


def test_merge_chunk_texts_dedup():
    a = "السيد الرئيس المحكمة الابتدائية بالدار البيضاء"
    b = "المحكمة الابتدائية بالدار البيضاء لهذه الأسباب"
    merged = merge_chunk_texts([a, b])
    assert merged.count("المحكمة الابتدائية") == 1
    assert "لهذه الأسباب" in merged


def test_merge_confidence_flags_review():
    meta = merge_confidence(
        [
            {"confidence": 80, "needs_review": False, "avg_logprob": -0.2},
            {"confidence": 40, "needs_review": True, "avg_logprob": -0.9},
        ]
    )
    assert meta["chunks"] == 2
    assert meta["needs_review"] is True
    assert 50 <= meta["confidence"] <= 70


def test_plan_short_audio_single_chunk(tmp_path: Path):
    wav = tmp_path / "short.wav"
    _write_tone_wav(wav, 8.0)
    plan = plan_speech_chunks(str(wav), max_chunk_sec=15.0, min_total_sec=22.0)
    assert len(plan) == 1
    assert abs(plan[0][1] - wav_duration_sec(str(wav))) < 0.2


def test_plan_long_audio_multiple_chunks(tmp_path: Path):
    wav = tmp_path / "long.wav"
    _write_tone_wav(wav, 36.0)
    plan = plan_speech_chunks(str(wav), max_chunk_sec=15.0, min_total_sec=22.0)
    assert len(plan) >= 2
    # Couverture globale
    assert plan[0][0] >= 0
    assert plan[-1][1] <= wav_duration_sec(str(wav)) + 0.05
    for start, end in plan:
        assert end > start
        assert (end - start) <= 16.5  # marge padding


def test_strip_prompt_leak_and_pick():
    from app.services.stt_quality import pick_best_transcript, strip_prompt_leak

    prompt = "مرافعة مغربية فصحى. السيد الرئيس، المحكمة، المدعى عليه."
    assert strip_prompt_leak("لا فرنسية ولا إنجليزية", prompt) == ""
    text, src = pick_best_transcript(
        "كلمة",
        "هذه جملة طويلة جدا من الاملاء الحقيقي للمحامي في الجلسة اليوم",
        confidence=40,
        needs_review=True,
    )
    assert src == "live"
    assert "الاملاء" in text
    assert "الجلسة" in text


def test_drop_bad_segments():
    from app.services.stt_quality import drop_bad_segments

    class Seg:
        def __init__(self, text, ns=0.1, lp=-0.2):
            self.text = text
            self.no_speech_prob = ns
            self.avg_logprob = lp

    kept = drop_bad_segments(
        [Seg("مرحبا بكم"), Seg("xxx", ns=0.95), Seg("ضعيف", lp=-1.5)]
    )
    assert len(kept) == 1
    assert kept[0].text == "مرحبا بكم"


def test_annotate_stt_guesses_keeps_and_adds_marks():
    from app.services.dictation_contradictions import annotate_stt_guesses

    src = "قضية عن التجار بالمخدرات امام المحكمة"
    pol = "قضية ‹الاتجار بالمخدرات› أمام المحكمة"
    out, guessed = annotate_stt_guesses(src, pol)
    assert "‹الاتجار بالمخدرات›" in out
    assert "الاتجار بالمخدرات" in guessed
