#!/usr/bin/env python3
"""Deploy assistant UX, audit archives, join code, plaidoirie link."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

FILES = [
    "backend/app/api/documents.py",
    "backend/app/api/team.py",
    "backend/app/api/admin.py",
    "backend/app/api/plaidoirie_templates.py",
    "backend/app/schemas/__init__.py",
    "backend/app/models/__init__.py",
    "backend/app/services/admin_audit_archive.py",
    "backend/alembic/versions/024_admin_audit_archives.py",
    "frontend/src/app/documents/[id]/page.tsx",
    "frontend/src/app/dashboard/page.tsx",
    "frontend/src/app/settings/page.tsx",
    "frontend/src/app/admin/logs/page.tsx",
    "frontend/src/app/admin/cabinets/page.tsx",
    "frontend/src/app/redaction/page.tsx",
    "frontend/src/lib/api.ts",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=90)
sftp = c.open_sftp()
for rel in FILES:
    local = ROOT / rel
    remote = f"{REMOTE}/{rel}"
    _, o, _ = c.exec_command(f"mkdir -p $(dirname {remote})")
    o.channel.recv_exit_status()
    sftp.put(str(local), remote)
    print("ok", rel)
sftp.close()

_, o, _ = c.exec_command(
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"up -d --force-recreate backend frontend 2>&1 | tail -25",
    timeout=600,
)
print(o.read().decode(errors="replace")[-3000:])
c.close()
print("done")
