#!/usr/bin/env python3
"""Deploy admin fixes: theme, purge, AI credits by plan, activity report graphs."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/alembic/versions/035_plan_ai_credits.py",
    "backend/app/models/__init__.py",
    "backend/app/services/cabinet_purge.py",
    "backend/app/services/billing.py",
    "backend/app/api/admin.py",
    "backend/app/api/billing.py",
    "frontend/src/components/layout/admin-shell.tsx",
    "frontend/src/app/admin/plans/page.tsx",
    "frontend/src/app/admin/cabinets/page.tsx",
    "frontend/src/lib/api.ts",
    "frontend/src/styles/sanad-ui.css",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
sftp = c.open_sftp()
for rel in FILES:
    remote = f"/opt/sanad/{rel}"
    parts = remote.rsplit("/", 1)[0]
    try:
        sftp.stat(parts)
    except OSError:
        c.exec_command(f"mkdir -p {parts}")
    sftp.put(str(ROOT / rel), remote)
    print("ok", rel)
sftp.close()

cmd = r"""
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml --env-file .env.vps exec -T backend alembic upgrade head 2>&1 | tail -20
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml --env-file .env.vps restart backend frontend 2>&1 | tail -15
sleep 22
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml --env-file .env.vps exec -T backend python -c "
from app.services.cabinet_purge import purge_cabinet
from app.services.billing import plan_ai_credits_limit
from app.models import SubscriptionPlan
print('imports_ok')
" 2>&1 | tail -10
curl -sf -o /dev/null -w 'plans:%{http_code}\n' https://lexhub.space/api/billing/plans || true
curl -sf -o /dev/null -w 'admin:%{http_code}\n' https://lexhub.space/admin || true
"""
_, o, e = c.exec_command(cmd, timeout=240)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace"))
c.close()
print("DONE")
