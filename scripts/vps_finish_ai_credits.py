#!/usr/bin/env python3
import paramiko

PASSWORD = "P@s$wiy.O0p"
cmd = r"""
cd /opt/sanad
grep -n 'ai_credits_used\|spend_ai_action\|assert_can_use_ai_action' backend/app/services/billing.py | head -8
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart backend celery-worker 2>&1 | tail -6
sleep 14
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend alembic upgrade head 2>&1 | tail -20
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.core.database import SessionLocal, engine
from sqlalchemy import text
from app.services.billing import assert_can_use_ai_action, spend_ai_action, AI_ACTION_CREDITS, ensure_default_plans, get_entitlements
from app.models import Cabinet

with engine.connect() as conn:
    cols = [r[0] for r in conn.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name='usage_counters' ORDER BY column_name"
    ))]
print('cols', cols)
assert 'ai_credits_used' in cols
assert 'revise_count' in cols
db = SessionLocal()
ensure_default_plans(db)
db.commit()
cab = db.query(Cabinet).first()
ent = get_entitlements(db, cab.id)
print('plan', ent.plan.slug, 'credits', ent.ai_credits_limit, 'pleas', ent.plaidoiries_limit)
print('costs', AI_ACTION_CREDITS)
db.close()
print('READY')
PY
"""

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
_, o, e = c.exec_command(cmd, timeout=180)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("STDERR", err[-800:])
c.close()
