#!/usr/bin/env python3
"""Deploy fair-use AI quotas + anti-abuse (daily caps, slots, locks)."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/app/services/billing.py",
    "backend/app/core/rate_limit.py",
    "backend/app/core/config.py",
    "backend/app/api/dictation.py",
    "backend/app/api/cases.py",
    "backend/app/api/documents.py",
    "backend/app/api/billing.py",
    "backend/app/api/summarize.py",
    "backend/app/services/plaidoirie_revise.py",
    "backend/app/services/plaidoirie_case_compose.py",
    "backend/app/services/cle_de_barre.py",
    "frontend/src/lib/billing-plans-fallback.ts",
    "frontend/src/lib/api.ts",
    "frontend/src/components/settings/billing-panel.tsx",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
sftp = c.open_sftp()
for rel in FILES:
    local = ROOT / rel
    if not local.exists():
        print("SKIP missing", rel)
        continue
    sftp.put(str(local), f"/opt/sanad/{rel}")
    print("ok", rel)
sftp.close()

cmd = r"""
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart backend celery-worker frontend 2>&1 | tail -10
sleep 16
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
import ast, pathlib
for p in [
  'app/api/dictation.py','app/api/documents.py','app/api/cases.py','app/services/billing.py','app/core/rate_limit.py'
]:
  ast.parse(pathlib.Path(p).read_text())
  print('syntax_ok', p)
from app.services.billing import AI_MONTHLY_LIMITS, AI_DAILY_CREDIT_CAPS, begin_ai_action, openai_model_for_plan
assert AI_MONTHLY_LIMITS['enterprise']['ai_credits'] == 5000
assert AI_MONTHLY_LIMITS['free']['ai_credits'] == 50
assert AI_DAILY_CREDIT_CAPS['pro'] == 180
assert openai_model_for_plan('free','compose') == 'gpt-4o-mini'
assert 'gpt-4o' in openai_model_for_plan('pro','compose')
from app.core.database import SessionLocal
from app.services.billing import ensure_default_plans, get_entitlements
from app.models import Cabinet
db=SessionLocal(); ensure_default_plans(db); db.commit()
cab=db.query(Cabinet).first()
ent=get_entitlements(db, cab.id)
d=ent.to_dict()
assert d['usage']['ai_credits_limit'] in (50,600,2000,5000) or d['usage']['ai_credits_limit']>0
assert 'ai_daily_limit' in d
print('plan', ent.plan.slug, 'credits', d['usage']['ai_credits_limit'], 'daily', d['ai_daily_limit'], 'pleas', d['usage']['plaidoiries_limit'])
db.close()
print('SMOKE_OK')
PY
curl -sf -o /dev/null -w 'web:%{http_code}\n' https://lexhub.space/
"""
_, o, e = c.exec_command(cmd, timeout=240)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("err", err[-1000:])
c.close()
print("DONE")
