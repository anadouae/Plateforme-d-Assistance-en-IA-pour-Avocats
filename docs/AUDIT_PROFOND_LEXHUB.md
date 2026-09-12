# Audit profond LexHub — 2026-08-24T23:12:27.509146+00:00

**Score:** 7/7

## Verdicts
- OK — `stack_up`
- OK — `encryption_ok`
- OK — `pdf_decrypt_ok`
- OK — `llm_ok`
- OK — `synth_ok`
- OK — `stt_pipeline_reachable`
- OK — `site_200`

## Lecture rapide

- **IA saturée** = quotas free-tier (429) ou modèle HS : le routeur tourne Mistral→Groq→Gemini… ; si tous échouent, tu vois « تعذر التلخيص » même si le PDF est OK.
- **Voix** = Chrome Web Speech en live ; Whisper/Groq = chemin serveur (fichier / fallback).
- **Whisper** = moteur speech→text (cloud Groq large-v3 prioritaire, sinon local `small` CPU).

## Détails bruts
```
{
  "stack_up": true,
  "encryption_ok": true,
  "pdf_decrypt_ok": true,
  "llm_ok": true,
  "synth_ok": true,
  "stt_pipeline_reachable": true,
  "site_200": true
}
```

### LLM ping
```
ok True
provider mistral
reply OK
ms 285
```

### Synthèse doc cible
```
warning: The `fitz` API is deprecated and will be removed in future. Use `import pymupdf` instead.
summary_len 2320
is_fallback False
risks 8 broken_risks 0
dates ['4/1/2018']
ms 52371
head # **تلخيص ذكي: البيوعات العقارية القضائية**  ## **المحور الرئيسي** تناول البحث **البيوعات العقارية القضائية** كآلية تنفي
```

### STT
```
prefer_groq True
local_only False
groq_key True
whisper_enabled True
whisper_model small
groq_whisper_model whisper-large-v3
stt_provider none
stt_text_len 0
stt_ok True
```

### PDF cible + chiffrement
```
same True
b_len 44 w_len 44
b_prefix hCeR w_prefix hCeR
warning: The `fitz` API is deprecated and will be removed in future. Use `import pymupdf` instead.
doc_status indexed
ocr_score 92
chars 60308
magic b'%PDF-1.7'
is_pdf True
is_fernet_raw False
pages 37
```

### Erreurs récentes (30 min)
```
backend-1  | INFO:     172.18.0.1:34296 - "GET /api/team/requests HTTP/1.1" 401 Unauthorized
backend-1  | INFO:     172.18.0.1:34296 - "POST /api/auth/refresh HTTP/1.1" 200 OK
backend-1  | INFO:     172.18.0.1:34296 - "GET /api/auth/me HTTP/1.1" 200 OK
---
```