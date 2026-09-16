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
    "backend/app/services/dictation.py",
    "backend/app/api/dictation.py",
    "backend/tests/test_dictation_pipeline.py",
    "frontend/src/lib/dictation-quality.ts",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
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
    time.sleep(12)
    # Smoke: nonsense gate + prompt idea
    _, o, _ = client.exec_command(
        "docker exec sanad-backend-1 python -c \""
        "from app.services.dictation import looks_like_nonsense; "
        "print('typo', looks_like_nonsense('السلا ن م السيد الؤيس')); "
        "print('mash', looks_like_nonsense('asdf')); "
        "\"",
        timeout=60,
    )
    print(o.read().decode(errors="replace"))
    client.close()
    print("done — https://lexhub.space")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
