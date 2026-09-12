#!/usr/bin/env bash
# Sauvegarde LexHub : PostgreSQL + fichiers MinIO — rétention 7 jours.
# Usage (VPS) :
#   cd /opt/sanad && bash scripts/backup.sh
# Automatique : cron quotidien 02:30 (installé sur le VPS).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -f "$ROOT/docker-compose.lexhub.yml" ]]; then
  DC=(docker compose -f docker-compose.yml -f docker-compose.lexhub.yml)
else
  DC=(docker compose)
fi

BACKUP_ROOT="${BACKUP_DIR:-$ROOT/backups}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
STAMP="$(date -u +%Y%m%d_%H%M%S)"
DEST="$BACKUP_ROOT/$STAMP"
mkdir -p "$DEST"

echo "[backup] start $STAMP → $DEST"

# --- PostgreSQL ---
PG_USER=""
PG_DB=""
for u in "${POSTGRES_USER:-lexhub}" "lexhub" "sanad"; do
  if "${DC[@]}" exec -T postgres pg_isready -U "$u" >/dev/null 2>&1; then
    PG_USER="$u"
    break
  fi
done

if [[ -n "$PG_USER" ]]; then
  if "${DC[@]}" exec -T postgres psql -U "$PG_USER" -d "${POSTGRES_DB:-lexhub}" -c "SELECT 1" >/dev/null 2>&1; then
    PG_DB="${POSTGRES_DB:-lexhub}"
  else
    PG_DB="sanad"
  fi
  "${DC[@]}" exec -T postgres pg_dump -U "$PG_USER" -d "$PG_DB" -Fc > "$DEST/lexhub.dump"
  cp -f "$DEST/lexhub.dump" "$DEST/sanad.dump" 2>/dev/null || true
  sz="$(du -h "$DEST/lexhub.dump" | cut -f1)"
  echo "[backup] postgres OK ($sz) [user=$PG_USER db=$PG_DB]"
else
  echo "[backup] WARN: postgres indisponible — skip DB"
fi

# --- Fichiers documents (volume MinIO) ---
if "${DC[@]}" ps 2>/dev/null | grep -qi minio; then
  VOL="$(docker volume ls -q | grep -E 'minio' | head -n1 || true)"
  if [[ -n "$VOL" ]]; then
    docker run --rm -v "$VOL":/data -v "$DEST":/out alpine \
      tar czf /out/minio_data.tar.gz -C /data .
    echo "[backup] minio volume OK"
  else
    echo "[backup] WARN: volume MinIO introuvable"
  fi
fi

if [[ -d "$ROOT/uploads" ]]; then
  tar czf "$DEST/uploads.tar.gz" -C "$ROOT" uploads
  echo "[backup] uploads/ OK"
fi

cat > "$DEST/MANIFEST.txt" <<EOF
LexHub backup $STAMP
retention_days=$RETENTION_DAYS
contents:
$(ls -la "$DEST")
EOF

find "$BACKUP_ROOT" -mindepth 1 -maxdepth 1 -type d -mtime +"$RETENTION_DAYS" -exec rm -rf {} +
echo "[backup] done. Kept last ${RETENTION_DAYS} days under $BACKUP_ROOT"
