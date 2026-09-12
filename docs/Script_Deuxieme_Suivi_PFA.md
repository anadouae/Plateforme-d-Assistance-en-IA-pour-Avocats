# Script oral — 2ᵉ suivi PFA Sanad (version pro, non redondante)

**Fichier :** `Sanad_Deuxieme_Suivi_PFA.pptx` (Bureau + `docs/`)  
**Durée :** 14–16 min + questions  
**Règle d’or :** ne jamais répéter une idée déjà dite — dire « comme sur la matrice » et avancer.

---

## Slide 1 — Titre
Bonjour. Douae El Assal, PFA WebVoice / ENSA Tétouan.  
Ce **deuxième suivi** montre comment nous avons **répondu aux remarques** du premier, avec des **preuves** dans le produit.

## Slide 2 — Objectif de la séance
Aujourd’hui on valide six points : matrice des remarques, livraisons, démo plaidoirie, architecture résiliente, benchmark OK/Non OK, et la suite.  
On **ne reprend pas** toute la problématique marché — déjà validée.

## Slide 3 — Ancrage (une fois)
Rappel unique du cœur : **voix arabe → plaidoirie structurée → Word/PDF → dossier**, sans dépendance cloud unique.  
Le reste du cabinet **soutient** ce flux.

## Slide 4 — Matrice (slide la plus importante)
Voici, ligne par ligne, chaque remarque et sa réponse.  
Les slides suivantes **approfondissent** STT et LLM une seule fois ; le reste est illustré par des captures.

## Slide 5 — STT
Quatre niveaux : Whisper local, upload audio, Chrome, saisie manuelle.  
Segments de 55 s pour les longues dictées. Arabe forcé.  
Phrase : *accélérateur, jamais blocage unique.*

## Slide 6 — Whisper ≠ Ollama (très important)
Whisper = **oreilles** : audio → texte.  
Ollama = **plume** : texte → texte corrigé / structuré.  
Chaîne : Audio → Whisper → texte → Ollama → document.  
Si le LLM tombe : édition + export restent.

## Slide 7 — UX plaidoirie
Deux écrans pour éviter la saturation : choix modèle, puis dictée/document.  
Capture à droite.

## Slide 8 — Domaines
Réponse directe : domaine à la création + filtre/recherche. Capture dossiers.

## Slide 9 — Agenda
Réponse directe : `case_id` sur événements/tâches/notes + filtre. Capture planning.

## Slide 10 — Synthèse
Pièce → OCR → synthèse structurée. Autour du cœur, pas à sa place.

## Slide 11 — Architecture
Schéma unique : Next, FastAPI, Postgres, Redis, MinIO, Celery, Whisper, Ollama.

## Slide 12 — APIs
Cartographie rapide pour les questions techniques. Swagger : `/docs`.

## Slide 13 — Docker
Trois images publiées (backend, frontend, celery) + images officielles.  
Publier = même binaire partout, démo/VPS, maturité DevOps. Hub : `anadouae1/sanad-*`.

## Slide 14 — Déploiement
Schéma Compose — infra réelle.

## Slide 15 — Benchmark
Format demandé : grille OK / Non OK. Sanad gagne sur le **flux intégré**, pas sur une seule brique.

## Slide 16 — Bilan
Checklist des livraisons depuis le 1ᵉʳ suivi — sans reformuler les slides 5–10.

## Slide 17 — Démo & suite
Je démarrerai la démo selon ce scénario. Suite : qualité STT/OCR, SMTP prod, VPS.

## Slide 18 — Merci
Chaque remarque a une réponse d’**architecture ou de produit**, pas seulement un écran. Questions ?

---

### Pendant la démo (ne pas relire les slides)
1. Login `demo@sanad.ma` / `Sanad2026!`  
2. Affaire + domaine + filtre  
3. Plaidoirie audio arabe → document  
4. Synthèse pièce  
5. Agenda lié  
