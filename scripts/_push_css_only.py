#!/usr/bin/env python3
from pathlib import Path
import time
import paramiko

ROOT = Path(__file__).resolve().parents[1]
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=45)
sftp = c.open_sftp()
sftp.put(str(ROOT / "frontend/src/styles/sanad-ui.css"), "/opt/sanad/frontend/src/styles/sanad-ui.css")
sftp.close()
print("css ok")
_, o, e = c.exec_command(
    "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart frontend 2>&1 | tail -8",
    timeout=120,
)
print(o.read().decode(errors="replace"))
time.sleep(8)
c.close()
print("DONE")
