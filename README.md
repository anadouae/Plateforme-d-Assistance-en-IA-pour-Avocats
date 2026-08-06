# Sanad – Avocat AI Assistance

Plateforme SaaS juridique sécurisée pour les cabinets d'avocats marocains.

**WebVoice** · Projet de Fin d'Année · 2026

## Stack production

| Composant | Technologie |
|-----------|-------------|
| Frontend | Next.js 14, TypeScript, Tailwind, Zustand |
| Backend | FastAPI, SQLAlchemy, Alembic, JWT |
| Base de données | PostgreSQL 16 |
| Fichiers | MinIO + chiffrement AES (Fernet) |
| IA | Ollama `sanad-legal` + ChromaDB (~148K entrées) + BGE-M3 |
| Workers | Celery + Redis |
| Email | SMTP (Mailhog en dev) |

## Démarrage rapide (Docker — recommandé)

```bash
docker compose up -d --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000/docs |
| Mailhog | http://localhost:8025 |
| MinIO | http://localhost:9001 |

### Compte démo (optionnel)

Les seeds automatiques sont **désactivés** en production. Pour créer un compte démo manuellement :

```bash
docker compose exec backend python scripts/seed_demo.py
```

- `demo@sanad.ma` / `Sanad2026!`
- `admin@webvoice.ma` / `WebVoice2026!`

## Démarrage local (sans Docker)

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
# PostgreSQL + Redis + MinIO requis (voir docker-compose.yml)
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Sprints réalisés

### Sprint 1 — Mise en prod
- PostgreSQL + Alembic (migrations au démarrage)
- Auth complète : verify email, forgot/reset, refresh token
- SMTP : vérification, reset, invitations équipe
- MinIO + chiffrement fichiers (Fernet)
- Seeds démo supprimés du démarrage automatique

### Sprint 2 — Cœur IA
- ChromaDB + BGE-M3 + corpus juridique marocain enrichi (DOC, CPC, CPP, travail, commerce, Moudawana…)
- Pipeline Celery : upload → OCR → indexation
- Fallback sync avec indexation ChromaDB
- OCR Tesseract (fra+ara) + pdf2image pour PDF scannés
- Alertes OCR (`ocr_alert` si score < 70 %)
- Recherche web DuckDuckGo + Tavily
- **LLM local Sanad-Legal (Ollama)** — streaming SSE (`/api/chat/stream`)
- Analyse dossier : `POST /api/cases/{id}/analyse`

### Sprint 3 — À venir
- i18n complète, 2FA, Google OAuth, dashboard live, export PDF

## Modèle IA local (sans Groq)

```powershell
# 1. Installer Ollama (https://ollama.com)
# 2. Créer sanad-legal
cd backend
.\scripts\setup_sanad_legal.ps1

# 3. Réindexer le corpus
python scripts/reindex_corpus.py
```

Config `.env` : `LLM_PROVIDER=ollama`, `OLLAMA_MODEL=sanad-legal`, `LLM_ALLOW_CLOUD_FALLBACK=false`

Voir `backend/models/README.md`.

Voir `DEPLOY.md` pour le guide de déploiement production.
