#!/usr/bin/env python3
"""Deploy parrainage (referral) — BE + FE + alembic 034."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/alembic/versions/034_referral_parrainage.py",
    "backend/app/models/__init__.py",
    "backend/app/schemas/__init__.py",
    "backend/app/services/referral.py",
    "backend/app/services/billing.py",
    "backend/app/api/auth.py",
    "backend/app/api/billing.py",
    "frontend/src/lib/api.ts",
    "frontend/src/lib/register-draft.ts",
    "frontend/src/lib/landing-faq.ts",
    "frontend/src/components/auth/unified-auth.tsx",
    "frontend/src/components/home/landing-referral-section.tsx",
    "frontend/src/components/home/home-page-content.tsx",
    "frontend/src/components/layout/public-navbar.tsx",
    "frontend/src/components/layout/app-shell.tsx",
    "frontend/src/components/billing/referral-nudge-modal.tsx",
    "frontend/src/components/settings/billing-panel.tsx",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
sftp = c.open_sftp()
for rel in FILES:
    local = ROOT / rel
    remote = f"/opt/sanad/{rel}"
    # ensure remote dir
    parts = remote.rsplit("/", 1)[0]
    try:
        sftp.stat(parts)
    except OSError:
        c.exec_command(f"mkdir -p {parts}")
    sftp.put(str(local), remote)
    print("ok", rel)
sftp.close()

cmd = r"""
cd /opt/sanad
# ensure referral service dir file exists
ls -la backend/app/services/referral.py backend/alembic/versions/034_referral_parrainage.py
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml --env-file .env.vps restart backend frontend 2>&1 | tail -15
sleep 18
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend alembic upgrade head 2>&1 | tail -30
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.core.database import SessionLocal
from sqlalchemy import inspect
from app.services.referral import ensure_referral_code, REFEREE_BONUS_DAYS, REFERRER_REWARD_DAYS
from app.models import Cabinet

db = SessionLocal()
insp = inspect(db.bind)
cols = {c["name"] for c in insp.get_columns("cabinets")}
assert "referral_code" in cols, cols
assert "cabinet_referrals" in insp.get_table_names()
cab = db.query(Cabinet).first()
if cab:
    code = ensure_referral_code(db, cab.id)
    db.commit()
    print("code_ok", code, REFEREE_BONUS_DAYS, REFERRER_REWARD_DAYS)
else:
    print("no_cabinet")
db.close()
print("SMOKE_OK")
PY
curl -sf -o /dev/null -w 'home:%{http_code}\n' https://lexhub.space/
curl -sf -o /dev/null -w 'api_plans:%{http_code}\n' https://lexhub.space/api/billing/plans || true
"""
_, o, e = c.exec_command(cmd, timeout=300)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("err", err[-2500:])
c.close()
print("DONE")
