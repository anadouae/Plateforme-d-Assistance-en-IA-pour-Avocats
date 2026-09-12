#!/usr/bin/env python3
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"
FILES = [
    "frontend/src/app/redaction/page.tsx",
    "frontend/src/components/redaction/template-picker.tsx",
    "frontend/src/app/settings/page.tsx",
    "frontend/src/lib/api.ts",
    "frontend/src/lib/i18n/translations.ts",
    "backend/app/api/settings.py",
    "backend/app/schemas/__init__.py",
    "backend/app/services/email.py",
    "backend/app/services/email_otp.py",
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
    f"up -d --force-recreate backend frontend 2>&1 | tail -22",
    timeout=300,
)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace")[:500])
c.close()
print("done")
