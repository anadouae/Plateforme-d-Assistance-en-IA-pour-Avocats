#!/usr/bin/env python3
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/alembic/versions/035_plan_ai_credits.py",
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
grep -E '^revision|^down_revision' backend/alembic/versions/035_plan_ai_credits.py
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml --env-file .env.vps exec -T -w /app backend alembic upgrade head 2>&1 | tail -25
# fallback SQL if alembic still fails
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml --env-file .env.vps exec -T -w /app backend python -c "from sqlalchemy import text; from app.core.database import SessionLocal; db=SessionLocal(); cols=[r[0] for r in db.execute(text(\"SELECT column_name FROM information_schema.columns WHERE table_name='subscription_plans'\")).fetchall()]; print(sorted(cols));
import sys
if 'max_ai_credits_month' not in cols:
 db.execute(text('ALTER TABLE subscription_plans ADD COLUMN max_ai_credits_month INTEGER NOT NULL DEFAULT 50'));
 db.execute(text(\"UPDATE subscription_plans SET max_ai_credits_month=50 WHERE slug='free'\"));
 db.execute(text(\"UPDATE subscription_plans SET max_ai_credits_month=600 WHERE slug='solo'\"));
 db.execute(text(\"UPDATE subscription_plans SET max_ai_credits_month=2000 WHERE slug='pro'\"));
 db.execute(text(\"UPDATE subscription_plans SET max_ai_credits_month=5000 WHERE slug='enterprise'\"));
 db.commit(); print('ADDED')
else: print('EXISTS')
db.close()" 2>&1 | tail -30
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml --env-file .env.vps restart backend 2>&1 | tail -5
sleep 16
curl -sf -o /dev/null -w 'plans:%{http_code}\n' https://lexhub.space/api/billing/plans
curl -s https://lexhub.space/api/billing/plans | head -c 600
echo
"""
_, o, e = c.exec_command(cmd, timeout=200)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace"))
c.close()
