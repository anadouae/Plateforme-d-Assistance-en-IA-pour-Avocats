#!/usr/bin/env bash
# Sanad — déploiement VPS Linux (Debian/Ubuntu)
# Prérequis : SSH ouvert, Docker + Compose installés
# Usage: bash scripts/deploy-vps.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Sanad deploy VPS"
echo "Repo: $ROOT"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker manquant. Installez Docker Engine puis relancez."
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose plugin manquant."
  exit 1
fi

# Secrets prod (créer une fois)
if [[ ! -f .env.vps ]]; then
  echo "Création .env.vps — changez SECRET_KEY / ENCRYPTION_KEY"
  cat > .env.vps <<'EOF'
ENVIRONMENT=production
SECRET_KEY=change-me-strong-random-64chars
ENCRYPTION_KEY=
CORS_ORIGINS=http://localhost:3000
FRONTEND_URL=http://localhost:3000
WHISPER_ENABLED=true
WHISPER_MODEL=medium
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
OLLAMA_SYNTHESIS_MODEL=mistral
SEED_DEMO_DATA=false
EOF
fi

echo "==> Build & up (Postgres Docker + Whisper + Ollama)"
docker compose --env-file .env.vps -f docker-compose.yml -f docker-compose.prod.yml up -d --build

echo "==> Attente backend..."
for i in $(seq 1 60); do
  if curl -sf http://127.0.0.1:8001/health/live >/dev/null 2>&1; then
    echo "Backend OK"
    break
  fi
  sleep 3
done

echo "==> Seed comptes démo (optionnel)"
docker compose exec -T backend python scripts/seed_test_accounts.py || true

echo "==> Ollama mistral (synthèse)"
docker compose exec -T ollama ollama pull mistral || true

echo ""
echo "Déployé. Frontend: port 3000 | API: port 8001"
echo "Login démo: demo@sanad.ma / Sanad2026!"
echo "Whisper: Micro Whisper sur /redaction"
echo ""
echo "NOTE: tant que le SSH port VPS est fermé, lancez ce script UNIQUEMENT quand l'accès SSH marche."
