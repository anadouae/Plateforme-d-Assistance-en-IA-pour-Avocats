#!/usr/bin/env python3
"""Quick VPS probe via SSH (password via env VPS_SSH_PASSWORD)."""
import os
import sys

import paramiko

HOST = os.environ.get("VPS_HOST", "51.38.78.23")
USER = os.environ.get("VPS_USER", "root")
PASSWORD = os.environ.get("VPS_SSH_PASSWORD", "")

if not PASSWORD:
    print("Set VPS_SSH_PASSWORD", file=sys.stderr)
    sys.exit(1)

cmds = [
    "uname -a",
    "df -h /",
    "free -h",
    "docker --version 2>/dev/null || echo NO_DOCKER",
    "docker compose version 2>/dev/null || echo NO_COMPOSE",
    "which git caddy nginx certbot 2>/dev/null; ls /opt /srv 2>/dev/null",
]

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASSWORD, timeout=30, allow_agent=False, look_for_keys=False)

for cmd in cmds:
    print(f"\n>>> {cmd}")
    _, stdout, stderr = client.exec_command(cmd, timeout=60)
    out = stdout.read().decode(errors="replace").strip()
    err = stderr.read().decode(errors="replace").strip()
    print(out or err or "(empty)")

client.close()
print("\nSSH OK")
