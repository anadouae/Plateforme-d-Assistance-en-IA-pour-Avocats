#!/usr/bin/env python3
"""Configure Resend API key on production VPS."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
ENV_PATH = "/opt/sanad/.env"
REMOTE = "/opt/sanad"


def upsert(content: str, key: str, value: str) -> str:
    line = f"{key}={value}"
    pat = re.compile(rf"(?m)^{re.escape(key)}=.*$")
    if pat.search(content):
        return pat.sub(line, content)
    if content and not content.endswith("\n"):
        content += "\n"
    return content + line + "\n"


def main() -> int:
    api_key = (sys.argv[1] if len(sys.argv) > 1 else "").strip()
    if not api_key.startswith("re_"):
        print("Usage: python vps_set_resend.py re_...", file=sys.stderr)
        return 1

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username="root", password=PASSWORD, timeout=45)

    sftp = client.open_sftp()
    with sftp.open(ENV_PATH, "r") as f:
        raw = f.read().decode("utf-8", errors="replace")

    raw = upsert(raw, "RESEND_API_KEY", api_key)
    raw = upsert(raw, "EMAIL_FROM", "LexHub <noreply@lexhub.space>")
    raw = upsert(raw, "FRONTEND_URL", "https://lexhub.space")

    with sftp.open(ENV_PATH, "w") as f:
        f.write(raw)

    sftp.put(str(ROOT / "docker-compose.lexhub.yml"), f"{REMOTE}/docker-compose.lexhub.yml")
    sftp.close()

    _, out, err = client.exec_command(
        f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d --force-recreate backend 2>&1",
        timeout=180,
    )
    print(out.read().decode()[-1500:])
    err_text = err.read().decode().strip()
    if err_text:
        print(err_text)

    import time

    time.sleep(8)
    _, out, _ = client.exec_command(
        "docker exec sanad-backend-1 curl -s http://127.0.0.1:8000/api/health 2>/dev/null | head -c 500",
        timeout=30,
    )
    print("health:", out.read().decode())
    client.close()
    print("DONE — Resend configured on lexhub.space")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
