#!/usr/bin/env python3
"""Deploy docx header fix (cabinet left, kingdom right)."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = ["backend/app/services/docx_export.py"]

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
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d --build backend 2>&1 | tail -12
sleep 12
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python -c "from app.services.docx_export import build_plaidoirie_docx; print('import ok')" 2>&1
"""
_, o, e = c.exec_command(cmd, timeout=600)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("err", err[-800:])
c.close()
print("DONE")
