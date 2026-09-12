#!/usr/bin/env python3
"""Deploy quota exhausted guidance modal (trial + paid). No --build."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"
FILES = [
    "backend/app/services/billing.py",
    "frontend/src/lib/api.ts",
    "frontend/src/components/billing/credits-exhausted-modal.tsx",
    "frontend/src/components/billing/quota-guidance-host.tsx",
    "frontend/src/components/layout/app-shell.tsx",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=90)
sftp = c.open_sftp()
for rel in FILES:
    local = ROOT / rel
    if not local.exists():
        raise SystemExit(f"missing: {rel}")
    remote = f"{REMOTE}/{rel}"
    _, o, _ = c.exec_command(f"mkdir -p $(dirname {remote})")
    o.channel.recv_exit_status()
    sftp.put(str(local), remote)
    print("ok", rel)
sftp.close()

cmd = r"""
set -e
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d --force-recreate backend frontend 2>&1 | tail -15
sleep 10
curl -s -o /dev/null -w 'home=%{http_code}\n' https://lexhub.space/
"""
_, o, e = c.exec_command(cmd, timeout=420)
print(o.read().decode(errors="replace")[-4000:])
err = e.read().decode(errors="replace")
if err.strip():
    print("stderr", err[-1000:])
c.close()
print("done")
