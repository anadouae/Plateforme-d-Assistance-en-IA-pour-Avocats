# -*- coding: utf-8 -*-
"""
LexHub — Plan & stratégie de rentabilisation (document pro, état prod + explications).
Génère un DOCX clair, prêt à envoyer (encadrant / partenaires).
"""

from pathlib import Path
from datetime import date

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor, Inches

REPO = Path(__file__).resolve().parents[2]
OUT_REPO = Path(__file__).resolve().parent
OUT_PFA = Path(r"C:\Users\daurinia\Desktop\S9\PFA")
OUT_DESKTOP = Path(r"C:\Users\daurinia\Desktop\documents de  rentabilisation et guide de test & use")
OUT_DESKTOP_ROOT = Path(r"C:\Users\daurinia\Desktop")
LOGO = OUT_REPO / "logo-lexhub.png"
LOGO_CUBE = OUT_REPO / "logo-cube.png"

NAVY = RGBColor(0x0B, 0x1A, 0x4D)
GOLD = RGBColor(0xC9, 0xA8, 0x4A)
MUTED = RGBColor(0x4A, 0x55, 0x68)
GREEN = RGBColor(0x0F, 0x6B, 0x4C)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)


def set_run_font(run, name="Calibri", size=11, bold=False, italic=False, color=None):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color is not None:
        run.font.color.rgb = color


def add_para(doc, text, *, bold=False, italic=False, size=11, space_after=6, color=None, align=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    if align is not None:
        p.alignment = align
    r = p.add_run(text)
    set_run_font(r, size=size, bold=bold, italic=italic, color=color)
    return p


def heading(doc, text, level=1):
    p = doc.add_heading(text, level=level)
    for run in p.runs:
        run.font.color.rgb = NAVY
    return p


def shade(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), hex_color)
    shd.set(qn("w:val"), "clear")
    tcPr.append(shd)


def set_cell_borders(cell):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:color"), "CBD5E1")
        tcBorders.append(el)
    tcPr.append(tcBorders)


def table(doc, headers, rows, col_widths=None):
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = "Table Grid"
    for i, h in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell.text = ""
        p = cell.paragraphs[0]
        r = p.add_run(h)
        set_run_font(r, bold=True, size=9, color=WHITE)
        shade(cell, "0B1A4D")
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            cell = t.rows[ri + 1].cells[ci]
            cell.text = ""
            p = cell.paragraphs[0]
            r = p.add_run(str(val))
            set_run_font(r, size=9)
            if ri % 2:
                shade(cell, "F1F5F9")
    doc.add_paragraph()
    return t


def bullet(doc, text, size=10):
    p = doc.add_paragraph(style="List Bullet")
    for run in list(p.runs):
        run.text = ""
    r = p.add_run(text)
    set_run_font(r, size=size)
    p.paragraph_format.space_after = Pt(3)
    return p


def callout(doc, title, body, fill="EEF2FF"):
    t = doc.add_table(rows=1, cols=1)
    cell = t.rows[0].cells[0]
    shade(cell, fill)
    cell.text = ""
    p0 = cell.paragraphs[0]
    r0 = p0.add_run(title)
    set_run_font(r0, bold=True, size=10, color=NAVY)
    p1 = cell.add_paragraph()
    r1 = p1.add_run(body)
    set_run_font(r1, size=9, color=MUTED)
    doc.add_paragraph()


def hrule(doc):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(8)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "12")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "C9A84A")
    pBdr.append(bottom)
    pPr.append(pBdr)


def build():
    doc = Document()
    for s in doc.sections:
        s.top_margin = Cm(1.6)
        s.bottom_margin = Cm(1.6)
        s.left_margin = Cm(1.9)
        s.right_margin = Cm(1.9)

    # —— Couverture ——
    logo = LOGO if LOGO.exists() else LOGO_CUBE
    if logo.exists():
        doc.add_picture(str(logo), width=Cm(2.8))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = t.add_run("LexHub")
    set_run_font(r, size=22, bold=True, color=NAVY)

    t2 = doc.add_paragraph()
    t2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = t2.add_run("Plan de croissance & stratégie de rentabilisation")
    set_run_font(r, size=14, bold=True, color=NAVY)

    t3 = doc.add_paragraph()
    t3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = t3.add_run(
        "Document de référence — production https://lexhub.space · "
        f"{date.today().strftime('%d/%m/%Y')}"
    )
    set_run_font(r, size=10, italic=True, color=MUTED)

    t4 = doc.add_paragraph()
    t4.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = t4.add_run(
        "Tarifs · essais plafonnés · quotas · packs prépayés · sièges à la carte · "
        "usage à la demande · parrainage · factures"
    )
    set_run_font(r, size=9, color=GOLD)

    hrule(doc)

    callout(
        doc,
        "Comment lire ce document",
        "Les sections marquées « EN PRODUCTION » décrivent ce qui tourne déjà sur lexhub.space. "
        "Les sections « FEUILLE DE ROUTE » sont des recommandations business non encore codées. "
        "Ne pas confondre les deux. Les chiffres de tarifs et quotas ci-dessous sont ceux du code déployé.",
        fill="FEF9EE",
    )

    # —— Sommaire court ——
    heading(doc, "Sommaire", 1)
    for line in [
        "1. Produit et modèle économique",
        "1.1 Méthodes professionnelles (gestion de projet & économie SaaS)",
        "1.2 Fondements mathématiques et unit economics",
        "2. Les 3 objets de facturation (clé de lecture)",
        "3. Grille tarifaire en production",
        "4. Quotas IA et coûts par action",
        "4.1 Ordre de consommation des crédits",
        "4.2 Repère IA du jour (tous plans) — choix client",
        "4.3 Quand le forfait est épuisé — popups de guidance",
        "5. Cycle client : inscription → essai → payant",
        "6. Essai hybride (durée + plafond d’usage)",
        "7. Packs de crédits prépayés — explication complète",
        "8. Usage à la demande (PAYG)",
        "9. Sièges avocats à la carte (Cabinet)",
        "10. Parrainage cabinet → cabinet",
        "11. Factures et gouvernance",
        "12. Feuille de route et qualifications commerciales",
        "13. Synthèse pour décideur",
    ]:
        bullet(doc, line, size=10)

    # —— 1 ——
    heading(doc, "1. Produit et modèle économique", 1)
    add_para(
        doc,
        "LexHub est un SaaS multi-tenant pour cabinets d’avocats au Maroc : dictée, documents, "
        "dossiers, rédaction de plaidoirie (arabe juridique), planning, équipe. "
        "Le revenu principal vient des abonnements payants (Solo, Cabinet, Entreprise). "
        "L’acquisition repose sur le freemium Découverte, les essais hybrides, et le parrainage. "
        "La marge est protégée par des quotas (mensuels et journaliers) et des add-ons contrôlés. "
        "Ces choix ne sont pas arbitraires : ils s’appuient sur des méthodes nommées du domaine "
        "SaaS / économie de l’innovation et de la gestion de projet (§ 1.1), avec des relations "
        "chiffrées explicites (§ 1.2). Source unique : code déployé (billing.py) et https://lexhub.space.",
        size=10,
    )
    bullet(doc, "Seul l’admin cabinet paie, change de plan, achète des packs, active le PAYG, gère le parrainage.")
    bullet(doc, "Avocats / assistants : quotas en lecture seule — ils ne paient pas.")
    bullet(doc, "Interface FR / AR · montants en MAD · site : https://lexhub.space")

    heading(doc, "1.1 Méthodes professionnelles mobilisées", 2)
    add_para(
        doc,
        "Cadre : économie SaaS (pricing & packaging), product management, conduite de projet itérative. "
        "Chaque méthode est reliée à une décision concrète LexHub.",
        size=10,
    )
    table(
        doc,
        ["Méthode / concept (domaine)", "Sens", "Application LexHub"],
        [
            [
                "Product-Led Growth (PLG) + Freemium",
                "Le produit sert d’acquisition ; palier gratuit limité",
                "Découverte : 0 MAD, 3 plaidoiries, 50 crédits",
            ],
            [
                "Good–Better–Best (GBB)",
                "Paliers de valeur croissante",
                "Découverte → Solo → Cabinet → Entreprise (+ Sur mesure)",
            ],
            [
                "Hybrid pricing (abo + usage)",
                "Recettes prévisibles + capture de la surconsommation",
                "Forfait inclus + packs + PAYG 0,25 MAD/crédit",
            ],
            [
                "Usage-based metering (crédits)",
                "Unités liées au coût variable LLM",
                "Barème : polish 1 … rédaction 10",
            ],
            [
                "Hybrid trial (durée + quota)",
                "Essai temporel ET plafonné",
                "Solo 14 j / 400 crédits ; Cabinet–Ent. 30 j / quotas ↓",
            ],
            [
                "Fair-use + soft cap informé",
                "Repère anti-abus avec choix éclairé",
                "Repère IA/jour + Continuer / Attendre demain",
            ],
            [
                "Unit economics & COGS",
                "Lier prix, volume inclus et coût variable",
                "Cible : COGS IA ~10–20 % du prix en usage réel",
            ],
            [
                "Land & expand",
                "Entrer petit, élargir ensuite",
                "Sièges +99 MAD · packs · upgrade de plan",
            ],
            [
                "Referral marketing B2B",
                "Acquisition virale contrôlée",
                "+14 j / +30 j · plafond 12 / an",
            ],
            [
                "Lean Startup + itération Agile",
                "MVP → mesure → prod",
                "Plateforme livrée sur lexhub.space",
            ],
            [
                "Gestion des risques (coût variable)",
                "Mitiger le risque OpenAI par design",
                "Double frein crédits + plaidoiries · slots",
            ],
            [
                "FIFO (lots)",
                "Premier entré / premier sorti",
                "Packs : expiration 12 mois, conso FIFO",
            ],
        ],
    )
    callout(
        doc,
        "Intégrité méthodologique",
        "Pas d’études Van Westendorp ni de LTV/CAC terrain non mesurés inventés ici. "
        "Les méthodes listées structurent réellement les décisions. "
        "Les formules § 1.2 dérivent des constantes du code (billing.py).",
        fill="FEF3C7",
    )

    heading(doc, "1.2 Fondements mathématiques et unit economics", 2)
    add_para(
        doc,
        "Notations : P = prix abo mensuel (MAD) ; N = crédits inclus / mois ; "
        "c_payg = 0,25 MAD/crédit ; w(a) = poids en crédits de l’action a "
        "(rédaction w = 10) ; Q_p = plafond plaidoiries / mois.",
        size=10,
    )
    bullet(doc, "Valeur indicative du forfait au tarif PAYG : V = N × c_payg. Solo : V = 600 × 0,25 = 150 MAD (abo 299 MAD).")
    bullet(doc, "Ratio forfait / prix : ρ = V / P. Solo ρ ≈ 150/299 ≈ 50 % — le reste = hébergement, support, marge, risque.")
    bullet(doc, "Packs dégressifs : u ∈ {0,22 ; 0,20 ; 0,18} < c_payg → recharge plus avantageuse que le dépassement.")
    bullet(doc, "Double frein rédaction : n ≤ min(⌊N/w⌋, Q_p). Solo : min(⌊600/10⌋, 35) = 35.")
    bullet(doc, "Ratio essai/payant (crédits) : Solo 400/600 ≈ 67 % · Cabinet 50 % · Entreprise 36 %.")
    bullet(doc, "Annuel : P_an ≈ 10 × P_mois (Solo 2 990 ≈ 10 × 299) → ~2 mois offerts.")
    bullet(doc, "Soft-cap journalier : si usage_j + w(a) > d_j → popup de choix (pas un mur).")
    add_para(
        doc,
        "Ces relations expliquent l’essai plafonné, le repère du jour informatif, et la séparation "
        "abonnement / packs / PAYG / sièges comme leviers d’expansion.",
        size=10,
    )

    # —— 2 ——
    heading(doc, "2. Les 3 objets de facturation (clé de lecture)", 1)
    add_para(
        doc,
        "Pour éviter toute confusion, LexHub sépare trois mécanismes. Ils ne se mélangent pas en base : "
        "chacun a son historique. L’UI peut afficher un total, mais la source de chaque crédit reste traçable.",
        size=10,
    )
    table(
        doc,
        ["Objet", "À quoi ça sert", "Quand on paie", "Exemple"],
        [
            [
                "1. Abonnement",
                "Accès au produit + forfait mensuel inclus (crédits, plaidoiries, sièges)",
                "Chaque mois ou année (après essai)",
                "Solo = 299 MAD/mois → 600 crédits inclus",
            ],
            [
                "2. Pack prépayé",
                "Recharge ponctuelle de crédits IA (lot), en plus du forfait",
                "Une fois, à l’achat (fenêtre carte)",
                "500 crédits pour 110 MAD, valables 12 mois",
            ],
            [
                "3. Usage à la demande (PAYG)",
                "Dépassement au fil de l’eau si forfait (+ packs) épuisés",
                "Surplus sur facture (~0,25 MAD/crédit)",
                "Option OFF par défaut — jamais silencieuse",
            ],
        ],
    )
    callout(
        doc,
        "Analogie simple",
        "Abonnement = forfait mobile 600 minutes/mois. Pack = carte prépayée de 500 minutes achetée en plus. "
        "PAYG = dépassement facturé à la minute. On n’achète la carte prépayée que si le forfait ne suffit plus.",
        fill="ECFDF5",
    )

    # —— 3 ——
    heading(doc, "3. Grille tarifaire en production", 1)
    table(
        doc,
        ["Plan", "Mensuel", "Annuel", "Essai", "Sièges", "Plaidoiries/mois", "Crédits IA/mois"],
        [
            ["Découverte", "0 MAD", "—", "aucun (freemium)", "1 av. · 0 ass.", "3", "50"],
            ["Solo", "299 MAD", "2 990 MAD", "14 jours", "1 av. + 1 ass.", "35", "600"],
            ["Cabinet ★", "699 MAD", "6 990 MAD", "30 jours", "5 av. + 3 ass.", "120", "2 000"],
            ["Entreprise", "1 290 MAD", "12 900 MAD", "30 jours", "15 av. + 10 ass.", "350", "5 000"],
        ],
    )
    bullet(doc, "Annuel ≈ 10 mois payés pour 12 (déjà dans les prix yearly).")
    bullet(doc, "Dossiers : 5 max sur Découverte · illimités dès Solo.")
    bullet(doc, "À partir de Solo : export PDF, logo cabinet, invitations d’équipe.")

    # —— 4 ——
    heading(doc, "4. Quotas IA et coûts par action", 1)
    add_para(
        doc,
        "Chaque action IA consomme des crédits. En parallèle, certaines actions ont un plafond d’occurrences / mois. "
        "Les deux garde-fous s’appliquent ensemble.",
        size=10,
    )
    table(
        doc,
        ["Action", "Coût crédits", "Max/mois Découverte", "Solo", "Cabinet", "Entreprise"],
        [
            ["Rédaction plaidoirie", "10", "3*", "35*", "120*", "350*"],
            ["Révision", "5", "8", "60", "250", "600"],
            ["Analyse", "8", "1", "12", "50", "150"],
            ["Synthèse", "4", "3", "25", "100", "300"],
            ["Question (ask)", "2", "10", "100", "400", "1 200"],
            ["Clé de barre", "8", "1", "10", "50", "150"],
            ["Budget crédits / mois", "—", "50", "600", "2 000", "5 000"],
        ],
    )
    add_para(
        doc,
        "* Une rédaction consomme 1 unité « plaidoiries » ET 10 crédits. "
        "Slots IA parallèles : Découverte / Solo = 1 · Cabinet = 2 · Entreprise = 3. "
        "Le repère du jour (section 4.2) n’est pas un mur : le client est informé et choisit.",
        size=9,
        italic=True,
        color=MUTED,
    )

    heading(doc, "4.1 Ordre de consommation des crédits (règle unique)", 2)
    add_para(doc, "À chaque action IA, LexHub décrémente dans cet ordre strict :", size=10)
    bullet(doc, "1) Forfait mensuel inclus dans l’abonnement (ou quotas d’essai pendant le trial)")
    bullet(doc, "2) Solde des packs prépayés (lots qui expirent le plus tôt d’abord — FIFO) — abonnés payants seulement")
    bullet(doc, "3) Usage à la demande, uniquement si l’admin l’a activé (payants seulement)")
    bullet(doc, "4) Sinon → popup de résolution (section 4.3)")

    heading(doc, "4.2 Repère IA du jour (tous les plans) — EN PRODUCTION", 2)
    add_para(
        doc,
        "Même logique pour Découverte, Solo, Cabinet et Entreprise — que le cabinet soit en essai ou déjà abonné payant. "
        "Ce n’est PAS un impayé et ce n’est PAS la fin de l’essai. C’est un repère anti-abus du jour : "
        "le client voit son usage et décide.",
        size=10,
    )
    table(
        doc,
        ["Plan", "Repère / jour en ESSAI", "Repère / jour en ABONNEMENT PAYÉ"],
        [
            ["Découverte (freemium)", "— (pas d’essai)", "12 crédits"],
            ["Solo", "35", "50"],
            ["Cabinet", "90", "180"],
            ["Entreprise", "105", "300"],
        ],
    )
    callout(
        doc,
        "Popup « Beaucoup d’IA aujourd’hui »",
        "Quand l’action suivante ferait dépasser le repère du jour : "
        "(1) le message indique clairement ESSAI ou ABONNEMENT + le plan + le compteur (ex. 33/35) ; "
        "(2) bouton « Continuer maintenant » → l’IA part, les crédits du mois / de l’essai sont débités ; "
        "(3) bouton « Attendre demain » → stop, compteur du jour remis à zéro demain. "
        "Après « Continuer », la session se souvient pour le reste de la journée. "
        "Pastille UI (crédits restants · auj.) + barre « IA aujourd’hui » dans Paramètres → Plan & usage.",
        fill="ECFDF5",
    )
    bullet(doc, "Urgence / volume de plaidoiries : le client n’est jamais bloqué dur sur le jour — il est informé et responsable.")
    bullet(doc, "Les vrais garde-fous durs restent : crédits / quotas du mois (ou de l’essai), et fin d’essai.")

    heading(doc, "4.3 Quand le forfait est épuisé — popups de guidance — EN PRODUCTION", 2)
    add_para(
        doc,
        "Deux situations distinctes du « repère du jour ». Ici le forfait (essai ou mois) est vraiment terminé : "
        "l’action IA est refusée tant que le client n’a pas choisi une issue.",
        size=10,
    )
    table(
        doc,
        ["Situation", "Ce que voit le client", "Ce qu’il peut faire"],
        [
            [
                "Forfait d’ESSAI épuisé",
                "Popup « Forfait d’essai épuisé » + date de fin d’essai",
                "Attendre la fin d’essai (pas d’achat de packs pendant l’essai) · OU souscrire (Voir les tarifs)",
            ],
            [
                "Forfait du MOIS (abonné payant) épuisé",
                "Popup « Forfait du mois épuisé »",
                "1) Activer usage à la demande · 2) Acheter un pack · 3) Passer au plan supérieur · sinon attendre le mois suivant",
            ],
            [
                "Découverte (gratuit) épuisé",
                "Même logique de blocage quota",
                "Upgrade Solo / Cabinet — pas de packs, pas de PAYG",
            ],
        ],
    )
    bullet(doc, "Toast « Crédits épuisés / solde bas » + pastille en bas à droite : information continue, en plus des popups.")
    bullet(doc, "Bannière d’abonnement : rappels essai bientôt fini, renouvellement proche, past_due, retour Découverte.")
    bullet(doc, "Avocat / assistant : peuvent voir les quotas ; seuls l’admin active PAYG, achète packs ou change de plan.")

    # —— 5 ——
    heading(doc, "5. Cycle client : inscription → essai → payant", 1)
    bullet(doc, "1. Inscription (e-mail OTP) → cabinet + admin → plan Découverte automatique.")
    bullet(doc, "2. Parrainage optionnel à l’inscription (code / lien ?ref=CODE).")
    bullet(doc, "3. Admin choisit Solo / Cabinet / Entreprise (Paramètres ou /tarifs).")
    bullet(doc, "4. Essai avec carte (modèle type Coursera) pour Solo (14 j) et Cabinet (30 j) · Pour Entreprise : qualification commerciale préalable obligatoire (§ 12.1), aucun essai direct en libre-service · 0 MAD pendant l’essai.")
    bullet(doc, "5. Parrainage valide → +14 jours d’essai pour le filleul (une fois).")
    bullet(doc, "6. Résiliation pendant l’essai → aucun débit.")
    bullet(doc, "7. Fin d’essai + carte encore là + pas d’annulation → statut ACTIF payant.")
    bullet(doc, "8. Parrain : +30 jours sur sa période quand le filleul devient vraiment payant.")
    bullet(doc, "9. Sans conversion / après résiliation → retour Découverte (données conservées).")
    bullet(doc, "10. Échec paiement → past_due · grâce 7 j puis restriction IA.")

    # —— 6 ——
    heading(doc, "6. Essai hybride (durée + plafond d’usage) — EN PRODUCTION", 1)
    add_para(
        doc,
        "Correction importante par rapport aux anciennes versions du document : "
        "l’essai n’offre PAS le quota plein du plan payant. "
        "L’essai suspend uniquement la facturation (0 MAD). Les quotas d’essai sont plafonnés "
        "pour maîtriser le coût OpenAI et créer un argument naturel de passage au payant.",
        size=10,
    )
    table(
        doc,
        ["Plan", "Durée essai", "Crédits pendant essai", "Plaidoiries essai", "Après conversion (payant)"],
        [
            ["Solo", "14 j", "400", "25", "600 · 35"],
            ["Cabinet", "30 j", "1 000", "60", "2 000 · 120"],
            ["Entreprise (pilote qualifié)", "7 à 14 j (calibré)", "1 800", "120", "5 000 · 350"],
        ],
    )
    callout(
        doc,
        "Pendant l’essai — règles commerciales & UX",
        "Aucune vente de pack, aucune bannière d’achat de recharge. "
        "Si le forfait d’essai (crédits / quotas) est atteint : popup « Forfait d’essai épuisé » "
        "avec date de fin — le client peut attendre cette date, ou souscrire via « Voir les tarifs ». "
        "Le repère du jour (ex. Solo essai 35 crédits/jour) reste un choix informé (continuer / demain), "
        "pas un mur et pas un message d’impayé.",
        fill="FEF3C7",
    )
    add_para(
        doc,
        "Repères du jour pendant l’essai (rappel) : Solo 35 · Cabinet 90 · Entreprise 105 "
        "(après conversion payante : 50 / 180 / 300). Voir § 4.2.",
        size=9,
        italic=True,
        color=MUTED,
    )

    # —— 7 ——
    heading(doc, "7. Packs de crédits prépayés — EN PRODUCTION", 1)
    heading(doc, "7.1 But (pourquoi ça existe)", 2)
    add_para(
        doc,
        "Le pack sert quand un cabinet déjà abonné payant a (presque) fini son forfait mensuel "
        "et veut continuer sans attendre le mois suivant ni upgrader immédiatement de plan. "
        "Ce n’est pas une étape de l’essai. Ce n’est pas obligatoire.",
        size=10,
    )

    heading(doc, "7.2 Qui peut acheter", 2)
    table(
        doc,
        ["Statut compte", "Packs visibles ?", "Pourquoi"],
        [
            ["Essai (trial)", "NON", "Le client teste ; pas de vente de recharge"],
            ["Découverte (gratuit)", "NON", "Freemium → upgrade, pas de packs"],
            ["Actif payant Solo / Cabinet / Entreprise", "OUI", "Recharge optionnelle du forfait"],
        ],
    )

    heading(doc, "7.3 Catalogue", 2)
    table(
        doc,
        ["Pack", "Crédits", "Prix", "≈ MAD / crédit", "Vs PAYG (0,25)"],
        [
            ["pack_500", "500", "110 MAD", "0,22", "moins cher"],
            ["pack_1000", "1 000", "200 MAD", "0,20", "moins cher"],
            ["pack_2500", "2 500", "450 MAD", "0,18", "moins cher"],
        ],
    )

    heading(doc, "7.4 Parcours d’achat (obligatoire)", 2)
    bullet(doc, "1. Clic « Acheter » → ouverture d’une fenêtre de paiement (carte) — aucun crédit ajouté.")
    bullet(doc, "2. Confirmation du paiement → alors seulement : crédit du lot + facture téléchargeable.")
    bullet(doc, "3. Chaque lot expire 12 mois après la date d’achat.")
    bullet(doc, "4. Consommation FIFO : le lot qui expire le plus tôt est utilisé en premier.")
    add_para(
        doc,
        "Interdit : créditer au simple clic sans fenêtre de paiement. "
        "Le prestataire cible est le même que l’abonnement (CMI / PayZone — activation opérateur).",
        size=9,
        italic=True,
        color=MUTED,
    )

    heading(doc, "7.5 Exemple pas à pas", 2)
    add_para(doc, "Cabinet Solo ACTIF payant. Début du mois : 600 / 600 crédits inclus.", size=10)
    bullet(doc, "Mi-mois : 400 / 600 utilisés → rien à faire.")
    bullet(doc, "Vers la fin : 580 / 600. Il reste plusieurs rédactions → bannière possible (« Besoin de plus de crédits ? ») car forfait ≥ 80 %.")
    bullet(doc, "Admin achète pack 500 → paie 110 MAD → solde packs = 500 (expire dans 12 mois).")
    bullet(doc, "Prochaines actions : d’abord les 20 restants du forfait, puis le pack.")
    bullet(doc, "Mois suivant : forfait remis à 600 ; le solde pack non consommé reste jusqu’à expiration.")

    heading(doc, "7.6 Nudge anti-récidive", 2)
    add_para(
        doc,
        "Si ≥ 2 achats de pack sur 3 mois glissants : l’UI propose d’abord l’upgrade de plan "
        "(comparatif chiffré), le pack reste disponible en option secondaire — nudge, pas blocage.",
        size=10,
    )

    # —— 8 ——
    heading(doc, "8. Usage à la demande (PAYG) — EN PRODUCTION", 1)
    bullet(doc, "Disponible Solo / Cabinet / Entreprise — pas sur Découverte.")
    bullet(doc, "OFF par défaut. Seul l’admin peut activer (avec ou sans plafond MAD mensuel).")
    bullet(doc, "Tarif : 0,25 MAD / crédit hors forfait (et hors packs).")
    bullet(doc, "Le surplus n’est jamais silencieux : visible dans Plan & usage et sur la facture.")
    bullet(doc, "Si forfait = 0, packs = 0, PAYG OFF → popup « Forfait du mois épuisé » : (1) activer PAYG (2) acheter pack (3) upgrader.")

    # —— 9 ——
    heading(doc, "9. Sièges avocats à la carte (Cabinet) — EN PRODUCTION", 1)
    add_para(
        doc,
        "Sur le plan Cabinet uniquement : l’admin peut ajouter 0 à 5 sièges avocats supplémentaires "
        "à 99 MAD / siège / mois (plafond total jusqu’à 10 avocats) sans sauter directement à Entreprise.",
        size=10,
    )
    bullet(doc, "Impossible de descendre sous le nombre d’avocats déjà actifs.")
    bullet(doc, "Solo et Entreprise : pas cet add-on (Solo = 1+1 fixe ; Entreprise = grille large).")

    # —— 10 ——
    heading(doc, "10. Parrainage cabinet → cabinet — EN PRODUCTION", 1)
    bullet(doc, "Code unique par cabinet (ex. LH-…) + lien d’inscription.")
    bullet(doc, "Filleul : +14 j d’essai à l’entrée Solo/Cabinet (une fois).")
    bullet(doc, "Parrain : +30 j sur sa période quand le filleul devient payant (une fois).")
    bullet(doc, "Anti-abus : pas d’auto-parrainage · plafond 12 invitations / an / parrain.")
    bullet(doc, "Pas de cashback : uniquement des jours d’abonnement.")

    # —— 11 ——
    heading(doc, "11. Factures et gouvernance — EN PRODUCTION", 1)
    bullet(doc, "Paramètres → Mes factures : reçus d’essai (0 MAD) et factures d’abonnement / packs.")
    bullet(doc, "Admin plateforme : détail cabinet (abonnement & factures) + Ops Coach.")
    bullet(doc, "Résiliation payante : motif obligatoire, effet en fin de période déjà payée.")

    # —— 12 ——
    heading(doc, "12. Feuille de route et qualifications commerciales", 1)
    add_para(
        doc,
        "Les items 12.1 et 12.2 sont désormais en production sur lexhub.space. "
        "Le 12.3 (paiement opérateur live, marketplace, barreaux) reste une feuille de route — "
        "l’environnement technique de paiement (CMI / PayZone, webhooks, cartes d’essai) est déjà préparé.",
        size=10,
    )

    heading(doc, "12.1 Qualification des essais Entreprise, Formulaire commercial & Protection Anti-Faux Comptes — EN PRODUCTION", 2)
    add_para(
        doc,
        "Le forfait Entreprise (1 290 MAD HT / mois ou 12 900 MAD / an) constitue le palier supérieur de la grille publique LexHub. "
        "Il octroie jusqu'à 25 collaborateurs (15 avocats + 10 assistants) et un volume massif de 5 000 crédits IA mensuels "
        "(~350 conclusions judiciaires rédigées par GPT-4o).",
        size=10,
    )

    add_para(
        doc,
        "12.1.1 Le risque du libre-service et l'impératif de rupture du self-service",
        bold=True,
        size=10,
        color=NAVY,
    )
    add_para(
        doc,
        "En libre-service automatisé (« Self-Service instantané » sans contrôle humain), le risque financier et opérationnel "
        "serait critique pour LexHub. Un utilisateur malveillant ou un robot pourrait créer des dizaines de comptes jetables "
        "en quelques minutes et consommer des centaines de milliers de tokens OpenAI GPT-4o aux frais exclusifs de la plateforme. "
        "Décision d'architecture produit : le plan Entreprise ne peut JAMAIS être activé en libre-service direct. "
        "Le checkout direct par carte bancaire refuse systématiquement ce plan, et les boutons d'action sur /tarifs "
        "redirigent obligatoirement vers le parcours commercial qualifié.",
        size=10,
    )

    add_para(
        doc,
        "12.1.2 Le formulaire de qualification commerciale (/commercial?intent=enterprise)",
        bold=True,
        size=10,
        color=NAVY,
    )
    add_para(
        doc,
        "Lorsqu'un cabinet manifeste son intérêt pour l'offre Entreprise, il accède à l'interface dédiée "
        "sur https://lexhub.space/commercial?intent=enterprise. Le formulaire recueille 7 données professionnelles structurées :",
        size=10,
    )
    bullet(doc, "Nom complet de l'avocat associé référent (ex. Me Mohamed El Amrani).")
    bullet(doc, "E-mail professionnel vérifiable (les noms de domaine d'adresses jetables sont filtrés à la saisie).")
    bullet(doc, "Numéro de téléphone direct (+212 6 XX XX XX XX) pour le contact vocal de cadrage.")
    bullet(doc, "Nom officiel du cabinet ou de la société civile professionnelle d'avocats (SCPA).")
    bullet(doc, "Ville d'exercice et barreau de rattachement (Casablanca, Rabat, Tanger, Marrakech, Fès, etc.).")
    bullet(doc, "Nombre d'avocats associés et collaborateurs (calibrage de l'espace de travail).")
    bullet(doc, "Message et contexte du besoin (matières juridiques traitées, volume prévisionnel de dossiers).")
    add_para(
        doc,
        "Flux technique : la soumission du formulaire n'active AUCUN compte utilisateur automatique. "
        "Elle enregistre une entrée dans la table relationnelle PostgreSQL commercial_leads avec le statut NOUVEAU. "
        "La demande apparaît instantanément dans la console d'administration plateforme (/admin/leads) "
        "pour prise en charge par l'équipe commerciale et technique de WEBVOICE.",
        size=10,
    )

    add_para(
        doc,
        "12.1.3 Les deux piliers de protection mathématique et déontologique contre les faux comptes",
        bold=True,
        size=10,
        color=NAVY,
    )
    add_para(
        doc,
        "Pour éliminer tout risque de dérive financière causée par de faux comptes tout en assurant une expérience "
        "fluide aux véritables cabinets, LexHub déploie un système de protection en deux piliers complémentaires :",
        size=10,
    )

    callout(
        doc,
        "Pilier 1 — Vérification d'authenticité par l'annuaire officiel du Barreau (KYC léger déontologique)",
        "Pourquoi un simple filtre téléphonique ou un e-mail ne suffit pas : n'importe quel fraudeur peut générer un e-mail temporaire "
        "ou louer un numéro VoIP virtuel. Cependant, il est strictement impossible de fabriquer une inscription légale au Barreau.\n"
        "La garantie de l'Ordre des Avocats : au Maroc, l'exercice de la profession d'avocat est régi par la loi n° 28-08. "
        "Chaque avocat en exercice est obligatoirement inscrit au tableau officiel de l'Ordre des Avocats de son barreau "
        "(Casablanca, Rabat, etc.). Ces tableaux officiels sont publics et vérifiables en ligne ou auprès des ordres.\n"
        "Protocole d'audit commercial (5 minutes chrono) : dès notification d'un nouveau lead, le conseiller LexHub "
        "vérifie en quelques instants l'existence réelle de l'avocat et du cabinet sur le tableau officiel de son barreau. "
        "Si l'identité ne correspond à aucun avocat en exercice, la demande est rejetée immédiatement : AUCUN compte n'est ouvert, "
        "AUCUN crédit d'IA n'est consommé. Pour les cabinets légitimes, un court appel de 5 minutes valide le projet, "
        "et l'activation du pilote est effectuée manuellement par l'administrateur plateforme (/admin/cabinets).",
        fill="EEF2FF",
    )

    callout(
        doc,
        "Pilier 2 — Le « Double Verrou » Anti-Abus (Période resserrée de 7 jours + Plafond strict de crédits Fair-Use)",
        "Pourquoi borner l'essai pilote à 7 jours (et non 30 jours) : en SaaS B2B juridique, les études de référence "
        "en Product-Led Growth (PLG) prouvent qu'un essai de 30 jours conduit à la procrastination : l'avocat reporte le test "
        "à la semaine suivante et le contact commercial s'effiloche (taux de conversion divisé par 3). "
        "À l'inverse, une fenêtre resserrée de 7 jours (renouvelable exceptionnellement à 14 jours si le cabinet le justifie) "
        "crée un sentiment d'urgence professionnelle vertueux : le cabinet mobilise son équipe pour tester 2 à 3 dossiers réels "
        "dès la première semaine, sous l'accompagnement personnalisé du conseiller.\n"
        "Le plafond strict de crédits IA (Fair-Use) : même lorsqu'un cabinet authentifié est activé en pilote Entreprise, "
        "il ne dispose jamais d'une génération illimitée. Son compte d'essai est bridé à un quota de test (1 800 crédits max "
        "au lieu des 5 000 du plan payé). Dès que ce plafond est atteint, l'IA se bloque automatiquement et invite à activer "
        "l'abonnement définitif. Mathématiquement, le coût d'API maximal absorbé par LexHub pendant l'essai reste borné "
        "à quelques dirhams, rendant toute prédation financière rigoureusement impossible.",
        fill="FEF3C7",
    )

    heading(doc, "12.2 Palier « Sur mesure » — EN PRODUCTION", 2)
    add_para(
        doc,
        "Au-delà de 15 avocats (grands cabinets, plusieurs villes, contrat spécial), la grille publique "
        "(Découverte, Solo, Cabinet, Entreprise) ne suffit plus. Une 5ᵉ case « Sur mesure / Appelez-nous » "
        "est affichée sur /tarifs, sans prix public et sans bouton « payer tout de suite ». "
        "Le devis se fait à la main via https://lexhub.space/commercial?intent=custom. "
        "Les demandes sont visibles dans l’admin plateforme (Demandes).",
        size=10,
    )

    heading(doc, "12.3 Autres pistes moyen / long terme (PAS encore produit)", 2)
    bullet(doc, "Activation opérateur CMI / PayZone (paiement réel unifié abo + packs) — l’environnement technique et les webhooks stub sont déjà en place.")
    bullet(doc, "Alertes d’usage faible + suivi proactif Entreprise (rétention).")
    bullet(doc, "Marketplace de modèles / modules payants.")
    bullet(doc, "Partenariats barreaux / ambassadeurs.")

    # —— 13 ——
    heading(doc, "13. Synthèse pour décideur", 1)
    add_para(
        doc,
        "LexHub monétise un SaaS juridique marocain par abonnement (cœur du CA), protège la marge IA "
        "par quotas et fair-use informé, et capture l’expansion via packs, PAYG et sièges. "
        "Le cadre méthodologique (PLG/freemium, GBB, hybrid pricing, hybrid trial, unit economics, "
        "Lean/Agile, land & expand, referral) et les formules § 1.2 rendent ces choix auditables — "
        "pas une grille inventée pour la soutenance.",
        size=10,
    )
    table(
        doc,
        ["Thème", "Statut", "Message clé"],
        [
            ["Tarifs 0 / 299 / 699 / 1 290", "Production", "Grille publique + annuel"],
            ["Essai plafonné", "Production", "0 MAD + quotas réduits (pas illimité)"],
            ["Repère IA du jour (choix)", "Production", "Tous plans · essai ou payé · continuer / demain"],
            ["Popup forfait essai / mois épuisé", "Production", "Guidance claire (tarifs / PAYG / packs)"],
            ["Packs prépayés", "Production", "Actif payant seulement · paiement puis crédit · 12 mois"],
            ["PAYG 0,25 MAD", "Production", "OFF par défaut · jamais silencieux"],
            ["Sièges +99 MAD (Cabinet)", "Production", "Expansion sans saut Entreprise"],
            ["Parrainage +14 / +30 j", "Production", "Récompense au paiement réel"],
            ["Qualification Entreprise", "Production", "Formulaire /commercial · pas d’essai instantané · KYC Barreau · Double verrou 7 j + plafond"],
            ["Palier Sur mesure", "Production", "5ᵉ case Appelez-nous · devis, pas de prix public"],
            ["Méthodes § 1.1–1.2", "Documenté", "PLG, GBB, hybrid pricing, unit economics, Agile"],
        ],
    )

    add_para(
        doc,
        "En résumé : abonnement = cœur du CA ; quotas + fair-use = protection de marge ; "
        "packs / PAYG / sièges = expansion. Cadre méthodologique et formules § 1.1–1.2 = "
        "choix auditables, pas une grille inventée pour la soutenance.",
        size=10,
    )

    hrule(doc)
    add_para(
        doc,
        "LexHub · WEBVOICE / ENSA · Document généré pour diffusion — vérifier toujours sur https://lexhub.space "
        "en cas de doute sur un chiffre vivant.",
        size=9,
        italic=True,
        color=MUTED,
        align=WD_ALIGN_PARAGRAPH.CENTER,
    )

    # Sorties
    OUT_PFA.mkdir(parents=True, exist_ok=True)
    OUT_DESKTOP.mkdir(parents=True, exist_ok=True)
    OUT_DESKTOP_ROOT.mkdir(parents=True, exist_ok=True)
    name = "Proposition_plan_rentabilisation_LexHub_COMPLET.docx"
    paths = [
        OUT_PFA / name,
        OUT_REPO / "01_Proposition_plan_rentabilisation_LexHub_v5.docx",
        OUT_DESKTOP / "01_Proposition_plan_rentabilisation_LexHub_v5.docx",
        OUT_DESKTOP / "01_Proposition_plan_rentabilisation_LexHub_v5_MAJ.docx",
        OUT_DESKTOP_ROOT / "01_Proposition_plan_rentabilisation_LexHub_v5.docx",
        OUT_DESKTOP_ROOT / "01_Proposition_plan_rentabilisation_LexHub_v5_MAJ.docx",
    ]
    for path in paths:
        try:
            doc.save(str(path))
            print("saved", path)
        except PermissionError:
            alt = path.with_name(path.stem + "_NOUVEAU" + path.suffix)
            doc.save(str(alt))
            print("locked → saved", alt)
    return paths


if __name__ == "__main__":
    build()
