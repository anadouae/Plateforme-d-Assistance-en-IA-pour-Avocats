#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import paramiko
import time

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"


def main() -> int:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=90)
    sftp = client.open_sftp()
    sftp.put(
        str(ROOT / "backend/app/services/dictation.py"),
        "/opt/sanad/backend/app/services/dictation.py",
    )
    print("ok dictation.py")
    sftp.close()
    _, o, _ = client.exec_command(
        "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        "restart backend 2>&1 | tail -8",
        timeout=120,
    )
    print(o.read().decode(errors="replace"))
    time.sleep(12)
    _, o, e = client.exec_command(
        "docker exec -e PYTHONIOENCODING=utf-8 sanad-backend-1 python /app/_polish_ar_tests.py",
        timeout=300,
    )
    print(o.read().decode(errors="replace"))
    err = e.read().decode(errors="replace")
    if err.strip():
        print("STDERR", err[-800:])
    client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
