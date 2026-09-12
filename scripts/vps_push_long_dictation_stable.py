#!/usr/bin/env python3
"""Push: dictée longue stable + UX + STT local only."""
import paramiko
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/opt/sanad"
FILES = [
    "backend/app/core/config.py",
    "backend/app/api/dictation.py",
    "backend/app/services/whisper_stt.py",
    "frontend/src/hooks/use-whisper-dictation.ts",
    "frontend/src/lib/api.ts",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "frontend/src/components/redaction/plea-step-carousel.tsx",
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
grep -q '^DICTATION_LOCAL_ONLY=' .env && sed -i 's/^DICTATION_LOCAL_ONLY=.*/DICTATION_LOCAL_ONLY=true/' .env || echo 'DICTATION_LOCAL_ONLY=true' >> .env
grep -q '^WHISPER_TIMEOUT_SEC=' .env && sed -i 's/^WHISPER_TIMEOUT_SEC=.*/WHISPER_TIMEOUT_SEC=1800/' .env || echo 'WHISPER_TIMEOUT_SEC=1800' >> .env
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d --force-recreate backend 2>&1
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart frontend 2>&1
sleep 6
docker exec sanad-backend-1 python -c "from app.core.config import settings; print('local', settings.DICTATION_LOCAL_ONLY, 'model', settings.WHISPER_MODEL, 'timeout', settings.WHISPER_TIMEOUT_SEC, 'chunk', settings.WHISPER_CHUNK_ENABLED, settings.WHISPER_CHUNK_SEC, settings.WHISPER_CHUNK_MIN_SEC)"
"""
_, o, e = c.exec_command(cmd, timeout=180)
print(o.read().decode(errors="replace")[-2500:])
print(e.read().decode(errors="replace")[-400:])
c.close()
print("done")
