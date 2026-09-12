#!/usr/bin/env python3
"""Deploy Word export fixes: roles, numbering, layout, closing."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/app/services/plaidoirie_postprocess.py",
    "backend/app/services/plaidoirie_layout.py",
    "backend/app/services/docx_export.py",
    "backend/app/services/pdf_export.py",
    "backend/app/services/dictation.py",
    "backend/app/services/plaidoirie_prompt.py",
    "backend/app/services/arabic_text_fix.py",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "scripts/_smoke_export_postprocess.py",
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
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml build backend frontend 2>&1 | tail -20
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d backend frontend 2>&1 | tail -8
sleep 14
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python /app/../scripts/_smoke_export_postprocess.py 2>&1 || true
curl -sf -o /dev/null -w 'web:%{http_code}\n' https://lexhub.space/
"""
_, o, e = c.exec_command(cmd, timeout=600)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("err", err[-800:])
c.close()
print("DONE")
