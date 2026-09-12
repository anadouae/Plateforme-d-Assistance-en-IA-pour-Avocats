#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

import paramiko

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    "frontend/src/styles/sanad-ui.css",
    "frontend/src/components/layout/app-shell.tsx",
    "frontend/src/components/layout/topbar-action-icons.tsx",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "frontend/src/components/settings/team-panel.tsx",
    "frontend/src/app/team/page.tsx",
]


def main() -> int:
    password = os.environ.get("VPS_SSH_PASSWORD", "")
    if not password:
        print("Set VPS_SSH_PASSWORD", file=sys.stderr)
        return 1
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        os.environ.get("VPS_HOST", "51.38.78.23"),
        username=os.environ.get("VPS_USER", "root"),
        password=password,
        timeout=30,
        allow_agent=False,
        look_for_keys=False,
    )
    sftp = client.open_sftp()
    for rel in FILES:
        local = ROOT / rel
        if not local.is_file():
            print("missing", rel, file=sys.stderr)
            return 1
        remote = f"/opt/sanad/{rel}"
        cur = ""
        for part in remote.rsplit("/", 1)[0].split("/"):
            if not part:
                continue
            cur += f"/{part}"
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
        "docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart frontend"
    )
    _, stdout, stderr = client.exec_command(cmd, timeout=180)
    code = stdout.channel.recv_exit_status()
    print(stdout.read().decode(errors="replace")[-800:])
    err = stderr.read().decode(errors="replace")[-400:]
    if err:
        print(err)
    client.close()
    print("done" if code == 0 else f"exit {code}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
