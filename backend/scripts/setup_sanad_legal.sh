#!/usr/bin/env bash
# Setup Sanad-Legal on Linux/macOS
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> Checking Ollama..."
ollama --version

echo "==> Pulling base model llama3.1:8b..."
ollama pull llama3.1:8b

echo "==> Creating sanad-legal..."
cd "$ROOT/models"
ollama create sanad-legal -f Modelfile

echo "==> Done. OLLAMA_MODEL=sanad-legal LLM_PROVIDER=ollama"
ollama list | grep sanad-legal || true
