# Rapport PFA LexHub — version Overleaf synchronisée

**Source :** export `me_pfaa.zip` (Overleaf) → `docs/rapport-pfa/`  
**Étudiante :** EL ASSAL Douae  
**Tuteur :** Prof. Mohammed Al Achhab  
**Encadrant entreprise :** Hatim Benhaddou (WEBVOICE)  
**Prod :** https://lexhub.space  
**GitHub :** https://github.com/anadouae/Plateforme-d-Assistance-en-IA-pour-Avocats

## Finalisation (contenu)

- Facturation à jour : **essai hybride** (durée + plafond), **repère IA du jour** (choix continuer / demain, tous plans), **popups** forfait essai / mois épuisé, **packs prépayés** (abo actif seulement), sièges Cabinet, PAYG optionnel, parrainage
- Perspectives = **évolution produit** (latence STT, précision AR, modèles par domaine, versions, indicateurs, CMI/PayZone) — **pas** le CI/CD (déjà en place)
- UML : UC, séquences, classes, activité, déploiement
- Annexe : cartographie diagrammes + matrice de complétude
- CI/CD décrit comme **livré** (GitHub Actions → GHCR + VPS)
- Version Word : `docs/livraison-encadrant-2026/01_Rapport_PFA_LexHub.docx` (aussi dans `Desktop/S9/PFA/`)

## Sommaire (version actuelle)

Dédicace · Remerciements · Résumé · Abstract · Abréviations · Listes figures/tableaux

1. Introduction générale
2. Étude de l'existant et positionnement
3. Analyse et spécification des besoins
4. Conception du système
5. **Modèle économique et stratégie de rentabilisation**
6. Réalisation et guide d'utilisation
7. Tests, déploiement et résultats
8. Conclusion générale et perspectives

Bibliographie / Webographie · Annexe A (captures)

## Compiler (Overleaf)

1. Uploader tout le dossier `rapport-pfa/` **et** le `main.tex` racine (`\input{rapport-pfa/main}`)
2. Document principal = `main.tex` à la racine
3. pdfLaTeX × 2

## PlantUML / Visual Paradigm

Fichiers dans `diagrams/*.puml` (uc, séquences, classes, activité, déploiement).
