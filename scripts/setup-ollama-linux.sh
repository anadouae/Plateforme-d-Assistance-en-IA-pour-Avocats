#!/usr/bin/env bash
# Sanad — install Ollama + Mistral sur VPS Linux (Ubuntu/Debian)
# Usage: sudo bash scripts/setup-ollama-linux.sh
set -euo pipefail

echo "==> Install Ollama (Linux)"
if ! command -v ollama >/dev/null 2>&1; then
  curl -fsSL https://ollama.com/install.sh | sh
else
  echo "Ollama déjà installé: $(ollama --version)"
fi

echo "==> Démarrer le service Ollama"
if command -v systemctl >/dev/null 2>&1; then
  systemctl enable --now ollama || true
fi

echo "==> Attente API :11434"
for i in $(seq 1 60); do
  if curl -sf http://127.0.0.1:11434/api/tags >/dev/null; then
    break
  fi
  sleep 2
done

echo "==> Pull mistral (synthèse documents)"
ollama pull mistral

echo "==> Pull llama3.1:8b (base sanad-legal, optionnel)"
ollama pull llama3.1:8b || true

echo "==> Modèles installés"
ollama list

echo ""
echo "IMPORTANT sécurité:"
echo "  - Ne pas exposer le port 11434 sur Internet (firewall: localhost / docker network only)"
echo "  - Dans Docker Compose backend: OLLAMA_BASE_URL=http://ollama:11434"
echo "  - OLLAMA_SYNTHESIS_MODEL=mistral"
echo ""
echo "Test rapide:"
echo '  ollama run mistral "Résume en 2 phrases : Le contrat de bail..."'
echo "Done."
