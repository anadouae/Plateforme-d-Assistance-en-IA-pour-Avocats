#!/bin/bash
set -euo pipefail
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml --env-file .env.vps up -d --build
for i in $(seq 1 90); do
  curl -sf http://127.0.0.1:8001/health/live >/dev/null && break
  sleep 5
done
curl -sf http://127.0.0.1:8001/health/live
docker compose exec -T backend python scripts/seed_test_accounts.py || true
for i in $(seq 1 60); do
  curl -sf http://127.0.0.1:3000/ >/dev/null && break
  sleep 5
done
curl -sf http://127.0.0.1:3000/ >/dev/null
systemctl reload caddy || systemctl restart caddy
curl -sfI https://lexhub.space/ | head -5
echo DEPLOY_OK
