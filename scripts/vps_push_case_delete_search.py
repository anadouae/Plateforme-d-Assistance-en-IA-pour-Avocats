#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import paramiko
import time

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

FILES = [
    "backend/app/api/cases.py",
    "backend/app/services/dictation.py",
    "frontend/src/lib/ownership.ts",
    "frontend/src/app/cases/page.tsx",
    "frontend/src/styles/sanad-ui.css",
]


def main() -> int:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=90)
    sftp = client.open_sftp()
    for rel in FILES:
        sftp.put(str(ROOT / rel), f"{REMOTE}/{rel}")
        print("ok", rel)
    sftp.close()
    _, o, _ = client.exec_command(
        f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        f"restart backend frontend 2>&1 | tail -15",
        timeout=180,
    )
    print(o.read().decode(errors="replace"))
    time.sleep(12)
    # Quick smoke: purge order imports
    _, o, e = client.exec_command(
        "docker exec sanad-backend-1 python -c \""
        "from app.api.cases import _purge_case_dependencies, delete_case; "
        "from app.models import PlaidoirieRevision; "
        "print('purge_ok', PlaidoirieRevision.__tablename__); "
        "\"",
        timeout=40,
    )
    print(o.read().decode(errors="replace"))
    err = e.read().decode(errors="replace")
    if err.strip():
        print("ERR", err[-400:])
    client.close()
    print("done — https://lexhub.space")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
