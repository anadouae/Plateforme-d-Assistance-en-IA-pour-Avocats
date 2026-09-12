#!/usr/bin/env python3
"""Hot-patch Coursera flow + Entreprise rescale + Help."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

BACKEND_FILES = [
    "backend/app/services/billing.py",
]

FRONTEND_FILES = [
    "frontend/src/lib/billing-plans-fallback.ts",
    "frontend/src/components/billing/card-brand-badges.tsx",
    "frontend/src/lib/plan-cta.ts",
    "frontend/src/components/home/landing-pricing-carousel.tsx",
    "frontend/src/components/billing/trial-pitch-modal.tsx",
    "frontend/src/components/settings/billing-panel.tsx",
    "frontend/src/app/tarifs/page.tsx",
    "frontend/src/app/aide/page.tsx",
    "frontend/src/components/billing/plans-nudge-modal.tsx",
    "frontend/src/components/billing/plan-checkout-modal.tsx",
]

BACKEND_CONTAINERS = ("sanad-backend-1", "sanad-celery-worker-1", "sanad-celery-beat-1")


def run(c, cmd, timeout=300):
    print(">>", cmd[:240])
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    code = o.channel.recv_exit_status()
    if out.strip():
        print(out[-4000:])
    if err.strip():
        print("stderr:", err[-1500:])
    print("exit", code)
    return code


c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=90)
sftp = c.open_sftp()

for rel in BACKEND_FILES + FRONTEND_FILES:
    local = ROOT / rel
    if not local.exists():
        raise SystemExit(f"missing: {rel}")
    remote = f"{REMOTE}/{rel}"
    _, o, _ = c.exec_command(f"mkdir -p $(dirname '{remote}')")
    o.channel.recv_exit_status()
    sftp.put(str(local), remote)
    print("sftp", rel)
sftp.close()

for rel in BACKEND_FILES:
    container_path = "/app/" + rel.replace("backend/", "", 1)
    for name in BACKEND_CONTAINERS:
        run(c, f"docker cp '{REMOTE}/{rel}' {name}:{container_path}")

run(
    c,
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    "restart backend celery-worker celery-beat frontend 2>&1 | tail -20",
    timeout=180,
)

run(
    c,
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    "exec -T backend python - <<'PY'\n"
    "from app.core.database import SessionLocal\n"
    "from app.services.billing import ensure_default_plans, get_plan_by_slug\n"
    "db = SessionLocal()\n"
    "ensure_default_plans(db)\n"
    "db.commit()\n"
    "p = get_plan_by_slug(db, 'enterprise')\n"
    "print('enterprise', p.price_mad_monthly, p.max_avocats, p.max_assistants, p.max_plaidoiries_month, p.trial_days)\n"
    "db.close()\n"
    "PY",
    timeout=120,
)

run(c, "curl -sS -o /dev/null -w 'home:%{http_code} aide:%{http_code}\\n' https://lexhub.space/ https://lexhub.space/aide")
run(
    c,
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    "ps --format 'table {{.Name}}\\t{{.Status}}' | head -12",
)
c.close()
print("DONE")
