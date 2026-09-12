#!/usr/bin/env python3
"""Push latest plaidoirie UX + related FE files to lexhub VPS."""
from __future__ import annotations

import os
import paramiko

HOST = os.environ.get("VPS_HOST", "51.38.78.23")
USER = os.environ.get("VPS_USER", "root")
PASSWORD = os.environ.get("VPS_SSH_PASSWORD", "P@s$wiy.O0p")
REMOTE = "/opt/sanad"

FILES = [
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "frontend/src/components/redaction/template-picker.tsx",
    "frontend/src/components/redaction/plea-step-carousel.tsx",
    "frontend/src/styles/sanad-ui.css",
    "frontend/src/app/agenda/page.tsx",
]


def main() -> int:
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(
        HOST,
        username=USER,
        password=PASSWORD,
        timeout=60,
        allow_agent=False,
        look_for_keys=False,
    )
    sftp = c.open_sftp()
    for rel in FILES:
        local = rel.replace("\\", "/")
        remote = f"{REMOTE}/{local}"
        sftp.put(local, remote)
        print("ok", local)
    sftp.close()

    cmd = (
        f"cd {REMOTE} && "
        "docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        "restart frontend 2>&1 | tail -10"
    )
    _, o, e = c.exec_command(cmd, timeout=180)
    code = o.channel.recv_exit_status()
    print(o.read().decode(errors="replace")[-1500:])
    err = e.read().decode(errors="replace")[-500:]
    if err.strip():
        print(err)
    c.close()
    print("done" if code == 0 else f"exit {code}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
