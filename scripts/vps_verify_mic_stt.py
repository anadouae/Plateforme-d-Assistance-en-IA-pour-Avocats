#!/usr/bin/env python3
import time
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=60, banner_timeout=120)
time.sleep(20)
cmd = r"""
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml ps
echo ---
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.core.config import settings
print("denoise", settings.WHISPER_DENOISE)
print("gain", settings.WHISPER_GAIN_DB)
from app.services.dictation import POLISH_SYSTEM_AR_AUDIO, polish_dictation
src = open("/app/app/services/dictation.py", encoding="utf-8").read()
print("no_rewrite_prompt", "أعد كتابته" not in src)
print("has_fidelity_prompt", "صحّح الإملاء والترقيم فقط" in src)
PY
echo ---
curl -sf -o /dev/null -w "web:%{http_code}\n" https://lexhub.space/ || echo web_fail
curl -sf -o /dev/null -w "api:%{http_code}\n" http://127.0.0.1:8001/health/live || echo api_fail
echo ---
grep -n "micTooQuiet\|audioBitsPerSecond\|WHISPER_GAIN" \
  /opt/sanad/frontend/src/hooks/use-whisper-dictation.ts \
  /opt/sanad/backend/app/core/config.py | head -20
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml logs backend --tail 20
"""
_, o, e = c.exec_command(cmd, timeout=120)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("STDERR:", err[-2000:])
c.close()
