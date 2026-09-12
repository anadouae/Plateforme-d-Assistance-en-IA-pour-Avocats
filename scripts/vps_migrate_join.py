#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

import paramiko

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    password = os.environ.get("VPS_SSH_PASSWORD", "")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        os.environ.get("VPS_HOST", "51.38.78.23"),
        username="root",
        password=password,
        timeout=30,
        allow_agent=False,
        look_for_keys=False,
    )
    sftp = client.open_sftp()
    for rel in [
        "backend/alembic/versions/015_onboarding_tour.py",
        "backend/alembic/versions/016_join_code_hardening.py",
    ]:
        sftp.put(str(ROOT / rel), f"/opt/sanad/{rel}")
        print("upload", rel)
    sftp.close()

    cmds = [
        "ls /opt/sanad/backend/alembic/versions/ | sort",
        "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T postgres psql -U sanad -d sanad -c 'select version_num from alembic_version;'",
        "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend alembic upgrade head",
        "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart backend frontend",
    ]
    for cmd in cmds:
        print(">>", cmd[:90])
        _, stdout, stderr = client.exec_command(cmd, timeout=180)
        code = stdout.channel.recv_exit_status()
        print(stdout.read().decode(errors="replace")[-1500:])
        err = stderr.read().decode(errors="replace")[-500:]
        if err:
            print(err)
        if code != 0:
            print("exit", code)
            client.close()
            return code
    client.close()
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
