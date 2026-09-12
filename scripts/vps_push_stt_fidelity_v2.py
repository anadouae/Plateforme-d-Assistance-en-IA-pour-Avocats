#!/usr/bin/env python3
"""Deploy fidelity STT fix v2: raw mic + no polish LLM + groq."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"
FILES = [
    "backend/app/core/config.py",
    "backend/app/services/whisper_stt.py",
    "backend/app/services/dictation.py",
    "frontend/src/hooks/use-whisper-dictation.ts",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "docker-compose.lexhub.yml",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
sftp = c.open_sftp()
for rel in FILES:
    sftp.put(str(ROOT / rel), f"{REMOTE}/{rel}")
    print("ok", rel)
sftp.close()

env = f"""
cd {REMOTE}
for kv in 'DICTATION_LOCAL_ONLY=false' 'DICTATION_STT_PREFER_GROQ=true' 'DICTATION_POLISH_USE_LLM=false' 'WHISPER_DENOISE=false' 'WHISPER_GAIN_DB=10.0'; do
  k=${{kv%%=*}}
  if grep -q "^$k=" .env.vps; then sed -i "s|^$k=.*|$kv|" .env.vps; else echo "$kv" >> .env.vps; fi
done
grep -E '^(DICTATION_|WHISPER_GAIN|WHISPER_DENOISE)' .env.vps
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml --env-file .env.vps up -d --force-recreate backend frontend 2>&1 | tail -30
sleep 15
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.core.config import settings
from app.services.dictation import polish_dictation
print("local_only", settings.DICTATION_LOCAL_ONLY)
print("prefer_groq", settings.DICTATION_STT_PREFER_GROQ)
print("polish_llm", settings.DICTATION_POLISH_USE_LLM)
print("gain", settings.WHISPER_GAIN_DB)
t,p = polish_dictation("السيد الرئيس امام المحكمه", language="ar", source="audio")
print("polish", p, t)
src=open("/opt/sanad/frontend/src/hooks/use-whisper-dictation.ts",encoding="utf-8").read()
print("raw_mic", "createMediaStreamDestination" not in src)
print("bitrate256", "256_000" in src)
PY
curl -sf -o /dev/null -w "web:%{{http_code}} api:" https://lexhub.space/
curl -sf -o /dev/null -w "%{{http_code}}\\n" http://127.0.0.1:8001/health/live
"""
_, o, e = c.exec_command(env, timeout=240)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("ERR", err[-1500:])
c.close()
print("DONE")
