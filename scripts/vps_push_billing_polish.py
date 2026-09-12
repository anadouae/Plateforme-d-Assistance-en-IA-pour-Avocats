#!/usr/bin/env python3
"""Deploy billing UX polish (30d trial, payments MA, admin detail, i18n tarifs)."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

FILES = [
    "backend/alembic/versions/027_billing_cancel_invoices.py",
    "backend/app/models/__init__.py",
    "backend/app/core/config.py",
    "backend/app/services/billing.py",
    "backend/app/api/billing.py",
    "backend/app/api/admin.py",
    "backend/app/api/auth.py",
    "backend/app/schemas/__init__.py",
    "frontend/src/lib/api.ts",
    "frontend/src/lib/i18n/translations.ts",
    "frontend/src/app/tarifs/page.tsx",
    "frontend/src/components/settings/billing-panel.tsx",
    "frontend/src/components/billing/subscription-banner.tsx",
    "frontend/src/components/layout/topbar-action-icons.tsx",
    "frontend/src/components/layout/public-navbar.tsx",
    "frontend/src/app/admin/cabinets/page.tsx",
    "frontend/src/app/cases/[id]/page.tsx",
    "frontend/src/app/settings/page.tsx",
]


def run(c, cmd, timeout=600):
    print(">>", cmd[:220])
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    code = o.channel.recv_exit_status()
    text = (out or "") + (("\n" + err) if err.strip() else "")
    if text.strip():
        print(text[-5000:])
    print("exit", code)
    return code


c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=90)

# Free a bit of space without full rebuild
run(c, "docker builder prune -af 2>&1 | tail -3; df -h / | tail -1", timeout=180)

sftp = c.open_sftp()
for rel in FILES:
    local = ROOT / rel
    if not local.exists():
        print("SKIP", rel)
        continue
    remote = f"{REMOTE}/{rel}"
    _, o, _ = c.exec_command(f"mkdir -p $(dirname {remote})")
    o.channel.recv_exit_status()
    sftp.put(str(local), remote)
    print("ok", rel)
sftp.close()

run(
    c,
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"exec -T backend alembic upgrade head 2>&1 | tail -25",
    timeout=180,
)
run(
    c,
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"up -d --force-recreate backend frontend 2>&1 | tail -25",
    timeout=300,
)
run(
    c,
    "sleep 14; curl -sS -o /dev/null -w 'tarifs=%{http_code} ' https://lexhub.space/tarifs; "
    "curl -sS https://lexhub.space/api/billing/plans | head -c 280; echo; "
    "curl -sS https://lexhub.space/api/billing/payment-methods | head -c 200; echo",
)
c.close()
print("done")
