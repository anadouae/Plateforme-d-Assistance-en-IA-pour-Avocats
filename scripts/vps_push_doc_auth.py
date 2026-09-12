#!/usr/bin/env python3
"""Push doc/auth fixes to VPS."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = os.environ.get("VPS_HOST", "51.38.78.23")
USER = os.environ.get("VPS_USER", "root")
PASSWORD = os.environ.get("VPS_SSH_PASSWORD", "")

FILES = [
    "frontend/src/components/auth/auth-product-demo.tsx",
    "frontend/src/lib/export-official-doc.ts",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "frontend/src/components/redaction/document-workspace.tsx",
    "frontend/src/app/redaction/page.tsx",
    "backend/app/services/docx_export.py",
    "backend/app/services/dictation.py",
    "backend/app/services/plaidoirie_prompt.py",
    "backend/app/assets/armoiries-maroc.png",
]


def main() -> int:
    if not PASSWORD:
        print("Set VPS_SSH_PASSWORD", file=sys.stderr)
        return 1
    missing = [f for f in FILES if not (ROOT / f).is_file()]
    if missing:
        print("Missing:", *missing, sep="\n  ", file=sys.stderr)
        return 1

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=30, allow_agent=False, look_for_keys=False)
    sftp = client.open_sftp()
    for rel in FILES:
        local = ROOT / rel
        remote = f"/opt/sanad/{rel.replace(chr(92), '/')}"
        remote_dir = remote.rsplit("/", 1)[0]
        parts = remote_dir.split("/")
        cur = ""
        for p in parts:
            if not p:
                continue
            cur += f"/{p}"
            try:
                sftp.stat(cur)
            except OSError:
                sftp.mkdir(cur)
        print("upload", rel)
        sftp.put(str(local), remote)
    sftp.close()

    cmd = (
        "cd /opt/sanad && "
        "docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        "exec -T frontend sh -lc 'rm -rf /app/.next' && "
        "docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        "restart frontend backend"
    )
    print("restart frontend+backend …")
    _, stdout, stderr = client.exec_command(cmd, timeout=180)
    code = stdout.channel.recv_exit_status()
    print(stdout.read().decode(errors="replace")[-1200:])
    err = stderr.read().decode(errors="replace")[-600:]
    if err:
        print(err)
    client.close()
    print("done" if code == 0 else f"exit {code}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
