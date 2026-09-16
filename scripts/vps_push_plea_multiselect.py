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
        f"restart frontend 2>&1 | tail -12",
        timeout=120,
    )
    print(o.read().decode(errors="replace"))
    time.sleep(8)
    _, o, _ = client.exec_command(
        "curl -s -o /dev/null -w '%{http_code}' https://lexhub.space/redaction",
        timeout=30,
    )
    print("redaction:", o.read().decode(errors="replace"))
    client.close()
    print("done — https://lexhub.space (hard refresh)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
