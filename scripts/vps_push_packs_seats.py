#!/usr/bin/env python3
"""Deploy prepaid packs + extra seats + migrate 036."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"
FILES = [
    "backend/alembic/versions/036_prepaid_packs_extra_seats.py",
    "backend/app/models/__init__.py",
    "backend/app/services/billing.py",
    "backend/app/api/billing.py",
    "frontend/src/lib/api.ts",
    "frontend/src/components/settings/billing-panel.tsx",
    "frontend/src/lib/billing-plans-fallback.ts",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=90)
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

cmd = r"""
set -e
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d --force-recreate backend frontend 2>&1 | tail -30
sleep 8
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend alembic upgrade head 2>&1 | tail -40
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python -c "
from app.services.billing import CREDIT_PACKS, EXTRA_AVOCAT_SEAT_MAD_MONTHLY, apply_trial_cap
print('packs', [(p['id'], p['credits'], p['price_mad']) for p in CREDIT_PACKS])
print('seat_mad', EXTRA_AVOCAT_SEAT_MAD_MONTHLY)
print('solo_trial', apply_trial_cap('solo','ai_credits',600,in_trial=True))
"
curl -s -o /dev/null -w 'home=%{http_code}\n' https://lexhub.space/
curl -s -o /dev/null -w 'addons_unauth=%{http_code}\n' https://lexhub.space/api/billing/addons
"""
_, o, e = c.exec_command(cmd, timeout=420)
print(o.read().decode(errors="replace")[-8000:])
err = e.read().decode(errors="replace")
if err.strip():
    print("stderr", err[-2000:])
c.close()
print("done")
