#!/usr/bin/env python3
"""Deploy Word bidi export fix."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/app/services/plaidoirie_layout.py",
    "backend/app/services/docx_export.py",
    "backend/app/services/pdf_export.py",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
sftp = c.open_sftp()
for rel in FILES:
    sftp.put(str(ROOT / rel), f"/opt/sanad/{rel}")
    print("ok", rel)
sftp.close()

cmd = """
cd /opt/sanad
CID=$(docker compose -f docker-compose.yml -f docker-compose.lexhub.yml ps -q backend)
for f in backend/app/services/plaidoirie_layout.py backend/app/services/docx_export.py backend/app/services/pdf_export.py; do
  docker cp /opt/sanad/$f ${CID}:/app/app/services/$(basename $f)
done
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart backend 2>&1 | tail -4
sleep 8
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python -c "from app.services.docx_export import _set_paragraph_rtl; print('ok')" 2>&1
"""
_, o, e = c.exec_command(cmd, timeout=120)
print(o.read().decode(errors="replace"))
if e.read().strip():
    print("err", e.read().decode()[-400:])
c.close()
print("DONE")
