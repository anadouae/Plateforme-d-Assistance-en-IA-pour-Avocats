#!/usr/bin/env python3
"""Deploy Coursera-like billing + Ouvrir atelier + browser mic dictation."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

FILES = [
    "backend/app/api/auth.py",
    "backend/app/api/billing.py",
    "backend/app/services/billing.py",
    "backend/app/services/email.py",
    "backend/app/services/trial_lifecycle.py",
    "frontend/src/lib/api.ts",
    "frontend/src/lib/billing-plans-fallback.ts",
    "frontend/src/components/billing/plan-checkout-modal.tsx",
    "frontend/src/components/settings/billing-panel.tsx",
    "frontend/src/components/home/landing-pricing-carousel.tsx",
    "frontend/src/app/tarifs/page.tsx",
    "frontend/src/app/redaction/page.tsx",
    "frontend/src/app/redaction/[templateId]/page.tsx",
    "frontend/src/components/redaction/template-picker.tsx",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
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
    f"exec -T backend python - <<'PY'\n"
    "from app.core.database import SessionLocal\n"
    "from app.services.billing import ensure_default_plans\n"
    "db = SessionLocal()\n"
    "ensure_default_plans(db)\n"
    "db.commit()\n"
    "print('plans synced')\n"
    "db.close()\n"
    "PY",
    timeout=120,
)
run(
    c,
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"up -d --force-recreate --build backend frontend 2>&1 | tail -50",
    timeout=900,
)
run(
    c,
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"ps --format 'table {{{{.Name}}}}\\t{{{{.Status}}}}' 2>&1 | head -20",
    timeout=60,
)
c.close()
print("DONE")
