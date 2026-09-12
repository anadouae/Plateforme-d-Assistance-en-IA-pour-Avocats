#!/usr/bin/env python3
"""Deploy full-text preview + extraction fixes; reextract biouaat PDF."""
from pathlib import Path
import paramiko
import time

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"
FILES = [
    "backend/app/api/documents.py",
    "backend/app/services/extraction.py",
    "backend/app/services/cloud_ocr.py",
    "backend/app/services/object_storage.py",
    "frontend/src/app/documents/[id]/page.tsx",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
_, o, e = c.exec_command("mkdir -p '/opt/sanad/frontend/src/app/documents/[id]'")
o.read(); e.read()
sftp = c.open_sftp()
for rel in FILES:
    sftp.put(str(ROOT / rel), f"{REMOTE}/{rel}")
    print("ok", rel)
sftp.close()

cmd = r"""
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d --force-recreate backend celery-worker 2>&1 | tail -20
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart frontend 2>&1 | tail -5
sleep 12
# verify preview is full text
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from pathlib import Path
p=Path('/app/app/api/documents.py').read_text()
assert 'raw_text[:2000]' not in p, 'still truncated'
print('preview_full_ok')
PY
curl -sf -o /dev/null -w 'web:%{http_code}\n' https://lexhub.space/
"""
_, o, e = c.exec_command(cmd, timeout=180)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace")[-500:])
c.close()
print("DONE")
