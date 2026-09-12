#!/usr/bin/env python3
"""Deploy pack payment flow + lots expiry + UI gates."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"
FILES = [
    "backend/alembic/versions/037_credit_pack_lots_expiry.py",
    "backend/app/models/__init__.py",
    "backend/app/services/billing.py",
    "backend/app/api/billing.py",
    "frontend/src/lib/api.ts",
    "frontend/src/components/settings/billing-panel.tsx",
    "frontend/src/components/billing/pack-checkout-modal.tsx",
    "frontend/src/components/billing/credits-exhausted-modal.tsx",
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
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d --force-recreate backend frontend 2>&1 | tail -25
sleep 8
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend alembic upgrade head 2>&1 | tail -20
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend alembic current 2>&1
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python -c "
from app.services.billing import is_active_paying, CREDIT_PACKS, PACK_EXPIRY_MONTHS
from types import SimpleNamespace
print('packs', len(CREDIT_PACKS), 'expiry_m', PACK_EXPIRY_MONTHS)
print('checkout_fn', hasattr(__import__('app.services.billing', fromlist=['start_credit_pack_checkout']), 'start_credit_pack_checkout'))
"
curl -s -o /dev/null -w 'home=%{http_code}\n' https://lexhub.space/
"""
_, o, e = c.exec_command(cmd, timeout=420)
print(o.read().decode(errors="replace")[-6000:])
err = e.read().decode(errors="replace")
if err.strip():
    print("stderr", err[-1500:])
c.close()
print("done")
