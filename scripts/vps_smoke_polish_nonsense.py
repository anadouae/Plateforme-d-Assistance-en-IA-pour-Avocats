#!/usr/bin/env python3
"""Smoke-test polish on VPS with nonsense Arabic STT loops."""
import json
import paramiko

PASSWORD = "P@s$wiy.O0p"
REMOTE_PY = r'''
import os, sys
sys.path.insert(0, "/app")
os.chdir("/app")

from app.services.dictation import polish_dictation, _stt_garbage_heavy
from app.core.config import settings

print("MODEL", settings.OPENAI_MODEL)
print("POLISH_LLM", settings.DICTATION_POLISH_USE_LLM)
print("FORCE_OPENAI", settings.LLM_FORCE_OPENAI)

raw = (
    "ان المرافعة الثانية الا المرافة التالية ان المرادعة التالية فان المرافعة ان المرافعة "
    "ان المرافعة الثانية الا المرافة التالية ان المرادعة التالية فان المرافعة ان المرافعة "
    "ان المرافعة الثانية الا المرافة التالية ان المرادعة التالية فان المرافعة ان المرافعة "
    "ان المرافعة الثانية الا المرافة التالية ان المرادعة التالية فان المرافعة ان المرافعة"
)
print("GARBAGE", _stt_garbage_heavy(raw))
print("RAW_LEN", len(raw))
out, provider = polish_dictation(raw, language="ar", source="audio")
print("PROVIDER", provider)
print("OUT_LEN", len(out or ""))
print("OUT", (out or "")[:500])
print("CHANGED", (out or "").strip() != raw.strip())
'''

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=90)
# Write script into container via docker exec stdin
cmd = (
    "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    "exec -T backend python - <<'PY'\n" + REMOTE_PY + "\nPY"
)
_, o, e = c.exec_command(cmd, timeout=180)
out = o.read().decode(errors="replace")
err = e.read().decode(errors="replace")
print(out)
if err.strip():
    print("---stderr---")
    print(err[-3000:])
c.close()
