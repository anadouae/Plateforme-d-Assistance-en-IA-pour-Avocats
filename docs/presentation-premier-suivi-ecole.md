# SANAD — Contenu PowerPoint · Premier suivi (encadrant école)

**À utiliser pour :** première réunion de suivi PFE avec l’encadrant ENSA  
**Durée conseillée :** 8–12 minutes + questions  
**Auteure :** Douae El Assal · Stage WebVoice · ENSA Tétouan · 2025-2026  

**Conseils oraux :**
- Rester sur le **sujet officiel** (titre ci-dessous).
- Cœur produit = **plaidoirie** (voix/audio → texte → document) + dossiers + synthèse.
- Ne pas présenter Sanad comme un « ChatGPT juridique » : l’IA aide le flux de rédaction, **l’avocat reste responsable**.

---

## Slide 1 — Page de titre

**Titre :** SANAD  
**Sous-titre :** Plateforme d’Assistance en Intelligence Artificielle pour Avocats  

**Lignes :**
- Projet de Fin d’Études — ENSA Tétouan  
- Entreprise d’accueil : WebVoice  
- Stagiaire : Douae El Assal  
- Encadrant entreprise : [Nom]  
- Encadrant école : [Nom]  
- Année universitaire 2025-2026  

**À dire :**  
« Bonjour. Je présente aujourd’hui mon premier suivi sur le projet Sanad, réalisé chez WebVoice. »

---

## Slide 2 — Objectif de cette séance

**Titre :** Objectif du premier suivi  

**Puces :**
- Présenter le contexte et le problème métier  
- Clarifier le périmètre du PFE  
- Montrer l’approche technique retenue  
- Faire le point sur l’avancement  
- Valider la feuille de route jusqu’au prochain suivi  

**À dire :**  
« L’objectif n’est pas encore la démo finale, mais de cadrer le sujet et de partager où j’en suis. »

---

## Slide 3 — Contexte entreprise

**Titre :** Contexte — WebVoice  

**Puces :**
- Éditeur / structure d’accueil du stage  
- Orientation LegalTech pour cabinets d’avocats marocains  
- Besoin : digitaliser le travail quotidien de l’avocat (rédaction, dossiers, collaboration)  
- Projet Sanad : produit SaaS multi-cabinets  

**À dire :**  
« Chez WebVoice, le besoin est de proposer un outil adapté au cabinet marocain, pas un logiciel générique. »

---

## Slide 4 — Problématique

**Titre :** Problématique  

**Idée centrale (grosse phrase) :**  
La rédaction de plaidoirie reste souvent manuelle (papier / ressaisie), chronophage et peu reliée au dossier numérique.

**Puces :**
- Dictée ou notes manuscrites → l’assistant retape  
- Pièces et dossiers dispersés (mail, WhatsApp, fichiers locaux)  
- Peu de traçabilité et de collaboration structurée  
- Outils existants = gestion de cabinet **ou** dictée générique, rarement le **flux plaidoirie** lié au dossier  

**Chiffre (optionnel) :** ~13 000–16 000 avocats au Maroc — digitalisation encore inégale  

**À dire :**  
« Le problème n’est pas “manquer d’IA”, c’est perdre du temps entre la parole de l’avocat et un document de plaidoirie exploitable, classé dans le dossier. »

---

## Slide 5 — Sujet officiel & solution

**Titre :** Sujet & solution proposée  

**Sujet (titre officiel — à garder tel quel) :**  
**Plateforme d’Assistance en Intelligence Artificielle pour Avocats**

**Solution — Sanad :**
plateforme web SaaS pour cabinets marocains qui permet de :

1. **Rédiger une plaidoirie** : dictée / audio → texte corrigé → document imprimable  
2. **Centraliser** dossiers et documents par cabinet  
3. **Synthétiser** les pièces / le dossier à la demande  
4. **Collaborer** (avocat, assistant, admin) avec droits  

**Principe :**  
L’IA accélère le passage voix → document. Elle **ne remplace pas** le jugement ni la signature de l’avocat.

**À dire :**  
« Sanad, c’est deux gestes : dicter la plaidoirie, synthétiser les pièces — le reste (dossier, équipe, document) suit. »

---

## Slide 6 — Objectifs du PFE

**Titre :** Objectifs du projet  

**Objectifs généraux :**
- Concevoir et développer une plateforme SaaS multi-tenant pour cabinets  
- Implémenter le cœur **plaidoirie** (dictée / audio → document)  
- Assurer sécurité, isolation des cabinets, rôles  

**Objectifs spécifiques :**
- Module plaidoirie (micro + upload audio + correction + export)  
- Gestion dossiers / documents  
- Synthèse de pièces  
- Authentification, rôles, espace cabinet  
- Documentation (cahier des charges, architecture) + démonstration  

---

## Slide 7 — Périmètre (inclus / hors scope)

**Titre :** Périmètre  

**Inclus (cœur PFE) :**
- Plaidoirie (voix / audio → texte → PDF / impression)  
- Dossiers & documents  
- Synthèse des pièces  
- Multi-cabinets, rôles, sécurité de base  
- Interface web (FR / AR / EN)  

**Hors scope (pour cette année / plus tard) :**
- Intégration Mahakim / tribunaux  
- Facturation SaaS complète  
- Remplacement de l’avocat par une IA « qui invente le droit »  
- Chat juridique libre comme produit principal  

**À dire :**  
« On reste focalisés sur le flux plaidoirie + espace cabinet, comme validé avec l’encadrant entreprise. »

---

## Slide 8 — Acteurs & cas d’usage

**Titre :** Acteurs  

| Acteur | Rôle principal |
|--------|----------------|
| Avocat | Dicte / dépose audio, valide, imprime, gère dossiers |
| Assistant | Upload, classement, aide à la révision |
| Admin cabinet | Équipe, paramètres, invitations |
| Admin WebVoice | Activation / suspension cabinets (sans lire le contenu confidentiel) |

**Cas d’usage phare :**  
Avocat dicte sa plaidoirie en arabe → Sanad transcrit et corrige → document à en-tête → archivé dans le dossier.

---

## Slide 9 — Architecture technique (vue simple)

**Titre :** Architecture technique  

**Schéma à dessiner (3 blocs) :**

```
[ Navigateur — Next.js ]
         |
         v
[ API — FastAPI ]
    |        |         |
    v        v         v
 Postgres   Redis    MinIO
              |
         (IA / Ollama + APIs LLM)
```

**Stack (puces) :**
- Frontend : Next.js, TypeScript, Tailwind  
- Backend : Python, FastAPI  
- Données : PostgreSQL, Redis, MinIO  
- Conteneurs : Docker / Docker Compose  
- IA : transcription / correction ; Ollama + APIs selon config  
- Versioning : Git / GitHub  

**À dire :**  
« Architecture classique SaaS : front, API, base, fichiers, services IA — le tout conteneurisé pour déployer ensuite sur un VPS Linux. »

---

## Slide 10 — Méthodologie & planning

**Titre :** Méthodologie & planning  

**Méthode :**
- Cadrage (besoin entreprise + cahier des charges)  
- Développement itératif (MVP → enrichissement)  
- Tests continus + retours encadrant entreprise  
- Documentation au fil de l’eau  

**Phases (exemple — adapte tes dates réelles) :**

| Phase | Contenu | Statut |
|-------|---------|--------|
| 1. Cadrage | Problème, CDC, périmètre plaidoirie | Fait / en cours |
| 2. Socle | Auth, cabinets, dossiers, UI | En cours / avancé |
| 3. Cœur | Module plaidoirie (dictée / audio / document) | En cours |
| 4. Enrichissement | Synthèse, rôles, sécurisation | À poursuivre |
| 5. Déploiement | VPS Linux, démo, rapport | Prochaine étape |

---

## Slide 11 — Avancement à ce jour

**Titre :** Avancement actuel  

**Réalisé / en place :**
- Application web Sanad (login, inscription cabinet, dashboard)  
- Modules dossiers / documents / plaidoirie (base)  
- Isolation multi-cabinets + rôles  
- Stack Docker opérationnelle en local  
- Cahier des charges orienté plaidoirie  
- Interface publique (landing, i18n FR/AR/EN)  

**En cours :**
- Consolidation du flux plaidoirie (audio serveur / qualité)  
- Amélioration UX / textes produit  
- Préparation déploiement VPS (avec l’entreprise)  

**À dire :**  
« Le socle tourne en local. La priorité reste de fiabiliser le parcours plaidoirie pour la démo. »

*(Adapte cette slide à ton réel % d’avancement le jour J.)*

---

## Slide 12 — Prochaines étapes

**Titre :** Prochaines étapes  

**Avant le prochain suivi :**
1. Finaliser / démontrer le parcours plaidoirie bout en bout  
2. Renforcer synthèse des pièces + lien au dossier  
3. Déployer une version sur VPS Linux (entreprise)  
4. Préparer scénario de démo (5–7 min)  
5. Avancer le rapport / documentation  

**Risques / besoins :**
- Qualité transcription arabe (micro navigateur vs Whisper serveur)  
- Accès VPS + clés API si besoin  
- Validation continue avec l’encadrant entreprise  

---

## Slide 13 — Conclusion

**Titre :** Conclusion  

**Messages clés :**
- Sujet clair : **assistance IA pour avocats**, cœur = **plaidoirie**  
- Sanad = outil de cabinet, pas un substitut à l’avocat  
- Architecture SaaS moderne, déployable sur Linux  
- Travail itératif avec l’entreprise (« on ajuste au fur et à mesure »)  

**Phrase de clôture :**  
« Je suis prête à répondre à vos questions et à intégrer vos remarques pour le prochain suivi. »

---

## Slide 14 (optionnelle) — Questions / échanges

**Titre :** Questions & validation  

**Points à valider avec l’encadrant école :**
- Le périmètre plaidoirie + dossiers + synthèse vous convient-il ?  
- Niveau de détail attendu pour le prochain suivi (démo ? architecture ?)  
- Format du rapport / livrables académiques  

---

## Annexe — Ce que tu peux montrer en 2 minutes (si demandé)

1. Landing Sanad (« Deux gestes… »)  
2. Connexion `demo@sanad.ma`  
3. Écran Plaidoirie (dictée / texte)  
4. Un dossier + document  

**Compte démo :** `demo@sanad.ma` / `Sanad2026!`

---

## Checklist avant la séance

- [ ] Remplir les noms des deux encadrants sur la slide 1  
- [ ] Ajuster la slide « Avancement » à la réalité du jour  
- [ ] Imprimer ou PDF le CDC (focus plaidoirie) en backup  
- [ ] Tester la démo locale **la veille**  
- [ ] Préparer 1 question à poser à l’encadrant école  

---

*Document préparé pour le premier suivi école — Sanad / WebVoice / ENSA Tétouan*
