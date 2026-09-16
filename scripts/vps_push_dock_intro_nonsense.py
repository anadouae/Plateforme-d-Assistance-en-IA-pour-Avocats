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
    "frontend/src/components/layout/app-sidebar.tsx",
    "frontend/src/styles/sanad-ui.css",
    "frontend/src/lib/dictation-quality.ts",
    "frontend/src/lib/export-official-doc.ts",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "backend/app/services/plaidoirie_revise.py",
    "backend/app/services/dictation.py",
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
    _, o, e = client.exec_command(
        f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        f"restart frontend backend 2>&1 | tail -20",
        timeout=180,
    )
    print(o.read().decode(errors="replace"))
    err = e.read().decode(errors="replace")
    if err:
        print("stderr:", err[-500:])
    time.sleep(8)
    _, o, _ = client.exec_command(
        "curl -s -o /dev/null -w '%{http_code}' https://lexhub.space/login",
        timeout=30,
    )
    print("login:", o.read().decode(errors="replace"))
    client.close()
    print("done — https://lexhub.space (hard refresh on phone)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
