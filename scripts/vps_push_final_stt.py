#!/usr/bin/env python3
import paramiko
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/opt/sanad"
PASS = "P@s$wiy.O0p"
FILES = [
    "docker-compose.lexhub.yml",
    "backend/app/services/whisper_stt.py",
    "backend/app/services/stt_quality.py",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "frontend/src/hooks/use-speech-input.ts",
    "frontend/src/hooks/use-whisper-dictation.ts",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASS, timeout=60, banner_timeout=90)
sftp = c.open_sftp()
for rel in FILES:
    sftp.put(str(ROOT / rel), f"{REMOTE}/{rel}")
    print("ok", rel)
sftp.close()

# Force env + recreate
cmds = f"""
cd {REMOTE}
# ensure .env has fallback off local-only
grep -q '^DICTATION_LOCAL_ONLY=' .env 2>/dev/null && sed -i 's/^DICTATION_LOCAL_ONLY=.*/DICTATION_LOCAL_ONLY=false/' .env || echo 'DICTATION_LOCAL_ONLY=false' >> .env
grep -q '^WHISPER_ENABLED=' .env || echo 'WHISPER_ENABLED=true' >> .env
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d --force-recreate backend 2>&1
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart frontend 2>&1
sleep 10
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend printenv | grep -E 'DICTATION_LOCAL|WHISPER_|GROQ_API'
# quick groq availability check
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python -c "
from app.core.config import settings
print('local_only', settings.DICTATION_LOCAL_ONLY)
print('whisper', settings.WHISPER_ENABLED, settings.WHISPER_MODEL)
print('groq_key', bool((settings.GROQ_API_KEY or '').strip()))
" 2>&1
"""
_, o, e = c.exec_command(cmds, timeout=180)
print(o.read().decode(errors="replace")[-2500:])
err = e.read().decode(errors="replace")
if err.strip():
    print("stderr", err[-800:])
c.close()
print("done")
