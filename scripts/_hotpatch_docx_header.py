#!/usr/bin/env python3
"""Hot-patch docx_export into running backend container (no rebuild)."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
LOCAL = ROOT / "backend/app/services/docx_export.py"
REMOTE = "/opt/sanad/backend/app/services/docx_export.py"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
sftp = c.open_sftp()
sftp.put(str(LOCAL), REMOTE)
print("ok pushed", REMOTE)
sftp.close()

cmd = """
cd /opt/sanad
CID=$(docker compose -f docker-compose.yml -f docker-compose.lexhub.yml ps -q backend)
echo backend_cid=$CID
docker cp /opt/sanad/backend/app/services/docx_export.py ${CID}:/app/app/services/docx_export.py
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart backend 2>&1 | tail -5
sleep 8
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python -c "
from app.services.docx_export import _add_letterhead, build_plaidoirie_docx
import inspect
src = inspect.getsource(_add_letterhead)
assert 'المملكة المغربية' in src and 'gauche' in src
print('letterhead ok')
" 2>&1
curl -sf -o /dev/null -w 'web:%{http_code}\\n' https://lexhub.space/
"""
_, o, e = c.exec_command(cmd, timeout=120)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("err", err[-800:])
c.close()
print("DONE")
