#!/usr/bin/env python3
from pathlib import Path
import paramiko
import time

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

FILES = [
    "backend/app/services/join_code.py",
    "backend/app/services/realtime.py",
    "backend/app/services/email.py",
    "backend/app/api/realtime_ws.py",
    "backend/app/api/team.py",
    "backend/app/api/plaidoirie_templates.py",
    "backend/app/main.py",
    "frontend/src/hooks/use-cabinet-realtime.ts",
    "frontend/src/components/layout/app-shell.tsx",
    "frontend/src/components/layout/topbar-action-icons.tsx",
    "frontend/src/components/layout/public-footer.tsx",
    "frontend/src/components/home/home-page-content.tsx",
    "frontend/src/components/home/landing-royal-test.css",
    "frontend/src/components/auth/unified-auth.tsx",
    "frontend/src/app/activity/page.tsx",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=90)
sftp = c.open_sftp()
for rel in FILES:
    local = ROOT / rel
    if not local.exists():
        print("MISSING", rel)
        continue
    remote = f"{REMOTE}/{rel}"
    _, o, _ = c.exec_command(f"mkdir -p $(dirname {remote})")
    o.channel.recv_exit_status()
    sftp.put(str(local), remote)
    print("ok", rel)
sftp.close()
_, o, e = c.exec_command(
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"up -d --force-recreate backend frontend 2>&1 | tail -20",
    timeout=240,
)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace")[:400])
c.close()
print("done")
