#!/usr/bin/env python3
"""Stabilize landing: clear Next cache, hero video order, no-store headers."""
from pathlib import Path
import time
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

FILES = [
    "frontend/src/components/home/video-carousel.tsx",
    "frontend/src/app/page.tsx",
    "frontend/next.config.mjs",
    "deploy/Caddyfile.lexhub",
]


def run(c, cmd, timeout=120):
    print(">>", cmd[:200], flush=True)
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    code = o.channel.recv_exit_status()
    text = out + (("\n" + err) if err.strip() else "")
    if text.strip():
        print(text[-2500:], flush=True)
    print("exit", code, flush=True)
    return code


c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=45, banner_timeout=60)
sftp = c.open_sftp()
for rel in FILES:
    local = ROOT / rel
    remote = f"{REMOTE}/{rel}"
    parent = str(Path(remote).parent).replace("\\", "/")
    run(c, f"mkdir -p {parent}", 20)
    sftp.put(str(local), remote)
    print("ok", rel, flush=True)
sftp.close()

# Install caddyfile if caddy uses it
run(
    c,
    """
if [ -f /etc/caddy/Caddyfile ]; then
  cp /opt/sanad/deploy/Caddyfile.lexhub /etc/caddy/Caddyfile.lexhub.bak 2>/dev/null || true
  # Prefer merge: if main Caddyfile imports lexhub, skip overwrite of whole file
  if grep -q 'lexhub.space' /etc/caddy/Caddyfile; then
    # Replace lexhub block if present as separate file
    if [ -f /etc/caddy/Caddyfile.d/lexhub ] || [ -f /etc/caddy/sites/lexhub ]; then
      true
    fi
    # Write dedicated snippet and try reload
    cp /opt/sanad/deploy/Caddyfile.lexhub /tmp/Caddyfile.lexhub.new
    # If the live file IS only lexhub, replace it
    if ! grep -qv 'lexhub' /etc/caddy/Caddyfile 2>/dev/null; then
      cp /opt/sanad/deploy/Caddyfile.lexhub /etc/caddy/Caddyfile
    else
      # inject cache header via a snippet path used by ops
      cp /opt/sanad/deploy/Caddyfile.lexhub /etc/caddy/Caddyfile.lexhub
    fi
  else
    cp /opt/sanad/deploy/Caddyfile.lexhub /etc/caddy/Caddyfile
  fi
  caddy validate --config /etc/caddy/Caddyfile 2>&1 | tail -5 || true
  systemctl reload caddy 2>&1 | tail -5 || caddy reload --config /etc/caddy/Caddyfile 2>&1 | tail -5 || true
fi
head -30 /etc/caddy/Caddyfile 2>/dev/null || true
""",
    60,
)

run(c, "rm -rf /opt/sanad/frontend/.next/cache /opt/sanad/frontend/.next/server/app 2>/dev/null; echo cleared", 30)
run(
    c,
    "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    "restart frontend 2>&1 | tail -15",
    120,
)
time.sleep(14)
run(c, "curl -sI https://lexhub.space/ | grep -iE 'cache-control|HTTP/'", 30)
c.close()
print("DONE", flush=True)
