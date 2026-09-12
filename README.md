# LexHub – Avocat AI Assistance

Plateforme SaaS juridique pour les cabinets d'avocats marocains.

**WebVoice** · Projet de Fin d'Année · 2026 · Production : https://lexhub.space

> Ancien nom de code interne : *Sanad*. Marque et produit : **LexHub**.

## Stack production

| Composant | Technologie |
|-----------|-------------|
| Frontend | Next.js 14, TypeScript, Tailwind, Zustand |
| Backend | FastAPI, SQLAlchemy, Alembic, JWT |
| Base de données | PostgreSQL 16 (`lexhub`) |
| Fichiers | MinIO + chiffrement AES (Fernet) |
| IA | STT / LLM cloud + routeur anti-invention |
| Workers | Celery + Redis |
| Email | SMTP / Resend |

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

Les seeds automatiques sont **désactivés** en production. Pour créer des comptes de test :

```bash
docker compose exec backend python scripts/seed_test_accounts.py
```

- `demo@lexhub.space` / `LexHub2026!` (admin cabinet)
- `avocat@lexhub.space` / `LexHub2026!`
- `assistant@lexhub.space` / `LexHub2026!`

## Admin base (ops)

PostgreSQL n’est **pas** exposé sur Internet. Sur le VPS : Adminer en `127.0.0.1:8088` uniquement (tunnel SSH). Voir `docs/ADMINER_ACCES.md`.
