#!/usr/bin/env python3
"""Recover backend + start celery-beat using worker image."""
from __future__ import annotations

from pathlib import Path
import paramiko
import time

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

FILES = [
    "docker-compose.yml",
    "docker-compose.lexhub.yml",
]


def main() -> int:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=90)
    sftp = client.open_sftp()
    for rel in FILES:
        sftp.put(str(ROOT / rel), f"{REMOTE}/{rel}")
        print("ok", rel)
    sftp.close()

    cmds = [
        "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        "up -d --no-build backend celery-worker celery-beat 2>&1 | tail -40",
        "sleep 8",
        "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        "ps 2>&1 | tail -20",
        "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        "exec -T backend alembic upgrade head 2>&1 | tail -40",
        "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        "logs --tail 30 backend 2>&1 | tail -35",
        "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        "logs --tail 20 celery-beat 2>&1 | tail -25",
    ]
    for cmd in cmds:
        print(">>>", cmd[:110])
        _, o, e = client.exec_command(cmd, timeout=300)
        print(o.read().decode(errors="replace"))
        err = e.read().decode(errors="replace")
        if err.strip():
            print(err[:1000])
        time.sleep(1)
    client.close()
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
