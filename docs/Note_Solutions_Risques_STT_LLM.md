# Note interne — Solutions aux risques (STT & LLM)

**Usage :** pour toi (préparation oral / rapport) — **pas obligatoire** dans le compte rendu officiel.  
**Contexte :** questions de l’encadrant école sur la dépendance aux outils externes.

---

## 1. Transcription de la voix (STT)

### Ce qu’on peut répondre aujourd’hui
Sanad s’appuie côté navigateur sur la **dictée Web Speech API** (micro, notamment arabe via Chrome) : l’avocat dicte → texte brut → puis correction IA → document.

### Risque soulevé
Et si l’API / le moteur de reconnaissance n’est plus disponible ?

### Stratégie de mitigation (à défendre)

| Niveau | Solution | Effet |
|--------|----------|--------|
| **A — Toujours disponible** | Saisie manuelle du texte (déjà possible dans l’UI) | L’app **fonctionne sans micro** |
| **B — Alternative STT** | Brancher un 2ᵉ fournisseur (ex. Whisper local via Ollama/serveur, ou API STT cloud) derrière une interface unique `transcribe()` | Si A tombe, on bascule sur B |
| **C — Mode offline cabinet** | Whisper / modèle local sur le VPS du cabinet | Moins de dépendance cloud |
| **D — Upload audio** | Déposer un fichier audio → transcription asynchrone (Celery) | Contourne le micro navigateur |

**Phrase clé pour l’encadrant :**  
> « La plateforme ne dépend pas d’un seul outil : la dictée accélère le flux, mais l’avocat peut toujours saisir ou coller le texte. L’architecture prévoit un service de transcription interchangeable. »

---

## 2. LLM (correction, synthèse, compose)

### Ce qu’on peut répondre aujourd’hui
Sanad route déjà vers plusieurs backends (Ollama local + fournisseurs cloud en fallback selon config).

### Risque soulevé
Et si le LLM payant de l’entreprise disparaît ?

### Stratégie de mitigation

| Niveau | Solution | Effet |
|--------|----------|--------|
| **A — Mode dégradé** | Sans LLM : texte dicté / saisi reste utilisable ; export PDF/DOC et classement dossier **continuent** | Cœur métier non bloqué |
| **B — Multi-fournisseurs** | Abstraction `LLMProvider` + liste ordonnée (Ollama → Mistral → autre…) | Basculer sans réécrire l’app |
| **C — Modèle local** | Ollama sur VPS (`sanad-legal` / Llama) | Indépendance partielle du cloud |
| **D — Cache / templates** | Formules de plaidoirie par domaine (réutilisation) | Moins d’appels LLM |

**Phrase clé :**  
> « L’IA est un accélérateur, pas un point de défaillance unique. Sans LLM, le cabinet garde dictée/saisie, édition, export et archivage. Avec LLM, on multiplie les fournisseurs et on privilégie un modèle local en secours. »

---

## 3. Lien avec les autres retours (actions concrètes)

| Retour encadrant | Action produit |
|------------------|----------------|
| Objectif = voice → plaidoirie | Garder ce flux en démo n°1 |
| Agenda ↔ affaires | Forcer / améliorer le lien `case_id` sur les événements |
| Classement par domaine | Champ `domaine` (ou affiner `case_type`) + filtre recherche |
| Benchmark OK / Non OK | Refaire le tableau avec colonnes cochables |
| Tendance « analyse intérêt du dossier » | Veille ; **hors cœur PFA** pour l’instant (backlog) |

---

## 4. Message de fond (ce qu’il voulait entendre)

Ce n’est pas « on achète un outil et c’est fini ».  
C’est : **architecture résiliente** =

1. Fonctionnalités critiques **sans** IA (saisie, édition, export, dossiers)  
2. IA derrière des **interfaces interchangeables**  
3. **Fallback local** quand c’est possible  

---

*Note interne · Douae El Assal · Sanad PFA*
