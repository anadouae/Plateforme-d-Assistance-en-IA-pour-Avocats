#!/usr/bin/env python3
"""Deploy collab plaidoirie + migrate 018."""
from __future__ import annotations

from pathlib import Path
import paramiko
import time

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

FILES = [
    "backend/alembic/versions/018_plaidoirie_draft_status.py",
    "backend/app/models/__init__.py",
    "backend/app/schemas/__init__.py",
    "backend/app/api/plaidoirie_templates.py",
    "frontend/src/lib/api.ts",
    "frontend/src/app/redaction/page.tsx",
    "frontend/src/components/layout/app-sidebar.tsx",
    "frontend/src/components/layout/app-shell.tsx",
    "frontend/src/styles/sanad-ui.css",
    "frontend/src/lib/onboarding-steps.ts",
    "frontend/src/lib/i18n/translations.ts",
]


def main() -> int:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=90)
    sftp = client.open_sftp()
    for rel in FILES:
        remote = f"{REMOTE}/{rel}"
        _, o, _ = client.exec_command(f"mkdir -p $(dirname {remote})")
        o.channel.recv_exit_status()
        sftp.put(str(ROOT / rel), remote)
        print("ok", rel)
    sftp.close()

    cmds = [
        f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        f"exec -T backend alembic upgrade head 2>&1 | tail -20",
        f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        f"up -d --force-recreate backend frontend 2>&1 | tail -15",
    ]
    for cmd in cmds:
        _, o, e = client.exec_command(cmd, timeout=240)
        print(o.read().decode(errors="replace"))
        err = e.read().decode(errors="replace")
        if err.strip():
            print(err[:500])
        time.sleep(2)
    client.close()
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
