# Sanad API — référence

Base URL locale : `http://localhost:8001`  
OpenAPI live (dev) : `/docs` · schéma exporté : [`openapi.json`](./openapi.json)

**Auth** : Bearer JWT (`POST /api/auth/login`).  
**Rôles** : `admin_cabinet` / `avocat` (plein accès) · `assistant_juridique` (lecture, pas IA destructive).

## Couverture documentation

| Indicateur | Statut |
|------------|--------|
| Spec OpenAPI locale | Oui (`docs/openapi.json`) |
| Spec Postman workspace | Aucune (vide) |
| Collection Postman « My Collection » | Hors Sanad (écho / autre API) |
| Auth documentée | Oui (Bearer) |
| Rate limits | Login / forgot / google / chat / dictation / summarize |
| Synthèse Ollama | Documentée ci-dessous |

**Overall estimé** : ~55 % (schémas FastAPI riches, descriptions métier partielles).  
Gaps principaux : exemples request/response manuels, codes d’erreur homogènes, collection Postman Sanad absente.

## Synthèse locale (Ollama + Mistral)

| Méthode | Chemin | Description |
|---------|--------|-------------|
| POST | `/api/summarize` | Synthèse d’un texte brut (`text`, 20–100k car.) |
| POST | `/api/summarize/document/{doc_id}` | Synthèse depuis `extracted_text` OCR |
| GET | `/api/documents/{doc_id}/synthese` | Synthèse structurée (Ollama d’abord, puis cloud) |

### Exemple `POST /api/summarize`

```http
POST /api/summarize
Authorization: Bearer <token>
Content-Type: application/json

{"text":"Le contrat de bail commercial ..."}
```

```json
{
  "summary": "## Faits\n...",
  "provider": "ollama",
  "model": "mistral",
  "degraded": false
}
```

Erreurs : `403` assistant · `503` Ollama down / timeout · `422` texte OCR insuffisant (document).

Variables : `OLLAMA_BASE_URL`, `OLLAMA_SYNTHESIS_MODEL=mistral`, `OLLAMA_CHAT_TIMEOUT=300`.  
VPS Linux : `scripts/setup-ollama-linux.sh` · guide : [`ollama-mistral-synthese.md`](./ollama-mistral-synthese.md).

## Endpoints principaux

### Auth — `/api/auth`
Login, register, refresh, Google (+ TOTP si 2FA), forgot/reset password, 2FA setup/enable/disable, `/me`.

### Dossiers — `/api/cases`
CRUD dossiers, analyse IA (`POST /{id}/analyse`). Delete bloqué pour assistant.

### Documents — `/api/documents`
Upload, liste, détail, download, re-extract OCR, synthèse, ask, delete.

### Dictée / plaidoirie — `/api/dictation`
`POST /polish`, `POST /compose` — **avocat / admin_cabinet uniquement**.

### Chat — `/api/chat`
Chat, stream, sessions, history — **pas pour assistant**.

### Workspace — `/api/workspace`
Summary, notes, tasks, agenda (lien `case_id`).

### Team / Settings / Admin / Corpus
Équipe, paramètres cabinet, admin WebVoice, corpus juridique & benchmarks.

## Déploiement Linux

Le serveur de prod cible est **Linux**. Ollama reste en local / réseau Docker (`http://ollama:11434`), **jamais** exposé sur Internet.
