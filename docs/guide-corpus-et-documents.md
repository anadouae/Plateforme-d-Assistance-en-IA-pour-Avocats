# Guide Sanad — Corpus juridique vs documents utilisateur

Ce guide explique **deux choses différentes** souvent confondues dans Sanad.

---

## Les 2 mondes de données

```
┌─────────────────────────────────────────────────────────────────┐
│  MONDE 1 — CORPUS JURIDIQUE (lois, déjà dans le projet)         │
│  ~147 000 articles · Bulletin officiel · OHADA · jurisprudence  │
│  Fichiers JSON dans backend/data/ · indexés dans ChromaDB       │
│  → sert au CHAT juridique général (pas à vos uploads)           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  MONDE 2 — VOS DOCUMENTS (uploadés par l'avocat)                │
│  PDF, Word, images de dossiers clients                          │
│  Stockés MinIO · texte en PostgreSQL · vecteurs par dossier     │
│  → sert à la SYNTHÈSE et aux questions SUR CE DOSSIER             │
└─────────────────────────────────────────────────────────────────┘
```

**Ce ne sont pas les mêmes fichiers.** Le corpus n'est pas uploadé par l'utilisateur dans l'app.

---

## Monde 1 — Le corpus juridique (lois marocaines)

### Qu'est-ce que c'est ?

Une **bibliothèque de textes de loi** pré-chargée dans le projet pour que l'IA réponde aux questions juridiques générales :

- Code pénal, Code civil, Code de procédure…
- Textes du Bulletin officiel (BO)
- Droit OHADA (19 instruments)
- Jurisprudence (échantillon)

### Où est-il stocké ?

| Emplacement | Contenu |
|-------------|---------|
| `backend/data/bo_shards/bo_*.json` | ~147 000 entrées BO (60 fichiers) |
| `backend/data/ohada_corpus.json` | 19 textes OHADA |
| `backend/data/jurisprudence_corpus.json` | Décisions de justice |
| `backend/data/legal_corpus.json` | Corpus de base |
| ChromaDB (`CHROMA_PERSIST_DIR`) | Vecteurs pour recherche sémantique |

### Comment a-t-il été créé ?

1. **Scripts Python** (pas d'upload manuel) :
   - `scripts/build_bo_corpus.py` — génère les shards BO massifs
   - `scripts/import_corpus.py` — importe en base vectorielle
   - `scripts/reindex_corpus.py` — réindexe tout dans ChromaDB

2. **Indexation** : chaque article est découpé en morceaux, transformé en vecteurs (BGE-M3), stocké dans ChromaDB.

3. **Mise à jour** : `backend/app/services/corpus_updater.py` + API `/api/corpus` pour rafraîchir.

### Quand est-il utilisé ?

Quand vous posez une **question juridique générale** dans le chat :

> « Quel est le délai d'appel en matière correctionnelle ? »

L'IA cherche dans le **corpus juridique** (pas dans vos PDF uploadés).

---

## Monde 2 — Vos documents (upload utilisateur)

### Qu'est-ce que c'est ?

Les fichiers que **vous** uploadez dans un **dossier client** :

- Contrats, assignations, jugements, courriers, pièces scannées…

### Où sont-ils stockés ?

| Emplacement | Contenu |
|-------------|---------|
| **MinIO** | Fichier original (PDF/DOCX/image) chiffré |
| **PostgreSQL (Neon)** | Métadonnées + `extracted_text` + statut |
| **ChromaDB** | Vecteurs **par dossier** (`case_{cabinet}_{case}`) |

### Que se passe-t-il à l'upload ?

```
Upload PDF/Word
    → Sauvegarde MinIO
    → Tâche Celery process_document
    → Extraction texte (PyMuPDF / Word / OCR arabe+français)
    → Texte sauvé en PostgreSQL
    → Indexation ChromaDB (par dossier)
    → Statut INDEXED
```

### Quand sont-ils utilisés ?

| Action | Source utilisée |
|--------|-----------------|
| **Synthèse** d'un document | Texte extrait + LLM Ollama |
| **Question sur un document** | RAG sur ce document |
| **Analyse d'un dossier** | Tous les docs du dossier + LLM |
| **Chat avec dossier sélectionné** | Docs du dossier en priorité |

---

## Multilingue (FR / AR / EN)

Depuis la mise à jour :

- **Chat** : répond dans la langue de votre question (ou la langue de l'interface si ambiguë)
- **Synthèse** : dans la langue choisie dans l'interface (FR/AR/EN)
- **Analyse dossier** : idem

Le LLM (`sanad-legal` via Ollama) fait le résumé — plus de faux « Non identifiées » quand le formulaire regex échoue.

---

## Résumé en une phrase

| | Corpus juridique | Vos documents |
|--|------------------|---------------|
| **Qui l'ajoute ?** | Scripts / équipe dev | Vous (upload) |
| **Contenu** | Lois, BO, OHADA | Pièces de dossiers |
| **Où ?** | `backend/data/` + ChromaDB global | MinIO + PostgreSQL + ChromaDB par dossier |
| **Pour quoi ?** | Questions juridiques générales | Synthèse, analyse, Q&A sur un cas |

---

## Vérifier que tout est réel (pas mock)

```bash
# Corpus indexé
curl http://localhost:8001/api/corpus/stats

# Ollama prêt
curl http://localhost:8001/health

# Vos documents en base
# → voir dans l'app : Dossiers → Documents
```
