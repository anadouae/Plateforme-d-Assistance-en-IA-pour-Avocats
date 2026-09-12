#!/usr/bin/env python3
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
sftp = c.open_sftp()
sftp.put(str(ROOT / "frontend/src/app/documents/page.tsx"), "/opt/sanad/frontend/src/app/documents/page.tsx")
sftp.close()
_, o, e = c.exec_command(
    "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart frontend 2>&1 | tail -5"
)
print(o.read().decode(errors="replace"))
c.close()
print("DONE")
