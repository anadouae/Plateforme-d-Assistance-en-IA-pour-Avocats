#!/usr/bin/env python3
"""Deploy admin mobile header + dock + i18n."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "frontend/src/styles/sanad-ui.css",
    "frontend/src/lib/i18n/translations.ts",
    "frontend/src/components/layout/admin-shell.tsx",
    "frontend/src/app/admin/page.tsx",
    "frontend/src/app/admin/cabinets/page.tsx",
    "frontend/src/app/admin/plans/page.tsx",
    "frontend/src/app/admin/leads/page.tsx",
    "frontend/src/app/admin/logs/page.tsx",
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
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart frontend 2>&1 | tail -10
sleep 18
curl -sf -o /dev/null -w 'web:%{http_code}\n' https://lexhub.space/
curl -sf -o /dev/null -w 'admin:%{http_code}\n' https://lexhub.space/admin || true
"""
_, o, e = c.exec_command(cmd, timeout=240)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("err", err[-600:])
c.close()
print("DONE")
