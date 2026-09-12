# Rapport PFA LexHub — Compilation LaTeX

**Étudiante :** Douae El Assal  
**École :** ENSA Tétouan — Université Abdelmalek Essaâdi  
**Entreprise :** WebVoice (Tanger)  
**Tuteur pédagogique :** Mohammed Al Achhab  
**Encadrant entreprise :** Hatim Benhaddou  
**Produit :** https://lexhub.space

## Contenu

| Fichier | Description |
|---------|-------------|
| `main.tex` | Page de garde PFA + inclusion des chapitres |
| `chapitres/` | Préliminaires, intro, état de l'art, analyse, conception, réalisation, tests, conclusion, annexes |
| `diagrams/*.puml` | Sources PlantUML (cas d'utilisation, séquences, classes) — exportables Visual Paradigm / PlantUML |
| `assets/logo-*.png` | Logos UAE, ENSA, WebVoice (officiel), LexHub |

## Points clés (version actuelle)

- Inscription cabinet : OTP puis **accès immédiat** (cabinet actif) ; l'admin plateforme peut **suspendre** / réactiver.
- Plaidoirie : 5 étapes ; correction de forme (faits conservés) ; marques orange STT ; validation / **assignation** / pin.
- Pas de liste d'abréviations ni de « Comment lire » ; pas d'annexe journal de bord.
- Benchmarking : grille **OK / Non OK** alignée premier suivi + PPTX.

## Overleaf --- si « No PDF / Emergency stop »

1. Menu (engrenage) → **Main document** = `rapport-pfa/main.tex`  
   **ou** racine `main.tex` contenant uniquement `\input{rapport-pfa/main}`.
2. Re-uploadez tout le dossier `rapport-pfa/` (dont `chapitres/`, `assets/`, `maquettes/`).
3. Compiler **pdfLaTeX**, deux fois.
4. Si erreur « file missing » : les chapitres doivent être dans `rapport-pfa/chapitres/`.

Ne pas compiler un vieux `main.tex` racine du type `\title{pfa}`.


### Overleaf

1. Racine : `docs/main.tex` contient `\input{rapport-pfa/main}` (déjà compatible).
2. Compiler **pdfLaTeX**, deux passes pour la TOC.
3. Logos dans `rapport-pfa/assets/` ; maquettes dans `docs/maquettes/` (chemins `\graphicspath` déjà prévus).

### Windows (MiKTeX / TeX Live)

```powershell
cd docs\rapport-pfa
pdflatex main.tex
pdflatex main.tex
```

### Diagrammes PlantUML (optionnel)

```bash
plantuml diagrams/*.puml
```

Les figures UML du PDF sont aussi en TikZ (acteurs stick-figure) dans les chapitres analyse / conception.

## Structure du rapport

1. Page de garde (PFA, logos, champs essentiels)
2. Dédicace / Remerciements / Résumé
3. Table des matières, figures, tableaux
4. Ch.1 Introduction (+ WebVoice)
5. Ch.2 État de l'art / benchmarking
6. Ch.3 Analyse des besoins
7. Ch.4 Conception
8. Ch.5 Réalisation (guide)
9. Ch.6 Tests et résultats
10. Ch.7 Conclusion
11. Annexes (dépôt + captures) + bibliographie
