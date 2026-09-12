#!/usr/bin/env python3
"""Deploy admin audit enrich + agenda 48h reminders."""
from __future__ import annotations

from pathlib import Path
import paramiko
import time

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

FILES = [
    "backend/app/api/admin.py",
    "backend/app/schemas/__init__.py",
    "backend/alembic/versions/023_agenda_reminder_48h.py",
    "backend/app/models/__init__.py",
    "backend/app/services/agenda_reminders.py",
    "backend/app/services/email.py",
    "backend/app/services/tasks.py",
    "backend/app/services/celery_app.py",
    "backend/app/main.py",
    "docker-compose.yml",
    "docker-compose.lexhub.yml",
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
        f"exec -T backend alembic upgrade head 2>&1 | tail -30",
        f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        f"up -d --force-recreate backend celery-worker celery-beat 2>&1 | tail -40",
    ]
    for cmd in cmds:
        _, o, e = client.exec_command(cmd, timeout=360)
        print(o.read().decode(errors="replace"))
        err = e.read().decode(errors="replace")
        if err.strip():
            print(err[:1200])
        time.sleep(2)
    client.close()
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
