#!/usr/bin/env python3
"""Deploy finalize_arabic_polish fixes + API fallback."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/app/services/arabic_text_fix.py",
    "backend/app/services/dictation.py",
    "backend/app/api/dictation.py",
    "frontend/src/components/redaction/plea-assist-panel.tsx",
    "scripts/_smoke_finalize_polish.py",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
sftp = c.open_sftp()
for rel in FILES:
    sftp.put(str(ROOT / rel), f"/opt/sanad/{rel}")
    print("ok", rel)
sftp.close()

cmd = r"""
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart backend 2>&1 | tail -5
sleep 12
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python /app/../scripts/_smoke_finalize_polish.py 2>&1 || \
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python /opt/sanad/scripts/_smoke_finalize_polish.py 2>&1
curl -sf -o /dev/null -w 'web:%{http_code}\n' https://lexhub.space/
"""
_, o, e = c.exec_command(cmd, timeout=180)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("err", err[-600:])
c.close()
print("DONE")
