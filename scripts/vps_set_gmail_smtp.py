#!/usr/bin/env python3
"""One-shot: set Gmail SMTP app password on VPS .env and recreate backend."""
from __future__ import annotations

import os
import re
import sys

import paramiko

HOST = os.environ.get("VPS_HOST", "51.38.78.23")
USER = os.environ.get("VPS_USER", "root")
PASSWORD = os.environ.get("VPS_SSH_PASSWORD", "P@s$wiy.O0p")
ENV_PATH = "/opt/sanad/.env"

SMTP_USER = os.environ["SMTP_USER"].strip()
SMTP_PASSWORD = os.environ["SMTP_PASSWORD"].replace(" ", "").strip()
SMTP_FROM = os.environ.get("SMTP_FROM", f"Sanad <{SMTP_USER}>").strip()


def upsert(content: str, key: str, value: str) -> str:
    line = f"{key}={value}"
    pat = re.compile(rf"(?m)^{re.escape(key)}=.*$")
    if pat.search(content):
        return pat.sub(line, content)
    if content and not content.endswith("\n"):
        content += "\n"
    return content + line + "\n"


def main() -> int:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        HOST,
        username=USER,
        password=PASSWORD,
        timeout=45,
        allow_agent=False,
        look_for_keys=False,
    )

    sftp = client.open_sftp()
    with sftp.open(ENV_PATH, "r") as f:
        raw = f.read().decode("utf-8", errors="replace")

    for k, v in [
        ("SMTP_HOST", "smtp.gmail.com"),
        ("SMTP_PORT", "587"),
        ("SMTP_USER", SMTP_USER),
        ("SMTP_PASSWORD", SMTP_PASSWORD),
        ("SMTP_FROM", SMTP_FROM),
        ("SMTP_TLS", "true"),
    ]:
        raw = upsert(raw, k, v)

    with sftp.open(ENV_PATH, "w") as f:
        f.write(raw)
    sftp.close()
    print("updated", ENV_PATH)

    cmd = (
        "cd /opt/sanad && "
        "grep -E '^SMTP_' .env | sed -E 's/(PASSWORD)=.*/\\1=***/' && "
        "docker compose -f docker-compose.yml -f docker-compose.lexhub.yml --env-file .env "
        "up -d --force-recreate backend && "
        "sleep 4 && "
        "docker exec sanad-backend-1 printenv | grep -E '^SMTP_' | "
        "sed -E 's/(PASSWORD)=.*/\\1=***/'"
    )
    _, stdout, stderr = client.exec_command(cmd, timeout=240)
    code = stdout.channel.recv_exit_status()
    print(stdout.read().decode(errors="replace")[-2500:])
    err = stderr.read().decode(errors="replace")[-1200:]
    if err.strip():
        print(err[-1200:])
    client.close()
    print("done" if code == 0 else f"exit {code}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
