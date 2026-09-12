#!/usr/bin/env python3
"""Finish frontend prod deploy on VPS (background build, poll)."""
from __future__ import annotations

import sys
import time

import paramiko

HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"


def run(client: paramiko.SSHClient, cmd: str, timeout: int = 120) -> tuple[int, str]:
    _, out, err = client.exec_command(cmd, timeout=timeout)
    code = out.channel.recv_exit_status()
    text = out.read().decode(errors="replace") + err.read().decode(errors="replace")
    return code, text


def connect() -> paramiko.SSHClient:
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username="root", password=PASSWORD, timeout=40, banner_timeout=60)
    transport = c.get_transport()
    if transport:
        transport.set_keepalive(30)
    return c


def main() -> int:
    client = connect()

    # Status
    _, st = run(client, "docker ps -a --filter name=sanad-frontend --format '{{.Names}} {{.Status}}'; docker images | head -5")
    print("STATUS:\n", st)

    # Prefer prod Dockerfile build in background via nohup
    start_cmd = f"""
cd {REMOTE}
nohup bash -c '
  set -e
  export COMPOSE_HTTP_TIMEOUT=300
  docker compose -f docker-compose.yml -f docker-compose.lexhub.yml build frontend > /tmp/sanad-fe-build.log 2>&1
  echo BUILD_EXIT:$? >> /tmp/sanad-fe-build.log
  docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d --force-recreate frontend >> /tmp/sanad-fe-build.log 2>&1
  echo UP_EXIT:$? >> /tmp/sanad-fe-build.log
' >/dev/null 2>&1 &
echo STARTED:$!
"""
    code, text = run(client, start_cmd)
    print(text)
    client.close()

    # Poll log
    for i in range(60):
        time.sleep(20)
        client = connect()
        _, log = run(client, "tail -n 40 /tmp/sanad-fe-build.log 2>/dev/null || echo NOLOG")
        print(f"--- poll {i+1} ---")
        print(log[-2000:])
        if "UP_EXIT:0" in log:
            _, fe = run(
                client,
                "docker ps --filter name=sanad-frontend --format '{{.Status}}'; "
                "docker exec sanad-frontend-1 sh -c 'ps aux | head -8' 2>/dev/null || true",
            )
            print("FRONTEND OK:\n", fe)
            client.close()
            return 0
        if "UP_EXIT:" in log and "UP_EXIT:0" not in log:
            print("frontend up failed")
            client.close()
            return 1
        if "BUILD_EXIT:" in log and "BUILD_EXIT:0" not in log:
            print("build failed — trying volume fallback next start")
            # fallback
            fb = f"""
cd {REMOTE}
# Temporarily override to volume+build+start without Dockerfile.prod
cat > /tmp/fe-fallback.yml <<'EOF'
services:
  frontend:
    build: ./frontend
    ports:
      - "127.0.0.1:3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: https://lexhub.space
      NODE_OPTIONS: --max-old-space-size=1536
    volumes:
      - ./frontend:/app
      - sanad_fe_node_modules:/app/node_modules
    depends_on:
      - backend
    command: ["sh", "-c", "npm run build && npx next start -H 0.0.0.0 -p 3000"]
    restart: unless-stopped
volumes:
  sanad_fe_node_modules:
EOF
nohup bash -c 'docker compose -f docker-compose.yml -f /tmp/fe-fallback.yml up -d --force-recreate --build frontend > /tmp/sanad-fe-fallback.log 2>&1; echo FB_EXIT:$? >> /tmp/sanad-fe-fallback.log' &
echo FB_STARTED
"""
            run(client, fb)
            client.close()
            # continue polling fallback
            for j in range(45):
                time.sleep(20)
                client = connect()
                _, flog = run(client, "tail -n 30 /tmp/sanad-fe-fallback.log 2>/dev/null || echo NOFB")
                print(f"--- fb poll {j+1} ---")
                print(flog[-1500:])
                if "FB_EXIT:0" in flog:
                    client.close()
                    return 0
                if "FB_EXIT:" in flog:
                    client.close()
                    return 1
                client.close()
            return 1
        client.close()

    print("timeout waiting for build")
    return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("FAILED:", exc, file=sys.stderr)
        raise SystemExit(1)
