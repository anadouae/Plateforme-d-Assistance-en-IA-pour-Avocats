#!/usr/bin/env python3
"""Deploy billing / plans / PII / clé de barre foundations."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

FILES = [
    "backend/alembic/versions/026_billing_subscriptions.py",
    "backend/app/models/__init__.py",
    "backend/app/core/config.py",
    "backend/app/main.py",
    "backend/app/api/auth.py",
    "backend/app/api/team.py",
    "backend/app/api/cases.py",
    "backend/app/api/dictation.py",
    "backend/app/api/billing.py",
    "backend/app/services/billing.py",
    "backend/app/services/pii_mask.py",
    "backend/app/services/cle_de_barre.py",
    "backend/app/services/free_llm_router.py",
    "backend/.env.example",
    "frontend/src/lib/api.ts",
    "frontend/src/components/billing/subscription-banner.tsx",
    "frontend/src/components/settings/billing-panel.tsx",
    "frontend/src/components/layout/app-shell.tsx",
    "frontend/src/components/layout/admin-shell.tsx",
    "frontend/src/components/layout/public-navbar.tsx",
    "frontend/src/app/settings/page.tsx",
    "frontend/src/app/tarifs/page.tsx",
    "frontend/src/app/admin/plans/page.tsx",
    "frontend/src/app/cases/[id]/page.tsx",
]


def run(c, cmd, timeout=600):
    print(">>", cmd[:220])
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    code = o.channel.recv_exit_status()
    if out.strip():
        print(out[-5000:])
    if err.strip():
        print("stderr:", err[-2000:])
    print("exit", code)
    return code


c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=90)
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

run(
    c,
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"exec -T backend alembic upgrade head 2>&1 | tail -30",
    timeout=180,
)
run(
    c,
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"up -d --force-recreate --build backend frontend 2>&1 | tail -40",
    timeout=900,
)
run(
    c,
    f"cd {REMOTE} && sleep 12 && curl -fsS -o /dev/null -w '%{{http_code}}' https://lexhub.space/tarifs 2>&1",
)
c.close()
print("done")
