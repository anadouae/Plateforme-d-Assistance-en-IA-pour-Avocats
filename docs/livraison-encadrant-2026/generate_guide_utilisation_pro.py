# -*- coding: utf-8 -*-
"""
LexHub — Guide d'utilisation & de tests (document professionnel, production validée).
Aligné rigoureusement sur la production https://lexhub.space (septembre 2026).
Génère le document de référence officiel pour l'encadrant et l'évaluation PFA.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

OUT_REPO = Path(__file__).resolve().parent
OUT_DESK_DIRECT = Path.home() / "Desktop"
OUT_DESK_FOLDER = Path.home() / "Desktop" / "documents de  rentabilisation et guide de test & use"
OUT_PFA = Path.home() / "Desktop" / "S9" / "PFA"

LOGO = OUT_REPO / "logo-lexhub.png"
LOGO_CUBE = OUT_REPO / "logo-cube.png"

NAVY = RGBColor(0x0B, 0x1A, 0x4D)
GOLD = RGBColor(0xC9, 0xA8, 0x4A)
MUTED = RGBColor(0x4A, 0x55, 0x68)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
DARK_TEXT = RGBColor(0x1E, 0x29, 0x3B)
RED = RGBColor(0x9A, 0x34, 0x1C)
GREEN = RGBColor(0x16, 0x65, 0x34)


def set_run_font(run, name="Calibri", size=10.5, bold=False, italic=False, color=None):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color is not None:
        run.font.color.rgb = color


def add_para(doc, text, *, bold=False, italic=False, size=10.5, space_after=5, color=None, align=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    if align is not None:
        p.alignment = align
    r = p.add_run(text)
    set_run_font(r, size=size, bold=bold, italic=italic, color=color or DARK_TEXT)
    return p


def heading(doc, text, level=1):
    p = doc.add_heading(text, level=level)
    p.paragraph_format.keep_with_next = True
    for run in p.runs:
        run.font.name = "Calibri"
        if level == 1:
            run.font.size = Pt(15)
            run.font.color.rgb = NAVY
            run.bold = True
        elif level == 2:
            run.font.size = Pt(12)
            run.font.color.rgb = NAVY
            run.bold = True
        elif level == 3:
            run.font.size = Pt(11)
            run.font.color.rgb = GOLD
            run.bold = True
    return p


def shade(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), hex_color)
    shd.set(qn("w:val"), "clear")
    tcPr.append(shd)


def table(doc, headers, rows, col_widths=None):
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = "Table Grid"
    t.autofit = False

    for i, h in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell.text = ""
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.space_before = Pt(3)
        r = p.add_run(h)
        set_run_font(r, bold=True, size=8.5, color=WHITE)
        shade(cell, "0B1A4D")

    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            cell = t.rows[ri + 1].cells[ci]
            cell.text = ""
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(2.5)
            p.paragraph_format.space_before = Pt(2.5)
            r = p.add_run(str(val))
            set_run_font(r, size=8.5, color=DARK_TEXT)
            if ri % 2:
                shade(cell, "F8FAFC")

    if col_widths and len(col_widths) == len(headers):
        for row in t.rows:
            for i, w in enumerate(col_widths):
                row.cells[i].width = Cm(w)

    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def bullet(doc, text, size=9.5, bold_prefix=None):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(2.5)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    for run in list(p.runs):
        run.text = ""
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        set_run_font(r_pre, size=size, bold=True, color=NAVY)
    r = p.add_run(text)
    set_run_font(r, size=size, color=DARK_TEXT)
    return p


def numbered(doc, text, size=9.5, bold_prefix=None):
    p = doc.add_paragraph(style="List Number")
    p.paragraph_format.space_after = Pt(2.5)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    for run in list(p.runs):
        run.text = ""
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        set_run_font(r_pre, size=size, bold=True, color=NAVY)
    r = p.add_run(text)
    set_run_font(r, size=size, color=DARK_TEXT)
    return p


def step_box(doc, n: int, title: str, lines: list[str]):
    heading(doc, f"Étape {n} — {title}", 3)
    for line in lines:
        numbered(doc, line, size=9.5)


def callout(doc, title, body, fill="EEF2FF", border_color="0B1A4D"):
    t = doc.add_table(rows=1, cols=1)
    cell = t.rows[0].cells[0]
    shade(cell, fill)
    cell.text = ""
    p0 = cell.paragraphs[0]
    p0.paragraph_format.space_before = Pt(4)
    p0.paragraph_format.space_after = Pt(2)
    r0 = p0.add_run(title)
    set_run_font(r0, bold=True, size=9.5, color=NAVY)
    p1 = cell.add_paragraph()
    p1.paragraph_format.space_after = Pt(4)
    r1 = p1.add_run(body)
    set_run_font(r1, size=9, color=MUTED)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def hrule(doc):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(6)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "12")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "C9A84A")
    pBdr.append(bottom)
    pPr.append(pBdr)


def build() -> list[Path]:
    doc = Document()
    for s in doc.sections:
        s.top_margin = Cm(1.5)
        s.bottom_margin = Cm(1.5)
        s.left_margin = Cm(1.8)
        s.right_margin = Cm(1.8)

    # ── LOGO & EN-TÊTE OFFICIEL ──
    logo = LOGO if LOGO.exists() else LOGO_CUBE
    if logo.exists():
        doc.add_picture(str(logo), width=Cm(2.8))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    t.paragraph_format.space_before = Pt(4)
    t.paragraph_format.space_after = Pt(2)
    r = t.add_run("LexHub")
    set_run_font(r, size=22, bold=True, color=NAVY)

    t2 = doc.add_paragraph()
    t2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    t2.paragraph_format.space_after = Pt(2)
    r = t2.add_run("Guide d’utilisation & de tests")
    set_run_font(r, size=14, bold=True, color=NAVY)

    t_sub = doc.add_paragraph()
    t_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    t_sub.paragraph_format.space_after = Pt(4)
    r = t_sub.add_run("Plateforme d'Intelligence Artificielle Juridique pour Cabinets d'Avocats au Maroc")
    set_run_font(r, size=10, bold=True, color=GOLD)

    t3 = doc.add_paragraph()
    t3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    t3.paragraph_format.space_after = Pt(6)
    r = t3.add_run(
        f"Production https://lexhub.space · Édition Finale Validée · {date.today().strftime('%d/%m/%Y')} · "
        "Comptes · Rôles · Parcours · Facturation · Scénarios d'évaluation"
    )
    set_run_font(r, size=8.5, italic=True, color=MUTED)

    hrule(doc)

    callout(
        doc,
        "Objet & Contexte du document",
        "Ce guide constitue la référence opérationnelle, fonctionnelle et technique officielle de LexHub (https://lexhub.space). "
        "Il est destiné à l'encadrement pédagogique, aux évaluateurs professionnels et aux cabinets partenaires. "
        "L'ensemble des données, comptes de démonstration, quotas, grilles tarifaires et architectures présentés dans ce document "
        "sont strictement conformes à l'environnement actuellement déployé en production.",
        fill="FEF9EE",
    )

    # ── SOMMAIRE DÉTAILLÉ ──
    heading(doc, "Sommaire général", 1)
    sommaire_items = [
        ("PARTIE A — Prise en main & Accès sécurisés", [
            "A1. Démarrer en 2 minutes (Accès, Prérequis, Recommandations)",
            "A2. Comptes de test & identifiants vérifiés en production",
            "A3. Matrice des rôles et droits d'accès (Admin, Avocat, Assistant, Plateforme)",
            "A4. Navigation réelle & interface (Dock latéral, menu compte, paramètres)",
            "A5. Accès sécurisé à la base de données (PostgreSQL & Adminer via tunnel SSH chiffré)",
        ]),
        ("PARTIE B — Parcours métier & Cœur d'Intelligence Artificielle", [
            "B1. Dossiers judiciaires & pièces probatoires (Bordereau, indexation, OCR)",
            "B2. Atelier de rédaction de plaidoirie (5 étapes, dictée vocale native Chrome, 3 statuts)",
            "B3. Export officiel Microsoft Word (.docx) (RTL arabe, armoiries du Royaume, standard judiciaire)",
            "B4. Assistant IA & Clé de barre d’audience (Révision interactive, points oraux)",
            "B5. Planning d'audience, journal d'activité et gestion d'équipe",
        ]),
        ("PARTIE C — Modèle économique & Facturation", [
            "C1. Grille des plans et quotas réels de production (Découverte, Solo, Cabinet, Entreprise, Sur mesure)",
            "C2. Fonctionnement des essais gratuits plafonnés (Anti-abus)",
            "C3. Packs prépayés, PAYG et sièges supplémentaires",
            "C4. Programme de parrainage confraternel et historique des factures",
            "C5. Offre Entreprise & préparation au paiement CMI / PayZone",
        ]),
        ("PARTIE D — Scénarios de test pas-à-pas (Grille d'évaluation)", [
            "Scénarios 1 à 9 : Checklist d'évaluation opérationnelle prête à cocher",
        ]),
        ("PARTIE E — Console d'Administration Plateforme WEBVOICE", [
            "Supervision métrique, qualification des leads Entreprise, Ops Coach, sécurité",
        ]),
        ("Annexe — Architecture technique & Dépannage rapide", [
            "Stack technologique, sécurité/chiffrement, sauvegardes automatiques & FAQ",
        ]),
    ]
    for section_title, subs in sommaire_items:
        bullet(doc, section_title, size=9.5, bold_prefix="")
        for sub in subs:
            p_sub = doc.add_paragraph()
            p_sub.paragraph_format.left_indent = Cm(0.8)
            p_sub.paragraph_format.space_after = Pt(1.5)
            r_s = p_sub.add_run("• " + sub)
            set_run_font(r_s, size=8.5, color=MUTED)

    # =========================================================================
    # PARTIE A — PRISE EN MAIN & ACCÈS SÉCURISÉS
    # =========================================================================
    heading(doc, "PARTIE A — Prise en main & Accès sécurisés", 1)

    heading(doc, "A1. Démarrer en 2 minutes", 2)
    numbered(doc, "Ouvrir l'application en ligne sur https://lexhub.space (navigateur Google Chrome fortement recommandé pour l'enregistrement vocal haute fidélité).")
    numbered(doc, "Cliquer sur « Connexion » en haut à droite ou accéder directement à https://lexhub.space/login.")
    numbered(doc, "Saisir l'un des comptes de test préconfigurés présentés dans le tableau A2 ci-dessous (mot de passe standard : LexHub2026!).")
    numbered(doc, "En cas de mise à jour récente de votre navigateur, effectuer un rafraîchissement complet : Ctrl+F5 (Windows) ou Cmd+Shift+R (Mac).")
    numbered(doc, "Débuter par le Scénario 1 de la Partie D pour valider l'accès aux différents espaces de travail.")

    callout(
        doc,
        "Recommandation importante pour les tests multi-rôles",
        "Pour tester les différences d'habilitation entre administrateur, avocat et assistant, "
        "veillez à toujours vous déconnecter via le menu compte en haut à droite avant de saisir de nouveaux identifiants. "
        "Le compte administrateur plateforme (admin@webvoice.ma) gère l'écosystème global et n'est pas rattaché à un cabinet d'avocats particulier.",
        fill="FEE2E2",
    )

    heading(doc, "A2. Comptes de test & identifiants vérifiés en production", 2)
    add_para(
        doc,
        "Cinq comptes opérationnels sont configurés sur la plateforme de production pour couvrir l'intégralité des rôles métier et des scénarios d'évaluation :",
        size=10,
    )
    table(
        doc,
        ["E-mail", "Mot de passe", "Rôle attribué", "Usage principal lors des tests"],
        [
            ["demo@lexhub.space", "LexHub2026!", "Admin cabinet", "Parcours complet : dossiers, plaidoiries, IA, gestion d'équipe, abonnement et factures."],
            ["avocat@lexhub.space", "LexHub2026!", "Avocat collaborateur", "Production juridique : dictée, rédaction, synthèse, clé de barre — sans gestion de l'abonnement."],
            ["assistant@lexhub.space", "LexHub2026!", "Assistant juridique", "Gestion documentaire, indexation de pièces, consultation des plaidoiries validées."],
            ["test@cabinet-rabat.ma", "Test2026!", "Admin cabinet tiers", "Démonstration du multi-tenant étanche : aucun accès aux dossiers du cabinet démo principal."],
            ["admin@webvoice.ma", "WebVoice2026!", "Admin plateforme", "Console /admin : supervision des cabinets, qualification Entreprise, Ops Coach, audit."],
        ],
        col_widths=[4.5, 2.5, 3.2, 6.8],
    )

    heading(doc, "A3. Matrice des rôles et droits d'accès", 2)
    add_para(
        doc,
        "La plateforme implémente un contrôle d'accès strict basé sur les rôles (RBAC) pour garantir le secret professionnel et la gouvernance du cabinet :",
        size=10,
    )
    table(
        doc,
        ["Fonctionnalité / Action", "Admin cabinet", "Avocat", "Assistant juridique", "Admin plateforme"],
        [
            ["Créer / modifier un dossier", "Oui", "Oui", "Lecture / Pièces", "Non (étanchéité)"],
            ["Uploader / indexer des pièces", "Oui", "Oui", "Oui", "Non"],
            ["Dictée vocale & rédaction", "Oui", "Oui", "Non", "Non"],
            ["Révision assistée par IA", "Oui", "Oui", "Non", "Non"],
            ["Générer une Clé de barre", "Oui", "Oui", "Non", "Non"],
            ["Export officiel Word (.docx)", "Oui", "Oui", "Lecture seule", "Non"],
            ["Valider une plaidoirie", "Oui", "Oui", "Non", "Non"],
            ["Gérer l'équipe (invitations)", "Oui", "Non", "Non", "Non"],
            ["Gestion abonnement & packs", "Oui", "Lecture quotas", "Lecture quotas", "Supervision"],
            ["Accès console globale /admin", "Non", "Non", "Non", "Oui (exclusif)"],
            ["Supprimer un cabinet", "Non (zone sensible)", "Non", "Non", "Oui (avec confirmation)"],
        ],
        col_widths=[5.5, 2.8, 2.8, 3.2, 2.7],
    )
    bullet(doc, "L'avocat responsable (Admin cabinet) détient la maîtrise juridique, technique et financière de son espace.")
    bullet(doc, "L'avocat collaborateur dispose de toute la puissance de l'IA rédactionnelle sans charge de gestion administrative.")
    bullet(doc, "L'assistant juridique décharge l'avocat sur les dépôts de pièces et la consultation des dossiers sans risque de dérapage de quota.")

    heading(doc, "A4. Navigation réelle & interface utilisateur", 2)
    add_para(
        doc,
        "L'ergonomie de LexHub a été spécifiquement conçue pour la pratique judiciaire avec une interface épurée à double niveau :",
        size=10,
    )
    add_para(doc, "1. Le Dock latéral gauche (Outils quotidiens du cabinet)", size=10, bold=True)
    table(
        doc,
        ["Élément", "Route URL", "Rôle dans le cabinet"],
        [
            ["Tableau de bord", "/dashboard", "Vue synthétique : dossiers récents, plaidoiries en cours, alertes délais et raccourcis."],
            ["Dossiers", "/cases", "Répertoire judiciaire : gestion par client, juridiction, tribunal et matière."],
            ["Documents", "/documents", "Bordereau centralisé de toutes les pièces déposées et indexées."],
            ["Rédaction / Plaidoirie", "/redaction", "Atelier intelligent : dictée, structuration, révision IA et exports officiels."],
            ["Planning", "/agenda", "Calendrier des audiences, échéances de conclusions et rappels légaux."],
            ["Équipe", "/team", "Gestion des collaborateurs du cabinet et invitations sécurisées par e-mail."],
            ["Activité", "/activity", "Journal d'audit des actions du cabinet assurant la traçabilité déontologique."],
        ],
        col_widths=[4.5, 3.0, 9.5],
    )

    add_para(doc, "2. Le Menu Compte utilisateur (Coin supérieur droit)", size=10, bold=True)
    bullet(doc, "Profil & Préférences : nom d'exercice, e-mail et langue de travail (Français / Arabe).")
    bullet(doc, "Paramètres (/settings) : onglets Général, Cabinet (nom, ville, logo officiel pour les en-têtes), Plan & usage (quotas, crédits, packs), Sécurité (mots de passe, 2FA).")
    bullet(doc, "Mes factures : historique comptable des forfaits et recharges avec téléchargement direct des reçus PDF.")
    bullet(doc, "Déconnexion unique : positionnée exclusivement dans ce menu supérieur (aucune déconnexion redondante dans le dock).")

    heading(doc, "A5. Accès sécurisé à la base de données (PostgreSQL & Adminer via tunnel SSH chiffré)", 2)
    add_para(
        doc,
        "La base de données PostgreSQL de LexHub héberge les données hautement confidentielles des cabinets d'avocats partenaires : "
        "identité des justiciables, pièces probatoires judiciaires, actes de procédure et projets de plaidoiries protégés par "
        "le secret professionnel le plus strict (article 30 de la loi n° 28-08 régissant la profession d'avocat au Maroc et conformité CNDP).",
        size=10,
    )

    add_para(
        doc,
        "1. Pourquoi Adminer et non pgAdmin ? (Distinction technique essentielle pour l'évaluation)",
        bold=True,
        size=10,
        color=NAVY,
    )
    bullet(doc, "pgAdmin est une application client lourde : son utilisation exigerait que l'encadrant ou l'évaluateur installe un logiciel volumineux sur son poste personnel, gère des dépendances système complexes (runtimes C++/Python) ou déploie un conteneur Docker local consommateur de ressources.")
    bullet(doc, "Adminer est un gestionnaire web de base de données ultra-léger : il est déjà déployé et conteneurisé directement sur le serveur VPS de production (51.38.78.23). Il ne nécessite strictement AUCUNE installation logicielle, aucun téléchargement et aucun conteneur Docker sur la machine locale de l'encadrant. Il s'exécute nativement et immédiatement dans n'importe quel navigateur web moderne (Google Chrome, Microsoft Edge, Firefox).")

    add_para(
        doc,
        "2. Pourquoi l'accès direct via le Web est coupé (Confidentialité & Secret professionnel)",
        bold=True,
        size=10,
        color=NAVY,
    )
    bullet(doc, "Exposer une interface d'administration de base de données directement sur le Web public (ex. https://lexhub.space/_ops/db/) représenterait une faille de sécurité critique face aux attaques par force brute, aux robots d'exploration et aux scanners de vulnérabilités.")
    bullet(doc, "L'accès public HTTPS direct a été totalement coupé et verrouillé au niveau du reverse-proxy Caddy : toute tentative d'accès externe renvoie systématiquement une erreur 404 / 308.")
    bullet(doc, "L'accès ne peut être déverrouillé que par un canal chiffré point-à-point (port-forwarding SSH) réservé aux personnes autorisées.")

    add_para(
        doc,
        "3. Le rôle du script automatisé Ouvrir_Adminer.bat (Passerelle 1-clic)",
        bold=True,
        size=10,
        color=NAVY,
    )
    bullet(doc, "Pour dispenser l'encadrant de toute manipulation technique complexe en invite de commande, un fichier autonome nommé Ouvrir_Adminer.bat est mis à disposition à la racine du projet et sur le Bureau.")
    bullet(doc, "Ce fichier script monte automatiquement un tunnel SSH chiffré avec redirection de port : il relie de façon transparente le port local 127.0.0.1:8088 au conteneur Adminer isolé sur le VPS.")
    bullet(doc, "Il exécute en arrière-plan le script Python dédié python scripts\\open_adminer_tunnel.py (via la bibliothèque paramiko) ou la commande OpenSSH native Windows ssh -L 8088:localhost:8088 root@51.38.78.23. Un simple double-clic suffit.")

    add_para(
        doc,
        "4. Les 4 étapes pas-à-pas garanties pour se connecter et auditer la base",
        bold=True,
        size=10,
        color=NAVY,
    )
    numbered(doc, "Étape 1 — Lancer le tunnel SSH sécurisé : faire un double-clic sur le fichier Ouvrir_Adminer.bat (ou taper dans un terminal : python scripts\\open_adminer_tunnel.py). Une fenêtre d'invite de commandes noire s'ouvre et affiche « Tunnel SSH actif sur http://127.0.0.1:8088 ». IMPORTANT : laisser cette fenêtre ouverte pendant toute la durée de consultation.")
    numbered(doc, "Étape 2 — Ouvrir votre navigateur web : lancer Google Chrome ou Microsoft Edge et naviguer sur l'adresse locale : http://127.0.0.1:8088. La page d'accueil officielle d'Adminer s'affiche instantanément.")
    numbered(doc, "Étape 3 — Renseigner les identifiants SQL stricts de production (disponibles dans LexHub_DB_credentials.txt) :")
    bullet(doc, "Système : sélectionner « PostgreSQL » dans la liste déroulante.")
    bullet(doc, "Serveur : saisir « postgres » (nom d'hôte interne du conteneur PostgreSQL sur le réseau Docker privé du VPS ; ne pas saisir localhost ni d'adresse IP).")
    bullet(doc, "Utilisateur : « lexhub »")
    bullet(doc, "Mot de passe : « LhPg-gGhAymhq7AnfnrlWCEdvsloQ » (clé de production rotatée et sécurisée).")
    bullet(doc, "Base de données : « lexhub »")
    bullet(doc, "Action : cliquer sur le bouton « S'identifier ».")
    numbered(doc, "Étape 4 — Consultation & Audit des tables en direct : vous êtes connecté au schéma relationnel de production. Vous pouvez inspecter directement :")
    bullet(doc, "commercial_leads : les formulaires de qualification reçus pour l'offre Entreprise et les devis Sur mesure.")
    bullet(doc, "cabinets : la liste des cabinets inscrits, leurs forfaits, quotas et dates d'échéance d'essai.")
    bullet(doc, "users : les comptes utilisateurs (avocats, assistants, administrateurs) et leurs rôles RBAC.")
    bullet(doc, "cases : les dossiers judiciaires ouverts avec références de juridiction.")
    bullet(doc, "plaidoirie_drafts : les projets de conclusions avec leurs trois statuts (Brouillon, Validée, Finalisée).")
    bullet(doc, "ai_credit_transactions : le journal d'audit de chaque consommation de crédits d'IA.")
    bullet(doc, "invoices : l'historique comptable des reçus d'essai (0 MAD) et factures d'abonnement.")
    add_para(
        doc,
        "Clôture de session : pour révoquer l'accès et sécuriser la passerelle, fermer simplement la fenêtre noire du tunnel. "
        "Le port 8088 local est immédiatement libéré et l'accès à la base de données redevient totalement inaccessible.",
        size=9.5,
        italic=True,
        color=MUTED,
    )

    # =========================================================================
    # PARTIE B — PARCOURS MÉTIER & CŒUR D'INTELLIGENCE ARTIFICIELLE
    # =========================================================================
    heading(doc, "PARTIE B — Parcours métier & Cœur d'Intelligence Artificielle", 1)

    heading(doc, "B1. Dossiers judiciaires & pièces probatoires", 2)
    numbered(doc, "Création d'un dossier (/cases) : saisir la référence interne, l'identité du client, la partie adverse, la juridiction compétente (Tribunal de Première Instance, Cour d'Appel, etc.), la ville et la matière juridique.")
    numbered(doc, "Dépôt des pièces (PDF, Word, images numérisées) : glisser-déposer les documents directement sur la zone de téléversement.")
    numbered(doc, "Indexation et OCR automatique : le pipeline d'extraction analyse la structure textuelle, calcule le score de lisibilité et extrait les passages clés.")
    numbered(doc, "Bordereau de pièces : pour chaque document, qualifier précisément :")
    bullet(doc, "N° de pièce : ordre d'apparition dans le bordereau officiel remis au tribunal (1, 2, 3...).")
    bullet(doc, "Type de pièce : contrat, acte d'état civil, PV de constat d'huissier, facture, correspondance, mise en demeure...")
    bullet(doc, "Producteur : partie demanderesse, partie défenderesse, expert judiciaire ou tribunal.")
    bullet(doc, "Version : original, copie certifiée conforme ou traduction assermentée.")
    bullet(doc, "Référence de citation : libellé exact à insérer dans la plaidoirie (ex. « Pièce n° 2 : Acte de mariage du 15/06/2020 »).")

    heading(doc, "B2. Atelier de rédaction de plaidoirie (5 étapes & 3 statuts)", 2)
    add_para(
        doc,
        "L'atelier de rédaction (/redaction) est le cœur de valeur de LexHub. Il transforme la voix et les notes de l'avocat "
        "en un document de conclusions judiciaires prêt pour l'audience, structuré selon les standards du droit marocain.",
        size=10,
    )
    add_para(doc, "Le cycle en 5 étapes clés :", size=10, bold=True)
    step_box(doc, 1, "Choix de la matière et du modèle juridique", [
        "Sélectionner le domaine du litige : Statut personnel / Famille (Moudawana), Droit civil, Commercial, Social / Travail, Pénal, etc.",
        "Le choix du domaine injecte automatiquement le cadre légal adapté (visas textuels, formulation des prétentions et structure requise par la juridiction).",
    ])
    step_box(doc, 2, "Dictée vocale directe du navigateur (Web Speech API)", [
        "Activer le microphone : dictée naturelle en arabe fusha, en arabe juridique ou en français.",
        "Moteur vocal direct : Reconnaissance vocale native intégrée au navigateur (Web Speech API / SpeechRecognition) — capture audio instantanée sans aucune latence de téléversement, parfaitement calibrée pour le vocabulaire procédural marocain, sans dépendance ni surcoût d'API externe.",
        "Lissage automatique : ponctuation, correction syntaxique et mise en forme sans jamais altérer les faits dictés.",
    ])
    step_box(doc, 3, "Liaison au dossier judiciaire & intégration des pièces", [
        "Lier la plaidoirie au dossier judiciaire correspondant.",
        "Le système associe automatiquement les pièces du bordereau pour appuyer les moyens de droit soulevés.",
    ])
    step_box(doc, 4, "Révision assistée par l'Assistant IA", [
        "L'avocat conserve l'entière maîtrise du texte rédigé.",
        "L'Assistant IA interactif permet de reformuler un paragraphe, de développer un moyen juridique précis ou de combler une section manquante (ex. demandes accessoires, dépens, exécution provisoire).",
        "Le modèle linguistique GPT-4o applique un masquage strict des données à caractère personnel (PII masking) avant tout traitement.",
    ])
    step_box(doc, 5, "Export officiel finalisé Microsoft Word (.docx)", [
        "Génération instantanée du document Word (.docx) officiel, standard incontournable de la profession d'avocat au Maroc.",
        "Le document Word est 100 % éditable pour permettre à l'avocat d'apporter ses annotations finales ou d'ajuster ses conclusions avant dépôt au greffe.",
        "À l'export, les bandeaux d'avertissement de rédaction sont automatiquement masqués pour garantir une mise en page d'audience irréprochable.",
    ])

    add_para(doc, "Les trois statuts réglementaires d'une plaidoirie :", size=10, bold=True)
    table(
        doc,
        ["Statut", "Visibilité & Droits", "Signification dans le flux de travail du cabinet"],
        [
            ["Brouillon", "Avocat rédacteur uniquement", "Travail préparatoire en cours d'élaboration. Non visible par les assistants."],
            ["Validée", "Cabinet entier (avocats & assistants)", "Plaidoirie validée sur le fond par l'avocat, mise à disposition des assistants pour formalités ou dépôt."],
            ["Finalisée", "Historique officiel du dossier", "Exportation Word (.docx) effectuée. La plaidoirie est classée au rang des actes définitifs du cabinet."],
        ],
        col_widths=[3.0, 5.0, 9.0],
    )

    heading(doc, "B3. Export officiel Microsoft Word (.docx) (Standard de la profession)", 2)
    add_para(
        doc,
        "L'export des conclusions judiciaires a été délibérément et exclusivement unifié sur le format Microsoft Word (.docx). "
        "En pratique judiciaire marocaine devant les tribunaux et cours d'appel, l'avocat ne dépose jamais un document figé : "
        "il doit pouvoir relire ses écritures, y apposer des annotations d'audience manuscrites ou tapées, insérer une cote de pièce "
        "de dernière minute ou adapter la mise en page avant signature et impression sur papier à en-tête. "
        "Le format Word (.docx) est le standard absolu de travail dans tous les barreaux du Royaume :",
        size=10,
    )
    bullet(doc, "Armoiries officielles du Royaume du Maroc centrées au sommet de la première page (avec repli élégant si aucun logo n'a été téléversé dans les paramètres du cabinet), garantissant la solennité de l'acte.")
    bullet(doc, "En-tête officiel bilingue conforme aux usages des barreaux marocains : coordonnées du cabinet en français à gauche, mentions arabes solennelles à droite.")
    bullet(doc, "Typographie arabe d'excellence : utilisation de la police vectorielle Noto Naskh Arabic avec gestion native et rigoureuse du sens d'écriture de droite à gauche (RTL), sans inversion de parenthèses ni de ponctuation.")
    bullet(doc, "Structure canonique des conclusions respectée : En-tête solennel (المملكة المغربية), Juridiction saisie, Identification des parties (demandeur / défendeur), Exposé des faits (الوقائع), Discussion en droit (المناقشة القانونية) et Dispositif clair (لهذه الأسباب).")
    bullet(doc, "Suppression totale des artefacts visuels : aucune substitution parasite, listes à puces arabes fluides et espacement d'interligne 1.15 conforme aux exigences du greffe.")
    bullet(doc, "Édition et annotation libres : l'avocat dispose d'un document ouvert, modifiable à volonté dans Word avant l'impression finale.")

    heading(doc, "B4. Assistant IA & Clé de barre d'audience", 2)
    add_para(doc, "La Clé de barre d'audience (Outil de plaidoirie orale) :", size=10, bold=True)
    bullet(doc, "Générée automatiquement en un clic depuis l'ensemble des pièces probatoires et conclusions d'un dossier.")
    bullet(doc, "Présente sur une seule page synthétique : la chronologie des faits irréfutables, les moyens juridiques péremptoires, les prétentions chiffrées et les pièges d'audience à anticiper face à la partie adverse.")
    bullet(doc, "Conçue pour être consultée rapidement sur tablette ou feuille imprimée pendant les débats à la barre.")

    add_para(doc, "L'Assistant IA interactif :", size=10, bold=True)
    bullet(doc, "Accessible directement depuis l'atelier de rédaction.")
    bullet(doc, "Comprend les requêtes en français ou en arabe (ex. « Renforce l'argument sur l'article 400 du DOC » ou « أضف طلباً بالنفاذ المعجل »).")
    bullet(doc, "Refuse catégoriquement d'inventer des éléments factuels non présents dans le dossier.")

    heading(doc, "B5. Planning d'audience, journal d'activité et gestion d'équipe", 2)
    bullet(doc, "Agenda judiciaire (/agenda) : suivi des dates d'audiences, des délibérés et des délais impératifs de notification.")
    bullet(doc, "Journal d'activité (/activity) : historique horodaté de chaque action (création de dossier, modification de conclusions, export de pièces).")
    bullet(doc, "Gestion d'équipe (/team) : invitation de collaborateurs par e-mail sécurisé avec attribution de rôle (avocat ou assistant) dans la limite des sièges du forfait.")

    # =========================================================================
    # PARTIE C — MODÈLE ÉCONOMIQUE & FACTURATION
    # =========================================================================
    heading(doc, "PARTIE C — Modèle économique & Facturation", 1)

    heading(doc, "C1. Grille des plans et quotas réels de production", 2)
    add_para(
        doc,
        "La grille tarifaire de LexHub est calibrée sur la structure économique des cabinets d'avocats marocains, "
        "du praticien individuel jusqu'aux grandes structures multi-associés (source : API /api/billing/plans vérifiée) :",
        size=10,
    )
    table(
        doc,
        ["Offre", "Mensuel (MAD)", "Annuel (MAD)", "Essai gratuit", "Composition équipe", "Plaidoiries / mois", "Crédits IA / mois"],
        [
            ["Découverte", "0", "—", "Permanent", "1 avocat · 0 assistant", "3", "50"],
            ["Solo", "299", "2 990", "14 jours", "1 avocat + 1 assistant", "35", "600"],
            ["Cabinet ★", "699", "6 990", "30 jours", "5 avocats + 3 assistants", "120", "2 000"],
            ["Entreprise", "1 290", "12 900", "Sur qualification", "15 avocats + 10 assistants", "350", "5 000"],
            ["Sur mesure", "Sur devis", "Sur contrat", "Accompagné", "Cabinets > 15 avocats", "Personnalisé", "Dédié"],
        ],
        col_widths=[2.8, 2.2, 2.2, 2.8, 4.0, 3.0, 3.0],
    )
    add_para(
        doc,
        "Note sur le plan Cabinet ★ : offre recommandée couvrant 85 % des structures d'exercice au Maroc. "
        "Possibilité d'ajouter des sièges d'avocats supplémentaires à la carte au tarif de 99 MAD / mois par avocat (jusqu'à 10 avocats au total).",
        size=9,
        italic=True,
    )

    add_para(doc, "Barème de consommation des crédits d'Intelligence Artificielle :", size=10, bold=True)
    table(
        doc,
        ["Opération d'Intelligence Artificielle", "Coût unitaire en crédits", "Volume mensuel inclus (Plan Solo)", "Volume mensuel inclus (Plan Cabinet)"],
        [
            ["Rédaction complète de plaidoirie", "10 crédits", "35 plaidoiries", "120 plaidoiries"],
            ["Révision de section par Assistant IA", "5 crédits", "60 révisions", "250 révisions"],
            ["Analyse approfondie d'une pièce", "8 crédits", "12 analyses", "50 analyses"],
            ["Synthèse globale d'un dossier", "4 crédits", "25 synthèses", "100 synthèses"],
            ["Question ponctuelle sur le dossier", "2 crédits", "100 questions", "400 questions"],
            ["Génération d'une Clé de barre", "8 crédits", "10 fiches d'audience", "50 fiches d'audience"],
        ],
        col_widths=[5.5, 3.5, 4.0, 4.0],
    )

    heading(doc, "C2. Fonctionnement des essais gratuits plafonnés", 2)
    add_para(
        doc,
        "Afin de protéger la plateforme contre les abus tout en permettant aux avocats d'évaluer la solution en conditions réelles, "
        "les périodes d'essai gratuit sur les forfaits Solo (14 jours) et Cabinet (30 jours) appliquent un quota calibré :",
        size=10,
    )
    table(
        doc,
        ["Plan souscrit", "Durée d'essai", "Crédits alloués en essai", "Plaidoiries en essai", "Volume à l'activation payante"],
        [
            ["Solo", "14 jours", "400 crédits IA", "25 plaidoiries", "600 crédits · 35 plaidoiries / mois"],
            ["Cabinet ★", "30 jours", "1 000 crédits IA", "60 plaidoiries", "2 000 crédits · 120 plaidoiries / mois"],
        ],
        col_widths=[3.0, 2.5, 3.5, 3.5, 4.5],
    )
    bullet(doc, "Enregistrement de carte bancaire à 0 MAD : valide l'identité du cabinet sans débit immédiat.")
    bullet(doc, "Plafond journalier de sécurité (fair-use) : prévient la consommation automatisée massive.")
    bullet(doc, "Résiliation libre en un clic depuis l'interface avant la fin de la période d'essai sans le moindre prélèvement.")

    heading(doc, "C3. Packs prépayés, PAYG et sièges supplémentaires", 2)
    add_para(doc, "Mécanismes de flexibilité financière pour les périodes de forte activité :", size=10, bold=True)
    bullet(doc, "Packs de recharges ponctuelles : packs de 100, 300 ou 500 crédits IA valables 12 mois. Disponibles uniquement pour les abonnements actifs payants (masqués pendant la période d'essai).")
    bullet(doc, "Ordre de consommation intelligent (FIFO) : le système consomme prioritairement le forfait mensuel inclus, puis les recharges de packs, et enfin l'option PAYG si activée.")
    bullet(doc, "Paiement à l'usage (PAYG) : option facultative activable par l'admin cabinet pour autoriser les dépassements mineurs à ~0,25 MAD par crédit.")
    bullet(doc, "Sièges collaborateurs additionnels : 99 MAD/mois par avocat supplémentaire pour le plan Cabinet.")

    heading(doc, "C4. Programme de parrainage confraternel et factures", 2)
    bullet(doc, "Code parrainage unique : chaque cabinet dispose d'un code du type LH-XXXX ou d'un lien d'invitation direct.")
    bullet(doc, "Avantages réciproques : +14 jours d'essai offerts pour le cabinet confrère filleul ; +30 jours d'abonnement offerts pour le cabinet parrain dès la première mensualité payée par le filleul.")
    bullet(doc, "Mes factures (/settings) : accès direct à toutes les factures dématérialisées conformes, téléchargeables au format PDF pour la comptabilité du cabinet.")

    heading(doc, "C5. Offre Entreprise & préparation au paiement CMI / PayZone", 2)
    add_para(doc, "Qualification de l'offre Entreprise :", size=10, bold=True)
    add_para(
        doc,
        "En raison du volume très important de ressources allouées (15 avocats, 5 000 crédits IA), l'offre Entreprise ne fait pas l'objet "
        "d'une souscription directe instantanée. Le bouton dirige vers le formulaire de contact dédié (/commercial?intent=enterprise). "
        "Un conseiller WebVoice prend contact sous 24 à 48 heures pour dimensionner le déploiement avant attribution par l'administrateur plateforme.",
        size=10,
    )
    add_para(doc, "État de l'intégration du paiement en ligne :", size=10, bold=True)
    bullet(doc, "L'infrastructure technique complète est déployée et opérationnelle : moteur d'abonnement, calcul des proratas, gestion des reçus fiscaux et webhooks de confirmation.")
    bullet(doc, "L'encaissement effectif par carte bancaire marocaine sera activé dès finalisation des formalités d'homologation auprès du CMI (Centre Monétique Interbancaire) et de PayZone.")

    # =========================================================================
    # PARTIE D — SCÉNARIOS DE TEST PAS-À-PAS (GRILLE D'ÉVALUATION)
    # =========================================================================
    heading(doc, "PARTIE D — Scénarios de test pas-à-pas (Grille d'évaluation)", 1)
    add_para(
        doc,
        "Cette grille permet aux évaluateurs de valider méthodiquement le fonctionnement de LexHub en production. "
        "Cochez chaque case lors du déroulement de vos essais :",
        size=10,
    )

    heading(doc, "Scénario 1 — Authentification & Navigation générale", 2)
    bullet(doc, "□ Connexion réussie avec demo@lexhub.space / LexHub2026! sur https://lexhub.space/login.")
    bullet(doc, "□ Vérification du Dock latéral gauche : accès aux 7 sections principales.")
    bullet(doc, "□ Vérification de l'ergonomie : présence d'un seul bouton de déconnexion dans le menu supérieur droit.")
    bullet(doc, "□ Test du sélecteur de langue : basculement fluide entre le Français et l'Arabe.")

    heading(doc, "Scénario 2 — Création de dossier & Indexation de pièces", 2)
    bullet(doc, "□ Menu Dossiers → « Nouveau dossier » : saisie d'un client, d'une juridiction et d'une matière juridique.")
    bullet(doc, "□ Dépôt d'un fichier PDF ou Word probatoire : suivi de la barre de progression d'analyse.")
    bullet(doc, "□ Vérification de l'état d'indexation : score OCR et aperçu du document sans erreur serveur.")
    bullet(doc, "□ Renseignement des métadonnées probatoires : N° de pièce, Type, Producteur et Référence d'audience.")

    heading(doc, "Scénario 3 — Atelier de plaidoirie, Révision IA & Export officiel", 2)
    bullet(doc, "□ Menu Rédaction → « Nouvelle plaidoirie » : sélection du domaine Famille / Statut personnel ou Civil.")
    bullet(doc, "□ Liaison au dossier créé au Scénario 2 : affichage du rappel de bordereau.")
    bullet(doc, "□ Test vocal : enregistrement d'une phrase au microphone ou collage d'un texte modèle en arabe.")
    bullet(doc, "□ Action de l'Assistant IA : demande de complément sur les demandes subsidiaires ou les dépens.")
    bullet(doc, "□ Exportation officielle Word (.docx) : téléchargement immédiat du document de conclusions prêt pour l'audience (en-tête bilingue officiel, logo/armoiries royales centrés, typographie arabe Noto Naskh en sens RTL parfait, document 100 % éditable pour les annotations de l'avocat).")
    bullet(doc, "□ Standard unique d'audience : confirmation de l'unification exclusive sur le format Word (.docx), standard modifiable incontournable des juridictions du Royaume.")
    bullet(doc, "□ Vérification du cycle de vie : passage automatique de la plaidoirie au statut « Finalisée ».")
    bullet(doc, "□ Masquage des avertissements : confirmation de l'absence de bandeau 'infos manquantes' sur la prévisualisation finale.")

    heading(doc, "Scénario 4 — Fiche d'audience « Clé de barre »", 2)
    bullet(doc, "□ Ouverture d'un dossier disposant de pièces indexées.")
    bullet(doc, "□ Clic sur « Clé de barre IA » : génération de la fiche d'audience synthétique.")
    bullet(doc, "□ Vérification de la structure : faits saillants, visas de droit marocain, demandes principales et points oraux.")

    heading(doc, "Scénario 5 — Contrôle d'accès & Étanchéité des rôles", 2)
    bullet(doc, "□ Connexion avocat (avocat@lexhub.space) : accès complet à la rédaction et aux dossiers ; absence d'accès à la souscription financière.")
    bullet(doc, "□ Connexion assistant (assistant@lexhub.space) : accès à la consultation et à l'indexation ; verrouillage de la rédaction lourde.")
    bullet(doc, "□ Connexion cabinet tiers (test@cabinet-rabat.ma) : étanchéité multi-tenant parfaite, aucun dossier du cabinet démo n'est visible.")

    heading(doc, "Scénario 6 — Gestion financière, Quotas & Factures", 2)
    bullet(doc, "□ Menu Paramètres → « Plan & usage » : visualisation claire du plan courant, des plaidoiries consommées et des crédits restants.")
    bullet(doc, "□ Accès à « Mes factures » : consultation de la liste des reçus et factures d'abonnement au format PDF.")
    bullet(doc, "□ Vérification anti-abus : masquage des offres de packs supplémentaires pour les comptes en période d'essai.")

    heading(doc, "Scénario 7 — Gestion d'équipe & Invitations", 2)
    bullet(doc, "□ Menu Équipe (/team) : formulaire d'invitation d'un confrère par e-mail professionnel sécurisé.")
    bullet(doc, "□ Absence de code cabinet affiché en clair sur l'écran (sécurité contre les adhésions non autorisées).")

    heading(doc, "Scénario 8 — Demandes d'offres Entreprise & Sur mesure", 2)
    bullet(doc, "□ Visite de https://lexhub.space/tarifs en mode déconnecté : affichage des 4 forfaits et de la 5ᵉ case Sur mesure.")
    bullet(doc, "□ Clic sur l'offre Entreprise : redirection automatique vers le formulaire /commercial?intent=enterprise.")
    bullet(doc, "□ Soumission d'une demande de test : apparition immédiate dans la console d'administration /admin/leads.")

    heading(doc, "Scénario 9 — Accès sécurisé Base de données (PostgreSQL & Adminer via tunnel SSH)", 2)
    bullet(doc, "□ Confirmation de l'étanchéité publique : l'accès direct via https://lexhub.space/_ops/db/ renvoie bien 404 / 308 (aucun port de base de données exposé au web).")
    bullet(doc, "□ Lancement du tunnel chiffré : double-clic sur Ouvrir_Adminer.bat (ou exécution de python scripts\\open_adminer_tunnel.py).")
    bullet(doc, "□ Ouverture locale dans le navigateur : navigation sur http://127.0.0.1:8088 sans aucune installation logicielle locale.")
    bullet(doc, "□ Authentification PostgreSQL de production : Système=PostgreSQL, Serveur=postgres, Utilisateur=lexhub, Base=lexhub, Mot de passe=LhPg-gGhAymhq7AnfnrlWCEdvsloQ.")
    bullet(doc, "□ Audit des données en direct : inspection des tables commercial_leads (demandes Entreprise), cabinets, users, cases et plaidoirie_drafts.")
    bullet(doc, "□ Révocation immédiate : fermeture de la console terminal coupant instantanément le tunnel SSH.")

    # =========================================================================
    # PARTIE E — CONSOLE D'ADMINISTRATION PLATEFORME WEBVOICE
    # =========================================================================
    heading(doc, "PARTIE E — Console d'Administration Plateforme WEBVOICE", 1)
    add_para(
        doc,
        "Réservée à l'opérateur technique et commercial WEBVOICE, la console d'administration (/admin) "
        "assure la gouvernance globale de l'écosystème LexHub (Accès : admin@webvoice.ma / WebVoice2026!) :",
        size=10,
    )
    bullet(doc, "Tableau de bord métrique : décompte des cabinets actifs, utilisateurs inscrits, documents traités, requêtes IA et volume d'affaires global.")
    bullet(doc, "Gestion des cabinets (/admin/cabinets) : consultation de la fiche détaillée de chaque cabinet, audit de conformité et attribution directe de forfaits (notamment activation du plan Entreprise après qualification).")
    bullet(doc, "Traitement des leads commerciaux (/admin/leads) : suivi du pipeline commercial pour les demandes d'essais Entreprise et de devis Sur mesure (statuts : Nouveau, En cours, Qualifié, Converti).")
    bullet(doc, "Module Ops Coach : analyse automatique de l'activité des cabinets, détection des points de friction et génération de recommandations d'accompagnement proactif.")
    bullet(doc, "Sécurité et zone critique : possibilité de suspendre ou purger un cabinet de test dans le strict respect de la traçabilité administrative.")

    # =========================================================================
    # ANNEXE — ARCHITECTURE TECHNIQUE & DÉPANNAGE
    # =========================================================================
    heading(doc, "Annexe — Architecture technique & Dépannage rapide", 1)

    heading(doc, "Architecture technologique de production", 2)
    table(
        doc,
        ["Composant système", "Technologies déployées", "Rôle & Spécificités"],
        [
            ["Frontend utilisateur", "Next.js 14, React 18, TypeScript, Tailwind CSS", "Application réactive avec rendu serveur optimisé et bascule bilingue FR/AR."],
            ["Backend API", "FastAPI (Python 3.11), Pydantic v2, SQLAlchemy", "Architecture micro-services asynchrone, haute performance et documentation OpenAPI."],
            ["Base de données relationnelle", "PostgreSQL 16 (Schéma relationnel étanche)", "Stockage relationnel complet, audit logs, migrations de schéma via Alembic."],
            ["File de messages & Tâches de fond", "Celery, Redis 7 (In-Memory)", "Traitement asynchrone des fichiers lourds, OCR et transcription audio."],
            ["Moteur vocal (Dictée)", "Web Speech API (Reconnaissance vocale native Chrome)", "Transcription audio instantanée sans latence ni coût d'API, compatible arabe fusha et français."],
            ["Moteur rédactionnel & révision", "ChatGPT (GPT-4o) via passerelle sécurisée", "Génération juridique encadrée avec anonymisation PII préalable."],
            ["Moteur d'export de plaidoiries", "python-docx (Générateur binaire Word avancé)", "Format officiel unique .docx, typographie vectorielle Noto Naskh RTL et armoiries royales."],
            ["Stockage objet (S3)", "MinIO S3-Compatible (bucket lexhub-documents)", "Stockage chiffré des pièces judiciaires probatoires."],
            ["Serveur web & Sécurité Edge", "Caddy 2, Reverse-Proxy avec HTTPS automatique", "Chiffrement TLS 1.3, certificats Let's Encrypt et en-têtes HSTS stricts."],
        ],
        col_widths=[4.0, 5.0, 8.0],
    )

    heading(doc, "Politique de sauvegarde & Rétention des données", 2)
    bullet(doc, "Sauvegarde automatique quotidienne déclenchée chaque nuit à 02:30 via le script scripts/backup.sh.")
    bullet(doc, "Format de sauvegarde : cliché binaire PostgreSQL complet (lexhub.dump) et archive compressée des documents MinIO (minio_data.tar.gz).")
    bullet(doc, "Rétention glissante sur 7 jours avec rotation automatique des archives.")
    bullet(doc, "Procédure de restauration d'urgence testée et validée via le script scripts/restore.sh.")

    heading(doc, "Guide de dépannage rapide (FAQ)", 2)
    table(
        doc,
        ["Constat rencontré", "Explication & Démarche de résolution"],
        [
            ["L'écran semble afficher une version antérieure", "Effectuer un rafraîchissement complet du cache navigateur : Ctrl+F5 sous Windows ou Cmd+Shift+R sous Mac."],
            ["Le microphone ne capture aucun son", "Vérifier que les autorisations du micro sont accordées sur https://lexhub.space dans les paramètres Chrome."],
            ["Une pièce affiche « Échec d'analyse »", "Vérifier que le document n'est pas protégé par un mot de passe ; cliquer sur « Réextraire » pour relancer l'OCR."],
            ["Le statut reste sur « Brouillon » après export", "Consulter l'onglet « Finalisées » dans /redaction : l'export bascule automatiquement le document en finalisé."],
            ["Pourquoi l'export plaidoirie est-il uniquement Word (.docx) ?", "Conforme aux impératifs judiciaires : les conclusions doivent être modifiables pour permettre à l'avocat d'annoter et d'adapter son mémoire avant audience."],
            ["Les offres de packs sont invisibles", "Comportement normal : les packs de crédits sont réservés aux abonnements payants et masqués pendant l'essai."],
            ["Adminer affiche une erreur 404 sur HTTPS", "Mesure de cybersécurité délibérée : l'accès public direct est coupé. Lancer Ouvrir_Adminer.bat pour accéder via le tunnel local sécurisé http://127.0.0.1:8088 sans aucune installation logicielle locale."],
        ],
        col_widths=[5.5, 11.5],
    )

    hrule(doc)
    add_para(
        doc,
        "LexHub · Guide d'utilisation et de tests de production · Projet de Fin d'Année (PFA) · "
        "Document certifié conforme à la version déployée en production (https://lexhub.space) · 2026",
        size=8,
        italic=True,
        color=MUTED,
        align=WD_ALIGN_PARAGRAPH.CENTER,
    )

    # ── SAUVEGARDE MULTI-DESTINATIONS ──
    OUT_PFA.mkdir(parents=True, exist_ok=True)
    OUT_DESK_FOLDER.mkdir(parents=True, exist_ok=True)

    targets = [
        OUT_DESK_DIRECT / "02_Guide_utilisation_et_tests_LexHub_v8.docx",
        OUT_REPO / "02_Guide_utilisation_et_tests_LexHub_v8.docx",
        OUT_REPO / "02_Guide_utilisation_et_tests_LexHub.docx",
        OUT_DESK_FOLDER / "02_Guide_utilisation_et_tests_LexHub_v8.docx",
        OUT_DESK_FOLDER / "Guide_utilisation_et_tests_LexHub_reorganise.docx",
        OUT_PFA / "Guide_utilisation_et_tests_LexHub_PRO.docx",
        OUT_PFA / "Guide_utilisation_et_tests_LexHub_reorganise.docx",
    ]

    saved_paths = []
    for p in targets:
        try:
            doc.save(str(p))
            saved_paths.append(p)
            print(f"[OK] Sauvegardé avec succès : {p}")
        except PermissionError:
            alt = p.with_name(p.stem + "_MAJ" + p.suffix)
            try:
                doc.save(str(alt))
                saved_paths.append(alt)
                print(f"[VERROUILLÉ] Écriture alternative : {alt}")
            except Exception as e:
                print(f"[ERREUR] Impossible d'écrire sur {p} : {e}")
        except Exception as e:
            print(f"[ERREUR] Exception inattendue sur {p} : {e}")

    return saved_paths


if __name__ == "__main__":
    build()
