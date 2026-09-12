# Préparation complète — 2ᵉ suivi PFA Sanad

**Projet :** Sanad — Plateforme d’Assistance en IA pour Avocats  
**Stagiaire :** Douae El Assal · ENSA Tétouan · WebVoice  
**PPT :** `docs/Sanad_Deuxieme_Suivi_PFA.pptx` (+ copie Bureau)  
**Script oral :** `docs/Script_Deuxieme_Suivi_PFA.md`  

---

## 1. Comment lancer & accéder (aujourd’hui)

| Service | URL |
|---------|-----|
| Application | http://localhost:3000 |
| API docs | http://localhost:8001/docs |
| Mailhog (emails locaux) | http://localhost:8025 |
| MinIO console | http://localhost:9001 |

### Comptes de test

| Email | Mot de passe | Espace |
|-------|--------------|--------|
| `demo@sanad.ma` | `Sanad2026!` | Admin cabinet (tout) |
| `avocat@sanad.ma` | `Sanad2026!` | Avocat |
| `assistant@sanad.ma` | `Sanad2026!` | Assistant (lecture limitée) |
| `admin@webvoice.ma` | `WebVoice2026!` | Admin plateforme `/admin` |

---

## 2. Comment tester TOUTES les features (checklist)

### A. Auth & espaces
1. http://localhost:3000/login → `demo@sanad.ma` / `Sanad2026!`
2. Vérifier redirection `/dashboard`
3. Déconnexion → reconnecter en `assistant@sanad.ma` → plaidoirie en lecture seule
4. `admin@webvoice.ma` → `/admin` (cabinets / logs)

### B. Cœur plaidoirie (PRIORITÉ DÉMO)
1. Menu **مرافعة / Plaidoirie** → `/redaction`
2. Choisir **صفحة فارغة** ou un **modèle**
3. Vous arrivez sur `/redaction/...`
4. Badge **Whisper prêt** (vert) = STT OK
5. **ملف صوتي** : uploader un mp3/wav arabe → texte dans la zone
6. Ou **ميكروفون** : parler ~1 min → texte progressif → إيقاف
7. **تصحيح** → **توليد الوثيقة** → export Word/PDF → archiver dans un dossier

### C. Dossiers + domaines
1. `/cases/new` → choisir un **domaine** (Civil, Pénal…)
2. `/cases` → filtre domaine + recherche

### D. Documents + synthèse
1. Ouvrir un dossier → upload PDF/DOC
2. Attendre indexation → `/documents/[id]`
3. Panneau **تلخيص منظم** → Actualiser si besoin

### E. Agenda ↔ affaires
1. `/agenda` → créer événement
2. Lier un **dossier**
3. Filtrer par affaire → cliquer le lien dossier

### F. Équipe
1. `/team` → invitation (email visible dans Mailhog :8025)

### G. Paramètres / login pro
1. `/settings`
2. Login : email + password (lien magique discret)

---

## 3. Remarques du 1ᵉʳ suivi → comment on a répondu

| Remarque encadrant | Réponse Sanad (preuve) |
|--------------------|------------------------|
| Cœur = voix → plaidoirie | Parcours 2 pages + Whisper arabe + compose + export |
| STT dépendance fragile | Whisper local + upload audio + Chrome + saisie manuelle |
| LLM dépendance | Multi-LLM + mode dégradé (édition/export sans IA) |
| Agenda ↔ affaires | `case_id` sur events/tasks/notes + filtre |
| Domaine + recherche | `case_type` + filtre UI |
| Benchmark OK/Non OK | `docs/benchmark-ok-nok.md` |
| Présentation redondante | PPT 2ᵉ suivi court, une idée / slide |
| Gestion cabinet | Auth, rôles, équipe, templates, multi-tenant |

---

## 4. Stack technique (tout ce qu’on utilise)

| Couche | Techno | Rôle |
|--------|--------|------|
| Frontend | Next.js 14, TypeScript, Tailwind, Zustand | UI RTL/arabe, pages métier |
| Backend | FastAPI, SQLAlchemy, Alembic, JWT | APIs REST |
| DB | **PostgreSQL 16** (pas SQLite en prod) | Données cabinets / users / docs |
| Cache / files / jobs | Redis, MinIO, Celery | Queue OCR, fichiers chiffrés |
| STT | faster-whisper (local) | Audio → texte arabe |
| LLM | Ollama/Mistral + fallbacks cloud | Polish, compose, synthèse |
| OCR | Tesseract fra+ara, pdf2image | Scans → texte |
| Vecteurs | ChromaDB + BGE-M3 | RAG corpus (si activé) |
| Emails | SMTP / Mailhog (dev) | OTP, magic link, invites |
| Conteneurs | Docker Compose | Empilement reproductible |

**SQLite ?** Un vieux `sanad.db` local pouvait exister en test hors Docker. **Ce n’est PAS la base réelle.** Docker utilise PostgreSQL.

---

## 5. APIs principales (à citer à l’oral)

| Groupe | Endpoints | Usage |
|--------|-----------|-------|
| Auth | `/api/auth/login`, register OTP, magic-link, google, refresh | Connexion |
| Dictée | `/api/dictation/transcribe`, `polish`, `compose`, `stt-status` | Voix → document |
| Dossiers | `/api/cases` | CRUD + domaines |
| Documents | `/api/documents`, `.../synthese`, ask | Pièces + synthèse |
| Workspace | `/api/workspace/...` | Agenda / tâches / notes |
| Templates | `/api/plaidoirie-templates` | Modèles cabinet |
| Équipe | `/api/team` | Invitations |
| Admin | `/api/admin/...` | Supervision WebVoice |
| Settings | `/api/settings/...` | Mot de passe OTP, etc. |

Swagger live : http://localhost:8001/docs

---

## 6. Images Docker — chacune sert à quoi ?

### Images qu’**on** a publiées (Docker Hub `anadouae1`)

| Image | Contenu | Sert à |
|-------|---------|--------|
| `anadouae1/sanad-backend` | FastAPI + Whisper + OCR deps | API métier |
| `anadouae1/sanad-frontend` | Next.js build | Interface web |
| `anadouae1/sanad-celery` | Worker Celery | OCR / indexation async |

### Images **officielles** (tirées automatiquement)

| Image | Sert à |
|-------|--------|
| `postgres:16-alpine` | Base de données |
| `redis:7-alpine` | Broker Celery + cache |
| `minio/minio` | Stockage fichiers |
| `mailhog/mailhog` | Boîte mail de test |
| `ollama/ollama` | LLM local |

### Pourquoi publier sur Internet (Docker Hub) ?

1. **Reproductibilité** : même image sur ton PC, VPS, machine du jury  
2. **Déploiement rapide** : `docker pull` sans rebuild 20 min  
3. **Partage équipe / encadrant** : preuve que le produit est packagé  
4. **Séparation code ≠ runtime** : GitHub = sources ; Hub = binaires prêts  

**Ce n’est PAS obligatoire pour le PFA**, mais c’est une **bonne pratique pro** (CI/CD, DevOps).

Liens :
- https://hub.docker.com/r/anadouae1/sanad-backend  
- https://hub.docker.com/r/anadouae1/sanad-frontend  
- https://hub.docker.com/r/anadouae1/sanad-celery  

---

## 7. Questions difficiles possibles → réponses courtes & claires

### Q1. Et si Whisper / l’API disparaît ?
**R :** On a 4 niveaux : Whisper local, upload audio, Chrome STT, saisie manuelle. L’avocat n’est jamais bloqué.

### Q2. Et si le LLM cloud est coupé ?
**R :** Fallback Ollama local + mode dégradé : édition, export, classement restent. L’IA accélère, elle ne bloque pas.

### Q3. Pourquoi pas seulement Dragon / ChatGPT ?
**R :** Dragon = dictée desktop isolée. ChatGPT = généraliste. Sanad = flux cabinet : dictée → document → dossier → rôles → multi-tenant.

### Q4. L’IA invente-t-elle le droit ?
**R :** Non. Whisper = transcription. Polish = forme. Synthèse = extraction du document uniquement. L’avocat valide toujours.

### Q5. Pourquoi PostgreSQL et pas SQLite ?
**R :** SQLite = fichier local mono-utilisateur. Un SaaS multi-cabinets a besoin de Postgres (concurrence, volumes, Docker, cloud Neon possible).

### Q6. Comment garantissez-vous la confidentialité ?
**R :** Multi-tenant (isolation cabinet), JWT + sessions, chiffrement fichiers (Fernet/MinIO), pas de secrets dans Git, rôles assistant limités.

### Q7. Qu’avez-vous vraiment livré depuis le 1ᵉʳ suivi ?
**R :** Whisper arabe robuste, UX plaidoirie en 2 pages, domaines + filtre, agenda↔dossiers, synthèse stricte, login pro, GitHub + Docker Hub.

### Q8. Quelle est la dépendance critique restante ?
**R :** Qualité OCR sur mauvais scans ; modèle Whisper `small` sur CPU (compromis vitesse/qualité). Améliorable (modèle plus grand / GPU).

### Q9. Où est le code / les images ?
**R :** Code : github.com/anadouae/Plateforme-d-Assistance-en-IA-pour-Avocats — Images : Docker Hub anadouae1/sanad-*

### Q10. Quelle est la suite ?
**R :** Qualité STT juridique, SMTP prod, durcissement VPS ; veille analyse globale dossier hors cœur PFA.

---

## 8. Phrases d’ouverture / clôture

**Ouverture :**  
> « Au premier suivi, vous avez recentré Sanad sur la voix vers la plaidoirie, et demandé une architecture résiliente. Aujourd’hui je montre comment on a répondu point par point, puis une démo. »

**Clôture :**  
> « Sanad n’est plus seulement un ensemble d’écrans : c’est un flux métier arabe, avec des alternatives STT/LLM, un packaging Docker, et un cabinet autour de la plaidoirie. »

---

*Document interne de préparation · Douae El Assal · Août 2026*
