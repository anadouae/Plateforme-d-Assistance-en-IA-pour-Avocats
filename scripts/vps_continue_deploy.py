#!/usr/bin/env python3
"""Upload changed files and run compose on VPS."""
import os
from pathlib import Path

import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = os.environ.get("VPS_SSH_PASSWORD", "")

FILES = [
    "docker-compose.lexhub.yml",
    "deploy/Caddyfile.lexhub",
    "scripts/vps_compose_up.sh",
    "frontend/src/app/documents/[id]/page.tsx",
    "frontend/src/app/admin/benchmark/page.tsx",
]

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username="root", password=PASSWORD, timeout=30, allow_agent=False, look_for_keys=False)
sftp = client.open_sftp()
for rel in FILES:
    local = ROOT / rel
    remote = f"/opt/sanad/{rel.replace(chr(92), '/')}"
    print(f"upload {rel}")
    sftp.put(str(local), remote)
sftp.close()

_, stdout, stderr = client.exec_command("chmod +x /opt/sanad/scripts/vps_compose_up.sh && bash /opt/sanad/scripts/vps_compose_up.sh", timeout=3600)
code = stdout.channel.recv_exit_status()
out = stdout.read().decode(errors="replace")
err = stderr.read().decode(errors="replace")
print(out[-12000:])
if err:
    print(err[-4000:])
print("exit", code)
client.close()
raise SystemExit(code)
