#!/usr/bin/env python3
"""Deploy admin cabinet purge + FE."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/app/services/cabinet_purge.py",
    "backend/app/api/admin.py",
    "backend/app/schemas/__init__.py",
    "frontend/src/lib/api.ts",
    "frontend/src/app/admin/cabinets/page.tsx",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
sftp = c.open_sftp()
for rel in FILES:
    remote = f"/opt/sanad/{rel}"
    parts = remote.rsplit("/", 1)[0]
    try:
        sftp.stat(parts)
    except OSError:
        c.exec_command(f"mkdir -p {parts}")
    sftp.put(str(ROOT / rel), remote)
    print("ok", rel)
sftp.close()

cmd = r"""
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml --env-file .env.vps restart backend frontend 2>&1 | tail -10
sleep 18
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python -c "from app.services.cabinet_purge import purge_cabinet; print('purge_import_ok')" 2>&1
curl -sf -o /dev/null -w 'admin_page:%{http_code}\n' https://lexhub.space/admin/cabinets || true
curl -sf -o /dev/null -w 'api:%{http_code}\n' https://lexhub.space/api/billing/plans || true
"""
_, o, e = c.exec_command(cmd, timeout=180)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("err", err[-1500:])
c.close()
print("DONE")
