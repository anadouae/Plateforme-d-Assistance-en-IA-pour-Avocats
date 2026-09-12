#!/usr/bin/env python3
"""Configure OpenAI API key on production VPS (never commit the key)."""
from __future__ import annotations

import re
import sys
import time
from pathlib import Path

import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"
ENV_FILES = [f"{REMOTE}/.env", f"{REMOTE}/.env.vps"]


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
    if not api_key.startswith("sk-"):
        print("Usage: python vps_set_openai.py sk-...", file=sys.stderr)
        return 1

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username="root", password=PASSWORD, timeout=45)
    sftp = client.open_sftp()

    sftp.put(str(ROOT / "docker-compose.yml"), f"{REMOTE}/docker-compose.yml")

    for env_path in ENV_FILES:
        try:
            with sftp.open(env_path, "r") as f:
                raw = f.read().decode("utf-8", errors="replace")
        except OSError:
            raw = ""
        raw = upsert(raw, "OPENAI_API_KEY", api_key)
        raw = upsert(raw, "OPENAI_BASE_URL", "https://api.openai.com/v1")
        raw = upsert(raw, "OPENAI_MODEL", "gpt-4o-mini")
        with sftp.open(env_path, "w") as f:
            f.write(raw)
        print("updated", env_path)

    sftp.close()

    _, out, err = client.exec_command(
        f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        f"--env-file .env.vps up -d --force-recreate backend celery-worker 2>&1",
        timeout=180,
    )
    print(out.read().decode()[-2000:])
    err_text = err.read().decode().strip()
    if err_text:
        print(err_text)

    time.sleep(10)
    _, out, _ = client.exec_command(
        "docker exec sanad-backend-1 printenv OPENAI_API_KEY 2>/dev/null | "
        "python3 -c \"import sys; k=sys.stdin.read().strip(); print('openai_key_set', bool(k), 'prefix', k[:7]+'…' if len(k)>7 else '')\"",
        timeout=30,
    )
    print(out.read().decode().strip())

    _, out, _ = client.exec_command(
        "docker exec sanad-backend-1 curl -s http://127.0.0.1:8000/health 2>/dev/null | head -c 200",
        timeout=30,
    )
    print("health:", out.read().decode())

    client.close()
    print("DONE — OpenAI configured on lexhub.space (backend + celery-worker)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
