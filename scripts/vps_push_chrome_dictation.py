#!/usr/bin/env python3
import time
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=60, banner_timeout=90)
sftp = c.open_sftp()
sftp.put(
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "/opt/sanad/frontend/src/components/redaction/plaidoirie-workspace.tsx",
)
sftp.close()
_, o, _ = c.exec_command(
    "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart frontend 2>&1"
)
print(o.read().decode(errors="replace"))
c.close()
print("ok")
