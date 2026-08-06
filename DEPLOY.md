# Sanad — Déploiement Production (Sprint 1 + 2)

## Stack haut niveau (100% open-source / free tier)

| Composant | Technologie |
|-----------|-------------|
| Base de données | **PostgreSQL 16** |
| Cache / Queue | **Redis 7** |
| Workers async | **Celery** |
| Stockage fichiers | **MinIO** (S3-compatible) + chiffrement AES Fernet |
| Vector DB | **ChromaDB** (persistant) |
| Embeddings | **BGE-M3** (sentence-transformers) |
| LLM | **Ollama `sanad-legal`** (local) — Groq optionnel désactivé par défaut |
| Web search | **DuckDuckGo** (gratuit) |
| Email | **SMTP** (Mailhog en dev) |
| Migrations | **Alembic** |

## Démarrage rapide (Docker)

```bash
# 1. Cloner et configurer
cp backend/.env.example backend/.env
# Installer Ollama puis: cd backend && ./scripts/setup_sanad_legal.sh
# (Windows: .\scripts\setup_sanad_legal.ps1)

# 2. Lancer toute la stack
docker compose up -d --build

# 3. Accès
# Frontend : http://localhost:3000
# API      : http://localhost:8000/health
# MinIO    : http://localhost:9001 (sanad_minio / sanad_minio_secret)
# Mailhog  : http://localhost:8025 (emails de test)
```

## Flux auth complet

1. **Inscription** → email vérification (Mailhog)
2. **Clic lien** → `/confirm-email?token=...` → `GET /api/auth/verify-email`
3. **Admin WebVoice** → approuve cabinet → `PATCH /api/admin/cabinets/{id}/approve`
4. **Connexion** → JWT access + refresh
5. **Mot de passe oublié** → `/forgot-password` → email reset

## Pipeline documents (Celery)

```
Upload → MinIO (chiffré) → Celery task
  → Extraction PDF/DOCX
  → OCR Tesseract (images/scans)
  → Alerte si OCR < 70%
  → Indexation ChromaDB (BGE-M3)
  → Statut INDEXED
```

## Pipeline IA

```
Question → Routeur (parallèle si besoin)
  → Document RAG (ChromaDB par dossier)
  → Corpus juridique RAG (~148K entrées)
  → Web DuckDuckGo/Tavily (URLs citées, cache 5 min)
  → sanad-legal (Ollama) rédige à partir des extraits
  → Citations + score confiance + SSE streaming
```

## Comptes démo (SEED_DEMO_DATA=true)

| Email | Mot de passe | Rôle |
|-------|-------------|------|
| demo@sanad.ma | Sanad2026! | Admin cabinet |
| admin@webvoice.ma | WebVoice2026! | Admin WebVoice |

## Production

```bash
# Désactiver les seeds démo
SEED_DEMO_DATA=false

# Générer clé chiffrement
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Variables obligatoires
SECRET_KEY=<64-char-random>
DATABASE_URL=postgresql://...
ENCRYPTION_KEY=<fernet-key>
GROQ_API_KEY=<groq-key>
SMTP_HOST=smtp.sendgrid.net  # ou Resend, Brevo...
```

## API nouveaux endpoints

- `GET /api/auth/verify-email?token=`
- `POST /api/auth/resend-verification`
- `POST /api/auth/forgot-password`
- `POST /api/auth/reset-password`
- `POST /api/auth/refresh`
- `POST /api/chat/stream` (SSE)
- `PATCH /api/admin/cabinets/{id}/approve`
