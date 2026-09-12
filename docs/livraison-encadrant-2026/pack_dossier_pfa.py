# -*- coding: utf-8 -*-
"""Range le dossier Desktop/S9/PFA : copies propres + archives + sources LaTeX."""

import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LIV = Path(__file__).resolve().parent
PFA = Path.home() / "Desktop" / "S9" / "PFA"
FINAL = PFA / "final"
ARCHIVE = PFA / "_anciennes_versions"
SRC_RAPPORT = REPO / "docs" / "rapport-pfa"
DEST_SRC = PFA / "sources_rapport_latex"


def copyf(src: Path, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    print("copy", src.name, "->", dest)


def main():
    PFA.mkdir(parents=True, exist_ok=True)
    FINAL.mkdir(parents=True, exist_ok=True)
    ARCHIVE.mkdir(parents=True, exist_ok=True)

    mapping = {
        "01_Rapport_PFA_LexHub.docx": LIV / "01_Rapport_PFA_LexHub.docx",
        "02_Proposition_plan_rentabilisation_LexHub.docx": LIV / "01_Proposition_plan_rentabilisation_LexHub_v5_MAJ.docx",
        "03_Guide_utilisation_et_tests_LexHub.docx": LIV / "02_Guide_utilisation_et_tests_LexHub_v8.docx",
        "04_Soutenance_PFA_LexHub.pptx": LIV / "04_Soutenance_PFA_LexHub.pptx",
        "05_Liste_captures_UI_rapport_PFA.docx": LIV / "03_Liste_captures_UI_rapport_PFA.docx",
    }
    # fallbacks if v5/v6 missing
    if not mapping["02_Proposition_plan_rentabilisation_LexHub.docx"].exists():
        alt = FINAL / "Proposition_plan_rentabilisation_LexHub_COMPLET.docx"
        if alt.exists():
            mapping["02_Proposition_plan_rentabilisation_LexHub.docx"] = alt
    if not mapping["03_Guide_utilisation_et_tests_LexHub.docx"].exists():
        alt = FINAL / "Guide_utilisation_et_tests_LexHub_PRO.docx"
        if alt.exists():
            mapping["03_Guide_utilisation_et_tests_LexHub.docx"] = alt

    for name, src in mapping.items():
        if src.exists():
            copyf(src, PFA / name)
            copyf(src, FINAL / name)
        else:
            print("MISSING", src)

    # Keep also the known "PRO/COMPLET" names in final
    if mapping["02_Proposition_plan_rentabilisation_LexHub.docx"].exists():
        copyf(mapping["02_Proposition_plan_rentabilisation_LexHub.docx"], FINAL / "Proposition_plan_rentabilisation_LexHub_COMPLET.docx")
    if mapping["03_Guide_utilisation_et_tests_LexHub.docx"].exists():
        copyf(mapping["03_Guide_utilisation_et_tests_LexHub.docx"], FINAL / "Guide_utilisation_et_tests_LexHub_PRO.docx")

    # Sources LaTeX (sans backups lourds de maquettes si trop gros — on copie le dossier utile)
    if DEST_SRC.exists():
        shutil.rmtree(DEST_SRC)
    DEST_SRC.mkdir(parents=True)
    for item in ("main.tex", "compile.bat", "README.md"):
        src = SRC_RAPPORT / item
        if src.exists():
            copyf(src, DEST_SRC / item)
    for folder in ("chapitres", "diagrams", "assets", "maquettes"):
        src = SRC_RAPPORT / folder
        if src.exists():
            shutil.copytree(src, DEST_SRC / folder, dirs_exist_ok=True)
            print("copy tree", folder)

    # Archive obsolete root files
    keep = {
        "01_Rapport_PFA_LexHub.docx",
        "02_Proposition_plan_rentabilisation_LexHub.docx",
        "03_Guide_utilisation_et_tests_LexHub.docx",
        "04_Soutenance_PFA_LexHub.pptx",
        "05_Liste_captures_UI_rapport_PFA.docx",
        "README_LIVRAISON.txt",
        "README.txt",
    }
    keep_dirs = {"final", "_anciennes_versions", "sources_rapport_latex"}
    for p in PFA.iterdir():
        if p.name.startswith("~$"):
            continue
        if p.is_dir():
            if p.name not in keep_dirs:
                dest = ARCHIVE / p.name
                try:
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.move(str(p), str(dest))
                    print("archive dir", p.name)
                except PermissionError:
                    print("locked skip dir", p.name)
            continue
        if p.name not in keep:
            dest = ARCHIVE / p.name
            try:
                if dest.exists():
                    dest.unlink()
                shutil.move(str(p), str(dest))
                print("archive", p.name)
            except PermissionError:
                print("locked skip", p.name)

    readme = PFA / "README_LIVRAISON.txt"
    readme.write_text(
        """Dossier PFA LexHub — livraison à jour (septembre 2026)
Produit : https://lexhub.space
Étudiante : EL ASSAL Douae · ENSA Tétouan · WEBVOICE

À remettre / imprimer
---------------------
01_Rapport_PFA_LexHub.docx
    Rapport PFA (Word). Contenu aligné prod : essai hybride, packs prépayés
    (abo actif seulement), sièges à la carte Cabinet, PAYG optionnel, parrainage.

02_Proposition_plan_rentabilisation_LexHub.docx
    Plan économique et règles de facturation.

03_Guide_utilisation_et_tests_LexHub.docx
    Guide d'utilisation + comptes / scénarios de test.

04_Soutenance_PFA_LexHub.pptx
    Présentation de soutenance — 16 slides (une idée = une slide).

05_Liste_captures_UI_rapport_PFA.docx
    Liste des captures d'écran pour le rapport.

sources_rapport_latex/
    Sources Overleaf (main.tex). Compiler avec pdfLaTeX × 2
    (MiKTeX / TeX Live / Overleaf). Pas de PDF ici : pdflatex absent sur ce PC.

final/
    Copies propres des mêmes livrables.

_anciennes_versions/
    Anciens fichiers (ne pas envoyer).

Règles facturation à retenir à l'oral
-------------------------------------
- Essai = 0 MAD + plafonds réduits (pas le forfait plein).
- Packs = 500/110 · 1000/200 · 2500/450 MAD, uniquement si abo ACTIF payant.
- Consommation : forfait du mois → packs FIFO (12 mois) → PAYG si ON → sinon blocage.
- Cabinet : +1 avocat = 99 MAD/mois (0 à 5 extra).
- CMI/PayZone : environnement prêt, activation opérateur encore en cours.
""",
        encoding="utf-8",
    )
    print("wrote", readme)
    print("OK", PFA)


if __name__ == "__main__":
    main()
