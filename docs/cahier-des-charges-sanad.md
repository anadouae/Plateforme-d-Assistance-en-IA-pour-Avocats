# Projet de fin d’études

# SANAD  

## Cahier des charges


|             |                                                                 |
| ----------- | --------------------------------------------------------------- |
| **Sujet**   | Plateforme SaaS — rédaction de plaidoiries & assistance cabinet |
| **Éditeur** | WebVoice                                                        |
| **École**   | ENSA Tétouan                                                    |
| **Auteure** | Douae El Assal                                                  |
| **Année**   | 2025-2026                                                       |
| **Version** | 3.1 — Juillet 2026                                              |

> **Deux versions du CDC :**  
> - **Focus plaidoirie / encadrant (sans chat)** → [`cahier-des-charges-sanad-plaidoirie.md`](./cahier-des-charges-sanad-plaidoirie.md)  
> - **Version élargie** (ce fichier) — modules optionnels éventuels.


---

## 1. Objet du projet

Concevoir une plateforme web **SaaS** pour les cabinets d’avocats marocains qui permet de :

1. **Rédiger une plaidoirie** plus rapidement : dictée vocale ou upload audio → texte → document mis en forme (en-tête / impression) ;
2. **Centraliser** dossiers et documents dans un espace sécurisé **par cabinet** ;
3. **Collaborer** avec l’équipe (avocat, assistant, admin) selon des droits définis ;
4. *(Module secondaire)* Interroger un assistant IA fondé sur des sources (corpus, web, documents du dossier) et obtenir des synthèses avec citations.

### Principe directeur

> **Sanad est un outil d’aide à la rédaction de plaidoirie.**  
> L’avocat connaît déjà le droit ; l’IA n’est pas là pour « inventer » une plaidoirie à sa place, mais pour **transformer sa parole (ou son audio) en texte exploitable**, le **corriger**, le **mettre en forme** dans un document officiel, et l’**organiser** dans le dossier du cabinet — à la place du circuit papier → assistant qui retape.

#### Où intervient l’IA dans ce principe ?


| Étape                         | Rôle de l’IA                                                  | Ce que l’IA ne fait pas                                     |
| ----------------------------- | ------------------------------------------------------------- | ----------------------------------------------------------- |
| Dictée / audio                | Transcription parole → texte                                  | Ne décide pas du fond juridique                             |
| Correction                    | Ponctuation, lisibilité, nettoyage des répétitions            | N’ajoute pas de faits ni d’arguments inventés               |
| Mise en forme                 | Structure légère + document imprimable (en-tête)              | Ne remplace pas la relecture / signature de l’avocat        |
| *(Optionnel)* Chat / synthèse | Aide ponctuelle **à partir de sources** (corpus, web, pièces) | Ne répond pas « de mémoire » ; sans source, elle le signale |


En résumé : **l’IA est le moteur technique du flux plaidoirie** (voix → texte → document). Le chat juridique, s’il existe, reste un **module secondaire** soumis à la règle des sources.

---

## 2. Contexte et problème


| Élément          | Description                                                                                                                                                         |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Problème**     | Rédaction de plaidoirie encore souvent manuelle (papier puis ressaisie) ; dossiers et pièces peu centralisés ; perte de temps entre avocat et assistant             |
| **Marché cible** | ~13 000 à 16 000 avocats inscrits au Maroc (19 barreaux) ; LegalTech                                                                                                |
| **Concurrence**  | LegalTech locale surtout orientée gestion de cabinet ou chat juridique ; dictée générique (OS / Word) sans workflow cabinet ni document métier                      |
| **Opportunité**  | SaaS multi-cabinets centré sur le **flux plaidoirie** (dictée / audio → document), avec dossiers, pièces et rôles — différenciation claire vs Word + dictée Windows |


---

## 3. Acteurs et rôles


| Acteur                  | Rôle                                  | Accès principal                                                                                         |
| ----------------------- | ------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| **Cabinet d’avocats**   | Client SaaS, espace isolé (tenant)    | Inscription, configuration, équipe                                                                      |
| **Avocat**              | Utilisateur principal                 | Plaidoirie (dictée / audio), dossiers, documents, export / impression ; accès module IA si activé       |
| **Assistant juridique** | Support documentaire et mise en forme | Upload, classement, aide à la révision selon droits ; **pas** de chat IA ni suppressions critiques      |
| **Admin cabinet**       | Gestion interne                       | Équipe, invitations, paramètres cabinet                                                                 |
| **Admin WebVoice**      | Supervision plateforme                | Activation / suspension cabinets, métriques, logs (**sans** accès au contenu confidentiel des dossiers) |


---

## 4. Exigences fonctionnelles

### 4.1 Authentification et accès


| ID   | Exigence                                                        |
| ---- | --------------------------------------------------------------- |
| F-01 | Inscription cabinet avec création automatique d’un espace isolé |
| F-02 | Authentification JWT (login, refresh, logout)                   |
| F-03 | Vérification email, mot de passe oublié, reset                  |
| F-04 | Blocage compte après 5 échecs de connexion                      |
| F-05 | 4 rôles : avocat, assistant, admin cabinet, admin WebVoice      |
| F-06 | Invitation collaborateurs par email (+ lien d’activation)       |
| F-07 | 2FA et Google OAuth                                             |


### 4.2 Rédaction de plaidoirie *(cœur produit)*


| ID    | Exigence                                                  |
| ----- | --------------------------------------------------------- |
| F-08  | Dictée vocale (arabe prioritaire) vers texte éditable     |
| F-08b | Upload fichier audio → transcription automatique          |
| F-08c | Correction / nettoyage du texte (ponctuation, lisibilité) |
| F-08d | Génération document imprimable avec en-tête professionnel |
| F-08e | Association de la plaidoirie à un dossier                 |
| F-08f | Priorité sur une rédaction (urgent / normal)              |


### 4.3 Dossiers et documents


| ID   | Exigence                                                      |
| ---- | ------------------------------------------------------------- |
| F-10 | CRUD dossiers avec référence unique `WV-AAAA-XXXX`            |
| F-11 | Upload PDF, DOCX, images (max 50 Mo)                          |
| F-12 | Extraction texte + OCR (français et arabe)                    |
| F-13 | Alerte si qualité OCR < 70 %                                  |
| F-14 | Stockage chiffré (MinIO) + indexation vectorielle par dossier |
| F-15 | Recherche, filtres et timeline d’activité dossier             |
| F-16 | Notes liées au dossier                                        |


### 4.4 Assistant IA *(module secondaire — non bloquant pour le cœur)*


| ID   | Exigence                                                    |
| ---- | ----------------------------------------------------------- |
| F-20 | Routage automatique : document → dossier → corpus RAG → web |
| F-21 | Réponses avec citations et score de confiance (0–100 %)     |
| F-22 | Alerte si confiance < 60 %                                  |
| F-23 | Streaming SSE des réponses                                  |
| F-24 | Historique des conversations (sessions)                     |
| F-25 | LLM via API (multi-providers) + mode dégradé local (Ollama) |
| F-26 | Export PDF des réponses IA                                  |
| F-27 | Disclaimer : « Ceci ne constitue pas un avis juridique »    |


### 4.5 Analyse documentaire *(secondaire / support)*


| ID   | Exigence                                                            |
| ---- | ------------------------------------------------------------------- |
| F-30 | Synthèse automatique : parties, dates, montants, clauses à risque   |
| F-31 | Questions libres sur un document avec citation du paragraphe source |
| F-32 | Synthèse d’un PDF de ~20 pages en moins de 30 secondes (cible)      |


### 4.6 Administration et audit


| ID   | Exigence                                                |
| ---- | ------------------------------------------------------- |
| F-40 | Back-office WebVoice : activation / suspension cabinets |
| F-41 | Dashboard métriques (cabinets, users, docs, requêtes)   |
| F-42 | Journalisation des actions sensibles et requêtes IA     |
| F-43 | Rétention logs (politique cible 5 ans)                  |


---

## 5. Exigences non fonctionnelles


| Catégorie     | Exigence                                                      | Cible                |
| ------------- | ------------------------------------------------------------- | -------------------- |
| Performance   | Connexion                                                     | < 3 s                |
| Performance   | Transcription / correction plaidoirie                         | Usage fluide cabinet |
| Performance   | Réponse RAG (module IA)                                       | < 3 s                |
| Performance   | Recherche web (module IA)                                     | < 5 s                |
| Performance   | Synthèse ~20 pages                                            | < 30 s               |
| Performance   | Utilisateurs simultanés                                       | 50                   |
| Sécurité      | HTTPS/TLS en production                                       | Obligatoire          |
| Sécurité      | Mots de passe hashés (bcrypt)                                 | Obligatoire          |
| Sécurité      | Isolation multi-tenant stricte                                | Obligatoire          |
| Sécurité      | Chiffrement fichiers (AES-256 / MinIO)                        | Obligatoire          |
| Sécurité      | Aucune donnée client utilisée pour entraîner un modèle public | Obligatoire          |
| Conformité    | Traçabilité des actions sensibles                             | Obligatoire          |
| UX            | Interface FR / AR (RTL)                                       | Obligatoire          |
| Disponibilité | Uptime cible en production                                    | 99 %                 |


---

## 6. Architecture fonctionnelle

### 6.1 Flux cœur — plaidoirie


| Étape          | Déclencheur                  | Résultat                      |
| -------------- | ---------------------------- | ----------------------------- |
| **Dictée**     | Micro navigateur             | Texte brut                    |
| **Audio**      | Upload fichier son           | Transcription                 |
| **Correction** | Action utilisateur / service | Texte lisible, ponctué        |
| **Document**   | Génération                   | PDF / impression avec en-tête |
| **Dossier**    | Association                  | Plaidoirie + pièces liées     |


### 6.2 Flux secondaire — agent IA


| Mode           | Déclencheur                    | Source                         |
| -------------- | ------------------------------ | ------------------------------ |
| **Document**   | Question sur un fichier        | Vecteurs du document           |
| **Dossier**    | Question dans un dossier       | Vecteurs des pièces du dossier |
| **RAG corpus** | Question juridique générale    | ChromaDB (corpus indexé)       |
| **Web**        | Corpus insuffisant / actualité | DuckDuckGo / Tavily            |


**Règle (module IA) :** la recherche récupère les extraits ; le LLM rédige la réponse finale. Le LLM ne « invente » pas de sources.

---

## 7. Stack technologique


| Couche            | Technologies                                                                                                 |
| ----------------- | ------------------------------------------------------------------------------------------------------------ |
| **Frontend**      | Next.js 14, TypeScript, Tailwind CSS, Zustand                                                                |
| **Backend**       | FastAPI, SQLAlchemy, Pydantic v2, Celery, Redis                                                              |
| **Données**       | PostgreSQL, ChromaDB, Redis, MinIO                                                                           |
| **IA / document** | BGE-M3, LLM cloud (ex. Mistral / Groq…), Ollama, Tesseract ; STT navigateur (+ cible STT serveur pour audio) |
| **Infra**         | Docker Compose, Alembic                                                                                      |


---

## 8. Périmètre — synthèse


| Inclus (cœur)                          | Secondaire / hors cœur                         |
| -------------------------------------- | ---------------------------------------------- |
| Dictée / audio → plaidoirie → document | Chat IA juridique (déjà réalisé, non bloquant) |
| Dossiers, documents, notes, priorités  |                                                |
| Rôles et invitations cabinet           | —                                              |
| Admin plateforme + audit               | —                                              |


---

## 9. Critères d’acceptation globaux

1. Un cabinet peut s’inscrire et gérer ses dossiers de bout en bout.
2. Un avocat peut **dicter** ou (cible) **uploader un audio**, obtenir un texte corrigé et un **document de plaidoirie** imprimable.
3. La rédaction peut être rattachée à un **dossier** contenant des pièces.
4. Un assistant intervient selon des **droits** définis (sans accès chat IA).
5. *(Module secondaire)* Un avocat peut obtenir une synthèse / questions avec **citations** ; aucune réponse IA sans source identifiée lorsque le mode sources s’applique.
6. Les actions sensibles sont **journalisées** ; les cabinets sont **isolés** entre eux.

---

## 10. Validation


|                           | Nom            | Date | Visa |
| ------------------------- | -------------- | ---- | ---- |
| **Auteure**               | Douae El Assal |      |      |
| **Encadrant entreprise**  |                |      |      |
| **Encadrant pédagogique** |                |      |      |


---

*Sanad v3.1 — Cœur = rédaction de plaidoirie. Module IA = secondaire.*