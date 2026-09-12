#!/usr/bin/env python3
"""Deploy AI credits quotas by plan + migrate usage_counters."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/app/services/billing.py",
    "backend/app/models/__init__.py",
    "backend/alembic/versions/032_ai_credits_usage.py",
    "backend/app/api/dictation.py",
    "backend/app/api/cases.py",
    "backend/app/api/documents.py",
    "backend/app/api/summarize.py",
    "backend/app/services/plaidoirie_revise.py",
    "frontend/src/lib/api.ts",
    "frontend/src/lib/billing-plans-fallback.ts",
    "frontend/src/components/settings/billing-panel.tsx",
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
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml --env-file .env.vps up -d backend celery-worker frontend 2>&1 | tail -20
sleep 18
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend alembic upgrade head 2>&1 | tail -20
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.core.database import SessionLocal
from app.services.billing import (
    AI_ACTION_CREDITS, AI_MONTHLY_LIMITS, ensure_default_plans,
    ai_credit_cost, assert_can_use_ai_action, spend_ai_action, get_entitlements,
)
from app.models import Cabinet

assert ai_credit_cost('compose') == 10
assert ai_credit_cost('revise') == 5
assert AI_MONTHLY_LIMITS['free']['ai_credits'] == 100
assert AI_MONTHLY_LIMITS['pro']['ai_credits'] == 3000

db = SessionLocal()
ensure_default_plans(db)
db.commit()
cab = db.query(Cabinet).first()
if cab:
    ent = get_entitlements(db, cab.id)
    d = ent.to_dict()
    assert 'ai_credits_limit' in d['usage']
    assert d.get('ai_credit_costs', {}).get('compose') == 10
    print('ent_ok', ent.plan.slug, d['usage']['ai_credits_limit'], d['usage']['plaidoiries_limit'])
else:
    print('no_cabinet_skip')
db.close()
print('SMOKE_OK')
PY
curl -sf -o /dev/null -w 'web:%{http_code}\n' https://lexhub.space/
"""
_, o, e = c.exec_command(cmd, timeout=300)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("err", err[-1200:])
c.close()
print("DONE")
