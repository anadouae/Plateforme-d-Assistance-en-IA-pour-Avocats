# Sanad — Benchmarking 2  
## Focus 100 % : rédaction de plaidoirie

| | |
|---|---|
| **Projet** | Sanad |
| **Auteure** | Douae El Assal · WebVoice |
| **Périmètre** | Marché marocain |
| **Version** | Benchmark 2 · v1.0 — Juillet 2026 |
| **Alignement** | Demande encadrant entreprise : **plaidoirie uniquement** |

> Ce document est la **version ciblée**.  
> La version large (LegalTech + gestion cabinet + IA) reste dans `benchmarking-sanad.md` (Benchmark 1).

---

## 0. Clarification : Mahakim

| Terme | Signification |
|---|---|
| **Mahakim** | Portail judiciaire marocain ([mahakim.ma](https://mahakim.ma)) : consultation des audiences, salles, état des affaires devant les tribunaux. |
| **Dans Avocato / AvocatPro** | Import / synchronisation automatique des audiences depuis ce portail. |
| **Pour Sanad (cœur encadrant)** | **Hors sujet.** Utile pour un logiciel de gestion de cabinet, pas pour la rédaction de plaidoirie. |

---

## 1. Objectif (Benchmark 2)

Comparer **uniquement** les solutions qui touchent au problème posé par l’encadrant :

> L’avocat dicte / parle → le système produit le texte de la **plaidoirie** → document prêt (mise en forme), éventuellement avec l’équipe du cabinet.

On **n’évalue pas** ici : chat juridique, fiscalité BO, OHADA, Mahakim, facturation, CRM.

---

## 2. Problème métier de référence

| Aujourd’hui | Demain (Sanad) |
|---|---|
| Avocat écrit sur papier | Avocat **dicte** ou **dépose un audio** |
| Assistant retape sous Word | Système **transcrit** et **corrige** |
| Document peu standardisé | Document **mis en forme** (en-tête) |
| Peu de lien dossier / droits | Lié au **dossier** + **rôles** cabinet |

---

## 3. Concurrentes pertinentes (plaidoirie / dictée) — Maroc

| Solution | Lien | Ce qu’ils font (lié à la rédaction) | Limite vs la demande encadrant |
|---|---|---|---|
| **Dragon Legal v16** (via Diskod MA) | [diskod.ma](https://diskod.ma/produit/nuance-dragon-legal-licence-dragon-legal/) | Dictée juridique précise vers Word / Docs ; vocabulaire légal ; commandes vocales | Desktop + licence ; **pas** SaaS cabinet ; **pas** workflow dossier / assistant / en-tête Sanad |
| **Dictée Windows / Google Docs** | Outils système / navigateur | Parole → texte brut | Aucun métier cabinet ; pas de plaidoirie structurée ; pas de rôles |
| **Adala** (génération docs) | [adala.ai](https://adala.ai/) | Génère des modèles (contrats, requêtes…) | Remplit des **templates** ; ce n’est **pas** « l’avocat dicte sa plaidoirie » |
| **SmartAvocat / Avocato / AvocatPro** | [smartavocat.ma](https://smartavocat.ma/) · [avocato.ma](https://avocato.ma/) · [avocatpro.ma](https://avocatpro.ma/) | Modèles d’actes, docs, gestion | Organisation cabinet / Mahakim — **pas** le flux dictée → plaidoirie |
| **Sanad** | Projet WebVoice | Dictée / audio → correction → document plaidoirie + dossier + rôles | Cœur produit à finaliser (audio serveur, lien dossier) |

**Exclus de ce Benchmark 2 :** Legaliq, Kanoun, Omniscient (hors cœur plaidoirie — voir Benchmark 1).

---

## 4. Tableau comparatif — critères plaidoirie uniquement

| Critère | Dragon (Diskod) | Dictée OS / Docs | Adala (templates) | Gestion cabinet MA | **Sanad** |
|---|:---:|:---:|:---:|:---:|:---:|
| Dictée vocale juridique | Oui | Partiel | — | — | Oui |
| Upload audio → transcription | — | — | — | — | Cible / à renforcer |
| Correction / ponctuation du texte | Partiel | — | — | — | Oui |
| Document plaidoirie mis en forme | — (Word libre) | — | Partiel (autres actes) | Partiel (modèles) | Oui |
| Lien au dossier du cabinet | — | — | Partiel | Oui | Oui (cible) |
| Rôles avocat / assistant | — | — | — | Oui | Oui |
| SaaS multi-cabinets | — | — | Non cabinet | Oui | Oui |
| Remplace le circuit papier → assistant | Partiel (frappe seule) | Partiel | Non | Non | **Oui (objectif)** |

---

## 5. Positionnement Sanad (100 % encadrant)

| Concurrent | Ils résolvent… | Ils ne résolvent pas… | Sanad |
|---|---|---|---|
| Dragon | La frappe (voix → Word) | Le cabinet, le dossier, l’assistant, le document métier | Voix/audio **dans** le SaaS + document + rôles |
| Dictée Windows | Un textarea système | Tout le métier | Workflow plaidoirie complet |
| Adala / modèles | Un acte type prérempli | La dictée personnelle de l’avocat | L’avocat **dit** sa plaidoirie ; le système formalise |
| Logiciels cabinet | Mahakim, factures, agenda | La rédaction orale de la plaidoirie | Cœur = rédaction ; Mahakim hors périmètre PFE |

---

## 6. Synthèse

1. **Mahakim** = tribunaux en ligne ; intéressant pour la **gestion**, pas pour la **plaidoirie**.  
2. Sur la demande de l’encadrant, le vrai concurrent direct est surtout **Dragon / dictée OS** (voix → texte), pas Legaliq ni Avocato.  
3. **Sanad se distingue** en transformant la dictée en **produit cabinet** : correction, document officiel, dossier, droits.  
4. Le **Benchmark 1** (`benchmarking-sanad.md`) reste utile pour le mémoire / panorama marché.  
5. Le **Benchmark 2** (ce fichier) est la référence pour le **cadrage encadrant** et la démo PFE.

---

## 7. Deux versions — usage

| Fichier | Usage |
|---|---|
| `docs/benchmarking-sanad.md` | **Benchmark 1** — panorama LegalTech MA (large) |
| `docs/benchmarking-sanad-plaidoirie.md` | **Benchmark 2** — 100 % plaidoirie (encadrant) |

---

*Benchmark 2 v1.0 — Aligné strictement sur la demande encadrant : rédaction de plaidoirie.*
