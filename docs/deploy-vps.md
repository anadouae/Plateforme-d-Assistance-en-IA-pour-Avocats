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

## Sur le VPS (quand SSH marche)

```bash
ssh -p 51008 -i ~/.ssh/sanad_vps_openssh root@51.38.78.22
# cloner / rsync le repo, puis :
bash scripts/deploy-vps.sh
```

Ou manuellement :

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
