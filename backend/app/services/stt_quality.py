"""Helpers pour choisir / nettoyer le texte STT (anti-hallucination)."""

from __future__ import annotations

import re


def arabic_ratio(text: str) -> float:
    t = text or ""
    if not t:
        return 0.0
    ar = sum(1 for c in t if "\u0600" <= c <= "\u06FF")
    letters = sum(1 for c in t if c.isalpha() or "\u0600" <= c <= "\u06FF")
    return ar / max(1, letters)


def strip_prompt_leak(text: str, prompt: str) -> str:
    """
    Retire les fuites du initial_prompt Whisper (phrases inventées non dites).
    Si le texte ressemble trop au prompt seul → vide.
    """
    t = (text or "").strip()
    if not t or not prompt:
        return t
    # Phrases-clés du prompt souvent hallucinées en bloc
    leak_phrases = [
        "لا فرنسية ولا إنجليزية",
        "العربية الفصحى فقط",
        "و السلام عليكم ورحمة الله",
    ]
    for p in leak_phrases:
        if p in t and len(t) < len(p) + 40:
            return ""
        t = t.replace(p, " ")
    t = re.sub(r"\s{2,}", " ", t).strip()
    # Si >55% des tokens du résultat sont déjà dans le prompt → soupçon fuite
    prompt_tokens = set(re.findall(r"[\u0600-\u06FF]{3,}", prompt))
    text_tokens = re.findall(r"[\u0600-\u06FF]{3,}", t)
    if len(text_tokens) >= 6:
        hits = sum(1 for w in text_tokens if w in prompt_tokens)
        if hits / len(text_tokens) >= 0.92 and len(t) < 120:
            # Uniquement si quasi = prompt seul
            return ""
    return t


def drop_bad_segments(segments: list) -> list:
    """Ignore segments silence / très peu fiables (source d’inventions)."""
    keep = []
    for seg in segments:
        text = (getattr(seg, "text", None) or "").strip()
        if not text:
            continue
        ns = getattr(seg, "no_speech_prob", None)
        lp = getattr(seg, "avg_logprob", None)
        if ns is not None and float(ns) > 0.75:
            continue
        if lp is not None and float(lp) < -1.15:
            continue
        words = text.split()
        # Boucles type "شكرا شكرا شكرا" / "والسلام عليكم" répété
        if len(set(words)) <= 2 and len(words) >= 5:
            continue
        if len(words) >= 8 and len(set(words)) <= 3:
            continue
        keep.append(seg)
    return keep


def confidence_from_segments(segments: list) -> tuple[int, bool, float | None]:
    """Score 0–100 + needs_review depuis avg_logprob / no_speech_prob Whisper."""
    if not segments:
        return 0, True, None
    lps: list[float] = []
    nss: list[float] = []
    for seg in segments:
        lp = getattr(seg, "avg_logprob", None)
        ns = getattr(seg, "no_speech_prob", None)
        if lp is not None:
            lps.append(float(lp))
        if ns is not None:
            nss.append(float(ns))
    avg_lp = sum(lps) / len(lps) if lps else None
    avg_ns = sum(nss) / len(nss) if nss else 0.0
    # Whisper: logprob ~0 = bon, <-1 = mauvais
    if avg_lp is None:
        score = 45
    else:
        score = int(max(0, min(100, round(100 + avg_lp * 55))))
    if avg_ns > 0.55:
        score = min(score, 48)
    needs_review = score < 58 or avg_ns > 0.65
    return score, needs_review, avg_lp


# Alias historique (tests / anciens imports)
_confidence_from_segments = confidence_from_segments


def pick_best_transcript(whisper: str, live: str, *, confidence: int | None, needs_review: bool) -> tuple[str, str]:
    """
    Retourne (texte, source) — source = whisper|live|merge.
    Préfère le live si Whisper a tout perdu / inventé.
    """
    w = (whisper or "").strip()
    l = (live or "").strip()
    if not w and not l:
        return "", "none"
    if not w:
        return l, "live"
    if not l:
        return w, "whisper"

    w_words = len(w.split())
    l_words = len(l.split())
    conf = confidence if confidence is not None else 50

    # Whisper beaucoup plus court → a perdu des mots
    if l_words >= w_words + 8 and l_words > int(w_words * 1.4):
        if arabic_ratio(l) >= 0.45:
            return l, "live"

    # Confiance faible : garder le plus long fidèle
    if needs_review or conf < 55:
        if l_words >= w_words and arabic_ratio(l) >= arabic_ratio(w):
            return l, "live"

    # Live très court / bruit → whisper
    if l_words < 4 and w_words >= 4:
        return w, "whisper"

    return w, "whisper"
