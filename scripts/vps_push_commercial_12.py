#!/usr/bin/env python3
"""Deploy 12.1/12.2 commercial qualification + cases load fixes. No --build."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"
FILES = [
    "backend/alembic/versions/038_commercial_leads.py",
    "backend/app/models/__init__.py",
    "backend/app/api/billing.py",
    "backend/app/api/cases.py",
    "backend/app/services/email.py",
    "frontend/src/app/commercial/page.tsx",
    "frontend/src/app/admin/leads/page.tsx",
    "frontend/src/app/tarifs/page.tsx",
    "frontend/src/app/checkout/page.tsx",
    "frontend/src/app/cases/page.tsx",
    "frontend/src/app/cases/[id]/page.tsx",
    "frontend/src/app/contact/contact-content.tsx",
    "frontend/src/components/home/landing-pricing-carousel.tsx",
    "frontend/src/components/settings/billing-panel.tsx",
    "frontend/src/components/layout/admin-shell.tsx",
    "frontend/src/components/layout/app-sidebar.tsx",
    "frontend/src/components/cases/new-case-modal.tsx",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "frontend/src/lib/api.ts",
    "frontend/src/lib/billing-intent.ts",
    "frontend/src/lib/plan-cta.ts",
    "frontend/src/lib/billing-plans-fallback.ts",
    "frontend/src/lib/i18n/translations.ts",
    "frontend/src/lib/plea-session.ts",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=90)
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

cmd = r"""
set -e
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d --force-recreate backend frontend 2>&1 | tail -20
sleep 10
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend alembic upgrade head 2>&1 | tail -25
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python -c "from app.models import CommercialLead; from app.api.billing import submit_commercial_lead; print('ok', CommercialLead.__tablename__)"
curl -s -o /dev/null -w 'home=%{http_code} tarifs=%{http_code}\n' https://lexhub.space/
curl -s -o /dev/null -w 'commercial=%{http_code}\n' https://lexhub.space/commercial
"""
_, o, e = c.exec_command(cmd, timeout=420)
print(o.read().decode(errors="replace")[-8000:])
err = e.read().decode(errors="replace")
if err.strip():
    print("stderr", err[-2000:])
c.close()
print("done")
