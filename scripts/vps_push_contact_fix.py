#!/usr/bin/env python3
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"
FILES = [
    "frontend/src/app/contact/page.tsx",
    "frontend/src/app/contact/contact-content.tsx",
    "frontend/src/components/billing/plan-checkout-modal.tsx",
    "frontend/src/components/settings/billing-panel.tsx",
    "frontend/src/app/settings/page.tsx",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=90)
sftp = c.open_sftp()
for rel in FILES:
    local = ROOT / rel
    remote = f"{REMOTE}/{rel}"
    remote_dir = "/".join(remote.split("/")[:-1])
    try:
        sftp.stat(remote_dir)
    except OSError:
        c.exec_command(f"mkdir -p {remote_dir}")
    sftp.put(str(local), remote)
    print("ok", rel)
sftp.close()
_, o, e = c.exec_command(
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"up -d --force-recreate frontend 2>&1 | tail -18",
    timeout=300,
)
out = (o.read() + e.read()).decode(errors="replace")
print(out[-2500:])
print("exit", o.channel.recv_exit_status())
# wait for next compile
import time
time.sleep(12)
_, o2, _ = c.exec_command(
    "docker logs sanad-frontend-1 2>&1 | tail -25",
    timeout=60,
)
print("--- logs ---")
print(o2.read().decode(errors="replace")[-2000:])
c.close()
print("done")
