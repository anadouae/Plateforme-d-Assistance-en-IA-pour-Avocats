# Sauvegardes & restauration — LexHub (VPS unique)

## Backup automatique

```bash
# Une fois
chmod +x scripts/backup.sh scripts/restore.sh
mkdir -p backups /var/log/sanad

# Cron quotidien 02:30
crontab -e
# 30 2 * * * cd /opt/sanad && bash scripts/backup.sh >> /var/log/sanad/backup.log 2>&1
```

Contenu d’un dump : `lexhub.dump` (PostgreSQL custom + copie miroir `sanad.dump`), `minio_data.tar.gz` et/ou `uploads.tar.gz`.  
Rétention : **7 jours** (`BACKUP_RETENTION_DAYS`).

## Restauration (urgence)

1. `docker compose stop backend celery-worker`
2. `bash scripts/restore.sh backups/YYYYMMDD_HHMMSS` → confirmer `yes`
3. `docker compose up -d`
4. Vérifier `curl -s http://localhost:8001/health` + login frontend

## Test de restauration (à faire avant la prod)

Sur Windows (dev) — validation dump seulement :

```powershell
powershell -File scripts/backup-smoke.ps1
```

Sur le VPS (Linux) — backup + restore :

```bash
bash scripts/backup.sh
# Noter le dossier créé sous backups/
docker compose exec -T postgres pg_restore -U lexhub -d lexhub --list < backups/.../lexhub.dump | head
bash scripts/restore.sh backups/...   # sur un environnement de test de préférence
```

Si le dump se liste et que `/health` répond après restore → procédure validée.

## Logs

- Backend : JSON stdout (`LOG_JSON=true`) + header `X-Request-ID`
- Rotation : `deploy/logrotate-sanad.conf` → `/etc/logrotate.d/sanad`
- Optionnel : `SENTRY_DSN=...` (tier gratuit) pour dashboard d’erreurs

## Espace disque

Surveiller `df -h` : garder au moins **2×** la taille du plus gros backup libre.  
Ajuster `BACKUP_RETENTION_DAYS` si le disque est petit.
