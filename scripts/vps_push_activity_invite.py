#!/usr/bin/env python3
"""Deploy activity archives + invite email + join pipeline + avocat admin."""
from __future__ import annotations

from pathlib import Path
import paramiko
import time

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

FILES = [
    "backend/alembic/versions/021_activity_archives.py",
    "backend/app/models/__init__.py",
    "backend/app/schemas/__init__.py",
    "backend/app/services/activity_archive.py",
    "backend/app/services/email.py",
    "backend/app/api/workspace.py",
    "backend/app/api/team.py",
    "frontend/src/lib/roles.ts",
    "frontend/src/lib/api.ts",
    "frontend/src/app/activity/page.tsx",
    "frontend/src/components/settings/team-panel.tsx",
    "frontend/src/components/auth/join-pipeline.tsx",
    "frontend/src/components/auth/unified-auth.tsx",
    "frontend/src/components/layout/app-shell.tsx",
    "frontend/src/styles/sanad-ui.css",
]


def main() -> int:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=90)
    sftp = client.open_sftp()
    for rel in FILES:
        local = ROOT / rel
        if not local.exists():
            print("MISSING", rel)
            continue
        remote = f"{REMOTE}/{rel}"
        _, o, _ = client.exec_command(f"mkdir -p $(dirname {remote})")
        o.channel.recv_exit_status()
        sftp.put(str(local), remote)
        print("ok", rel)
    sftp.close()

    cmds = [
        f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        f"exec -T backend alembic upgrade head 2>&1 | tail -25",
        f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        f"up -d --force-recreate backend frontend 2>&1 | tail -20",
    ]
    for cmd in cmds:
        _, o, e = client.exec_command(cmd, timeout=300)
        print(o.read().decode(errors="replace"))
        err = e.read().decode(errors="replace")
        if err.strip():
            print(err[:800])
        time.sleep(2)
    client.close()
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
