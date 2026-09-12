#!/usr/bin/env python3
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"
rel = "frontend/src/components/layout/topbar-action-icons.tsx"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=90)
sftp = c.open_sftp()
sftp.put(str(ROOT / rel), f"{REMOTE}/{rel}")
sftp.close()
print("sftp ok")
_, o, e = c.exec_command(
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart frontend",
    timeout=120,
)
print(o.read().decode(errors="replace")[-1000:])
print(e.read().decode(errors="replace")[-500:])
print("exit", o.channel.recv_exit_status())
c.close()
print("DONE")
