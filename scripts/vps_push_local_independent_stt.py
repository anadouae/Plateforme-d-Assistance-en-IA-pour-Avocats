#!/usr/bin/env python3
"""Dictée 100% locale — plus de Groq STT / quotas."""
import paramiko
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/opt/sanad"
FILES = [
    "backend/app/services/whisper_stt.py",
    "backend/app/core/config.py",
    "docker-compose.lexhub.yml",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=60, banner_timeout=90)
sftp = c.open_sftp()
for rel in FILES:
    sftp.put(str(ROOT / rel), f"{REMOTE}/{rel}")
    print("ok", rel)
sftp.close()

cmd = f"""
cd {REMOTE}
sed -i 's/^DICTATION_LOCAL_ONLY=.*/DICTATION_LOCAL_ONLY=true/' .env 2>/dev/null || echo 'DICTATION_LOCAL_ONLY=true' >> .env
grep -q '^DICTATION_LOCAL_ONLY=' .env || echo 'DICTATION_LOCAL_ONLY=true' >> .env
# force true even if line missing/wrong
grep -q '^DICTATION_LOCAL_ONLY=true' .env || (sed -i '/^DICTATION_LOCAL_ONLY=/d' .env; echo 'DICTATION_LOCAL_ONLY=true' >> .env)
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d --force-recreate backend 2>&1
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart frontend 2>&1
sleep 6
docker exec sanad-backend-1 python -c "from app.core.config import settings; print('local_only', settings.DICTATION_LOCAL_ONLY); print('model', settings.WHISPER_MODEL)"
"""
_, o, e = c.exec_command(cmd, timeout=180)
print(o.read().decode(errors="replace")[-2500:])
print(e.read().decode(errors="replace")[-400:])
c.close()
print("done")
