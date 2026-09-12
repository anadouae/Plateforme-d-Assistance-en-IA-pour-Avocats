#!/usr/bin/env python3
"""Set Turnstile keys on VPS .env and restart backend+frontend."""
from __future__ import annotations

import os
import re
import sys

import paramiko

HOST = os.environ.get("VPS_HOST", "51.38.78.23")
USER = os.environ.get("VPS_USER", "root")
PASSWORD = os.environ.get("VPS_SSH_PASSWORD", "")
SITE = os.environ.get("TURNSTILE_SITE_KEY", "").strip()
SECRET = os.environ.get("TURNSTILE_SECRET_KEY", "").strip()
ENV_PATH = "/opt/sanad/.env"


def upsert(content: str, key: str, value: str) -> str:
    line = f"{key}={value}"
    pat = re.compile(rf"(?m)^{re.escape(key)}=.*$")
    if pat.search(content):
        return pat.sub(line, content)
    if content and not content.endswith("\n"):
        content += "\n"
    return content + line + "\n"


def main() -> int:
    if not PASSWORD:
        print("Set VPS_SSH_PASSWORD", file=sys.stderr)
        return 1
    if not SITE or not SECRET:
        print("Set TURNSTILE_SITE_KEY and TURNSTILE_SECRET_KEY env vars", file=sys.stderr)
        return 1

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=30, allow_agent=False, look_for_keys=False)

    sftp = client.open_sftp()
    with sftp.open(ENV_PATH, "r") as f:
        raw = f.read().decode("utf-8", errors="replace")
    raw = upsert(raw, "TURNSTILE_SITE_KEY", SITE)
    raw = upsert(raw, "TURNSTILE_SECRET_KEY", SECRET)
    # ensure frontend can read site key if compose passes it
    with sftp.open(ENV_PATH, "w") as f:
        f.write(raw)
    sftp.close()
    print("updated", ENV_PATH, "(keys set)")

    cmd = (
        "cd /opt/sanad && "
        "grep -E '^TURNSTILE_(SITE|SECRET)_KEY=' .env | sed 's/=.*/=***/' && "
        "docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d --force-recreate backend frontend && "
        "sleep 2 && "
        "docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend "
        "printenv TURNSTILE_SITE_KEY TURNSTILE_SECRET_KEY 2>/dev/null | "
        "awk '{ if(NR==1) print \"backend SITE=\" substr($0,1,12) \"...\"; else print \"backend SECRET=set\" }'"
    )
    _, stdout, stderr = client.exec_command(cmd, timeout=180)
    code = stdout.channel.recv_exit_status()
    print(stdout.read().decode(errors="replace")[-2000:])
    err = stderr.read().decode(errors="replace")[-800:]
    if err:
        print(err[-800:])
    client.close()
    print("done" if code == 0 else f"exit {code}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
