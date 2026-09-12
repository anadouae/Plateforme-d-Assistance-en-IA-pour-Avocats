#!/usr/bin/env python3
"""Deploy: intelligent polish (no dumb form-edit panel)."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/app/services/dictation_assist.py",
    "backend/app/services/dictation_contradictions.py",
    "backend/app/services/dictation.py",
    "backend/app/services/arabic_text_fix.py",
    "frontend/src/components/redaction/plea-assist-panel.tsx",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "scripts/_smoke_form_edits.py",
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
# Hot-copy backend sources + restart
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml cp backend/app/services/dictation_assist.py backend:/app/app/services/dictation_assist.py
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml cp backend/app/services/dictation_contradictions.py backend:/app/app/services/dictation_contradictions.py
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml cp backend/app/services/dictation.py backend:/app/app/services/dictation.py
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml cp backend/app/services/arabic_text_fix.py backend:/app/app/services/arabic_text_fix.py
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart backend 2>&1 | tail -3
# Rebuild frontend (TSX changes)
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml build frontend 2>&1 | tail -20
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d frontend 2>&1 | tail -8
sleep 14
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml cp scripts/_smoke_form_edits.py backend:/tmp/_smoke_form_edits.py
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T -e PYTHONPATH=/app -w /app backend python /tmp/_smoke_form_edits.py 2>&1
curl -sf -o /dev/null -w 'web:%{http_code}\n' https://lexhub.space/
"""
_, o, e = c.exec_command(cmd, timeout=900)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("err", err[-1200:])
c.close()
print("DONE")
