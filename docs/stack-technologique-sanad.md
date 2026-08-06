# Sanad — Frameworks et Stack Technologique

**Projet :** Sanad · Avocat AI Assistance  
**Auteur :** Douae El Assal · WebVoice · Juillet 2026

---

## 1. Vue d'ensemble

| Couche | Technologies principales |
|--------|--------------------------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS, Zustand |
| Backend | FastAPI, SQLAlchemy, Pydantic v2, Celery, Redis |
| Base de données | PostgreSQL, ChromaDB, Redis, MinIO |
| Intelligence artificielle | BGE-M3, Groq, Ollama, Tesseract, Tavily |
| Infrastructure | Docker Compose, Alembic |

---

## 2. Frontend

| Composant | Framework / librairie | Rôle |
|-----------|----------------------|------|
| Framework UI | **Next.js 14** (App Router) | Pages, routing, SSR |
| Langage | **TypeScript** | Typage fort, maintenance |
| Style | **Tailwind CSS** | Interface responsive |
| État global | **Zustand** | Auth, locale, UI |
| Animations | Framer Motion | Transitions interface |
| 3D | React Three Fiber | Logo et hero 3D |

---

## 3. Backend

| Composant | Framework / librairie | Rôle |
|-----------|----------------------|------|
| API REST | **FastAPI** | Endpoints, validation, OpenAPI |
| ORM | **SQLAlchemy 2** | Modèles Cabinet, User, Case, Document |
| Validation | **Pydantic v2** | Schémas entrée/sortie API |
| Migrations | **Alembic** | Évolution schéma PostgreSQL |
| Tâches async | **Celery** + **Redis** | Pipeline upload → OCR → index |
| Authentification | JWT + bcrypt | Login, refresh, blocage après 5 échecs |
| Email | SMTP (MailHog en dev) | Vérification, reset, invitations |
| Extraction PDF | PyMuPDF (fitz) | Texte natif des PDF |
| Extraction DOCX | python-docx | Texte des documents Word |

---

## 4. Base de données et stockage

| Composant | Technologie | Rôle |
|-----------|-------------|------|
| Base relationnelle | **PostgreSQL** (Neon) | Users, cabinets, dossiers, audit |
| Base vectorielle | **ChromaDB** | Embeddings corpus juridique et documents |
| Cache / queue | **Redis** | Broker Celery, sessions |
| Object storage | **MinIO** (S3-compatible) | Fichiers uploadés chiffrés |
| Chiffrement fichiers | Fernet (AES-256) | Confidentialité documents clients |

---

## 5. Intelligence artificielle

| Composant | Technologie | Rôle |
|-----------|-------------|------|
| Embeddings | **BGE-M3** | Vectorisation multilingue (FR/AR) |
| Génération LLM | **Groq** — Llama 3.3 70B | Rédaction réponses avec citations |
| Fallback local | **Ollama** | Mode dégradé si Groq indisponible |
| OCR | **Tesseract** (fra + ara) | Extraction texte scans et images |
| OCR PDF scanné | pdf2image + Tesseract | PDF image → texte |
| Recherche web | **Tavily** / DuckDuckGo | Complément si corpus insuffisant |
| Orchestration agent | Module `agent.py` | Routage RAG / Web / Document |

---

## 6. Infrastructure et déploiement

| Composant | Technologie | Rôle |
|-----------|-------------|------|
| Conteneurisation | **Docker Compose** | 8 services orchestrés (dev/prod) |
| Frontend (prévu) | Vercel | Hébergement Next.js + HTTPS |
| Backend (prévu) | Render / Railway | API FastAPI + workers Celery |
| Monitoring (prévu) | Sentry | Erreurs production |
| CI/CD (prévu) | GitHub Actions | Tests et déploiement automatique |

---

## 7. Principe architectural IA

```
Question utilisateur
        │
        ▼
   Routeur agent
   ┌────┴────┬──────────┐
   ▼         ▼          ▼
Document   Corpus     Recherche
 dossier   RAG MA      web
   │         │          │
   └────┬────┴──────────┘
        ▼
   Extraits + citations
        ▼
   Groq (rédaction)
        ▼
   Réponse SSE + score confiance
```

**Règle :** ChromaDB et la recherche web récupèrent les sources. Groq rédige la réponse. Le LLM ne répond jamais sans source identifiée.

---

## 8. Justification des choix clés

| Choix | Raison |
|-------|--------|
| FastAPI + Python | Même écosystème que ChromaDB, Tesseract et BGE-M3 |
| Next.js 14 | SSR, déploiement Vercel, pages publiques indexables |
| PostgreSQL | ACID, multi-tenant, audit fiable |
| ChromaDB | Self-hosted, pas de coût par requête, données sensibles locales |
| BGE-M3 | Open source, multilingue, standard RAG 2025–2026 |
| Groq | Inférence rapide (< 3 s), coût faible |
| MinIO + chiffrement | Stockage S3-compatible avec confidentialité cabinet |
| Celery | OCR et indexation sans bloquer l'API |
