#!/usr/bin/env python3
import paramiko
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
rel = "backend/app/services/dictation_contradictions.py"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
sftp = c.open_sftp()
sftp.put(str(ROOT / rel), f"/opt/sanad/{rel}")
sftp.close()
print("ok", rel)
_, o, e = c.exec_command(
    "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart backend 2>&1 | tail -5",
    timeout=120,
)
print(o.read().decode(errors="replace"))
c.close()
