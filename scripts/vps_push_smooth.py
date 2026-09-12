#!/usr/bin/env python3
"""Push polish files + run tests."""
from __future__ import annotations

from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

FILES = [
    "frontend/src/components/layout/app-shell.tsx",
    "frontend/src/components/motion/page-transition.tsx",
    "frontend/src/styles/sanad-ui.css",
    "backend/app/services/stt_quality.py",
    "backend/tests/test_dictation_pipeline.py",
]


def main() -> int:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username="root", password=PASSWORD, timeout=40)
    sftp = client.open_sftp()
    for rel in FILES:
        local = ROOT / rel
        remote = f"{REMOTE}/{rel}"
        _, o, _ = client.exec_command(f"mkdir -p $(dirname {remote})")
        o.channel.recv_exit_status()
        sftp.put(str(local), remote)
        print("ok", rel)
    sftp.close()
    _, o, _ = client.exec_command(
        f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d --force-recreate backend frontend 2>&1 | tail -15",
        timeout=180,
    )
    print(o.read().decode())
    import time
    time.sleep(6)
    _, o, _ = client.exec_command(
        "docker exec sanad-backend-1 python -m pytest tests/ -q --tb=line 2>&1 | tail -25",
        timeout=180,
    )
    print(o.read().decode())
    client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
