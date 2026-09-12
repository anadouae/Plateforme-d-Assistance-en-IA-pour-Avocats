#!/usr/bin/env python3
"""Update PFA Word docs: trial caps, prepaid packs, extra seats + explain Enterprise/Sur mesure."""
from pathlib import Path
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

PFA = Path(r"C:\Users\daurinia\Desktop\S9\PFA")
REPO_DOCS = Path(r"C:\Users\daurinia\Desktop\Avocat-AI-Assistance\docs\livraison-encadrant-2026")

RENTAB_SECTIONS = [
    ("\n5bis. Add-ons déjà en production (sept. 2026)", True),
    (
        "Deux leviers de la stratégie de rentabilisation sont désormais branchés dans LexHub "
        "(Paramètres → Plan & usage), en plus des plafonds d’essai hybrides.",
        False,
    ),
    ("5bis.1 Packs de crédits IA prépayés", True),
    (
        "Pourquoi : l’usage à la demande (0,25 MAD/crédit) est flexible mais imprévisible. "
        "Un pack prépayé donne un revenu immédiat, un prix unitaire plus bas pour le cabinet, "
        "et un solde qui reste jusqu’à consommation (ne expire pas avec le mois).",
        False,
    ),
    (
        "Comment ça marche : seul l’admin cabinet (plans Solo / Cabinet / Entreprise) achète un pack "
        "dans Plan & usage. Ordre de consommation des crédits : 1) forfait mensuel inclus → "
        "2) solde pack prépayé → 3) usage à la demande (si activé). "
        "Packs : 500 crédits / 110 MAD (~0,22) · 1 000 / 200 MAD (~0,20) · 2 500 / 450 MAD (~0,18). "
        "Une facture mock « PACK-… » apparaît dans Mes factures.",
        False,
    ),
    ("5bis.2 Sièges avocats à la carte (Cabinet ★)", True),
    (
        "Pourquoi : un cabinet de 6–7 avocats ne doit pas être forcé vers Entreprise (1 290 MAD). "
        "Les sièges extra capturent du revenu intermédiaire et réduisent le churn « trop cher / trop petit ».",
        False,
    ),
    (
        "Comment ça marche : sur le plan Cabinet uniquement, l’admin règle 0 à 5 sièges avocats "
        "supplémentaires à 99 MAD / siège / mois. Plafond total = 5 inclus + extra (max 10). "
        "Impossible de descendre sous le nombre d’avocats déjà actifs. Solo et Entreprise n’ont pas cet add-on.",
        False,
    ),
    ("5bis.3 Essai hybride (rappel)", True),
    (
        "Pendant l’essai, les quotas sont plafonnés sous le forfait payant : Solo 400 crédits / 25 plaidoiries "
        "(payant 600 / 35) · Cabinet 1 000 / 60 (payant 2 000 / 120) · Entreprise 1 800 / 120 (payant 5 000 / 350). "
        "0 MAD pendant l’essai ; les sièges du plan restent disponibles pour tester en équipe.",
        False,
    ),
    ("5ter. Recommandations pas encore produit — explications", True),
    ("5ter.1 Qualification Entreprise — pourquoi et comment", True),
    (
        "Pourquoi on en a besoin : un essai Entreprise ouvre jusqu’à 15 avocats + 10 assistants et "
        "un gros volume IA. En libre-service, un concurrent ou un faux cabinet peut consommer beaucoup "
        "de crédits OpenAI puis abandonner (ou recréer un compte). Le ticket Entreprise est élevé : "
        "un contact humain augmente fortement la conversion et filtre les tireurs au flanc.",
        False,
    ),
    (
        "Comment ça fonctionnerait (recommandation, pas encore codé) : quand l’admin clique « Essai Entreprise », "
        "au lieu d’activer immédiatement : 1) formulaire court (nom cabinet, ICE, taille équipe, barreau, besoin) "
        "ou 2) prise de rendez-vous / appel commercial WEBVOICE. Après validation, l’essai 30 jours "
        "est activé manuellement (ou automatiquement si le formulaire est propre). "
        "Solo et Cabinet restent en self-service avec plafonds d’essai.",
        False,
    ),
    ("5ter.2 Palier « Sur mesure » — pourquoi et comment", True),
    (
        "Pourquoi : Entreprise plafonne à 15 avocats. Au-delà (grands cabinets, directions juridiques, "
        "réseaux multi-villes), le besoin dépasse la grille publique : sièges custom, SLA, facturation "
        "multi-sites, éventuellement hébergement dédié. Sans ce palier, le prospect tombe dans le vide "
        "ou négocie hors process — perte de crédibilité B2B.",
        False,
    ),
    (
        "Comment ça fonctionnerait : sur /tarifs, une 5ᵉ carte « Sur mesure / Contactez-nous » "
        "(pas de prix public). CTA → formulaire ou e-mail commercial. Contrat annuel, devis, "
        "support dédié. Ce n’est pas un self-checkout comme Solo/Cabinet.",
        False,
    ),
]

GUIDE_BLOCK = [
    ("\nPacks de crédits & sièges à la carte (tests)", True),
    (
        "1) Connectez-vous en admin cabinet sur un plan Solo ou Cabinet (essai ou payant).",
        False,
    ),
    (
        "2) Paramètres → Plan & usage → section « Packs de crédits prépayés ». "
        "Notez le solde, achetez le pack 500, vérifiez que le solde augmente et qu’une ligne "
        "apparaît dans Mes factures.",
        False,
    ),
    (
        "3) Épuisez (ou simulez) le forfait mensuel : les actions IA doivent d’abord consommer "
        "le solde prépayé avant l’usage à la demande.",
        False,
    ),
    (
        "4) Sur plan Cabinet uniquement : réglez « Sièges extra » à 1 ou 2, Enregistrer, "
        "puis invitez un avocat supplémentaire sans erreur 402. Remettez à 0 si besoin "
        "(seulement si le nombre d’avocats actifs le permet).",
        False,
    ),
    (
        "5) Essai : vérifiez que les compteurs affichent les plafonds d’essai (ex. Solo 400 crédits), "
        "pas le forfait payant complet.",
        False,
    ),
]


def append_sections(doc: Document, sections: list[tuple[str, bool]]) -> None:
    for text, is_heading in sections:
        if is_heading:
            p = doc.add_heading(text.strip(), level=2)
        else:
            p = doc.add_paragraph(text.strip())
            for run in p.runs:
                run.font.size = Pt(11)


def update_rentab(path: Path) -> None:
    doc = Document(str(path))
    marker = "5bis. Add-ons déjà en production"
    already = any(marker in (p.text or "") for p in doc.paragraphs)
    if not already:
        append_sections(doc, RENTAB_SECTIONS)
        for p in doc.paragraphs:
            if "Ce n’est pas une feuille de route" in (p.text or ""):
                p.text = (
                    "Ce document décrit ce qui tourne sur https://lexhub.space, "
                    "y compris plafonds d’essai, packs prépayés et sièges à la carte (sept. 2026). "
                    "Les sections « 5ter » restent des recommandations non encore produit."
                )
                break
    out = path.with_name(path.stem + "_MAJ_packs_sieges.docx")
    doc.save(str(out))
    try:
        doc.save(str(path))
        print("updated", path.name, "+", out.name)
    except PermissionError:
        print("source locked — saved", out.name)


def update_guide(path: Path) -> None:
    doc = Document(str(path))
    marker = "Packs de crédits & sièges à la carte"
    already = any(marker in (p.text or "") for p in doc.paragraphs)
    if not already:
        append_sections(doc, GUIDE_BLOCK)
    out = path.with_name(path.stem + "_MAJ_packs_sieges.docx")
    doc.save(str(out))
    try:
        doc.save(str(path))
        print("updated", path.name, "+", out.name)
    except PermissionError:
        print("source locked — saved", out.name)


def main() -> None:
    rentab = PFA / "Proposition_plan_rentabilisation_LexHub_avec_essai.docx"
    guide = PFA / "Guide_utilisation_et_tests_LexHub_reorganise.docx"
    if rentab.exists():
        update_rentab(rentab)
    else:
        print("MISSING", rentab)
    if guide.exists():
        update_guide(guide)
    else:
        print("MISSING", guide)
    # mirror into repo livraison if present
    for name in (
        "01_Proposition_plan_rentabilisation_LexHub_v5.docx",
        "02_Guide_utilisation_et_tests_LexHub_v6.docx",
    ):
        pass
    print("done")


if __name__ == "__main__":
    main()
