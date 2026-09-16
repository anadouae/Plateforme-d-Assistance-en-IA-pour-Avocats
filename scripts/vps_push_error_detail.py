#!/usr/bin/env python3
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "frontend/src/app/error.tsx",
    "frontend/src/components/layout/admin-shell.tsx",
    "frontend/src/app/admin/page.tsx",
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
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T frontend sh -c 'rm -rf /app/.next'
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart frontend
sleep 22
curl -sf -o /dev/null -w 'admin:%{http_code}\n' https://lexhub.space/admin
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml logs frontend --tail 15 2>&1 | tail -12
"""
_, o, e = c.exec_command(cmd, timeout=240)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("err", err[-500:])
c.close()
print("DONE")
