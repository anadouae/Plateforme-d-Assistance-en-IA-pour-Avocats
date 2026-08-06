# Sanad-Legal — modèle local

## Installation rapide (recommandée, sans GPU)

1. Installer [Ollama](https://ollama.com/download)
2. Depuis `backend/` :

```powershell
.\scripts\setup_sanad_legal.ps1
```

ou :

```bash
ollama pull llama3.1:8b
cd models
ollama create sanad-legal -f Modelfile
```

3. Vérifier `.env` :

```
LLM_PROVIDER=ollama
OLLAMA_MODEL=sanad-legal
LLM_ALLOW_CLOUD_FALLBACK=false
```

## Fine-tune LoRA (optionnel, GPU)

Dataset : `data/sanad_legal_qa.jsonl` (~40 Q/R droit marocain)

```bash
pip install transformers peft datasets accelerate bitsandbytes trl
python scripts/finetune_sanad_lora.py
```

Sans GPU, le script exporte `models/sanad-legal-lora/train_ready.json` pour un run ultérieur.

## Architecture

- **Ollama `sanad-legal`** : rédaction / synthèse (chez toi)
- **ChromaDB + BGE-M3** : mémoire juridique (corpus MA / OHADA / jurisprudence)
- **Agent Sanad** : routage chat / document / dossier
