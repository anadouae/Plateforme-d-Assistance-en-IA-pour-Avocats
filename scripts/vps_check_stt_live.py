#!/usr/bin/env python3
"""Inspect latest dictation logs and test Groq vs local Whisper on sample audio."""
from __future__ import annotations

import paramiko

PASSWORD = "P@s$wiy.O0p"
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)

cmd = r"""
cd /opt/sanad
echo '=== LAST TRANSCRIBE LOGS ==='
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml logs backend --since 30m 2>&1 | grep -iE 'STT|groq|whisper|dictation|transcrib|polish|hallucin' | tail -60

echo '=== RUNTIME FLAGS ==='
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend printenv | grep -E 'DICTATION_|WHISPER_|GROQ_WHISPER|GROQ_API' | sed -E 's/(KEY)=.*/\1=***/'

echo '=== QUICK GROQ PING ==='
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.core.config import settings
print("prefer", settings.DICTATION_STT_PREFER_GROQ, "local_only", settings.DICTATION_LOCAL_ONLY)
print("key", bool(settings.GROQ_API_KEY), "model", settings.GROQ_WHISPER_MODEL)
# tiny silent wav should return empty / none, not invent text
import struct, wave, io, tempfile, os
from app.services.whisper_stt import _transcribe_groq, transcribe_audio_bytes
buf=io.BytesIO()
with wave.open(buf,'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
    # 1s of near-silence
    w.writeframes(struct.pack('<'+'h'*16000, *([0]*16000)))
data=buf.getvalue()
t,p=_transcribe_groq(data,'silence.wav','ar')
print('groq_silence', repr(t), p)
PY
"""
_, o, e = c.exec_command(cmd, timeout=180)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("STDERR:", err[-2000:])
c.close()
