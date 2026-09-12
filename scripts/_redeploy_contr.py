#!/usr/bin/env python3
import paramiko
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=60)
sftp = c.open_sftp()
sftp.put(
    str(ROOT / "backend/app/services/dictation_contradictions.py"),
    "/opt/sanad/backend/app/services/dictation_contradictions.py",
)
sftp.put(str(ROOT / "scripts/_smoke_polish_contr.py"), "/opt/sanad/backend/_smoke_polish_contr.py")
sftp.close()
_, o, e = c.exec_command(
    "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart backend 2>&1 | tail -4; "
    "sleep 12; docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python /app/_smoke_polish_contr.py 2>&1",
    timeout=120,
)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace")[-400:])
c.close()
