# Setup Sanad-Legal (Windows PowerShell)
# Prerequisites: install Ollama from https://ollama.com/download

$ErrorActionPreference = "Stop"
$ModelDir = Split-Path -Parent $PSScriptRoot
$Modelfile = Join-Path $ModelDir "models\Modelfile"

Write-Host "==> Checking Ollama..."
ollama --version

Write-Host "==> Pulling base model llama3.1:8b (first time may take a while)..."
ollama pull llama3.1:8b

Write-Host "==> Creating sanad-legal from Modelfile..."
Push-Location (Join-Path $ModelDir "models")
ollama create sanad-legal -f Modelfile
Pop-Location

Write-Host "==> Verifying..."
ollama list | Select-String "sanad-legal"

Write-Host ""
Write-Host "Done. Set OLLAMA_MODEL=sanad-legal and LLM_PROVIDER=ollama in .env"
Write-Host "Test: ollama run sanad-legal `"Quel est le délai d'appel correctionnel ?`""
