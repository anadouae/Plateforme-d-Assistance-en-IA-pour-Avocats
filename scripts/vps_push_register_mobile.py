#!/usr/bin/env python3
"""Deploy minimal register + mobile UX fixes."""
from __future__ import annotations

from pathlib import Path
import paramiko
import time

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

FILES = [
    "backend/app/schemas/__init__.py",
    "backend/app/api/auth.py",
    "frontend/src/lib/register-draft.ts",
    "frontend/src/lib/api.ts",
    "frontend/src/lib/i18n/translations.ts",
    "frontend/src/components/auth/unified-auth.tsx",
    "frontend/src/components/onboarding/profile-completion-modal.tsx",
    "frontend/src/components/layout/app-shell.tsx",
    "frontend/src/components/layout/topbar-action-icons.tsx",
    "frontend/src/styles/auth-glass.css",
    "frontend/src/styles/sanad-ui.css",
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

    _, o, e = client.exec_command(
        f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        f"restart backend frontend 2>&1 | tail -20",
        timeout=180,
    )
    print(o.read().decode(errors="replace"))
    err = e.read().decode(errors="replace")
    if err.strip():
        print("stderr:", err[-2000:])
    time.sleep(12)
    _, o, _ = client.exec_command(
        "curl -s -o /dev/null -w '%{http_code}' https://lexhub.space/login && echo && "
        "curl -s https://lexhub.space/api/health | head -c 400",
        timeout=45,
    )
    print("check:", o.read().decode(errors="replace"))
    client.close()
    print("done — https://lexhub.space")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
