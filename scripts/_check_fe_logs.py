#!/usr/bin/env python3
from pathlib import Path
import paramiko

PASSWORD = "P@s$wiy.O0p"
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60)
_, o, _ = c.exec_command(
    "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml logs frontend --tail 80 2>&1",
    timeout=90,
)
print(o.read().decode(errors="replace")[-4000:])
c.close()
