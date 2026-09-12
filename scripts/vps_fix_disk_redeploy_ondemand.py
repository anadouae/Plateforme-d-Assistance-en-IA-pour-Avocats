#!/usr/bin/env python3
"""Free disk + restart services with volume copy (no full rebuild)."""
from pathlib import Path
import paramiko

PASSWORD = "P@s$wiy.O0p"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)

cmd = r"""
set -e
df -h / | tail -1
docker builder prune -af >/tmp/prune1.txt 2>&1 || true
docker image prune -af >/tmp/prune2.txt 2>&1 || true
# remove dangling build cache / unused
docker system prune -af >/tmp/prune3.txt 2>&1 || true
journalctl --vacuum-size=80M >/dev/null 2>&1 || true
# trim apt cache if present
apt-get clean >/dev/null 2>&1 || true
df -h / | tail -1
tail -3 /tmp/prune1.txt /tmp/prune2.txt /tmp/prune3.txt 2>/dev/null || true

cd /opt/sanad
# How are services mounted?
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml --env-file .env.vps config 2>/dev/null | grep -A2 'source:' | head -40 || true

# Prefer restart without rebuild: copy into running containers if needed
# Backend: usually bind-mounted or image-copied — restart after alembic
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml --env-file .env.vps exec -T backend alembic upgrade head 2>&1 | tail -15

# Copy changed source into frontend/backend containers then restart processes
BE=$(docker compose -f docker-compose.yml -f docker-compose.lexhub.yml --env-file .env.vps ps -q backend | head -1)
FE=$(docker compose -f docker-compose.yml -f docker-compose.lexhub.yml --env-file .env.vps ps -q frontend | head -1)
echo "BE=$BE FE=$FE"

if [ -n "$BE" ]; then
  docker cp /opt/sanad/backend/app/services/billing.py "$BE":/app/app/services/billing.py
  docker cp /opt/sanad/backend/app/api/billing.py "$BE":/app/app/api/billing.py
  docker cp /opt/sanad/backend/app/models/__init__.py "$BE":/app/app/models/__init__.py
  docker cp /opt/sanad/backend/alembic/versions/033_on_demand_ai.py "$BE":/app/alembic/versions/033_on_demand_ai.py || true
  docker restart "$BE"
  echo backend_restarted
fi

# Frontend Next.js needs rebuild of pages — try lightweight rebuild if space OK
AVAIL=$(df -B1 / | awk 'NR==2{print $4}')
echo avail_bytes=$AVAIL
if [ "$AVAIL" -gt 3000000000 ] && [ -n "$FE" ]; then
  docker compose -f docker-compose.yml -f docker-compose.lexhub.yml --env-file .env.vps up -d --build frontend 2>&1 | tail -30
else
  echo "SKIP_FULL_FE_BUILD — try copy + next build inside container"
  if [ -n "$FE" ]; then
    docker cp /opt/sanad/frontend/src/lib/api.ts "$FE":/app/src/lib/api.ts 2>/dev/null || docker cp /opt/sanad/frontend/src/lib/api.ts "$FE":/usr/src/app/src/lib/api.ts 2>/dev/null || true
    docker cp /opt/sanad/frontend/src/components/settings/billing-panel.tsx "$FE":/app/src/components/settings/billing-panel.tsx 2>/dev/null || true
    docker cp /opt/sanad/frontend/src/app/settings/page.tsx "$FE":/app/src/app/settings/page.tsx 2>/dev/null || true
    # detect workdir
    docker exec "$FE" sh -c 'pwd; ls; ls src 2>/dev/null | head'
  fi
fi

sleep 12
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml --env-file .env.vps exec -T backend alembic upgrade head 2>&1 | tail -10
curl -sf -o /dev/null -w 'web:%{http_code}\n' https://lexhub.space/
"""

_, o, e = c.exec_command(cmd, timeout=420)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("STDERR", err[-2500:])
c.close()
print("DONE")
