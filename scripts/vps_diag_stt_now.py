#!/usr/bin/env python3
import paramiko

PASSWORD = "P@s$wiy.O0p"
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
cmd = r"""
cd /opt/sanad
echo '=== ENV ==='
grep -E '^(WHISPER_|DICTATION_|GROQ_)' .env.vps 2>/dev/null | sed -E 's/(KEY|SECRET)=.*/\1=***/' || true
echo '=== CONTAINER ==='
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend printenv | grep -E 'WHISPER_|DICTATION_|GROQ_' | sed -E 's/(KEY|SECRET)=.*/\1=***/' || true
echo '=== CONFIG ==='
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.core.config import settings
print("model", settings.WHISPER_MODEL)
print("local_only", settings.DICTATION_LOCAL_ONLY)
print("denoise", settings.WHISPER_DENOISE)
print("gain", getattr(settings, "WHISPER_GAIN_DB", None))
print("groq", bool((settings.GROQ_API_KEY or "").strip()))
print("groq_model", getattr(settings, "GROQ_WHISPER_MODEL", None))
PY
echo '=== LOGS ==='
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml logs backend --tail 120 2>&1 | grep -iE 'STT|whisper|dictation|transcrib' | tail -40 || true
"""
_, o, e = c.exec_command(cmd, timeout=90)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("STDERR", err[-1500:])
c.close()
