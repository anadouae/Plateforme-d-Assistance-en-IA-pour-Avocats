#!/usr/bin/env python3
"""Deploy on-demand AI spending + Plan & usage settings UI."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/app/services/billing.py",
    "backend/app/models/__init__.py",
    "backend/alembic/versions/033_on_demand_ai.py",
    "backend/app/api/billing.py",
    "frontend/src/lib/api.ts",
    "frontend/src/components/settings/billing-panel.tsx",
    "frontend/src/app/settings/page.tsx",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
sftp = c.open_sftp()
for rel in FILES:
    sftp.put(str(ROOT / rel), f"/opt/sanad/{rel}")
    print("ok", rel)
sftp.close()

cmd = r"""
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml --env-file .env.vps up -d --build backend frontend 2>&1 | tail -40
sleep 25
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend alembic upgrade head 2>&1 | tail -25
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.core.database import SessionLocal
from app.services.billing import (
    AI_OVERAGE_MAD_PER_CREDIT,
    set_on_demand_settings,
    get_entitlements,
    ensure_default_plans,
)
from app.models import Cabinet, CabinetSubscription
from sqlalchemy import inspect

db = SessionLocal()
ensure_default_plans(db)
db.commit()
insp = inspect(db.bind)
cols = {c["name"] for c in insp.get_columns("cabinet_subscriptions")}
assert "on_demand_enabled" in cols, cols
ucols = {c["name"] for c in insp.get_columns("usage_counters")}
assert "ai_overage_credits" in ucols, ucols
assert AI_OVERAGE_MAD_PER_CREDIT == 0.25
cab = db.query(Cabinet).first()
if cab:
    ent = get_entitlements(db, cab.id)
    d = ent.to_dict()
    assert "on_demand_enabled" in d
    assert "on_demand_available" in d
    print("ent_ok", ent.plan.slug, d["on_demand_enabled"], d["usage"].get("ai_overage_mad_estimate"))
else:
    print("no_cabinet_skip")
db.close()
print("SMOKE_OK")
PY
curl -sf -o /dev/null -w 'web:%{http_code}\n' https://lexhub.space/
curl -sf -o /dev/null -w 'settings:%{http_code}\n' https://lexhub.space/settings || true
"""
_, o, e = c.exec_command(cmd, timeout=600)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("err", err[-2000:])
c.close()
print("DONE")
