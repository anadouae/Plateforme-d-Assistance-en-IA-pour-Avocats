# SANAD — Plan de présentation (≈ 10 min)

**Projet :** Avocat AI Assistance Platform  
**Auteure :** Douae El Assal · WebVoice · ENSA Tétouan · 2025-2026  

**Timing suggéré :** ~10 minutes · **12 slides** · 45–50 s / slide en moyenne  

---

## Timing global

| Min | Bloc | Slides |
|:---:|---|:---:|
| 0–2 | Accroche · problème · besoin | 1–3 |
| 2–3 | Idée Sanad | 4 |
| 3–5 | Fonctionnalités | 5–6 |
| 5–7,5 | Benchmarking concurrents | 7–10 |
| 7,5–9 | Pourquoi Sanad | 11 |
| 9–10 | Conclusion | 12 |

---

## Contenu slide par slide

### Slide 1 — Titre (15 s)
**Titre :** SANAD  
**Sous-titre :** Le copilote du cabinet d’avocat marocain  
**Ligne :** WebVoice · ENSA Tétouan · Douae El Assal · 2025-2026  

**À dire :** « Sanad, c’est l’outil qui fait gagner du temps à l’avocat — sans remplacer son jugement. »

---

### Slide 2 — Le problème (realité du cabinet) (50 s)
**Titre :** Une journée type — où part le temps ?  

**Visuel recommandé :** 3 cases (pas une liste plate)

| Avant audience | Pendant le dossier | Après |
|---|---|---|
| Chercher l’article / le dahir dans le BO ou Google | Relire 20–50 pages de PDF scannés | Retrouver « qui a dit quoi » dans le dossier |
| Vérifier si la loi a changé | Extraire parties, dates, clauses à risque | Classer sans vraie traçabilité |

**Chiffre d’accroche (1 ligne en bas) :**  
~13 000–16 000 avocats au Maroc · digitalisation encore faible · Excel / papier / WhatsApp fréquents

**À dire :**  
« Le vrai problème n’est pas “il manque une IA”. C’est que l’avocat passe des heures à *chercher*, *résumer* et *retrouver* — des tâches à faible valeur, mais critiques. Une erreur de citation ou une loi obsolète peut coûter cher. »

---

### Slide 3 — Le besoin (ce que le marché n’offre pas) (55 s)
**Titre :** Ce dont le cabinet a vraiment besoin  

**Important (à bien expliquer au jury) :**  
Sanad **utilise aussi des LLM** (Groq, Gemini, Kimi… — même famille que ChatGPT).  
Ce n’est **pas** « LLM = mauvais ». Ce qui manque chez ChatGPT *ouvert dans le navigateur*, c’est le **cadre métier**.

**Pas ça (= ChatGPT seul, sans Sanad) :**
- Répond « de mémoire » → risque d’inventer un article / une loi
- **Pas** branché sur un corpus juridique marocain indexé
- **Pas** accès aux PDF / dossiers du cabinet
- **Pas** multi-tenant, rôles, audit, chiffrement

**Mais ça (= Sanad) :**  
> Même type de LLM pour **rédiger**, mais **après** recherche dans corpus MA + web + documents du dossier → réponses **avec sources** + espace cabinet.

**Écart marché :** LegalTech locales = souvent **1 brique** (chat *ou* contrats). Il manque le **parcours complet** cabinet + IA sourcée.

**À dire :**  
« Oui, on utilise des LLM comme ChatGPT. La différence : ChatGPT répond tout seul ; Sanad fait d’abord chercher dans le droit marocain et dans le dossier, puis le LLM rédige à partir de ces sources. »

---

### Slide 4 — L’idée Sanad (45 s)
**Titre :** Sanad = la réponse à ce besoin  

**Formule (grosse typo) :**  
**Cabinet numérique + Copilote IA multi-sources**

**3 piliers :**
1. **Gérer** — dossiers, docs, équipe, isolation par cabinet  
2. **Chercher** — corpus marocain · web · documents uploadés  
3. **Rédiger** — LLM via API keys · citations · score · disclaimer  

**Principe :** chercher d’abord → rédiger ensuite · pas d’invention de références

**À dire :** « Sanad relie le besoin métier (cabinet) et le besoin IA (sources marocaines). Ce n’est pas l’un ou l’autre — c’est les deux. »

---

### Slide 5 — Fonctionnalités (1) — Cabinet (45 s)
**Titre :** Ce que Sanad fait — côté cabinet  

**Puces :**
- SaaS **multi-cabinets** (isolation stricte)
- Dossiers (CRUD) + upload PDF/DOCX/images
- OCR FR/AR + alerte qualité
- Rôles (avocat, assistant, admin) + audit
- Chiffrement des fichiers

**À dire :** « Chaque cabinet a son espace isolé. L’équipe gère dossiers et documents en sécurité. »

---

### Slide 6 — Fonctionnalités (2) — IA (50 s)
**Titre :** Ce que Sanad fait — côté IA  

**Puces :**
- Routage auto : document / dossier / corpus RAG / web
- Citations + score de confiance + disclaimer
- Chat streaming + historique multi-tours
- LLM via **API keys** (Groq, Gemini, DeepSeek, Together, SambaNova, Kimi) + failover
- Secours local **Ollama**
- Synthèse document + templates contrats

**À dire :** « L’IA route vers la bonne source. Plusieurs moteurs cloud via clés API, avec bascule auto si un service est saturé. »

---

### Slide 7 — Benchmarking : vue d’ensemble (40 s)
**Titre :** LegalTech marocaine — chacun sa spécialité  

**Tableau mini :**

| Concurrent | Ils excellent en… |
|---|---|
| **Legaliq** | Législation / fiscalité + docs |
| **Kanoun** | OHADA + audit contrats |
| **Adala** | Q&R + génération docs + FR/AR |
| **Omniscient** | Revue de contrats rapide |

**Lien avec le besoin :**  
→ Preuve que le marché existe… mais **fragmenté**.

**À dire :** « Quatre acteurs, quatre forces. Aucun ne couvre le besoin complet vu à la slide 3. »

---

### Slide 8 — Legaliq & Kanoun (50 s)
**Titre :** Legaliq & Kanoun  

**Deux colonnes :**

| | **Legaliq** | **Kanoun** |
|---|---|---|
| Force | BO + fiscal + analyse docs | OHADA + audit contrats |
| Limite | Pas de SaaS dossiers multi-tenant | Pas de workflow cabinet complet |
| **Sanad** | Corpus BO + docs + **cabinet** | OHADA déjà + **dossiers + équipe** |

**À dire :** « On reprend leurs forces et on les place dans un vrai SaaS cabinet. »

---

### Slide 9 — Adala & Omniscient (50 s)
**Titre :** Adala & Omniscient  

| | **Adala** | **Omniscient** |
|---|---|---|
| Force | Q&R, jurisprudence, génération, langues | Revue contrat + export |
| Limite | Grand public, pas multi-tenant cabinet | Contrats seulement |
| **Sanad** | Templates + i18n + **dossiers** | Analyse doc + chat dossier + **plateforme** |

**À dire :** « Adala démocratise le Q&R ; Omniscient excelle sur le contrat. Sanad intègre les deux dans le flux cabinet. »

---

### Slide 10 — Eux vs Sanad (45 s)
**Titre :** Qui répond au besoin complet ?  

| Besoin cabinet | Concurrent typique | Sanad |
|---|:---:|:---:|
| Multi-cabinets + dossiers | — | ✅ |
| RAG droit marocain | ✅ | ✅ |
| Recherche web | rare | ✅ |
| Docs du dossier | partiel | ✅ |
| Multi-LLM API + failover | — | ✅ |
| Fallback local | — | ✅ |

**À dire :** « Sanad est la plateforme qui **ferme le trou** du besoin : pas une brique de plus — le parcours entier. »

---

### Slide 11 — Pourquoi Sanad (55 s)
**Titre :** Pourquoi Sanad — et pourquoi maintenant  

**Message :**  
> Au Maroc, **première combinaison** : SaaS multi-cabinets + dossiers + IA multi-sources (corpus · web · docs) + multi-LLM + option locale.

**3 raisons (courtes) :**
1. Répond au **besoin réel** (temps + sources + cabinet) — pas à la mode « chatbot »
2. Droit **marocain** natif + web pour l’actualité
3. Résilience : plusieurs **API keys** + Ollama

**À dire :** « On ne prétend pas battre les géants US. On prétend remplir un vide marocain : le package complet du cabinet. »

---

### Slide 12 — Conclusion (40 s)
**Titre :** En une phrase  

> **Sanad = le cabinet numérique + le copilote IA que l’avocat utilise tous les jours.**

- Absorbe les forces Legaliq / Kanoun / Adala / Omniscient  
- Roadmap : revue contrat, fiscalité, export Word…  

**Merci — Questions ?**

---

## Script oral condensé (ouverture améliorée)

1. **Accroche** — « Où part le temps de l’avocat ? Chercher, résumer, retrouver. »  
2. **Besoin** — « Pas un chatbot : un cabinet + une IA sourcée marocaine. »  
3. **Écart** — « Les LegalTech locales sont excellentes… mais fragmentées. »  
4. **Sanad** — « On réunit le parcours complet. »  
5. **Benchmark** — « Chacun sa force → Sanad les combine. »  
6. **Close** — « Outil du quotidien, pas un gadget. »

---

## Conseils présentation

- Slide problème : **histoire / journée type**, pas « liste de bugs ».  
- Slide besoin : contraste **Pas ça / Mais ça**.  
- Dire « **combinaison rare / première à réunir** » (Maroc), pas « seul au monde ».  
- Ne jamais afficher de clés API.  

---

*Fichiers liés : `docs/benchmarking-sanad.md` · `docs/cahier-des-charges-sanad.md`*
