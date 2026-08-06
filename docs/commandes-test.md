# Sanad — Commandes de lancement et comptes de test

## 1. Prérequis

1. **Docker Desktop** installé et **démarré** (icône verte)
2. Être dans le dossier projet :
   ```powershell
   cd C:\Users\daurinia\Desktop\Avocat-AI-Assistance
   ```

---

## 2. Lancer toute l'application (une seule commande)

```powershell
docker compose up -d --build
```

**Premier lancement** : Ollama télécharge le modèle (~5 Go) — attendre 10–20 min.

---

## 3. Créer les comptes de test (déjà fait une fois, relancer si besoin)

```powershell
docker compose exec backend python scripts/seed_test_accounts.py
```

**Sans Docker** (base Neon cloud) :
```powershell
cd backend
.\venv\Scripts\activate
$env:DATABASE_URL="postgresql://neondb_owner:npg_uganzkQ4cp3I@ep-shy-wildflower-asi3sswu.c-4.eu-central-1.aws.neon.tech/neondb?sslmode=require"
python scripts/seed_test_accounts.py
```

---

## 4. Comptes de test

| Email | Mot de passe | Rôle | Accès |
|-------|--------------|------|-------|
| `demo@sanad.ma` | `Sanad2026!` | Admin cabinet | Tout (synthèse, chat, upload) |
| `avocat@sanad.ma` | `Sanad2026!` | Avocat | Chat, synthèse, dossiers |
| `assistant@sanad.ma` | `Sanad2026!` | Assistant | Lecture seule (pas synthèse IA) |
| `test@cabinet-rabat.ma` | `Test2026!` | Admin 2e cabinet | Cabinet séparé |
| `admin@webvoice.ma` | `WebVoice2026!` | Admin plateforme | Panel admin |

**Connexion :** http://localhost:3000/login

---

## 5. URLs utiles

| Service | URL |
|---------|-----|
| Application | http://localhost:3000 |
| API docs | http://localhost:8001/docs |
| Santé API | http://localhost:8001/health |
| Emails test | http://localhost:8025 |
| MinIO console | http://localhost:9001 |

MinIO : `sanad_minio` / `sanad_minio_secret`

---

## 6. Vérifier que tout tourne

```powershell
docker compose ps
curl http://localhost:8001/health
curl http://localhost:8001/api/corpus/stats
```

Réponse `/health` attendue : `"ollama": true` (après chargement du modèle).

---

## 7. Indexer le corpus juridique (première fois ou après mise à jour)

```powershell
docker compose exec backend python scripts/reindex_corpus.py
```

Durée : 20–60 minutes (~147 000 articles).

---

## 8. Tester la connexion API

```powershell
curl -X POST http://localhost:8001/api/auth/login `
  -H "Content-Type: application/json" `
  -d '{\"email\":\"demo@sanad.ma\",\"password\":\"Sanad2026!\"}'
```

---

## 9. Arrêter / redémarrer

```powershell
docker compose down
docker compose restart backend
docker compose logs -f backend
docker compose logs -f ollama-init
```

---

## 10. Scénario de test rapide

1. Lancer : `docker compose up -d --build`
2. Comptes : `docker compose exec backend python scripts/seed_test_accounts.py`
3. Ouvrir http://localhost:3000/login → `demo@sanad.ma` / `Sanad2026!`
4. Aller dans **Dossiers** → ouvrir `WV-2026-0001`
5. Onglet **Documents** → voir les 3 pièces de test
6. Cliquer sur un document → **Générer la synthèse**
7. Onglet **Assistant** → poser une question en français, arabe ou anglais
8. Upload un vrai PDF dans `WV-2026-0002` pour tester l'upload

---

## 11. Dépannage

| Problème | Solution |
|----------|----------|
| Docker ne démarre pas | Ouvrir Docker Desktop, attendre qu'il soit prêt |
| `ollama: false` dans /health | `docker compose logs ollama-init` puis `docker compose restart backend` |
| Synthèse vide | Vérifier Ollama : `docker compose exec ollama ollama list` |
| Upload bloqué | Vérifier celery : `docker compose logs celery-worker` |
