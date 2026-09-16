#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import paramiko
import time

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

FILES = [
    "backend/app/api/plaidoirie_templates.py",
    "backend/app/models/__init__.py",
    "frontend/src/app/redaction/page.tsx",
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
    _, o, _ = client.exec_command(
        f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        f"restart backend frontend 2>&1 | tail -20",
        timeout=180,
    )
    print(o.read().decode(errors="replace"))
    time.sleep(10)
    _, o, _ = client.exec_command(
        "curl -s -o /dev/null -w '%{http_code}' https://lexhub.space/api/health",
        timeout=30,
    )
    print("health:", o.read().decode(errors="replace"))
    client.close()
    print("done — https://lexhub.space")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
