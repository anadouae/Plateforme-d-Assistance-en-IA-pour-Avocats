# Ollama + Mistral — synthèse locale Sanad

## Serveur de déploiement

Le VPS cible est **Linux** (Ubuntu/Debian). Ollama y tourne soit :

- en **service système** (`scripts/setup-ollama-linux.sh`), ou
- en **conteneur** Docker Compose (`ollama` + `ollama-init`).

Ne jamais exposer `:11434` sur Internet.

## Local (Windows / dev)

```bash
docker compose up -d ollama
docker exec -it avocat-ai-assistance-ollama-1 ollama pull mistral
docker exec -it avocat-ai-assistance-ollama-1 ollama list
```

## VPS Linux

```bash
sudo bash scripts/setup-ollama-linux.sh
```

## Variables

| Variable | Valeur recommandée |
|----------|--------------------|
| `OLLAMA_BASE_URL` | `http://ollama:11434` (Docker) / `http://127.0.0.1:11434` (host) |
| `OLLAMA_SYNTHESIS_MODEL` | `mistral` |
| `OLLAMA_MODEL` | `sanad-legal` (chat local optionnel) |
| `OLLAMA_CHAT_TIMEOUT` | `120` |

## API Sanad

- `POST /api/summarize` — corps `{ "text": "..." }`
- `POST /api/summarize/document/{doc_id}` — utilise `documents.extracted_text`
- `GET /api/documents/{id}/synthese` — synthèse structurée (Ollama d’abord, puis cloud)

Si Ollama est down → **mode dégradé** (extrait OCR / message clair), l’app reste utilisable.
