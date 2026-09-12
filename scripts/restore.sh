#!/usr/bin/env bash
# Restauration Sanad depuis un dossier créé par scripts/backup.sh
#
# PROCÉDURE (urgence / test avant prod) :
# 1. Arrêter l'app : docker compose stop backend celery-worker frontend
# 2. Choisir un backup : ls backups/
# 3. Restaurer : bash scripts/restore.sh backups/YYYYMMDD_HHMMSS
# 4. Redémarrer : docker compose up -d
# 5. Vérifier : curl -s localhost:8001/health && ouvrir le frontend
#
# Test restauration (même VPS, dossier parallèle) :
#   mkdir -p /tmp/sanad-restore-test && cp -a backups/LATEST /tmp/sanad-restore-test/
#   # restaurer DB dans un conteneur postgres jetable si besoin, puis valider le dump :
#   docker compose exec -T postgres pg_restore -U sanad -d sanad --list < backups/.../sanad.dump | head
set -euo pipefail

SRC="${1:-}"
if [[ -z "$SRC" || ! -d "$SRC" ]]; then
  echo "Usage: bash scripts/restore.sh backups/YYYYMMDD_HHMMSS"
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "[restore] from $SRC"
echo "[restore] ATTENTION: écrase la DB et/ou les fichiers actuels."

read -r -p "Confirmer restauration ? (yes/NO) " CONFIRM
if [[ "$CONFIRM" != "yes" ]]; then
  echo "Annulé."
  exit 0
fi

docker compose stop backend celery-worker || true

DUMP_FILE=""
if [[ -f "$SRC/lexhub.dump" ]]; then
  DUMP_FILE="$SRC/lexhub.dump"
elif [[ -f "$SRC/sanad.dump" ]]; then
  DUMP_FILE="$SRC/sanad.dump"
fi

if [[ -n "$DUMP_FILE" ]]; then
  echo "[restore] PostgreSQL depuis $DUMP_FILE…"
  PG_USER="${POSTGRES_USER:-lexhub}"
  PG_DB="${POSTGRES_DB:-lexhub}"
  if ! docker compose exec -T postgres pg_isready -U "$PG_USER" >/dev/null 2>&1; then
    PG_USER="sanad"
    PG_DB="sanad"
  fi
  # Drop/recreate schema objects via pg_restore --clean
  docker compose exec -T postgres pg_restore -U "$PG_USER" -d "$PG_DB" --clean --if-exists < "$DUMP_FILE" \
    || echo "[restore] WARN: pg_restore a signalé des erreurs (souvent OK si objets déjà absents)"
  echo "[restore] DB OK"
fi

if [[ -f "$SRC/uploads.tar.gz" ]]; then
  echo "[restore] uploads/…"
  rm -rf "$ROOT/uploads"
  tar xzf "$SRC/uploads.tar.gz" -C "$ROOT"
  echo "[restore] uploads OK"
fi

if [[ -f "$SRC/minio_data.tar.gz" ]]; then
  VOL="$(docker volume ls -q | grep -E 'minio|avocat.*minio' | head -n1 || true)"
  if [[ -n "$VOL" ]]; then
    echo "[restore] MinIO volume $VOL…"
    docker run --rm -v "$VOL":/data -v "$(cd "$SRC" && pwd)":/in alpine \
      sh -c 'rm -rf /data/* /data/.[!.]* 2>/dev/null; tar xzf /in/minio_data.tar.gz -C /data'
    echo "[restore] MinIO OK"
  else
    echo "[restore] WARN: volume MinIO introuvable — skip"
  fi
fi

docker compose up -d
echo "[restore] terminé. Vérifier : curl -s http://localhost:8001/health"
