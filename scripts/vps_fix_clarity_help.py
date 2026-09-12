#!/usr/bin/env python3
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

FILES = [
    "backend/app/services/billing.py",
    "frontend/src/lib/billing-plans-fallback.ts",
    "frontend/src/lib/i18n/translations.ts",
    "frontend/src/app/tarifs/page.tsx",
    "frontend/src/app/aide/page.tsx",
    "frontend/src/components/settings/billing-panel.tsx",
]

BACKEND_CONTAINERS = ("sanad-backend-1", "sanad-celery-worker-1", "sanad-celery-beat-1")


def run(c, cmd, timeout=180):
    print(">>", cmd[:200])
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    code = o.channel.recv_exit_status()
    if out.strip():
        print(out[-2000:])
    if err.strip():
        print("stderr:", err[-800:])
    print("exit", code)
    return code


c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=90)
sftp = c.open_sftp()
for rel in FILES:
    local = ROOT / rel
    remote = f"{REMOTE}/{rel}"
    _, o, _ = c.exec_command(f"mkdir -p $(dirname '{remote}')")
    o.channel.recv_exit_status()
    sftp.put(str(local), remote)
    print("sftp", rel)
sftp.close()

for rel in FILES:
    if not rel.startswith("backend/"):
        continue
    container_path = "/app/" + rel.replace("backend/", "", 1)
    for name in BACKEND_CONTAINERS:
        run(c, f"docker cp '{REMOTE}/{rel}' {name}:{container_path}")

run(
    c,
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    "restart backend frontend 2>&1 | tail -15",
)
run(
    c,
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    "exec -T backend python - <<'PY'\n"
    "from app.core.database import SessionLocal\n"
    "from app.services.billing import ensure_default_plans, MOROCCO_PAYMENT_METHODS\n"
    "db = SessionLocal()\n"
    "ensure_default_plans(db)\n"
    "db.commit()\n"
    "print('methods', [m['id'] for m in MOROCCO_PAYMENT_METHODS])\n"
    "db.close()\n"
    "PY",
)
c.close()
print("DONE")
