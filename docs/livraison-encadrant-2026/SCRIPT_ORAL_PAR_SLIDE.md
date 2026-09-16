# Script oral — Soutenance PFA LexHub
**EL ASSAL Douae** · ENSA Tétouan · WEBVOICE · https://lexhub.space  

Durée indicative : **10–12 min** (+ démo + questions).  
Fichier PPT : `Soutenance_PFA_LexHub.pptx` (18 diapositives).

---

## Slide 1 — Couverture
**Durée : ~20 s**

Bonjour. Je m’appelle **EL ASSAL Douae**, étudiante en génie informatique à l’**ENSA Tétouan**.  
Mon Projet de Fin d’Année a été réalisé chez **WEBVOICE** à Tanger, sous l’encadrement de **M. Hatim Benhaddou**, avec pour tuteur pédagogique le **Prof. Mohammed Al Achhab**.

Le livrable s’appelle **LexHub** : un **système d’information de cabinet** d’avocats au Maroc, avec assistance IA, **déjà en production** sur **lexhub.space**.

---

## Slide 2 — Plan
**Durée : ~15 s**

Je vous propose le plan suivant : le cadrage métier, le positionnement marché, les objectifs, les rôles, l’atelier de plaidoirie, l’architecture MADI, le modèle économique, le déploiement, une démonstration visuelle, puis le bilan et les perspectives.

---

## Slide 3 — Contexte & problématique
**Durée : ~50 s**

Dans beaucoup de cabinets marocains, la plaidoirie reste préparée de façon **artisanale** : notes, dictée, ressaisie Word, juste avant l’audience. C’est lent, source d’erreurs, et peu traçable. Le contexte est **bilingue**, et le **secret professionnel** impose une isolation stricte des données.

**Problématique :** comment concevoir et **mettre en production** un SaaS multi-cabinets où l’avocat mène un atelier en cinq étapes, où l’assistant ne voit que le **validé**, où l’abonnement fonctionne, **sans que l’IA n’invente** le fond juridique ?

---

## Slide 4 — Positionnement marché
**Durée : ~45 s**

Nous avons structuré le benchmarking en **AS-IS → écart → TO-BE**.

- Les logiciels de **gestion** couvrent le dossier, pas la voix vers l’acte.  
- La **dictée desktop** transcrit, mais n’est pas un SaaS multi-tenant.  
- Les **chatbots** rédigent, mais risquent d’inventer des faits et n’offrent pas d’équipe cabinet.

**LexHub** se place sur cet écart : **dossier + plaidoirie + rôles + SaaS**, déployé en production.

---

## Slide 5 — Objectifs du PFA
**Durée : ~40 s**

Cinq objectifs, tous livrés :

1. Atelier en **cinq étapes**, jusqu’à l’export Word.  
2. Espace cabinet : dossiers, pièces, équipe, planning.  
3. Quatre rôles distincts.  
4. La **validation** comme seuil de visibilité pour l’assistant.  
5. Modèle d’abonnement et **exploitation réelle**.

**Règle d’or :** Postgres est la vérité métier ; le LLM propose, il n’est **jamais** maître des faits ; l’avocat reste responsable.

---

## Slide 6 — Acteurs & RBAC
**Durée : ~40 s**

Quatre rôles :

- **Avocat** : dicte, corrige, rédige, valide, exporte.  
- **Assistant** : uniquement les plaidoiries **validées** ou finalisées.  
- **Admin cabinet** : équipe, abonnement, identité visuelle.  
- **Admin plateforme** : supervise les cabinets, **sans lire** les affaires.

Cycle : **brouillon** → invisible ; **validée** → visible équipe ; **finalisée** → export Word.

---

## Slide 7 — Atelier 5 étapes
**Durée : ~50 s**

Le cœur produit suit : **dossier et pièces → dictée → correction de forme → rédaction assistée → export Word**.

- En étape 1, le **domaine** de plaidoirie est **lié au dossier** (ex. commercial → modèle commercial).  
- Ensuite on dicte ou on importe un audio, on corrige la forme, on clarifie éventuellement par QCM, on rédige sans inventer, on peut encore **réviser en chat**, puis on exporte un document **éditable** pour l’audience.

---

## Slide 8 — Dictée & correction
**Durée : ~40 s**

Deux modes de capture : micro navigateur (**Web Speech**), ou fichier audio (**WAV, MP3, OGG, M4A, WebM**) via **Whisper OpenAI**.

La correction nettoie la forme en arabe standard, avec surlignage.  
Si le texte n’a **pas de sens**, on **refuse** de le présenter comme « bien corrigé ». L’IA ne doit jamais inventer faits, articles ou montants.

---

## Slide 9 — Urbanisation MADI
**Durée : ~45 s**

LexHub n’est **pas** « une appli IA ». C’est un SI urbanisé selon **MADI** :

- **M**étier : dossier → pièces → plaidoirie → équipe → abonnement  
- **A**pplications : cases, documents, rédaction, billing, admin ; l’IA est un **service partagé**  
- **D**onnées : Postgres vérité, MinIO fichiers  
- **I**nfra : Docker, VPS, Caddy ; le cloud IA reste **extérieur** au cadastre  

Urbaniser, c’est garder des **frontières claires**.

---

## Slide 10 — Architecture
**Durée : ~35 s**

Architecture classique d’un SaaS : navigateur **Next.js** → **Caddy** HTTPS → **FastAPI** → **PostgreSQL**, **Redis**, **MinIO**.  
Isolation par `cabinet_id`. Les services STT/LLM sont externes : on les utilise, on ne leur confie pas le cadastre.

---

## Slide 11 — Modèle économique
**Durée : ~40 s**

Offre SaaS : Découverte, Solo, Cabinet, Entreprise, avec **essai hybride** (durée + plafond de crédits), **repère IA du jour**, packs pour abonnés actifs, sièges et parrainage.  
Objectif : un produit **facturable**, pas seulement une démo technique.

---

## Slide 12 — Production & CI/CD
**Durée : ~35 s**

Le système tourne sur un VPS, Docker Compose, Caddy TLS.  
Les images sont publiées par **GitHub Actions** vers GHCR.  
Sauvegardes planifiées. Le livrable PFA est un **produit live** : lexhub.space.

**Atout multi-support :** LexHub n’est pas seulement un outil de bureau. C’est le **même SaaS** sur ordinateur (rédaction approfondie) et sur **smartphone** (continuité hors cabinet) — dock fixé, rôles conservés, pas d’app native à installer. Testé sur écrans tactiles courants (~360–430 px).

---

## Slide 13 — Démo Accueil & dossiers
**Durée : ~25 s** *(ou bascule navigateur)*

Voici l’accueil public et la gestion des dossiers.  
*[Si démo live : ouvrir lexhub.space, se connecter, montrer un dossier. Option : basculer en vue mobile (DevTools) pour montrer le dock.]*

---

## Slide 14 — Démo Atelier
**Durée : ~30 s**

L’atelier en cinq étapes : workspace et correction de forme.  
*[Live : ouvrir une plaidoirie, montrer le pipeline.]*

---

## Slide 15 — Démo Export & équipe
**Durée : ~25 s**

Export Word officiel et gestion d’équipe / rôles.  
*[Live : aperçu export ; page équipe.]*

---

## Slide 16 — Bilan
**Durée : ~35 s**

Tous les objectifs initiaux sont **conformes** : atelier cinq étapes, multi-tenant et RBAC, MADI, modèle économique, production sur lexhub.space, **expérience desktop et mobile** (même produit, même URL).

---

## Banque — phrase « mobile » (à coller si question jury)

> LexHub propose une expérience **multi-support** : sur ordinateur pour la rédaction approfondie, et sur **mobile** pour la continuité du travail en mobilité. L’interface s’adapte aux écrans tactiles (navigation dock, mise en page mono-colonne) tout en conservant les rôles et le contrôle d’accès du SaaS cabinet — sans application native séparée.

## Slide 17 — Perspectives
**Durée : ~25 s**

Suite produit : encaissement réel CMI/PayZone, amélioration STT, continuité dossier–audience, interopérabilités **sans casser** les maîtres de donnée.

---

## Slide 18 — Remerciements
**Durée : ~15 s**

Je vous remercie pour votre attention.  
Je reste disponible pour vos **questions**, et pour une **démonstration** sur https://lexhub.space.

---

## Aide-mémoire (si stress)

| Mot-clé | Phrase courte |
|--------|----------------|
| Produit | SI cabinet, pas chatbot |
| Cœur | Dossier + plaidoirie |
| IA | Service ; LLM ≠ vérité |
| Assistant | Voir seulement le validé |
| Prod | lexhub.space |

## Questions fréquentes (réponses courtes)

**Pourquoi pas seulement ChatGPT ?**  
Parce qu’il manque dossiers, rôles, isolation, export officiel et facturation.

**L’IA invente-t-elle le droit ?**  
Non : ancrage sur dictée + pièces ; l’avocat valide.

**Qu’est-ce que MADI ?**  
Cartographie Métier / Applications / Données / Infrastructure du SI.

**C’est déployé ?**  
Oui, https://lexhub.space.
