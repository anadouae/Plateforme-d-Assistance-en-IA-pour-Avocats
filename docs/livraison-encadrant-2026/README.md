# Livraison encadrant / PFA — LexHub (sept. 2026)

Documents alignés sur **https://lexhub.space** (API `/api/billing/plans`).

Copie propre pour remise : `C:\Users\daurinia\Desktop\S9\PFA\`

| Fichier | Contenu |
|---------|---------|
| `01_Rapport_PFA_LexHub.docx` | Rapport PFA (Word) — essai hybride, packs, sièges, parrainage |
| `01_Proposition_plan_rentabilisation_LexHub_v5.docx` | Plan de rentabilisation |
| `02_Guide_utilisation_et_tests_LexHub_v7.docx` | Guide d’utilisation & tests (prod sept. 2026) |
| `03_Note_base_de_donnees_LexHub.docx` | Note BDD pour encadrant entreprise |
| `03_Liste_captures_UI_rapport_PFA.docx` | Captures rapport PFA |
| `04_Soutenance_PFA_LexHub.pptx` | Soutenance PFA (16 slides) |

Sources LaTeX du rapport : `docs/rapport-pfa/` (Overleaf, pdfLaTeX × 2).

```bash
python docs/livraison-encadrant-2026/generate_rapport_pfa_docx.py
python docs/livraison-encadrant-2026/generate_rentabilisation_complet.py
python docs/livraison-encadrant-2026/generate_guide_utilisation_pro.py
python docs/livraison-encadrant-2026/generate_soutenance_pfa.py
python docs/livraison-encadrant-2026/pack_dossier_pfa.py
```

**Prod :** essai hybride (durée + plafond) · packs 500/110, 1000/200, 2500/450 MAD (abo **actif payant** seulement) · sièges Cabinet 99 MAD · quotas plaidoiries **3 / 35 / 120 / 350**.
