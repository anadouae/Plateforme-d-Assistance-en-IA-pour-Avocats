#!/usr/bin/env python3
from pathlib import Path
import paramiko
import time

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"
FILES = [
    "backend/alembic/versions/019_cabinet_notifications.py",
    "backend/app/models/__init__.py",
    "backend/app/api/notifications.py",
    "backend/app/api/plaidoirie_templates.py",
    "backend/app/main.py",
    "frontend/src/lib/api.ts",
    "frontend/src/components/layout/topbar-action-icons.tsx",
    "frontend/src/components/layout/app-sidebar.tsx",
    "frontend/src/styles/sanad-ui.css",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=90)
sftp = c.open_sftp()
for rel in FILES:
    remote = f"{REMOTE}/{rel}"
    _, o, _ = c.exec_command(f"mkdir -p $(dirname {remote})")
    o.channel.recv_exit_status()
    sftp.put(str(ROOT / rel), remote)
    print("ok", rel)
sftp.close()
_, o, _ = c.exec_command(
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"up -d --force-recreate backend frontend 2>&1 | tail -12",
    timeout=240,
)
print(o.read().decode(errors="replace"))
time.sleep(6)
_, o, _ = c.exec_command(
    "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    "exec -T backend alembic upgrade head 2>&1",
    timeout=90,
)
print("migrate:", o.read().decode(errors="replace")[-600:])
c.close()
print("done")
