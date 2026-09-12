#!/usr/bin/env python3
"""Deploy mobile dictation + ephemeral AI fixes."""
from __future__ import annotations

from pathlib import Path
import paramiko
import time

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

FILES = [
    "frontend/src/hooks/use-whisper-dictation.ts",
    "frontend/src/app/layout.tsx",
    "frontend/src/components/ai/synthesis-panel.tsx",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "backend/app/core/config.py",
    "backend/app/services/agent.py",
    "backend/app/services/web_search.py",
    "backend/app/api/dictation.py",
]


def main() -> int:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=90)
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
        f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        f"up -d --force-recreate backend frontend 2>&1 | tail -12",
        timeout=240,
    )
    print(o.read().decode(errors="replace"))
    time.sleep(8)
    _, o, _ = client.exec_command(
        "curl -s https://lexhub.space/api/health | head -c 400",
        timeout=30,
    )
    print("health:", o.read().decode(errors="replace"))
    client.close()
    print("done — https://lexhub.space")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
