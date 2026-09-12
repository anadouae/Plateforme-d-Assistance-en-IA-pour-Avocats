# Rapport PFA LexHub — version Overleaf synchronisée

**Source :** export `me_pfaa.zip` (Overleaf) → `docs/rapport-pfa/`  
**Étudiante :** EL ASSAL Douae  
**Tuteur :** Prof. Mohammed Al Achhab  
**Encadrant entreprise :** Hatim Benhaddou (WEBVOICE)  
**Prod :** https://lexhub.space  
**GitHub :** https://github.com/anadouae/Plateforme-d-Assistance-en-IA-pour-Avocats

## Finalisation (contenu)

- Perspectives = **évolution produit** (latence STT, précision AR, modèles par domaine, versions, indicateurs) — **pas** le CI/CD (déjà en place)
- UML : UC, séquences, classes, activité, déploiement
- Annexe : cartographie diagrammes + matrice de complétude
- CI/CD décrit comme **livré** (GitHub Actions → GHCR + VPS)

## Compiler (Overleaf)

1. Uploader tout le dossier `rapport-pfa/`
2. Main document = `rapport-pfa/main.tex` **ou** racine `\input{rapport-pfa/main}`
3. pdfLaTeX × 2

## PlantUML / Visual Paradigm

Fichiers dans `diagrams/*.puml` (uc, séquences, classes, activité, déploiement).
