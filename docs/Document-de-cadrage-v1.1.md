# Projet de Fin d'Année
# Plateforme Avocat AI Assistance

**Document de cadrage et de spécifications — Version 1.1**

Réalisé par : Douae El Assal  
Éditeur : WebVoice  
Date : Juin 2026  
*Version 1.1 — Intégration de la recherche web, de l'analyse documentaire et clarification de l'architecture agent IA*

---

## Table des matières

1. [Objet et vision du projet](#1-objet-et-vision-du-projet)
2. [Problématique et solution](#2-problématique-et-solution)
3. [Acteurs de la plateforme](#3-acteurs-de-la-plateforme)
4. [Spécifications fonctionnelles](#4-spécifications-fonctionnelles)
5. [Spécifications non fonctionnelles](#5-spécifications-non-fonctionnelles)
6. [Stack technologique](#6-stack-technologique)
7. [Architecture de l'agent IA](#7-architecture-de-lagent-ia)
8. [Pipeline RAG et recherche web](#8-pipeline-rag-et-recherche-web)
9. [Roadmap de réalisation](#9-roadmap-de-réalisation)
10. [Annexes](#10-annexes)

---

## 1. Objet et vision du projet

### 1.1 Objet

Le projet consiste à concevoir et livrer **Avocat AI Assistance** : une plateforme web SaaS d'aide à la pratique juridique, destinée aux cabinets d'avocats marocains.

L'assistance recherchée par l'avocat marocain porte prioritairement sur **trois axes** :

1. **La recherche et l'interprétation des textes juridiques marocains**, avec citation systématique des sources — via un corpus juridique indexé (RAG) **et** une recherche web complémentaire ;
2. **L'analyse et la synthèse des documents de dossier** uploadés par l'utilisateur (contrats, conclusions, pièces scannées) ;
3. **La centralisation et la traçabilité des dossiers et pièces** dans un espace sécurisé multi-cabinets.

Un avocat marocain ne cherche pas une IA qui « fait le travail à sa place », mais un outil qui lui fait gagner du temps, réduit le risque d'erreur, et structure un métier où une erreur de procédure ou de citation peut coûter cher.

### 1.2 Vision

Un **copilote juridique intelligent** permettant à l'avocat de :

- centraliser ses dossiers et documents dans un espace sécurisé ;
- interroger un assistant IA capable de **trois modes de recherche** :
  - recherche dans un **corpus juridique marocain** pré-indexé (RAG) ;
  - **recherche web** pour les informations récentes ou absentes du corpus ;
  - **analyse des documents uploadés** dans le contexte d'un dossier ;
- obtenir des **synthèses et analyses documentaires** assistées par IA, avec citations obligatoires et score de confiance.

### 1.3 Principe directeur de l'agent IA

> **L'agent ne répond jamais « de mémoire ».** Il cherche d'abord (dans le corpus, sur le web, ou dans un document uploadé), puis rédige sa réponse à partir des sources trouvées. Si aucune source pertinente n'est disponible, il le dit explicitement — sans inventer.

---

## 2. Problématique et solution

### 2.1 Problème adressé

Les cabinets d'avocats au Maroc consacrent une part importante de leur temps à des tâches à faible valeur ajoutée :

- recherche manuelle dans les textes législatifs (Bulletins Officiels, codes, dahirs) ;
- synthèse de dossiers volumineux ;
- classement et suivi documentaire peu traçable.

Ces activités sont chronophages, sujettes à erreur et peu traçables. Aucune solution locale n'intègre aujourd'hui simultanément la gestion de dossiers et une IA juridique adaptée au droit marocain.

### 2.2 Contexte marché (Maroc)

| Facteur | Situation |
|---------|-----------|
| Digitalisation juridique | Faible — majorité des cabinets en papier / Excel |
| LegalTech locale | Quasi inexistante — opportunité de premier entrant |
| Concurrence IA généraliste | Chatbots génériques (ChatGPT, etc.) sans spécialisation juridique marocaine |
| Volume cible | Environ 12 000 avocats inscrits aux barreaux marocains |

### 2.3 Solution proposée

Une plateforme web sécurisée, multi-cabinets (SaaS), permettant à un avocat de :

- gérer ses dossiers et documents juridiques ;
- interroger un **assistant IA multi-sources** :
  - corpus juridique marocain (RAG via ChromaDB) ;
  - recherche web en temps réel (DuckDuckGo / Tavily) ;
  - documents du dossier en cours (contexte local isolé) ;
- obtenir des **synthèses automatiques** et poser des **questions libres** sur tout document uploadé.

---

## 3. Acteurs de la plateforme

Avocat AI Assistance est un service SaaS multi-tenant édité par WebVoice. Chaque cabinet d'avocats s'inscrit, configure son espace de travail, puis y ajoute ses collaborateurs. Chaque cabinet dispose d'un espace totalement isolé des autres.

### 3.1 Le cabinet d'avocats — client de la plateforme

Le cabinet est l'entité qui souscrit au service. Il peut s'agir d'un avocat seul ou d'une structure de plusieurs avocats. Lors de l'inscription, le fondateur ou gérant crée le compte et devient le premier utilisateur de l'espace. Ses données (dossiers, documents, conversations IA) restent strictement confinées à son espace, invisibles pour les autres cabinets.

**Cas d'utilisation représentatifs :**

- **CU-C01** Inscription d'un nouveau cabinet, avec nom, ville et coordonnées — création automatique d'un espace isolé.
- **CU-C02** Ajout de collaborateurs (avocats, assistants) par lien d'activation envoyé par email.
- **CU-C03** Isolation garantie : deux cabinets sur la même plateforme ne voient jamais les données l'un de l'autre.

### 3.2 L'avocat — acteur principal

L'avocat est l'utilisateur central : il crée et gère ses dossiers, interroge l'assistant IA, analyse des documents, et retrouve l'historique complet de son travail sur chaque affaire.

**Cas d'utilisation représentatifs :**

- **CU-A01** Consultation de la synthèse automatique d'un dossier avant audience, puis question à l'IA sur un délai de prescription — l'agent cherche dans le corpus DOC (RAG) et complète par une recherche web si nécessaire, avec citation de l'article et lien vers la source.
- **CU-A02** Upload d'un contrat de bail commercial et obtention en moins de 30 secondes d'un résumé structuré (parties, dates, montants, clauses à risque).
- **CU-A03** Recherche d'un article de loi sans en connaître la référence exacte (ex. délai d'appel en correctionnel) — l'agent interroge le corpus RAG puis le web.
- **CU-A04** Question posée à l'IA dans le contexte strict d'un dossier, sans mélange avec d'autres affaires — l'agent ne consulte que les documents indexés de ce dossier.
- **CU-A05** Question libre sur un document uploadé : *« Quelle est la durée du bail ? »* — réponse citant le paragraphe exact du PDF.

### 3.3 L'assistant(e) juridique

Support administratif et documentaire du cabinet. Peut créer des dossiers, y déposer des documents et consulter leur statut de traitement, mais ne peut ni produire d'analyses juridiques via le chat IA, ni supprimer un dossier.

**Cas d'utilisation représentatifs :**

- **CU-AS01** Dépôt d'un contrat scanné reçu par courrier dans le dossier concerné.
- **CU-AS02** Détection automatique d'un scan de mauvaise qualité (OCR < 70 %) avec demande de re-scan.
- **CU-AS03** Recherche rapide d'un document existant pour un avocat, par nom de client.
- **CU-AS04** Création d'un nouveau dossier pour un client se présentant au cabinet.

### 3.4 L'administrateur de l'application (WebVoice)

Ne fait partie d'aucun cabinet et ne gère pas de dossiers juridiques. Supervise l'ensemble des cabinets, la santé technique du système et le moteur IA, sans accès au contenu confidentiel des dossiers sauf support autorisé.

**Cas d'utilisation représentatifs :**

- **CU-AD01** Activation d'un nouveau cabinet après vérification des informations.
- **CU-AD02** Suspension d'un cabinet ne respectant plus les conditions d'utilisation.
- **CU-AD03** Suivi du dashboard technique : disponibilité, latence des réponses IA, taux d'erreur, volume de requêtes.
- **CU-AD04** Consultation des logs système (connexions, IP, erreurs) sans accès au contenu des dossiers.
- **CU-AD05** Suivi de l'usage global de l'IA et du score de confiance moyen, pour décider d'un enrichissement du corpus.

---

## 4. Spécifications fonctionnelles

### SF-1 — Gestion des cabinets (SaaS multi-tenant)

- Inscription d'un nouveau cabinet et création automatique d'un espace isolé (tenant).
- Configuration des informations du cabinet : nom, ville, coordonnées.
- Invitation de collaborateurs par email (avocats, assistants).
- Activation / suspension d'un cabinet par l'administrateur WebVoice.

### SF-2 — Authentification et gestion des accès

- Connexion par email et mot de passe ; trois rôles : Avocat, Assistant juridique, Administrateur application.
- Tokens JWT (accès 30 min, rafraîchissement 7 jours) ; expiration de session après 30 min d'inactivité.
- Blocage temporaire après 5 échecs de connexion (15 min) ; mot de passe ≥ 12 caractères avec majuscule, chiffre et caractère spécial.
- Réinitialisation du mot de passe par email ; redirection vers le dashboard selon le rôle.

### SF-3 — Gestion des dossiers juridiques

- Création d'un dossier (titre, fiche client, type d'affaire, statut, avocat responsable) avec référence unique (format `WV-2026-XXXX`).
- Modification, consultation, archivage (lecture seule) et suppression logique (corbeille 30 jours).
- Recherche textuelle, filtres combinables (type, statut, avocat, dates), tri et pagination (20 résultats/page).
- Timeline d'activité par dossier, incluant les actions de l'IA.

### SF-4 — Gestion documentaire

- Upload de documents (PDF, DOCX, images scannées) — limites : PDF 50 Mo, DOCX 25 Mo, images 20 Mo.
- Extraction automatique du texte (PDF natif, Word) et OCR pour les scans, avec alerte si qualité OCR insuffisante (< 70 %).
- Rejet explicite des fichiers corrompus ou non supportés ; versioning à chaque re-upload.
- Stockage chiffré des fichiers et **indexation vectorielle** pour la recherche IA dans le contexte du dossier.

### SF-5 — Assistant IA juridique (chat multi-sources)

L'assistant IA est un **agent unique** doté de **trois capacités de recherche**, activées automatiquement selon le contexte de la question :

| Mode | Déclencheur | Source | Exemple |
|------|-------------|--------|---------|
| **RAG corpus** | Question juridique générale | ChromaDB (DOC, CPP, CPC indexés) | *« Délai de prescription en responsabilité civile ? »* |
| **Recherche web** | Info absente du corpus ou actualité récente | DuckDuckGo / Tavily API | *« Dernière réforme du code pénal ? »* |
| **Document dossier** | Question dans le contexte d'un dossier ou d'un fichier | Vecteurs des docs uploadés du dossier | *« Quelles sont les parties au contrat ? »* |

**Comportement attendu :**

- Chat en langage naturel avec routage automatique vers la bonne source.
- Réponses avec **citations obligatoires** (article, dahir, paragraphe, URL web) et lien vers le texte intégral.
- Score de confiance affiché (0–100 %), alerte si inférieur à 60 %, disclaimer visible sur chaque réponse.
- Message explicite si l'information n'est pas trouvée (aucune invention) ; refus poli des questions hors périmètre juridique.
- Réponse en streaming (SSE), historique lié au dossier, export PDF, mode dégradé (Ollama local) si Groq est indisponible.

**Endpoints API associés :**

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/chat` | POST | Question libre — l'agent choisit la source |
| `/api/chat/stream` | POST (SSE) | Même chose en streaming |
| `/api/documents/{id}/ask` | POST | Question sur un document précis |
| `/api/documents/{id}/synthese` | GET | Synthèse automatique d'un document |

### SF-6 — Analyse et synthèse documentaire

- **Synthèse automatique** d'un PDF de 20 pages en moins de 30 secondes :
  - Faits, parties, dates clés, montants, demandes.
  - Détection de clauses à risque dans les contrats.
  - Extraction d'entités (personnes, dates, montants, articles cités).
- **Questions libres** sur un document uploadé, avec réponse citant le paragraphe exact source.
- Déclenchement automatique de la synthèse à l'upload (optionnel) ou sur demande.

### SF-7 — Administration application (back-office WebVoice)

- Liste des cabinets (actifs / suspendus), activation / suspension, dashboard global.
- Logs système, métriques IA agrégées, export de rapport mensuel (PDF / CSV).
- Aucun accès au contenu juridique confidentiel des dossiers, sauf support autorisé.

### SF-8 — Audit et traçabilité

- Journalisation de toute action utilisateur (utilisateur, action, horodatage, IP).
- Journalisation de toute requête IA : question, **source utilisée** (RAG / web / document), extraits consultés, réponse, score de confiance, durée.
- Rétention des logs : 5 ans ; piste d'audit consultable par l'avocat pour son propre cabinet.

### SF-9 — Interface utilisateur

- Interface web responsive (desktop et tablette), en français pour le MVP.
- Dashboard avocat : dossiers actifs, documents récents, conversations IA.
- Module **Chat IA** : zone de saisie, historique, indicateur de source (corpus / web / document), score de confiance.
- Module **Documents** : upload drag-and-drop, bouton « Synthétiser », chat contextuel sur le document sélectionné.
- Navigation par modules : Dossiers, Documents, Chat IA, Paramètres.

---

## 5. Spécifications non fonctionnelles

| Catégorie | Exigences principales |
|-----------|----------------------|
| **Performance** | Connexion < 3 s ; recherche dossiers < 1 s ; recherche RAG < 3 s ; recherche web < 5 s ; synthèse 20 pages < 30 s ; premier token IA < 5 s ; 50 utilisateurs simultanés minimum |
| **Sécurité** | HTTPS (TLS 1.2+) ; JWT ; hash bcrypt ; isolation multi-tenant stricte (`cabinet_id`) ; chiffrement AES-256 au repos ; aucune donnée client utilisée pour entraîner les modèles ; protection CSRF/XSS |
| **Scalabilité** | Architecture modulaire ; conteneurisation Docker ; base vectorielle extensible ; stockage fichiers externalisé |
| **Utilisabilité** | Création de dossier en ≤ 5 clics ; feedback visuel systématique ; interface en français clair, sans jargon |
| **Maintenabilité** | Code versionné (Git) ; API documentée (OpenAPI/Swagger) ; CI/CD automatisé |
| **Conformité** | Disclaimer systématique « Ceci ne constitue pas un avis juridique » ; traçabilité complète ; localisation des données à définir |
| **Compatibilité** | Chrome, Firefox, Edge (2 dernières versions) ; PDF, DOCX, JPG, PNG, TIFF ; UTF-8 (caractères arabes) |

---

## 6. Stack technologique

L'ensemble du projet est réalisable **sans aucun coût**, avec des outils open-source ou des offres gratuites suffisantes pour un MVP de projet de fin d'année.

### 6.1 Frontend

| Composant | Technologie | Coût |
|-----------|-------------|------|
| Framework | Next.js 14 (App Router) | Gratuit / open-source |
| Langage | TypeScript | Gratuit / open-source |
| Styles | Tailwind CSS | Gratuit / open-source |
| Composants UI | shadcn/ui | Gratuit / open-source |
| État global | Zustand | Gratuit / open-source |
| Chat streaming | EventSource (SSE) | Natif navigateur, gratuit |

### 6.2 Backend

| Composant | Technologie | Coût |
|-----------|-------------|------|
| Framework API | FastAPI (Python 3.11+) | Gratuit / open-source |
| ORM | SQLAlchemy 2.0 + Alembic | Gratuit / open-source |
| Validation | Pydantic v2 | Gratuit / open-source |
| Auth | python-jose + passlib[bcrypt] | Gratuit / open-source |
| Tâches async | Celery + Redis | Gratuit / open-source |
| Documentation API | Swagger UI (auto FastAPI) | Gratuit, généré automatiquement |

### 6.3 Données et stockage

| Composant | Technologie | Coût |
|-----------|-------------|------|
| BDD relationnelle | PostgreSQL 15+ (Supabase en cloud) | Gratuit |
| BDD vectorielle | ChromaDB | Gratuit / open-source |
| Cache / files | Redis 7 (Upstash en cloud) | Gratuit |
| Stockage fichiers | MinIO ou Cloudflare R2 | Gratuit / open-source |

### 6.4 Couche IA / ML

| Composant | Technologie | Rôle | Coût |
|-----------|-------------|------|------|
| Orchestration | LangChain | Pipeline RAG + routage agent | Gratuit |
| LLM (génération) | Groq (Llama 3.3) | Rédige toutes les réponses | Gratuit |
| Fallback local | Ollama + Llama 3 | Si Groq indisponible | Gratuit |
| Embeddings | BGE-M3 (HuggingFace) | Vectorise textes pour ChromaDB | Gratuit |
| Recherche web | DuckDuckGo / Tavily API | Recherche internet temps réel | Gratuit |
| OCR | Tesseract + pdf2image | Scans de mauvaise qualité | Gratuit |
| Parsing | PyMuPDF + python-docx | Extraction texte PDF/Word | Gratuit |

> **Règle fondamentale :** ChromaDB et DuckDuckGo **cherchent**, Groq **écrit**. Groq ne consulte jamais directement le corpus ni le web — il ne voit que les extraits transmis par les modules de recherche.

### 6.5 Infrastructure et déploiement

| Composant | Technologie | Coût |
|-----------|-------------|------|
| Conteneurisation | Docker + Docker Compose | Gratuit |
| CI/CD | GitHub Actions | Gratuit |
| Hébergement frontend | Vercel | Gratuit |
| Hébergement backend | Render | Gratuit (limites) |
| BDD cloud | Supabase | Gratuit (500 Mo) |
| Redis cloud | Upstash | Gratuit |
| Monitoring | Sentry | Gratuit |
| **Plan B soutenance** | Docker Compose local | Gratuit, sans quota cloud |

**Coût total MVP : 0 €**

---

## 7. Architecture de l'agent IA

### 7.1 Vue d'ensemble

L'agent IA n'est pas un chatbot générique. C'est un **système de routage intelligent** qui sélectionne automatiquement la bonne source selon le contexte de la question.

```
                         UTILISATEUR
                              │
              ┌───────────────┼───────────────┐
              │               │               │
         Question         Upload PDF     "Synthétise
          libre                              ce doc"
              │               │               │
              ▼               ▼               ▼
        ┌──────────┐   ┌──────────┐   ┌──────────────┐
        │ ROUTEUR  │   │ STOCKAGE │   │   ANALYSE    │
        │  AGENT   │   │  MinIO   │   │  DOCUMENT    │
        └────┬─────┘   └────┬─────┘   └──────┬───────┘
             │              │               │
    ┌────────┼────────┐     │               │
    ▼        ▼        ▼     ▼               ▼
┌───────┐┌───────┐┌───────┐┌────────┐┌──────────┐
│ RAG   ││  WEB  ││ DOCS  ││Extract.││ Synthèse │
│Chroma ││DuckDuck││dossier││ texte  ││ + Q&A    │
│  DB   ││Go/Tavily││vectors││+ OCR  ││          │
└───┬───┘└───┬───┘└───┬───┘└────────┘└────┬─────┘
    │        │        │                    │
    └────────┴────────┴────────────────────┘
                       │
                       ▼
                 ┌──────────┐
                 │   GROQ   │  ← Rédige TOUJOURS la réponse
                 │  (LLM)   │    à partir des extraits trouvés
                 └────┬─────┘
                      │
                      ▼
              RÉPONSE + CITATIONS
              + score confiance
              + disclaimer
```

### 7.2 Les trois capacités de l'agent

#### Capacité 1 — Recherche dans le corpus juridique (RAG)

- **Quand :** question juridique générale sur le droit marocain.
- **Comment :** ChromaDB retrouve les chunks les plus proches dans le corpus indexé (DOC, CPP, CPC).
- **Exemple :** *« Quel est le délai de prescription en responsabilité civile contractuelle ? »*
- **Réponse :** citation de l'article du DOC + lien vers le texte intégral.

#### Capacité 2 — Recherche sur Internet

- **Quand :** information absente du corpus, actualité récente, ou complément nécessaire.
- **Comment :** DuckDuckGo (ou Tavily) recherche des pages web pertinentes ; Groq synthétise les résultats.
- **Exemple :** *« Quelles sont les dernières réformes du code de procédure pénale ? »*
- **Réponse :** synthèse + URLs des sources web consultées.

#### Capacité 3 — Analyse de documents uploadés

- **Quand :** l'utilisateur upload un fichier ou pose une question dans le contexte d'un dossier.
- **Comment :** le texte est extrait (PyMuPDF/OCR), indexé dans ChromaDB par dossier, puis interrogé.
- **Exemples :**
  - Upload → synthèse automatique (parties, dates, montants, clauses à risque).
  - Question : *« Quelle est la durée du bail ? »* → réponse citant le paragraphe exact du PDF.

### 7.3 Logique de routage automatique

```python
def router_agent(question: str, dossier_id: str = None, document_id: str = None):
    if document_id:
        return "document"      # Question sur un fichier précis
    if dossier_id:
        return "dossier"       # Question dans le contexte d'un dossier
    if is_legal_question(question):
        corpus_results = search_chromadb(question)
        if corpus_results.confidence >= 0.6:
            return "rag"       # Corpus suffisant
        return "web"           # Corpus insuffisant → compléter par le web
    return "web"               # Question non juridique ou actualité
```

### 7.4 Structure des services backend

```
backend/app/services/
├── agent/
│   ├── router.py          # Décide quelle source utiliser
│   ├── rag_search.py      # Recherche ChromaDB (corpus + dossier)
│   ├── web_search.py      # Recherche DuckDuckGo / Tavily
│   └── llm.py             # Appel Groq (génération + streaming)
├── documents/
│   ├── extractor.py       # PyMuPDF, python-docx, Tesseract OCR
│   ├── indexer.py         # Chunking + embeddings BGE-M3 → ChromaDB
│   ├── synthesizer.py     # Synthèse automatique
│   └── qa.py              # Questions/réponses sur un document
└── audit/
    └── logger.py          # Traçabilité de chaque requête IA
```

---

## 8. Pipeline RAG et recherche web

### 8.1 Pipeline RAG (corpus juridique marocain)

**Étape 1 — Préparation du corpus (une seule fois)**

```
PDFs juridiques (DOC, CPP, CPC)
        │
        ▼
Découpage en chunks (~500 tokens)
        │
        ▼
Vectorisation BGE-M3
        │
        ▼
Stockage ChromaDB (collection "corpus_marocain")
```

**Étape 2 — Recherche à chaque question**

```
Question avocat
        │
        ▼
Embedding de la question (BGE-M3)
        │
        ▼
Similarity search ChromaDB (top 5 chunks)
        │
        ▼
Score de confiance calculé
        │
        ├── Score ≥ 60 % → Groq rédige avec citations
        └── Score < 60 %  → déclencher recherche web en complément
```

**Étape 3 — Génération (Groq)**

Groq reçoit uniquement les chunks trouvés + la question, et rédige en citant les sources. Il ne consulte jamais le corpus directement.

**Étape 4 — Affichage**

Réponse en streaming (SSE) + citations + score de confiance + disclaimer.

### 8.2 Pipeline recherche web

```
Question (corpus insuffisant ou actualité)
        │
        ▼
Recherche DuckDuckGo (5 résultats max)
        │
        ▼
Filtrage : sites juridiques marocains prioritaires
        │
        ▼
Groq synthétise les extraits web
        │
        ▼
Réponse + URLs sources + disclaimer
```

### 8.3 Pipeline analyse documentaire

```
Upload PDF/DOCX/image
        │
        ▼
Extraction texte (PyMuPDF / OCR si scan)
        │
        ├── Qualité OCR < 70 % → alerte re-scan
        └── Qualité OK
                │
                ▼
        Chunking + indexation ChromaDB (par dossier)
                │
        ┌───────┴───────┐
        ▼               ▼
   SYNTHÈSE AUTO    QUESTION LIBRE
   (Groq)           (ChromaDB → Groq)
        │               │
        ▼               ▼
   Résumé structuré  Réponse + citation paragraphe
```

---

## 9. Roadmap de réalisation

### 9.1 Périmètre MVP (soutenance)

| Fonctionnalité | Priorité | Semaine |
|----------------|----------|---------|
| Auth avocat (login JWT) | Obligatoire | S1 |
| CRUD dossiers | Obligatoire | S1–S2 |
| Upload PDF + extraction texte | Obligatoire | S2 |
| Synthèse automatique document | Obligatoire | S3 |
| Chat IA — recherche web | Obligatoire | S3 |
| Chat IA — questions sur document | Obligatoire | S4 |
| Chat IA — RAG corpus juridique | Fort impact | S4–S5 |
| Interface Next.js (chat + documents) | Obligatoire | S5–S6 |
| Déploiement Vercel + Render | Obligatoire | S6 |
| Multi-tenant complet | Simplifié (1 cabinet démo) | — |
| Back-office admin WebVoice | Optionnel | — |
| OCR avancé | Optionnel | — |

### 9.2 Planning détaillé (16 semaines)

| Phase | Semaines | Livrables |
|-------|----------|-----------|
| **Fondations** | S1–S3 | Repo GitHub, FastAPI + auth JWT, PostgreSQL, CRUD dossiers, structure frontend |
| **Documents** | S4–S6 | Upload, extraction texte, stockage MinIO, synthèse automatique |
| **Agent IA** | S7–S10 | Recherche web, Q&A document, RAG corpus, streaming SSE, score confiance |
| **Interface** | S11–S13 | Dashboard, module chat, module documents, responsive |
| **Déploiement** | S14–S16 | Docker Compose, Vercel + Render, tests, documentation, préparation soutenance |

### 9.3 Comptes à créer (jour 1)

| Service | URL | Usage |
|---------|-----|-------|
| Groq | console.groq.com | Clé API LLM |
| GitHub | github.com | Code + CI/CD |
| Supabase | supabase.com | PostgreSQL cloud |
| Vercel | vercel.com | Frontend |
| Render | render.com | Backend API |
| Hugging Face | huggingface.co | Modèle BGE-M3 |

### 9.4 Structure du projet

```
avocat-ai-assistance/
├── frontend/                    # Next.js 14
│   ├── app/
│   │   ├── (auth)/login/
│   │   ├── dashboard/
│   │   ├── dossiers/[id]/
│   │   ├── documents/
│   │   └── chat/
│   └── components/
│       ├── chat/                # Interface chat IA
│       └── documents/           # Upload + synthèse
├── backend/                     # FastAPI
│   ├── app/
│   │   ├── api/
│   │   │   ├── auth.py
│   │   │   ├── dossiers.py
│   │   │   ├── documents.py
│   │   │   └── chat.py
│   │   ├── models/
│   │   ├── services/
│   │   │   ├── agent/           # ⭐ Agent IA
│   │   │   │   ├── router.py
│   │   │   │   ├── rag_search.py
│   │   │   │   ├── web_search.py
│   │   │   │   └── llm.py
│   │   │   └── documents/
│   │   │       ├── extractor.py
│   │   │       ├── synthesizer.py
│   │   │       └── qa.py
│   │   └── core/
│   └── scripts/
│       └── index_corpus.py      # Indexer le droit marocain
├── data/
│   └── corpus/                  # PDFs juridiques marocains
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 10. Annexes

### Annexe A — Disclaimer affiché sur chaque réponse IA

> **Avertissement :** Les informations fournies par cet assistant sont à titre indicatif uniquement et ne constituent pas un avis juridique. Consultez toujours les textes officiels et un avocat qualifié avant toute décision. Score de confiance affiché à titre indicatif.

### Annexe B — Exemples de scénarios de démonstration (soutenance)

**Scénario 1 — Recherche juridique (RAG + web)**

1. L'avocat se connecte au dashboard.
2. Il ouvre le module Chat IA.
3. Il pose : *« Quel est le délai d'appel en matière correctionnelle au Maroc ? »*
4. L'agent cherche dans le corpus CPP (RAG), complète par le web si nécessaire.
5. Réponse affichée en streaming avec citation de l'article et lien source.
6. Score de confiance : 87 %.

**Scénario 2 — Synthèse documentaire**

1. L'avocat ouvre le dossier `WV-2026-0042`.
2. Il upload un contrat de bail commercial (PDF, 15 pages).
3. En moins de 30 secondes : synthèse structurée (parties, loyer, durée, clauses à risque).
4. Il pose : *« Y a-t-il une clause de résiliation anticipée ? »*
5. Réponse citant le paragraphe 12 du contrat.

**Scénario 3 — Contexte dossier isolé**

1. L'avocat ouvre le dossier `WV-2026-0018` (affaire pénale).
2. Il pose une question dans le contexte de ce dossier uniquement.
3. L'agent ne consulte que les documents de ce dossier — aucun mélange avec d'autres affaires.

### Annexe C — Matrice sources / confiance

| Source | Fiabilité | Quand l'utiliser | Limite |
|--------|-----------|------------------|--------|
| Corpus RAG (ChromaDB) | Haute | Textes de loi connus | Corpus à maintenir |
| Recherche web | Moyenne | Actualités, infos absentes du corpus | Vérification humaine recommandée |
| Document uploadé | Haute | Analyse de dossier | Qualité OCR variable |

### Annexe D — Évolutions post-MVP

- Intégration de nouveaux codes (Code de commerce, Code de la famille).
- Support de l'arabe dans l'interface et les réponses IA.
- Notifications email (délai procédural, document traité).
- API publique pour intégration avec des outils tiers (Outlook, etc.).
- Module de facturation SaaS pour WebVoice.

---

*Document de cadrage — Avocat AI Assistance v1.1 — WebVoice / Douae El Assal — Juin 2026*
