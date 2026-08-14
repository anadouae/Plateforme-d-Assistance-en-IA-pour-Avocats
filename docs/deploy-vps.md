# Déploiement VPS — Sanad

## Décision stack

| Composant | Choix VPS |
|-----------|-----------|
| Base | **PostgreSQL Docker** (dans Compose) |
| STT | **faster-whisper** local (`medium`, CPU int8) |
| Correction | Mistral cloud / Ollama |
| Dictée secours | Chrome Web Speech |

Le port SSH fermé **n’empêche pas** de préparer le code. Il empêche seulement de **pousser** sur le serveur tant qu’il n’est pas ouvert.

## Chez toi (dev)

```bash
docker compose up -d postgres redis minio ollama backend
# rebuild si deps Whisper changent :
docker compose build backend
docker compose up -d backend
docker compose exec backend python scripts/seed_test_accounts.py
cd frontend && npm run dev
```

Plaidoirie → **Micro Whisper** → Stop → texte → **Corriger**.

## Images registry (sans rebuild)

Par défaut **GHCR** (publiées par GitHub Actions) :

- `ghcr.io/anadouae/sanad-backend`
- `ghcr.io/anadouae/sanad-celery`
- `ghcr.io/anadouae/sanad-frontend`

(Anciennes images Docker Hub encore dispo : `anadouae1/sanad-*` — `SANAD_REGISTRY=docker.io/anadouae1`.)

Sur n’importe quelle machine (après clone du repo pour le `docker-compose`) :

```bash
# si packages GHCR privés :
# echo YOUR_GITHUB_PAT | docker login ghcr.io -u YOUR_GITHUB_USER --password-stdin

docker compose -f docker-compose.yml -f docker-compose.pull.yml pull
docker compose -f docker-compose.yml -f docker-compose.pull.yml up -d
```

Republier : push sur `main` (dossiers `backend/` ou `frontend/`) ou **Actions → Publish Sanad Docker images → Run workflow**.

Push manuel depuis ton PC (si le réseau Docker Hub/GHCR répond) :

```bash
docker tag avocat-ai-assistance-backend:latest ghcr.io/anadouae/sanad-backend:latest
docker tag avocat-ai-assistance-backend:latest ghcr.io/anadouae/sanad-celery:latest
docker tag avocat-ai-assistance-frontend:latest ghcr.io/anadouae/sanad-frontend:latest
echo YOUR_GITHUB_PAT | docker login ghcr.io -u YOUR_GITHUB_USER --password-stdin
docker push ghcr.io/anadouae/sanad-backend:latest
docker push ghcr.io/anadouae/sanad-celery:latest
docker push ghcr.io/anadouae/sanad-frontend:latest
```

## Sur le VPS (quand SSH marche)

```bash
ssh -p 51008 -i ~/.ssh/sanad_vps_openssh root@51.38.78.22
# cloner / rsync le repo, puis :
bash scripts/deploy-vps.sh
```

Ou manuellement (pull images, sans `--build`) :

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.pull.yml --env-file .env.vps pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.pull.yml --env-file .env.vps up -d
docker compose exec backend python scripts/seed_test_accounts.py
```

Ou avec rebuild local :

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.vps up -d --build
docker compose exec backend python scripts/seed_test_accounts.py
```

## Variables Whisper

- `WHISPER_ENABLED=true`
- `WHISPER_MODEL=medium` (ou `small` si RAM faible, `large-v3` si serveur costaud)
- `WHISPER_DEVICE=cpu`
- `WHISPER_COMPUTE_TYPE=int8`

## Base de données

Compose force :

`postgresql://sanad:sanad_secret@postgres:5432/sanad`

→ indépendant de Neon dans le `.env` Windows. Neon reste optionnel pour un usage cloud séparé plus tard.

## Backups / logs / rate limits (prod)

Voir **[BACKUP_RESTORE.md](./BACKUP_RESTORE.md)** (pg_dump + MinIO, rétention 7j, restore testée).

Limites par défaut (prod, `DEBUG=false`) :

- Login : 5 / min / IP
- Code cabinet : 10 / min / IP
- Upload documents : 20 / min / utilisateur
