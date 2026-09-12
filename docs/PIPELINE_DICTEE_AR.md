# Pipeline dictée arabe juridique — Sanad

## Objectif
Maximiser la **précision** du تفريغ en **عربية فصحى** pour la مرافعة, en local (Docker / Whisper), sans API STT payante.

## État actuel vs cible

| Étape | Aujourd’hui | Cible | Phase |
|-------|-------------|-------|-------|
| Capture | MediaRecorder WebM | idem | 1 ✓ |
| Signal | ffmpeg WAV 16 kHz + denoise léger | soft denoise | **2 ✓** |
| VAD | énergie (RMS) pré-filtre | Silero-like léger sans download | **2 ✓** |
| Segmentation | chunks ≤ 15 s si audio > 22 s | fusion anti-doublon | **2 ✓** |
| Whisper | prompt juridique + beam AR | confiance avg_logprob | **1 ✓** |
| Lexique | `arabic_text_fix` | phonétique MA | **1 ✓** |
| Confiance | score + needs_review + chunks | badge UI | **1–2 ✓** |

## Architecture livrée

```
MediaRecorder (+ aperçu Chrome)
  → POST /api/dictation/transcribe
Serveur:
  ffmpeg → WAV 16k mono
  → soft denoise (optionnel)
  → VAD énergie → plan chunks ≤15s (si durée >22s)
  → Whisper par chunk (prompt juridique, beam=5 AR)
  → fusion textes + moyenne confiance
  → repair_arabic_stt
UI:
  badge ثقة % · راجعوا التفريغ · N مقاطع
```

## Config

- `WHISPER_CHUNK_SEC=15`
- `WHISPER_CHUNK_MIN_SEC=22`
- `WHISPER_DENOISE=true`

## Fichiers

- `backend/app/services/audio_chunks.py`
- `backend/app/services/whisper_stt.py`
- `backend/app/services/arabic_text_fix.py`
- `backend/tests/test_dictation_pipeline.py`
- `frontend/.../plaidoirie-workspace.tsx`

## Tests

```bash
cd backend && python -m pytest tests/test_dictation_pipeline.py -q
```

## Contrainte VPS (~2 Go)

Rester sur `tiny` / `base` / `small`. Pas de modèle `medium` ni Silero torchhub (téléchargement). Le VAD énergie est volontairement léger.
