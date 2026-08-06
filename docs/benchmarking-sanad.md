# Sanad — Benchmarking LegalTech (Maroc)

| | |
|---|---|
| **Projet** | Sanad — SaaS cabinets d’avocats |
| **Auteure** | Douae El Assal · WebVoice |
| **Périmètre** | **Marché marocain uniquement** (LegalTech et logiciels cabinets au Maroc) |
| **Version** | 3.2 — Juillet 2026 |
| **Cœur produit** | Rédaction de plaidoirie (dictée / audio → document) |

> **Périmètre volontairement marocain.** Aucun concurrent international type Harvey / LexisNexis n’est inclus comme référence principale. Dragon Legal n’apparaît que via son **revendeur au Maroc** (Diskod), comme objection « dictée Windows / desktop ».
>
> **Deux versions :**  
> - **Benchmark 1** (ce fichier) = panorama LegalTech / gestion cabinet.  
> - **Benchmark 2** = focus 100 % plaidoirie → [`benchmarking-sanad-plaidoirie.md`](./benchmarking-sanad-plaidoirie.md).

---

## 0. Sources et sites officiels (Maroc)

| Concurrent | Pays / ancrage | Site officiel |
|---|---|---|
| **Legal IQ (Legaliq)** | Maroc (Rabat) — LegalTech / FiscalTech | [https://legaliq.ma/](https://legaliq.ma/) |
| **Kanoun** | Maroc — IA droit marocain + OHADA | [https://kanoun.com/](https://kanoun.com/) |
| **Adala** | Maroc — assistant juridique IA | [https://adala.ai/](https://adala.ai/) |
| **Omniscient** | Maroc — outil Westfield Avocats (Casablanca / Rabat) | [https://ai.westfieldavocats.com/](https://ai.westfieldavocats.com/) · cabinet : [https://westfieldavocats.com/](https://westfieldavocats.com/) |
| **SmartAvocat** | Maroc — SaaS gestion cabinet | [https://smartavocat.ma/](https://smartavocat.ma/) |
| **Avocato** | Maroc — gestion cabinet + Mahakim | [https://avocato.ma/](https://avocato.ma/) |
| **AvocatPro** | Maroc — gestion cabinet + Mahakim | [https://avocatpro.ma/](https://avocatpro.ma/) |
| **Dragon Legal** *(via revendeur MA)* | Produit Nuance distribué au Maroc | [https://diskod.ma/produit/nuance-dragon-legal-licence-dragon-legal/](https://diskod.ma/produit/nuance-dragon-legal-licence-dragon-legal/) |

Tous les acteurs du tableau principal ci-dessus sont **positionnés sur le marché marocain** (site `.ma`, offre droit marocain, ou cabinet / revendeur établi au Maroc).

---

## 1. Objectif

Comparer Sanad aux LegalTech **marocaines**, puis capitaliser leurs forces dans Sanad :

1. identifier ce que chaque concurrent fait mieux ;
2. montrer ce que Sanad a déjà ;
3. planifier ce qu’on ajoute pour rester compétitif **sur le cœur plaidoirie**, sans perdre les acquis cabinet / documents.

### Critères du projet (référence)

| Critère | Rôle dans Sanad |
|---|---|
| SaaS multi-cabinets | Socle obligatoire |
| Gestion dossiers + documents | Socle obligatoire |
| **Rédaction de plaidoirie** (dictée / audio → texte → document) | **Cœur produit** |
| OCR / analyse documentaire | Support du dossier et des pièces |
| Agent IA multi-sources | Module secondaire (aide ponctuelle) |
| Sécurité (rôles, audit, chiffrement) | Obligatoire |
| LLM via API keys | Technique (correction, synthèse, chat) |

**Périmètre géographique :** Maroc.

---

## 2. Vue rapide des concurrents (marché marocain)

| Plateforme | Marché | Ce qu’ils vendent | Force principale | Limite principale | Lien |
|---|---|---|---|---|---|
| **Legaliq** | Maroc | IA B2B juridique / fiscale | BO + fiscalité + docs uploadés | Pas de vrai SaaS cabinet ; pas de flux plaidoirie | [legaliq.ma](https://legaliq.ma/) |
| **Kanoun** | Maroc | Expert IA MA + OHADA | OHADA + audit contrats + précision | Pas de workflow multi-tenant cabinet | [kanoun.com](https://kanoun.com/) |
| **Adala** | Maroc | Assistant grand public | Q&R + jurisprudence + génération docs + FR/AR/EN | Pas conçu pour cabinet multi-équipes ni dictée plaidoirie | [adala.ai](https://adala.ai/) |
| **Omniscient** | Maroc | Revue de contrats (Westfield) | Analyse contrat rapide + export Word | Scope contrats uniquement, pas plateforme cabinet | [ai.westfieldavocats.com](https://ai.westfieldavocats.com/) |
| **SmartAvocat** | Maroc | Gestion de cabinet SaaS | Dossiers, bilingue AR/FR, hébergement MA | Pas centré dictée → plaidoirie | [smartavocat.ma](https://smartavocat.ma/) |
| **Avocato** | Maroc | Gestion cabinet + Mahakim | Sync audiences, portail client | Pas centré dictée → plaidoirie | [avocato.ma](https://avocato.ma/) |
| **AvocatPro** | Maroc | Gestion cabinet + Mahakim | Import Mahakim, organisation | Pas centré dictée → plaidoirie | [avocatpro.ma](https://avocatpro.ma/) |
| **Dragon Legal** | Distribué au Maroc | Dictée desktop (Nuance) | Reconnaissance vocale juridique | Pas SaaS multi-cabinets ; pas workflow Sanad | [diskod.ma](https://diskod.ma/produit/nuance-dragon-legal-licence-dragon-legal/) |

### 2.1 Fiches détaillées — ce que font ces plateformes (sources sites officiels)

#### A. Nuance Dragon Legal v16 — via Diskod (Maroc)

| | |
|---|---|
| **Site** | [diskod.ma — Dragon Legal v16](https://diskod.ma/produit/nuance-dragon-legal-licence-dragon-legal/) |
| **Type** | Logiciel desktop de reconnaissance vocale (licence Nuance) ; Diskod = distributeur officiel au Maroc |
| **Ancrage MA** | Revendeur agréé Casablanca ; support FR/AR ; facturation TVA 20 % / Loi 09-08 |

**Fonctionnalités annoncées :**

- Reconnaissance vocale avec vocabulaire juridique avancé (contrats, mémoires, actes, requêtes)
- Dictée en temps réel vers Word, Google Docs, Outlook et logiciels de gestion de cabinet
- Précision revendiquée élevée (jusqu’à ~99 %) ; adaptation à la voix / accent / style du juriste
- Commandes vocales personnalisables (clauses types, formules, structures de mémoires)
- Licence perpétuelle (pas d’abonnement SaaS cabinet)
- Cibles : avocats, notaires, huissiers, magistrats, assistantes juridiques, etc.

**Limite pour le benchmarking Sanad :** excellente brique « parole → texte », mais **pas** d’espace multi-cabinets, **pas** de dossier collaboratif, **pas** de document métier Sanad (en-tête / rôles / upload audio cloud).

---

#### B. AvocatPro (Neologix) — Maroc

| | |
|---|---|
| **Site** | [https://avocatpro.ma/](https://avocatpro.ma/) |
| **Type** | Plateforme digitale de gestion de cabinet |
| **Ancrage MA** | Conçu pour avocats marocains ; import Mahakim ; UI FR/AR |

**Fonctionnalités annoncées :**

- Gestion des dossiers juridiques et archivage
- Suivi des audiences et rendez-vous
- **Import automatique depuis mahakim.ma** (audiences sans ressaisie)
- Alertes intelligentes (~48 h avant audience / délai)
- Synchronisation mobile et web
- Tableau de bord / pilotage d’activité
- Chiffrement / sécurité des dossiers
- **Assistant IA** : analyse de documents, classement, questions juridiques
- Cibles : avocat indépendant, cabinet en croissance, cabinet multi-avocats

**Limite :** fort sur **organisation / Mahakim** ; pas positionné sur le flux **dictée → plaidoirie → document officiel**.

---

#### C. AVOCATO — Maroc

| | |
|---|---|
| **Site** | [https://avocato.ma/](https://avocato.ma/) |
| **Type** | Logiciel de gestion cabinet + IA + portail client |
| **Ancrage MA** | Hébergement 100 % Maroc ; Loi 09-08 / CNDP ; support AR/FR ; Rabat |

**Fonctionnalités annoncées :**

- Gestion dossiers, clients, facturation, documentaire
- **Synchronisation Mahakim** (audiences, salles, état des procédures)
- Portail client (dépôt documents, suivi dossier — réduction des appels)
- Interface arabe native (RTL)
- Notifications WhatsApp (rappels clients)
- Calcul diligences / suivi honoraires et rentabilité
- Analyse IA des dossiers
- Annuaire des avocats / inscription visibilité
- Migration depuis un ancien outil
- Essai / plan gratuit annoncé ; support 24/7

**Limite :** plateforme **gestion + Mahakim + client** ; pas le cœur **rédaction de plaidoirie par dictée/audio**.

---

#### D. SmartAvocat — Maroc

| | |
|---|---|
| **Site** | [https://smartavocat.ma/](https://smartavocat.ma/) |
| **Type** | SaaS gestion de cabinet (bilingue AR/FR) |
| **Ancrage MA** | Conforme CNBM / Loi 09-08 ; hébergement Maroc ; Casablanca ; tarifs en MAD |

**Fonctionnalités annoncées :**

- Gestion des dossiers (suivi, pièces, alertes d’échéances)
- Agenda et audiences (rappels SMS/email)
- Facturation & honoraires (TVA marocaine, DH)
- Interface bilingue arabe / français (RTL)
- Application mobile iOS / Android
- Collaboration d’équipe (droits par rôle / dossier)
- Rapports et statistiques (CA, dossiers, rentabilité)
- Bibliothèque de modèles d’actes (AR/FR)
- Formules Solo / Cabinet / Entreprise (essai 30 jours)
- Communication : ~1 500+ cabinets clients (chiffre site)

**Limite :** référence **CRM / gestion cabinet** ; pas de parcours dédié **dictée → plaidoirie**.

---

#### Synthèse catégorie « gestion cabinet » vs Sanad

| Besoin avocat | SmartAvocat / Avocato / AvocatPro | Dragon (Diskod) | Sanad (cible) |
|---|---|---|---|
| Dossiers, audiences, Mahakim | Fort | — | Socle dossiers (Mahakim hors cœur PFE) |
| Dictée juridique précise | — | Fort (desktop) | Dictée / audio **dans** le SaaS |
| Document plaidoirie + rôles | Partiel (modèles / docs) | Texte dans Word | **Cœur** : voix → document cabinet |
| Multi-tenant + invitations | Oui | Non | Oui |

---

## 3. Tableau comparatif fonctionnel

Légende : Oui · Partiel · — (absent ou non positionné)

| Critère | Legaliq | Kanoun | Adala | Omniscient | Gestion cabinet MA* | Sanad |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| SaaS multi-cabinets | — | — | — | — | Oui | Oui |
| Gestion dossiers (CRUD) | — | — | Partiel | — | Oui | Oui |
| Upload + OCR + alerte qualité | Partiel | Partiel | Partiel | Oui | Partiel | Oui |
| **Dictée / audio → plaidoirie** | — | — | — | — | — | **Oui (cœur)** |
| Document imprimable (en-tête) | — | — | Partiel | Export Word | Partiel | Oui |
| Rôles avocat / assistant + invitations | — | — | — | — | Oui | Oui |
| RAG corpus marocain | Oui | Oui | Oui | Partiel | — | Oui |
| OHADA / droit africain | — | Oui | — | — | — | Oui |
| Recherche web | — | Partiel | — | — | — | Oui |
| Routage RAG / Web / Doc | — | Partiel | — | — | — | Oui |
| Synthèse / Q&R document | Oui | Oui | Oui | Oui | — | Oui |
| Génération de documents | — | Partiel | Oui | Export Word | Partiel | Oui (templates + plaidoirie) |
| Multilingue FR / AR | Partiel | Partiel | Oui | Partiel | Oui | Oui |
| Audit + chiffrement | — | — | — | Partiel | Partiel | Oui |
| LLM via API keys | Oui | Oui | Oui | Oui | Variable | Oui |
| Multi-providers + failover | — | — | — | — | — | Oui |
| Fallback LLM local (Ollama) | — | — | — | — | — | Oui |

\* SmartAvocat, Avocato, AvocatPro (catégorie « gestion cabinet »).

---

## 4. Forces des concurrents → intégration dans Sanad

Idée centrale : ne pas seulement « gagner » sur le SaaS cabinet, mais absorber ce qui rend les concurrents attractifs — **tout en restant centré sur la plaidoirie**.

### 4.1 Legaliq — ce qui les rend forts

| Force Legaliq | Pourquoi c’est important | Dans Sanad | Comment on l’ajoute / renforce |
|---|---|---|---|
| Couverture législation + fiscalité MA | L’avocat cherche souvent du fiscal + du BO | Partiel | Enrichir le corpus fiscal (CGI, codes) via imports BO ; utile en module secondaire |
| Analyse de documents uploadés | Gain de temps sur pièces clients | Déjà | Pipeline upload → OCR → index → synthèse ; pièces liées à la plaidoirie / dossier |
| Réponses sourcées | Crédibilité | Déjà (module IA) | Citations + score de confiance + disclaimer |

### 4.2 Kanoun — ce qui les rend forts

| Force Kanoun | Pourquoi c’est important | Comment on l’ajoute / renforce |
|---|---|---|
| Corpus OHADA + cartographie | Cabinets avec dossiers Afrique / OHADA | Maintenir le corpus OHADA ; citer les articles dans le module secondaire |
| Audit de contrats | Détection risques / clauses | Étendre l’analyse document : checklist clauses + export ; utile avant / pendant la plaidoirie |
| Benchmark qualité (ex. 50 Q) | Preuve de sérieux IA | Scripts de benchmark + suivi admin (mémoire / annexe) |

### 4.3 Adala — ce qui les rend forts

| Force Adala | Pourquoi c’est important | Comment on l’ajoute / renforce |
|---|---|---|
| Jurisprudence accessible | Les avocats citent la jurisprudence | Enrichir le corpus jurisprudence (module secondaire) |
| Génération de documents | Contrats / actes en 1 clic | Templates existants + **priorité** : document de plaidoirie mis en forme |
| FR / AR fluide | Barreaux bilingues | i18n UI + dictée / rédaction en arabe (cœur) |
| UX simple | Adoption rapide | Parcours principal clair : **Dicter → Corriger → Document** (page plaidoirie en premier) |

### 4.4 Omniscient — ce qui les rend forts

| Force Omniscient | Pourquoi c’est important | Comment on l’ajoute / renforce |
|---|---|---|
| Revue contrat rapide | Usage quotidien affaires | Mode revue sur document (parties, dates, montants, risques) |
| Export Word | Livrable client / dossier | Ajouter export DOCX en plus du PDF (plaidoirie + synthèses) |
| RAG sur doc client | Réponse ancrée dans la pièce | Chat / synthèse scoped document-dossier (déjà) |

### 4.5 Gestion cabinet (SmartAvocat, Avocato…) — ce qu’il faut retenir

| Force | Pourquoi | Dans Sanad |
|---|---|---|
| Dossiers + équipe | Socle métier | Déjà (CRUD, rôles, invitations) |
| Bilingue AR/FR | Adoption MA | Déjà |
| Suivi audiences / Mahakim | Organisation | Hors cœur ; notes / priorités dossier suffisent pour le PFE |

### 4.6 Dragon Legal / dictée générique — l’objection « Word + Windows »

| Force | Limite | Réponse Sanad |
|---|---|---|
| Dictée précise | Desktop, licence, pas SaaS cabinet | Dictée / audio **dans** le cabinet, liée au dossier, avec rôles et document officiel |
| Vocabulaire juridique | Pas de workflow assistant | Avocat dicte · assistant révise / imprime |

---

## 5. Architecture LLM Sanad (API keys)

Sanad utilise des clés API côté serveur pour plusieurs LLM cloud, avec bascule automatique si un provider est saturé :

| Provider | Config |
|---|---|
| Mistral | `MISTRAL_API_KEY` (prioritaire pour rédaction / correction) |
| Groq | `GROQ_API_KEY` |
| Gemini | `GEMINI_API_KEY` |
| DeepSeek | `DEEPSEEK_API_KEY` |
| Together | `TOGETHER_API_KEY` |
| SambaNova | `SAMBANOVA_API_KEY` |
| Kimi | `KIMI_API_KEY` |
| Ollama (local) | Fallback `sanad-legal` |

**Principe :**

- **Cœur plaidoirie :** STT (navigateur / futur serveur) → LLM pour correction / mise en forme → document.
- **Module secondaire :** recherche (corpus + web + docs) trouve les sources ; le LLM rédige la réponse.

---

## 6. Positionnement final

| Concurrent | Ils excellent en… | Sanad répond par… |
|---|---|---|
| Legaliq | Fiscal + BO | Corpus + SaaS cabinet + pièces liées à la plaidoirie |
| Kanoun | OHADA + audit | OHADA + analyse doc ; cœur = plaidoirie |
| Adala | Q&R + génération + langues | Templates + i18n + **parcours dictée → document** |
| Omniscient | Revue contrat + Word | Analyse doc + export PDF (DOCX en roadmap) |
| Gestion cabinet MA | Organisation / Mahakim | Dossiers + rôles déjà ; pas diluer le cœur |
| Dragon / dictée OS | Speech-to-text seul | **Workflow cabinet** autour de la plaidoirie |

### Synthèse

Les concurrents marocains sont forts sur **une brique** (recherche, OHADA, contrats, grand public, ou gestion de cabinet).

Sanad part d’un **cabinet numérique multi-tenant**, place au centre la **rédaction de plaidoirie** (dictée / audio → document), et conserve un agent multi-sources en **module secondaire**, en reprenant volontairement les forces utiles des concurrents **sans en faire le pitch principal**.

---

## 7. Roadmap benchmarking (priorisée)

| Priorité | Action | Lien concurrent |
|---|---|---|
| P0 | Finaliser upload audio → transcription → plaidoirie liée au dossier | Différenciation vs Dragon / Word |
| P0 | Parcours UX « plaidoirie d’abord » (accueil / menu) | Adala (simplicité) |
| P1 | Export DOCX de la plaidoirie / synthèses | Omniscient |
| P1 | Enrichir templates d’actes MA | Adala |
| P2 | Enrichir corpus fiscal / jurisprudence | Legaliq / Adala |
| P2 | Mode revue contrat dédié | Omniscient / Kanoun |
| P3 | Benchmark 50 questions (annexe mémoire) | Kanoun |

---

*Document de benchmarking Sanad v3.2 — Périmètre marocain. Fiches détaillées section 2.1 (Diskod/Dragon, AvocatPro, Avocato, SmartAvocat). Aligné CDC v3.1.*
