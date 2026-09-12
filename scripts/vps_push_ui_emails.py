#!/usr/bin/env python3
from pathlib import Path
import paramiko
import time

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"
FILES = [
    "frontend/src/styles/sanad-ui.css",
    "frontend/src/lib/i18n/translations.ts",
    "frontend/src/app/redaction/page.tsx",
    "frontend/src/components/layout/topbar-action-icons.tsx",
    "frontend/src/hooks/use-cabinet-realtime.ts",
    "backend/app/services/email.py",
    "backend/app/api/plaidoirie_templates.py",
    "backend/app/api/notifications.py",
    "backend/app/api/settings.py",
    "backend/app/api/realtime_ws.py",
    "backend/app/services/realtime.py",
    "backend/app/main.py",
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
    f"up -d --force-recreate backend frontend 2>&1 | tail -18",
    timeout=240,
)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace")[:400])
c.close()
print("done")
