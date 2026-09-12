#!/usr/bin/env python3
"""Stabilize VPS after OOM-ish build load; restore volume frontend so uploaded code is live."""
from __future__ import annotations

import time
import paramiko

HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

FALLBACK_COMPOSE = """
services:
  frontend:
    build: ./frontend
    ports:
      - "127.0.0.1:3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: https://lexhub.space
      NEXT_PUBLIC_GOOGLE_CLIENT_ID: ${GOOGLE_CLIENT_ID:-}
      NODE_OPTIONS: --max-old-space-size=1024
    volumes:
      - ./frontend:/app
      - /app/node_modules
    depends_on:
      - backend
    command: ["npm", "run", "dev", "--", "--hostname", "0.0.0.0", "--port", "3000"]
    restart: unless-stopped
"""


def connect():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    for i in range(10):
        try:
            c.connect(HOST, username="root", password=PASSWORD, timeout=70, banner_timeout=120)
            break
        except Exception as e:
            print("retry", i, e)
            time.sleep(10)
    else:
        raise RuntimeError("ssh failed")
    t = c.get_transport()
    if t:
        t.set_keepalive(20)
    return c


def run(c, cmd, timeout=180):
    _, o, e = c.exec_command(cmd, timeout=timeout)
    code = o.channel.recv_exit_status()
    return code, o.read().decode(errors="replace") + e.read().decode(errors="replace")


def main():
    c = connect()
    print("freeing build pressure...")
    run(
        c,
        "pkill -9 -f 'next build' 2>/dev/null || true; "
        "pkill -9 -f 'npm run build' 2>/dev/null || true; "
        "docker builder prune -af 2>/dev/null || true; "
        "sleep 2; uptime",
    )
    # Write fallback overlay so we don't use Dockerfile.prod on 2GB box during demo
    sftp = c.open_sftp()
    with sftp.file(f"{REMOTE}/docker-compose.lexhub-fe-dev.yml", "w") as f:
        f.write(FALLBACK_COMPOSE)
    sftp.close()

    print("recreate frontend with volume+dev (code already on disk)...")
    code, out = run(
        c,
        f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        f"-f docker-compose.lexhub-fe-dev.yml up -d --force-recreate frontend 2>&1",
        timeout=240,
    )
    print(out[-2000:])
    print("exit", code)
    time.sleep(8)
    _, st = run(c, "uptime; docker ps --filter name=sanad- --format '{{.Names}} {{.Status}}'")
    print(st)
    c.close()
    return 0 if code == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
