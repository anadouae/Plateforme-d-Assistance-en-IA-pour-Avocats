#!/usr/bin/env python3
"""Restart FE/BE on bind mounts + migrate (no docker build)."""
import paramiko

PASSWORD = "P@s$wiy.O0p"
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)

cmd = r"""
set -e
cd /opt/sanad
df -h / | tail -1
# clear leftover build junk
docker builder prune -af >/dev/null 2>&1 || true
rm -rf /var/lib/docker/tmp/* 2>/dev/null || true
df -h / | tail -1

# Confirm files on host
grep -n "on-demand\|Usage à la demande\|Plan & usage" frontend/src/components/settings/billing-panel.tsx | head -10
grep -n "update_on_demand\|OnDemandUpdate" backend/app/api/billing.py | head -5
grep -n "SettingsSection\|Plan & usage" frontend/src/app/settings/page.tsx | head -8
test -f backend/alembic/versions/033_on_demand_ai.py && echo mig033_ok

# Restart only (bind mounts already have new code)
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml --env-file .env.vps restart backend frontend celery-worker 2>&1 | tail -20
sleep 20
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml --env-file .env.vps exec -T backend alembic upgrade head 2>&1 | tail -20

# Frontend prod often needs rebuild of .next — check CMD
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml --env-file .env.vps ps frontend
FE=$(docker compose -f docker-compose.yml -f docker-compose.lexhub.yml --env-file .env.vps ps -q frontend)
docker inspect "$FE" --format '{{.Config.Cmd}} {{.Config.Entrypoint}}'
# If next start (prod), rebuild inside container using host node_modules
docker exec "$FE" sh -c 'cd /app && (npm run build 2>&1 | tail -40)' || echo BUILD_FAILED
docker restart "$FE"
sleep 15

docker compose -f docker-compose.yml -f docker-compose.lexhub.yml --env-file .env.vps exec -T backend python - <<'PY'
from app.core.database import SessionLocal
from app.services.billing import get_entitlements, AI_OVERAGE_MAD_PER_CREDIT
from app.models import Cabinet
from sqlalchemy import inspect
db=SessionLocal()
insp=inspect(db.bind)
assert "on_demand_enabled" in {c["name"] for c in insp.get_columns("cabinet_subscriptions")}
cab=db.query(Cabinet).first()
d=get_entitlements(db, cab.id).to_dict()
print("OK", d.get("on_demand_enabled"), d.get("on_demand_mad_per_credit"), AI_OVERAGE_MAD_PER_CREDIT)
db.close()
PY

curl -sf -o /dev/null -w 'web:%{http_code}\n' https://lexhub.space/
curl -sf https://lexhub.space/settings 2>/dev/null | grep -o 'Plan & usage\|الخطة والاستخدام\|abonnement\|Usage à la demande' | head -5 || echo 'html_check_skip'
"""

_, o, e = c.exec_command(cmd, timeout=600)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("STDERR", err[-3000:])
c.close()
print("DONE")
