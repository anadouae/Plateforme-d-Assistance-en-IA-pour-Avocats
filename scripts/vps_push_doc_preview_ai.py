#!/usr/bin/env python3
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"
FILES = [
    "frontend/src/components/documents/document-preview-modal.tsx",
    "frontend/src/app/documents/page.tsx",
    "frontend/src/app/documents/[id]/page.tsx",
    "frontend/src/app/cases/[id]/page.tsx",
    "frontend/src/lib/api.ts",
    "backend/app/services/billing.py",
    "backend/app/services/cle_de_barre.py",
    "backend/app/api/documents.py",
    "backend/app/models/__init__.py",
    "backend/alembic/versions/028_synthesis_usage.py",
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

cmd = f"""
cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml --env-file .env.vps exec -T backend alembic upgrade head 2>&1 | tail -15
cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml --env-file .env.vps up -d --force-recreate backend celery-worker frontend 2>&1 | tail -20
"""
_, o, e = c.exec_command(cmd, timeout=300)
print((o.read() + e.read()).decode(errors="replace")[-3500:])
print("exit", o.channel.recv_exit_status())
c.close()
print("done")
