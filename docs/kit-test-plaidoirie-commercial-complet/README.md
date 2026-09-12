# Kit test — Dossier commercial complet (arabe)

Dossier **fictif** prêt pour LexHub : fiche + 5 pièces + dictée courte + dictée longue.

## Contenu

| Fichier | Rôle |
|---------|------|
| `00_FICHE_DOSSIER_LexHub.md` | **Tous les champs** à remplir dans LexHub |
| `01_عقد_توريد_ليلى_إحسان.docx` | Contrat de fourniture |
| `02_فاتورة_وفاتورة_مذكرة.docx` | 3 factures / dette 247.450 MAD |
| `03_إنذار_رسمي.docx` | Mise en demeure |
| `04_مقال_افتتاحي.docx` | Requête + RG 2025/1547 |
| `05_محضر_معاينة.docx` | PV d’huissier |
| `06_dictée_courte.txt` | ~20 s — teste si l’IA développe depuis les pièces |
| `07_dictée_longue.txt` | ~90 s — dictée barreau complète |
| `08_ATTENDU_qualité_IA.md` | Critères de réussite |

## Parcours rapide (prod)

1. Connexion cabinet démo / admin
2. **Dossiers** → Nouveau → recopier `00_FICHE_DOSSIER_LexHub.md`
3. Uploader les 5 DOCX → attendre indexation
4. **Plaidoirie** → type commercial → lier le dossier
5. Micro : d’abord `06` (court), puis éventuellement `07` (long)
6. Rédaction IA → comparer avec `08_ATTENDU…`

Régénérer : `python docs/kit-test-plaidoirie-commercial-complet/generate_kit.py`
