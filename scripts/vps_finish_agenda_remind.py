#!/usr/bin/env python3
"""Finish deploy: prune disk, migrate, recreate without rebuild."""
from __future__ import annotations

import paramiko
import time

HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"


def main() -> int:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=90)
    cmds = [
        "df -h / | tail -1",
        "docker system df",
        "docker builder prune -af 2>&1 | tail -8",
        "docker image prune -af 2>&1 | tail -8",
        "df -h / | tail -1",
        "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        "exec -T backend alembic upgrade head 2>&1 | tail -30",
        "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        "up -d --no-build --force-recreate backend celery-worker celery-beat 2>&1 | tail -50",
        "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        "ps 2>&1 | tail -25",
    ]
    for cmd in cmds:
        print(">>>", cmd[:100])
        _, o, e = client.exec_command(cmd, timeout=360)
        print(o.read().decode(errors="replace"))
        err = e.read().decode(errors="replace")
        if err.strip():
            print(err[:1200])
        time.sleep(1)
    client.close()
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
