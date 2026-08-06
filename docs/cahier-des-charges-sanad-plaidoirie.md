# CAHIER DES CHARGES

# SANAD

**Plateforme d’Assistance en Intelligence Artificielle pour Avocats**

Document de spécifications fonctionnelles et techniques

| | |
|---|---|
| **Éditeur** | WebVoice |
| **École** | ENSA Tétouan |
| **Auteure** | Douae El Assal |
| **Année** | 2025-2026 |
| **Version** | 5.0 — Document de référence (focus plaidoirie) |

---

## 1. Objet du projet

Concevoir une plateforme web **SaaS** pour les cabinets d’avocats marocains qui permet de :

- **Rédiger une plaidoirie** plus rapidement : dictée vocale ou upload audio → texte → document mis en forme (en-tête / impression) ;
- **Centraliser** dossiers et documents dans un espace sécurisé **par cabinet** ;
- **Synthétiser** les pièces et le dossier (usage libre : préparation, revue, transmission interne, etc.) ;
- **Collaborer** avec l’équipe (avocat, assistant, admin) selon des droits définis.

### Principe directeur

> **Sanad** est un outil d’aide à la rédaction de plaidoirie.  
> L’avocat connaît déjà le droit. L’intelligence artificielle n’est pas là pour inventer une plaidoirie à sa place, mais pour **transformer sa parole (ou son audio) en texte exploitable**, le **corriger**, le **mettre en forme** dans un document officiel, et l’**organiser** dans le dossier du cabinet — à la place du circuit papier → assistant qui retape.

### Où intervient l’IA ?


| Étape | Rôle de l’IA | Ce que l’IA ne fait pas |
|---|---|---|
| Dictée / audio | Transcription parole → texte | Ne décide pas du fond juridique |
| Correction | Ponctuation, lisibilité, nettoyage des répétitions | N’ajoute pas de faits ni d’arguments inventés |
| Mise en forme | Structure légère + document imprimable (en-tête) | Ne remplace pas la relecture / signature de l’avocat |
| Synthèse pièces / dossier | Résume documents et dossier à la demande (tout usage utile) | N’invente pas le contenu des pièces |

**En résumé :** l’IA est le **moteur technique** du flux plaidoirie (voix → texte → document).

---

## 2. Contexte et problème


| Élément | Description |
|---|---|
| **Problème** | Rédaction de plaidoirie encore souvent manuelle (papier puis ressaisie) ; dossiers et pièces peu centralisés ; perte de temps entre avocat et assistant |
| **Marché cible** | Environ 13 000 à 16 000 avocats inscrits au Maroc (19 barreaux) ; LegalTech |
| **Concurrence** | Logiciels de gestion de cabinet (organisation, audiences) ; dictée générique (OS / Word / Dragon) sans workflow cabinet ni document métier lié au dossier |
| **Opportunité** | SaaS multi-cabinets centré sur le **flux plaidoirie** (dictée / audio → document), avec dossiers, pièces et rôles |

---

## 3. Acteurs et rôles


| Acteur | Rôle | Accès principal |
|---|---|---|
| **Cabinet d’avocats** | Client SaaS, espace isolé (tenant) | Inscription, configuration, équipe |
| **Avocat** | Utilisateur principal | Plaidoirie (dictée / audio), dossiers, documents, export / impression |
| **Assistant juridique** | Support documentaire et mise en forme | Upload, classement, aide à la révision selon droits ; pas de suppressions critiques |
| **Admin cabinet** | Gestion interne | Équipe, invitations, paramètres cabinet |
| **Admin WebVoice** | Supervision plateforme | Activation / suspension cabinets, métriques, logs (**sans** accès au contenu confidentiel des dossiers) |

---

## 4. Exigences fonctionnelles

### 4.1 Authentification et accès

| ID | Exigence |
|---|---|
| F-01 | Inscription cabinet avec création automatique d’un espace isolé |
| F-02 | Authentification JWT (login, refresh, logout) |
| F-03 | Vérification email, mot de passe oublié, reset |
| F-04 | Blocage compte après 5 échecs de connexion |
| F-05 | 4 rôles : avocat, assistant, admin cabinet, admin WebVoice |
| F-06 | Invitation collaborateurs par email (+ lien d’activation) |
| F-07 | 2FA et Google OAuth |

### 4.2 Rédaction de plaidoirie *(cœur produit)*

| ID | Exigence |
|---|---|
| F-08 | Dictée vocale navigateur (MVP / démo ; arabe prioritaire) |
| F-08b | Upload audio → transcription serveur (Whisper / `faster-whisper`, multilingue FR / AR / EN) |
| F-08c | Correction / nettoyage du texte (ponctuation, lisibilité, sans altérer le fond) |
| F-08d | Génération document imprimable avec en-tête professionnel |
| F-08e | Association de la plaidoirie à un dossier |
| F-08f | Priorité sur une rédaction (urgent / normal) |

### 4.3 Dossiers et documents

| ID | Exigence |
|---|---|
| F-10 | CRUD dossiers avec référence unique `WV-AAAA-XXXX` |
| F-11 | Upload PDF, DOCX, images (max 50 Mo) |
| F-12 | Extraction texte + OCR (français et arabe) |
| F-13 | Alerte si qualité OCR &lt; 70 % |
| F-14 | Stockage chiffré (MinIO) |
| F-15 | Recherche, filtres et timeline d’activité dossier |
| F-16 | Notes liées au dossier |

### 4.4 Synthèse des dossiers et documents

L’avocat peut joindre des pièces à son dossier. Le système lui permet de **synthétiser** un document ou l’ensemble du dossier **pour n’importe quel besoin** (préparation, revue, briefing, etc.).

| ID | Exigence |
|---|---|
| F-30 | Synthèse automatique d’un document : parties, dates, montants, points saillants / clauses à risque |
| F-31 | Synthèse à l’échelle du **dossier** (vue consolidée des pièces uploadées) |
| F-32 | Synthèse d’un PDF volumineux (cible : ~20 pages en moins de 30 secondes) |

### 4.5 Administration et audit

| ID | Exigence |
|---|---|
| F-40 | Back-office WebVoice : activation / suspension cabinets |
| F-41 | Dashboard métriques (cabinets, users, documents) |
| F-42 | Journalisation des actions sensibles |
| F-43 | Rétention logs (politique cible 5 ans) |

---

## 5. Exigences non fonctionnelles

### Performance

- Connexion : &lt; 3 s  
- Synthèse d’un document / dossier (~20 pages) : &lt; 30 s  
- 50 utilisateurs simultanés supportés  

### Sécurité

- HTTPS / TLS obligatoire en production  
- Mots de passe hashés (bcrypt)  
- Isolation multi-tenant stricte entre cabinets  
- Fichiers chiffrés (AES-256 / MinIO)  
- Aucune donnée client utilisée pour entraîner un modèle public  

### Conformité et disponibilité

- Traçabilité des actions sensibles  
- Interface bilingue FR / AR (RTL)  
- Uptime cible : 99 % en production  

---

## 6. Architecture fonctionnelle

### Flux cœur — plaidoirie


| Étape | Déclencheur | Résultat |
|---|---|---|
| **Dictée** | Micro navigateur | Texte brut |
| **Audio** | Upload fichier son | Transcription |
| **Correction** | Action utilisateur / service | Texte lisible, ponctué |
| **Document** | Génération | PDF / impression avec en-tête |
| **Dossier** | Association | Plaidoirie + pièces liées |
| **Synthèse** | Document ou dossier sélectionné | Résumé des pièces / du dossier (usage libre) |

---

## 7. Stack technologique


| Couche | Technologies |
|---|---|
| **Frontend** | Next.js 14, TypeScript, Tailwind CSS, Zustand |
| **Backend** | FastAPI, SQLAlchemy, Pydantic v2, Celery, Redis |
| **Données** | PostgreSQL, Redis, MinIO |
| **STT** | Web Speech (MVP navigateur) + Whisper / `faster-whisper` serveur (cible qualité, multilingue FR / AR / EN) |
| **IA texte** | LLM cloud pour correction / mise en forme / synthèse ; Tesseract (OCR) ; Ollama en secours si besoin |
| **Infra** | Docker Compose, Alembic |

---

## 8. Périmètre


| Inclus (cœur) | Hors périmètre de ce cahier |
|---|---|
| Dictée / audio → plaidoirie → document | Assistant conversationnel / questions juridiques libres (chat) |
| Dossiers, documents, notes, priorités | Planning type agenda avancé / Mahakim |
| Synthèse des pièces et du dossier (usage libre) | Facturation / CRM cabinet |
| Rôles et invitations cabinet | — |
| Admin plateforme + audit | — |

---

## 9. Critères d’acceptation globaux

1. Un cabinet peut s’inscrire et gérer ses dossiers de bout en bout.  
2. Un avocat peut **dicter** ou **uploader un audio**, obtenir un texte corrigé et un **document de plaidoirie** imprimable.  
3. La rédaction peut être rattachée à un **dossier** contenant des pièces.  
4. Un avocat peut obtenir une **synthèse** d’un document ou du dossier, sans restriction d’usage.  
5. Un assistant intervient selon des **droits** définis.  
6. Les actions sensibles sont **journalisées** ; les cabinets sont **isolés** entre eux.

---

## 10. Analyse concurrentielle (benchmark)

Cette section situe Sanad par rapport aux solutions existantes. L’étude détaillée figure dans le document dédié *Étude de marché et Benchmark — Sanad*.

### Le marché marocain de la gestion de cabinet

Plusieurs plateformes SaaS marocaines couvrent déjà la **gestion administrative** des cabinets :

- **AvocatPro** et **Avocato** : dossiers, audiences, facturation, avec intégration à [Mahakim.ma](https://mahakim.ma) ;
- **SmartAvocat** : gestion bilingue, conformité fiscale marocaine ;
- **Oasis Avocat** : assistant IA de recherche juridique et d’aide à la rédaction d’actes.

**Aucune de ces solutions ne prend en charge la chaîne** *dictée / audio → transcription → document de plaidoirie formaté, rattaché à un dossier*.

### Les outils de dictée juridique existants

À l’international, des solutions comme **Dragon Legal**, **Isidictée**, **Philips SpeechLive** ou **Septeo AI Transcription** assurent la transcription vocale pour les professions juridiques. Ce sont des outils de dictée **génériques** : non conçus pour le marché marocain, non bilingues français-arabe dans un SaaS cabinet, et non intégrés à un espace de dossiers et de rôles par cabinet.

### Ce que cela signifie pour Sanad

Les solutions marocaines actuelles excellent surtout dans la **gestion du cabinet** (dossiers, audiences, facturation, Mahakim). Les outils internationaux excellent surtout dans la **dictée générique**.  

**Sanad** vise autre chose : une **plateforme d’assistance IA** pour l’avocat marocain, où la rédaction de plaidoirie (voix / audio → document), les dossiers, les pièces, la synthèse et la collaboration en équipe forment **un même produit**, bilingue FR/AR, multi-cabinets.

Sanad n’est donc **pas** une copie d’AvocatPro, d’Avocato ou de Dragon : son positionnement repose sur l’**assistance intelligente au travail juridique quotidien**, centrée sur la production documentaire et le dossier — dans le contexte des 19 barreaux marocains.

**Sources :** sites officiels AvocatPro, SmartAvocat, Avocato, Oasis Avocat ; Diskod / Dragon Legal ; Isidictée ; Septeo Digital Services. Liste complète des liens dans le document Benchmark.

---

## 11. Validation


| | Nom | Date | Visa |
|---|---|---|---|
| **Auteure** | Douae El Assal | | |
| **Encadrant entreprise** | | | |
| **Encadrant pédagogique** | | | |

---

*Sanad v5.0 — Plateforme d’Assistance en Intelligence Artificielle pour Avocats. Cœur produit de ce cahier : rédaction de plaidoirie.*
