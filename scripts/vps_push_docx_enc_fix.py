#!/usr/bin/env python3
"""Fix BadZipFile (ENCRYPTION_KEY) + case fields + remember hint."""
from pathlib import Path
import time
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

FILES = [
    "docker-compose.lexhub.yml",
    "backend/app/services/object_storage.py",
    "backend/app/services/tasks.py",
    "backend/app/api/documents.py",
    "frontend/src/components/cases/new-case-modal.tsx",
    "frontend/src/components/auth/unified-auth.tsx",
    "frontend/src/lib/i18n/translations.ts",
]


def run(c, cmd, timeout=180):
    print(">>", cmd[:220], flush=True)
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    code = o.channel.recv_exit_status()
    text = out + (("\n" + err) if err.strip() else "")
    if text.strip():
        print(text[-3500:], flush=True)
    print("exit", code, flush=True)
    return code


c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=45, banner_timeout=60)
sftp = c.open_sftp()
for rel in FILES:
    local = ROOT / rel
    if not local.exists():
        print("SKIP", rel, flush=True)
        continue
    remote = f"{REMOTE}/{rel}"
    parent = str(Path(remote).parent).replace("\\", "/")
    run(c, f"mkdir -p {parent}", 20)
    sftp.put(str(local), remote)
    print("ok", rel, flush=True)
sftp.close()

# Align ENCRYPTION_KEY in .env.vps to the backend default (files already encrypted with it)
run(
    c,
    r"""
cd /opt/sanad
KEY='hCeRRvr67dcQN5XmoTWEJ_ccj889oCLztQnEP0xRqok='
if grep -q '^ENCRYPTION_KEY=' .env.vps 2>/dev/null; then
  sed -i "s|^ENCRYPTION_KEY=.*|ENCRYPTION_KEY=$KEY|" .env.vps
else
  echo "ENCRYPTION_KEY=$KEY" >> .env.vps
fi
grep '^ENCRYPTION_KEY=' .env.vps | cut -c1-28
""",
    30,
)

run(
    c,
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"--env-file .env.vps up -d --force-recreate backend celery-worker celery-beat 2>&1 | tail -40",
    180,
)
run(
    c,
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"restart frontend 2>&1 | tail -15",
    120,
)
time.sleep(18)
run(
    c,
    "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend "
    "python -c 'from app.core.config import settings; print(\"be\", (settings.ENCRYPTION_KEY or \"\")[:12])' && "
    "docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T celery-worker "
    "python -c 'from app.core.config import settings; print(\"cw\", (settings.ENCRYPTION_KEY or \"\")[:12])'",
    60,
)
run(c, "curl -sS -o /dev/null -w 'home=%{http_code}\\n' https://lexhub.space/", 30)
c.close()
print("DONE", flush=True)
