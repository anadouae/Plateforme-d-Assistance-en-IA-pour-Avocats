# -*- coding: utf-8 -*-
"""
Livraison encadrant entreprise (Hatim / WEBVOICE) + PPT soutenance PFA.
Sources de vérité : plans API prod https://lexhub.space/api/billing/plans
et code déployé (billing.py, plea-step-carousel, seed_test_accounts).
"""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor, Emu, Inches
from pptx import Presentation
from pptx.dml.color import RGBColor as PptRGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches as PInches, Pt as PPt

OUT = Path(__file__).resolve().parent
LOGO = OUT / "logo-lexhub.png"
LOGO_CUBE = OUT / "logo-cube.png"
NAVY = RGBColor(0x0A, 0x12, 0x28)
GOLD = RGBColor(0xC9, 0xA8, 0x4A)
ORANGE = RGBColor(0xFF, 0x6A, 0x00)
MUTED = RGBColor(0x4A, 0x55, 0x68)

# Grille EXACTE prod (API /api/billing/plans — sept. 2026) — NE PAS RÉGRESSER
PLANS = [
    {
        "name": "Découverte",
        "slug": "free",
        "m": "0 MAD",
        "y": "0 MAD",
        "trial": "Aucun (gratuit permanent)",
        "seats": "1 avocat · 0 assistant",
        "cases": "5 dossiers",
        "plea": "3 plaidoiries / mois",
        "ai": "50 crédits IA / mois",
        "feat": "Dictée · Export Word · ChatGPT léger",
        "pos": "Freemium d'acquisition",
    },
    {
        "name": "Solo",
        "slug": "solo",
        "m": "299 MAD / mois",
        "y": "2 990 MAD / an",
        "trial": "14 jours (avec carte, annulable)",
        "seats": "1 avocat + 1 assistant",
        "cases": "Dossiers illimités",
        "plea": "35 plaidoiries / mois",
        "ai": "600 crédits IA / mois",
        "feat": "Word + PDF · branding · invitations",
        "pos": "Avocat indépendant",
    },
    {
        "name": "Cabinet ★",
        "slug": "pro",
        "m": "699 MAD / mois",
        "y": "6 990 MAD / an",
        "trial": "30 jours (avec carte, annulable)",
        "seats": "Jusqu'à 5 avocats + 3 assistants",
        "cases": "Dossiers illimités",
        "plea": "120 plaidoiries / mois",
        "ai": "2 000 crédits IA / mois · OpenAI premium",
        "feat": "Clé de barre · branding · support prioritaire",
        "pos": "Plan recommandé",
    },
    {
        "name": "Entreprise",
        "slug": "enterprise",
        "m": "1 290 MAD / mois",
        "y": "12 900 MAD / an",
        "trial": "30 jours (avec carte, annulable)",
        "seats": "Jusqu'à 15 avocats + 10 assistants",
        "cases": "Dossiers illimités",
        "plea": "350 plaidoiries / mois",
        "ai": "5 000 crédits fair-use / mois",
        "feat": "Quotas élevés · support prioritaire",
        "pos": "Grands cabinets",
    },
]


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
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), hex_color)
    shd.set(qn("w:val"), "clear")
    tcPr.append(shd)


def table(doc, headers, rows, col_widths=None):
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = "Table Grid"
    for i, h in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell.text = ""
        p = cell.paragraphs[0]
        r = p.add_run(h)
        set_run_font(r, bold=True, size=9, color=RGBColor(0xFF, 0xFF, 0xFF))
        shade(cell, "0A1228")
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            cell = t.rows[ri + 1].cells[ci]
            cell.text = ""
            p = cell.paragraphs[0]
            r = p.add_run(str(val))
            set_run_font(r, size=9)
            if ri % 2:
                shade(cell, "EEF1F8")
    if col_widths:
        for row in t.rows:
            for i, w in enumerate(col_widths):
                row.cells[i].width = Cm(w)
    doc.add_paragraph()
    return t


def add_logo_header(doc, title: str, subtitle: str):
    for s in doc.sections:
        s.top_margin = Cm(1.6)
        s.bottom_margin = Cm(1.6)
        s.left_margin = Cm(2.0)
        s.right_margin = Cm(2.0)

    if LOGO_CUBE.exists():
        doc.add_picture(str(LOGO_CUBE), width=Cm(2.6))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif LOGO.exists():
        doc.add_picture(str(LOGO), width=Cm(3.2))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = t.add_run(title)
    set_run_font(r, size=20, bold=True, color=NAVY)

    s = doc.add_paragraph()
    s.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = s.add_run(subtitle)
    set_run_font(r, size=10, italic=True, color=MUTED)

    line = doc.add_paragraph()
    line.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = line.add_run("LexHub · https://lexhub.space · WEBVOICE · ENSA Tétouan")
    set_run_font(r, size=9, color=GOLD)
    doc.add_paragraph()


# ---------------------------------------------------------------------------
# DOC 1 — Proposition de plan de rentabilisation
# ---------------------------------------------------------------------------
def build_rentabilisation() -> Path:
    doc = Document()
    add_logo_header(
        doc,
        "Proposition de plan de rentabilisation",
        "Offre SaaS LexHub pour cabinets d'avocats marocains — document commercial destinataire : encadrant entreprise",
    )

    add_para(
        doc,
        "Objet. Ce document présente, de façon justifiée et alignée sur la version déployée "
        "en production (https://lexhub.space), le modèle économique retenu : grille tarifaire réelle, "
        "essais liés aux plans payants, logique freemium, et politique de fidélisation / rétention "
        "lorsqu'un client abonné depuis une durée significative demande la résiliation.",
        size=10,
    )
    add_para(
        doc,
        "Principe d'intégrité commerciale. Les prix et durées d'essai ci-dessous sont ceux "
        "configurés dans l'application (service billing + API publique /api/billing/plans). "
        "Aucune grille alternative, aucun essai « aléatoire » et aucun tarif marketing inventé "
        "n'est proposé ici.",
        size=10,
        italic=True,
        color=MUTED,
    )

    heading(doc, "1. Contexte et enjeu de rentabilisation", 1)
    add_para(
        doc,
        "LexHub est un SaaS multi-tenant LegalTech : dictée arabe → correction de forme → "
        "rédaction assistée de plaidoirie → export Word/PDF, au sein d'un espace cabinet "
        "(dossiers, documents, planning, équipe, activité). Le coût variable principal est "
        "lié à la reconnaissance vocale, aux appels modèles et au stockage ; le coût fixe "
        "est l'infrastructure VPS (Docker Compose, PostgreSQL, Redis, objet storage, Caddy).",
        size=10,
    )
    add_para(
        doc,
        "La rentabilisation repose donc sur (a) l'acquisition via un freemium crédible, "
        "(b) la conversion d'essai vers un abonnement mensuel ou annuel, (c) l'upsell Solo → Cabinet → Entreprise "
        "quand l'équipe et les quotas IA augmentent, (d) la réduction du churn par des offres "
        "de fidélité ciblées — sans casser la grille publique.",
        size=10,
    )

    heading(doc, "2. Grille tarifaire déployée (production)", 1)
    table(
        doc,
        ["Plan", "Mensuel", "Annuel", "Essai", "Sièges", "Plaidoiries / mois"],
        [
            [p["name"], p["m"], p["y"], p["trial"].split("(")[0].strip(), p["seats"], p["plea"]]
            for p in PLANS
        ],
    )
    add_para(
        doc,
        "Note annuelle. Le tarif annuel correspond à ~10 mois payés pour 12 mois d'usage "
        "(économie d'environ 2 mois), pratique SaaS standard, déjà codée dans price_mad_yearly.",
        size=9,
        italic=True,
    )

    heading(doc, "3. Détail et justification par plan", 1)
    for p in PLANS:
        add_para(doc, f"{p['name']} ({p['slug']})", bold=True, color=NAVY, size=12)
        add_para(doc, f"Positionnement : {p['pos']}", size=10)
        add_para(
            doc,
            f"Tarif : {p['m']} · {p['y']} · Essai : {p['trial']}. "
            f"{p['seats']} · {p['cases']} · {p['plea']} · {p['ai']}. Fonctions : {p['feat']}.",
            size=10,
        )
        if p["slug"] == "free":
            add_para(
                doc,
                "Justification. Le freemium permanent crée une habitude d'usage (dictée + Word) "
                "sans friction carte. Les quotas bas (dossiers, plaidoiries, IA) poussent naturellement "
                "vers Solo dès qu'un assistant ou un volume réel apparaît.",
                size=10,
                italic=True,
            )
        elif p["slug"] == "solo":
            add_para(
                doc,
                "Justification. Prix d'entrée accessible pour un indépendant (≈ 10 MAD/jour). "
                "Essai 14 jours : assez long pour dicter plusieurs affaires, assez court pour "
                "éviter l'usage prolongé sans conversion. PDF + branding + 1 assistant = valeur "
                "immédiatement perceptible en audience.",
                size=10,
                italic=True,
            )
        elif p["slug"] == "pro":
            add_para(
                doc,
                "Justification. Plan recommandé (is_recommended). Le ticket 699 MAD est cohérent "
                "avec un cabinet de 3–8 personnes qui mutualise la plateforme. Essai 30 jours : "
                "nécessaire pour ancrer l'équipe (invitations, clé de barre, branding). "
                "C'est le plan sur lequel se calcule la marge cible du produit.",
                size=10,
                italic=True,
            )
        else:
            add_para(
                doc,
                "Justification. Volume et sièges élevés (15+10) pour structures multi-équipes. "
                "Quotas IA illimités (soft) et OpenAI premium justifient le premium 1 290 MAD. "
                "Essai 30 jours identique au Cabinet pour ne pas fragmenter le parcours commercial.",
                size=10,
                italic=True,
            )

    heading(doc, "4. Cycle de vie commercial (tel que codé)", 1)
    for i, s in enumerate(
        [
            "Inscription cabinet (OTP e-mail) → accès immédiat (cabinet actif).",
            "Choix / upgrade de plan depuis Paramètres → Abonnement (admin cabinet uniquement).",
            "Essai Solo 14 j ou Cabinet/Entreprise 30 j (carte, annulable) → e-mails de rappel de fin d'essai.",
            "Sans conversion ou après résiliation effective → retour plan Découverte (quotas freemium).",
            "Paiement électronique Maroc (CMI / PayZone) en préparation ; sélection de plan opérationnelle (mode sécurisé mock carte en attendant).",
            "Seuls les admin_cabinet (créateur / coordinateur) paient, changent de plan et téléchargent les factures ; avocats / assistants voient l'état et demandent à l'admin.",
        ],
        1,
    ):
        add_para(doc, f"{i}. {s}", size=10)

    heading(doc, "5. Politique de fidélisation et offres de rétention", 1)
    add_para(
        doc,
        "Objectif. Lorsqu'un client payant depuis une durée significative demande la résiliation "
        "(motifs déjà prévus dans l'app : trop cher, fonctionnalités manquantes, changement d'outil, "
        "pause temporaire, complexité, autre), on propose une offre de rétention avant confirmation "
        "du cancel_at_period_end — sans modifier la grille publique affichée sur /tarifs.",
        size=10,
    )

    heading(doc, "5.1 Critères d'éligibilité (proposition)", 2)
    table(
        doc,
        ["Profil", "Condition minimale", "Offre de rétention proposée"],
        [
            [
                "Client fidèle Solo",
                "≥ 6 mois d'abonnement payant consécutifs",
                "1 mois offert OU -20 % sur le prochain trimestre mensuel (au choix du client)",
            ],
            [
                "Client fidèle Cabinet",
                "≥ 6 mois payants · ≥ 3 sièges utilisés",
                "1 mois offert OU passage temporaire annuel avec 1 mois supplémentaire offert",
            ],
            [
                "Client Entreprise",
                "≥ 6 mois payants",
                "Négociation encadrée : jusqu'à 15 % sur 3 mois OU extension de sièges assistants (+2) pendant 1 mois",
            ],
            [
                "Motif « trop cher »",
                "Tout plan payant · 1ʳᵉ demande de résiliation",
                "Downgrade assisté (Cabinet→Solo ou Solo→Découverte) plutôt qu'une réduction permanente du ticket",
            ],
            [
                "Motif « pause temporaire »",
                "≥ 3 mois payants",
                "Gel 30–60 jours (statut pause) sans perte de données, reprise au même plan",
            ],
            [
                "Win-back (déjà parti)",
                "Retour ≤ 90 jours après fin d'abo",
                "Réactivation avec 14 jours d'essai du dernier plan payant (hors Entreprise sur devis)",
            ],
        ],
    )
    add_para(
        doc,
        "Garde-fous. (1) Une seule offre de rétention par période de 12 mois. "
        "(2) Jamais de prix public différent de la grille (les remises sont des crédits "
        "d'abonnement ou des mois offerts, tracés en facturation). "
        "(3) Après offre refusée → résiliation en fin de période déjà payée (comportement actuel cancel_at_period_end). "
        "(4) Le freemium Découverte reste le filet de sécurité : le cabinet ne perd pas ses dossiers.",
        size=10,
    )

    heading(doc, "5.2 Leviers de rétention produit (déjà dans LexHub)", 2)
    add_para(
        doc,
        "Collecte du motif de résiliation (codes CANCEL_REASON) pour piloter le produit ; "
        "bannières d'essai / d'abonnement ; confirmation modale avant paiement ou annulation ; "
        "factures consultables par l'admin cabinet ; espace admin plateforme (/admin) pour "
        "suivre cabinets, plans et logs.",
        size=10,
    )

    heading(doc, "6. Projection de marge (cadre de décision)", 1)
    add_para(
        doc,
        "Ordre de grandeur illustratif (à affiner avec la compta WEBVOICE) : "
        "un cabinet sur plan Cabinet à 699 MAD/mois couvre largement la part d'infra "
        "attribuable dès quelques dizaines d'abonnés actifs. L'annuel (6 990 MAD) améliore "
        "la trésorerie et réduit le churn. Le freemium n'est pas « gratuit pour toujours sans limite » : "
        "il est plafonné pour rester un tunnel de conversion.",
        size=10,
    )
    table(
        doc,
        ["Indicateur", "Cible indicative an 1"],
        [
            ["Taux de conversion essai → payant", "≥ 25 % (Cabinet recommandé)"],
            ["Part d'abonnements annuels", "≥ 30 % du MRR"],
            ["Churn mensuel payant", "< 5 %"],
            ["Taux d'acceptation offre rétention", "≥ 35 % des demandes d'annulation éligibles"],
            ["Upsell Solo → Cabinet", "≥ 15 % des Solo > 3 mois"],
        ],
    )

    heading(doc, "7. Recommandation à l'encadrant", 1)
    add_para(
        doc,
        "Valider cette grille telle qu'elle est en production (0 / 299 / 699 / 1 290 MAD) "
        "et autoriser la politique de fidélité §5 comme procédure commerciale WEBVOICE, "
        "sans republier de tarifs « promo » sur le site. Priorité produit : finaliser le "
        "paiement CMI/PayZone pour remplacer le mock carte, puis industrialiser les crédits "
        "de rétention dans le module billing.",
        size=10,
    )

    add_para(doc, "Document généré à partir du code et de l'API de production LexHub — septembre 2026.", italic=True, size=9, color=MUTED)
    path = OUT / "01_Proposition_plan_rentabilisation_LexHub.docx"
    doc.save(path)
    return path


# ---------------------------------------------------------------------------
# DOC 2 — Guide utilisation & tests
# ---------------------------------------------------------------------------
def build_guide() -> Path:
    """Délègue au générateur à jour (évite de réécrire d'anciennes grilles)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "generate_guide_utilisation",
        OUT / "generate_guide_utilisation.py",
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod.build()


# (ancien corps du guide supprimé — utiliser generate_guide_utilisation.py)

def build_captures_checklist() -> Path:
    doc = Document()
    add_logo_header(
        doc,
        "Captures d'écran à réaliser pour le rapport PFA",
        "Liste exhaustive — emplacements laissés vides dans le rapport LaTeX (annexes)",
    )
    add_para(
        doc,
        "Consigne. Sur https://lexhub.space, capturer en plein écran (navigateur FR puis éventuellement AR). "
        "Nommer les fichiers exactement comme ci-dessous et les placer dans "
        "docs/rapport-pfa-overleaf2/rapport-pfa/maquettes/ (et copie assets si besoin).",
        size=10,
    )
    table(
        doc,
        ["#", "Fichier cible", "Écran / action", "Compte"],
        [
            ["1", "01-accueil.png", "Landing LexHub (hero + marque)", "Visiteur"],
            ["2", "02-connexion.png", "Page connexion", "Visiteur"],
            ["3", "03-inscription.png", "Inscription / demande OTP", "Visiteur"],
            ["4", "10-tableau-de-bord.png", "Dashboard cabinet", "demo@"],
            ["5", "11-dossiers.png", "Liste dossiers (+ filtre domaine)", "demo@"],
            ["6", "24-dossier-detail.png", "Détail d'un dossier", "demo@"],
            ["7", "13-documents.png", "Espace documents", "demo@"],
            ["8", "14b-plaidoirie-workspace.png", "Atelier : rail Étape X/5 visible", "demo@"],
            ["9", "14c-transcription-fusha.png", "Étape Transcription + orange + contradictions", "demo@"],
            ["10", "19-export-document.png", "Export Word/PDF / aperçu", "demo@"],
            ["11", "15-planning.png", "Planning / échéances", "demo@"],
            ["12", "16-equipe.png", "Équipe + invitations", "demo@"],
            ["13", "17-parametres.png", "Paramètres (onglet abo visible)", "demo@"],
            ["14", "18-join-cabinet.png", "Rejoindre un cabinet (code)", "Visiteur / invite"],
            ["15", "22a-admin-dashboard.png", "Admin plateforme métriques", "admin@webvoice"],
            ["16", "22-admin-cabinets.png", "Liste cabinets admin", "admin@webvoice"],
            ["17", "23-activite-cabinet.png", "Journal d'activité", "demo@"],
            ["18", "tarifs-lexhub.png", "Page /tarifs 4 plans réels", "Visiteur"],
        ],
    )
    add_para(
        doc,
        "Dans le rapport LaTeX, les figures d'annexe sont des cadres « À capturer » : "
        "remplacer par \\includegraphics{…} une fois les PNG déposés.",
        size=10,
        italic=True,
    )
    path = OUT / "03_Liste_captures_UI_rapport_PFA.docx"
    doc.save(path)
    return path


# ---------------------------------------------------------------------------
# PPT soutenance PFA (aligné rapport + prod lexhub.space)
# ---------------------------------------------------------------------------
MAQ = OUT.parent / "maquettes"
NAVY_RGB = (10, 18, 40)
GOLD_RGB = (201, 168, 74)
CREAM_RGB = (250, 248, 243)
DARK_RGB = (30, 40, 55)
MUTED_RGB = (74, 85, 104)
WHITE_RGB = (255, 255, 255)
LINE_RGB = (216, 210, 200)


def _set_run(run, text, size=18, bold=False, color=NAVY_RGB):
    run.text = text
    run.font.size = PPt(size)
    run.font.bold = bold
    run.font.name = "Calibri"
    run.font.color.rgb = PptRGBColor(*color)


def _add_bg(slide, r, g, b):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = PptRGBColor(r, g, b)


def _title_bar(slide, title: str, subtitle=None):
    h = 1.15 if subtitle else 0.95
    box = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, PInches(0), PInches(0), PInches(13.333), PInches(h)
    )
    box.fill.solid()
    box.fill.fore_color.rgb = PptRGBColor(*NAVY_RGB)
    box.line.fill.background()
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    run = p.add_run()
    _set_run(run, "  " + title, size=22 if subtitle else 24, bold=True, color=WHITE_RGB)
    if subtitle:
        p2 = tf.add_paragraph()
        r2 = p2.add_run()
        _set_run(r2, "  " + subtitle, size=12, color=(180, 190, 210))


def _footer(slide, page: int, total: int):
    box = slide.shapes.add_textbox(PInches(0.5), PInches(7.1), PInches(10.5), PInches(0.28))
    r = box.text_frame.paragraphs[0].add_run()
    _set_run(r, "LexHub · ENSA Tétouan · WEBVOICE · Soutenance PFA", size=10, color=MUTED_RGB)
    num = slide.shapes.add_textbox(PInches(11.4), PInches(7.1), PInches(1.5), PInches(0.28))
    nr = num.text_frame.paragraphs[0].add_run()
    _set_run(nr, f"{page} / {total}", size=10, color=MUTED_RGB)
    num.text_frame.paragraphs[0].alignment = PP_ALIGN.RIGHT


def _bullets(slide, items, top=1.25, left=0.55, width=12.2, size=16, gap=9):
    box = slide.shapes.add_textbox(PInches(left), PInches(top), PInches(width), PInches(5.6))
    tf = box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = PPt(gap)
        run = p.add_run()
        _set_run(run, "▸  " + item, size=size, color=DARK_RGB)


def _card(slide, left, top, w, h, fill=WHITE_RGB):
    sh = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, PInches(left), PInches(top), PInches(w), PInches(h)
    )
    sh.fill.solid()
    sh.fill.fore_color.rgb = PptRGBColor(*fill)
    sh.line.color.rgb = PptRGBColor(*LINE_RGB)
    sh.line.width = PPt(1)
    return sh


def _card_text(slide, left, top, w, h, title, lines, title_size=14, body_size=12):
    _card(slide, left, top, w, h)
    tb = slide.shapes.add_textbox(
        PInches(left + 0.18), PInches(top + 0.14), PInches(w - 0.35), PInches(0.35)
    )
    r = tb.text_frame.paragraphs[0].add_run()
    _set_run(r, title, size=title_size, bold=True, color=NAVY_RGB)
    bb = slide.shapes.add_textbox(
        PInches(left + 0.18), PInches(top + 0.5), PInches(w - 0.35), PInches(h - 0.65)
    )
    tf = bb.text_frame
    tf.word_wrap = True
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = PPt(4)
        run = p.add_run()
        _set_run(run, line, size=body_size, color=DARK_RGB)


def _try_pic(slide, path: Path, left, top, width, height=None):
    if not path.exists():
        return False
    if height is None:
        slide.shapes.add_picture(str(path), PInches(left), PInches(top), width=PInches(width))
    else:
        slide.shapes.add_picture(
            str(path), PInches(left), PInches(top), width=PInches(width), height=PInches(height)
        )
    return True


def build_pptx() -> Path:
    prs = Presentation()
    prs.slide_width = PInches(13.333)
    prs.slide_height = PInches(7.5)
    slides_meta: list = []

    def cream():
        s = prs.slides.add_slide(prs.slide_layouts[6])
        _add_bg(s, *CREAM_RGB)
        slides_meta.append(s)
        return s

    def navy():
        s = prs.slides.add_slide(prs.slide_layouts[6])
        _add_bg(s, *NAVY_RGB)
        slides_meta.append(s)
        return s

    # —— 1 Couverture ——
    s = navy()
    if LOGO.exists():
        s.shapes.add_picture(str(LOGO), PInches(5.6), PInches(0.45), width=PInches(2.1))
    box = s.shapes.add_textbox(PInches(0.7), PInches(2.35), PInches(11.9), PInches(3.8))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    _set_run(r, "Soutenance — Projet de Fin d'Année", size=18, color=GOLD_RGB)
    p2 = tf.add_paragraph()
    p2.alignment = PP_ALIGN.CENTER
    p2.space_before = PPt(10)
    r2 = p2.add_run()
    _set_run(
        r2,
        "LexHub — Plateforme d'assistance IA\npour cabinets d'avocats au Maroc",
        size=30,
        bold=True,
        color=WHITE_RGB,
    )
    for line, sz, col in (
        ("De la voix à la plaidoirie officielle — produit en production", 15, (180, 190, 210)),
        ("ENSA Tétouan  ·  WEBVOICE (Tanger)  ·  https://lexhub.space", 15, (180, 190, 210)),
        ("Stagiaire : Douae El Assal", 14, (160, 170, 190)),
        ("Encadrant entreprise : M. Hatim Benhaddou  ·  Tuteur : M. Mohammed Al Achhab", 13, (150, 160, 180)),
    ):
        px = tf.add_paragraph()
        px.alignment = PP_ALIGN.CENTER
        px.space_before = PPt(6)
        rx = px.add_run()
        _set_run(rx, line, size=sz, color=col)
    bar = s.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, PInches(0), PInches(7.05), PInches(13.333), PInches(0.45)
    )
    bar.fill.solid()
    bar.fill.fore_color.rgb = PptRGBColor(*GOLD_RGB)
    bar.line.fill.background()

    # —— 2 Plan ——
    s = cream()
    _title_bar(s, "Plan de la présentation")
    plan = [
        ("01", "Contexte & problématique"),
        ("02", "Objectifs du PFA"),
        ("03", "Positionnement LexHub"),
        ("04", "Acteurs & rôles"),
        ("05", "Architecture technique"),
        ("06", "Pipeline plaidoirie (5 étapes)"),
        ("07", "Cabinet numérique"),
        ("08", "Collaboration & sécurité"),
        ("09", "Abonnement, quotas, parrainage"),
        ("10", "Tests, déploiement, bilan"),
    ]
    for i, (num, title) in enumerate(plan):
        col = i % 2
        row = i // 2
        left = 0.45 + col * 6.4
        top = 1.25 + row * 1.05
        _card(s, left, top, 6.15, 0.9)
        nb = s.shapes.add_textbox(PInches(left + 0.22), PInches(top + 0.25), PInches(0.7), PInches(0.4))
        nr = nb.text_frame.paragraphs[0].add_run()
        _set_run(nr, num, size=18, bold=True, color=GOLD_RGB)
        tb = s.shapes.add_textbox(PInches(left + 1.0), PInches(top + 0.28), PInches(4.9), PInches(0.4))
        tr = tb.text_frame.paragraphs[0].add_run()
        _set_run(tr, title, size=15, bold=True, color=NAVY_RGB)

    # —— 3 Contexte ——
    s = cream()
    _title_bar(s, "1. Contexte et problématique", "Cabinet marocain · charge documentaire · bilinguisme")
    _card_text(
        s,
        0.4,
        1.4,
        6.15,
        5.2,
        "Réalité du terrain",
        [
            "• Production dense : plaidoiries, mémoires, délais",
            "• Circuit artisanal : notes → ressaisie → Word tardif",
            "• Arabe (fusḥā / mixte) + français",
            "• Secret professionnel — données sensibles",
            "• ChatGPT générique ≠ outil de cabinet",
            "  (pas de dossiers, rôles, export officiel)",
            "",
            "WEBVOICE (Tanger) : LegalTech déployable,",
            "démontrable, multi-tenant.",
        ],
    )
    _card_text(
        s,
        6.75,
        1.4,
        6.15,
        5.2,
        "Problématique",
        [
            "Comment concevoir et déployer une plateforme",
            "SaaS multi-cabinets qui :",
            "",
            "• transforme une dictée arabe en document",
            "  de plaidoirie structuré (export officiel) ;",
            "• collabore avec le stagiaire sans exposer",
            "  les brouillons non validés ;",
            "• isole strictement les cabinets ;",
            "• sans que l'IA n'invente le fond juridique ?",
            "",
            "Livrable : https://lexhub.space (prod)",
        ],
        body_size=13,
    )

    # —— 4 Objectifs ——
    s = cream()
    _title_bar(s, "2. Objectifs du PFA", "Alignés sur le rapport — version déployée")
    _bullets(
        s,
        [
            "O1 — Pipeline voix → texte → document (5 étapes guidées)",
            "O2 — Espace cabinet : dossiers, documents, planning, équipe, activité, clé de barre",
            "O3 — Isolation multi-tenant stricte (cabinet_id)",
            "O4 — Rôles : avocat, assistant, admin cabinet, admin plateforme",
            "O5 — Validation / assignation / épinglage avant partage stagiaire",
            "O6 — Abonnement freemium + quotas IA + usage à la demande + parrainage",
            "O7 — Production TLS, e-mails, temps réel, export Word/PDF sur lexhub.space",
        ],
        size=15,
        gap=8,
    )

    # —— 5 Positionnement ——
    s = cream()
    _title_bar(s, "3. Positionnement LexHub", "Pas un chatbot — une plateforme de cabinet")
    _card_text(
        s,
        0.4,
        1.4,
        4.05,
        5.2,
        "LexHub fait",
        [
            "• Dictée → correction forme → document",
            "• Dossiers, pièces, planning liés",
            "• Rôles & validation contrôlée",
            "• Export Word / PDF charte cabinet",
            "• Quotas, abonnement, parrainage",
            "• Isolation multi-tenant",
        ],
    )
    _card_text(
        s,
        4.65,
        1.4,
        4.05,
        5.2,
        "LexHub ne fait pas",
        [
            "• Remplacer le conseil juridique",
            "• Inventer articles / faits / montants",
            "• ERP facturation cabinet",
            "• Substitut à Mahakim",
            "• Lecture des dossiers par",
            "  l'admin plateforme",
        ],
    )
    _card_text(
        s,
        8.9,
        1.4,
        4.0,
        5.2,
        "Promesse",
        [
            "Gagner du temps sur la",
            "rédaction sous pression,",
            "avec contrôle permanent",
            "de l'avocat.",
            "",
            "L'avocat reste seul",
            "responsable du contenu",
            "plaidé ou déposé.",
        ],
    )

    # —— 6 Acteurs ——
    s = cream()
    _title_bar(s, "4. Acteurs de la version déployée")
    actors = [
        ("Admin cabinet", "Avocat + responsable : produit, équipe, abo, branding, parrainage, zone sensible"),
        ("Avocat", "Dicter, relire, valider, assigner, exporter, dossiers, clé de barre ; quitter son compte"),
        ("Assistant", "Plaidoiries validées / assignées, dépôt pièces ; pas d'IA lourde ; peut quitter"),
        ("Admin plateforme", "Suspendre / réactiver / purger cabinets — sans lire les dossiers clients"),
    ]
    for i, (role, desc) in enumerate(actors):
        y = 1.25 + i * 1.25
        _card(s, 0.45, y, 12.4, 1.1)
        a = s.shapes.add_textbox(PInches(0.7), PInches(y + 0.18), PInches(3.2), PInches(0.7))
        ar = a.text_frame.paragraphs[0].add_run()
        _set_run(ar, role, size=15, bold=True, color=NAVY_RGB)
        b = s.shapes.add_textbox(PInches(4.0), PInches(y + 0.22), PInches(8.5), PInches(0.7))
        br = b.text_frame.paragraphs[0].add_run()
        _set_run(br, desc, size=13, color=DARK_RGB)

    # —— 7 Architecture ——
    s = cream()
    _title_bar(s, "5. Architecture technique", "Stack de production")
    _card_text(
        s,
        0.4,
        1.35,
        6.15,
        5.3,
        "Couches",
        [
            "Frontend — Next.js, TypeScript, Tailwind, FR/AR",
            "API — FastAPI, SQLAlchemy, Alembic, JWT",
            "Workers — Celery (OCR, jobs longs)",
            "Données — PostgreSQL, Redis, stockage objet",
            "Voix — STT cloud + correction forme locale",
            "IA — routeur de modèles, anti-invention",
            "Export — Word / PDF (arabe, en-tête)",
            "Infra — Docker Compose, Caddy, VPS",
        ],
        body_size=13,
    )
    _card_text(
        s,
        6.75,
        1.35,
        6.15,
        5.3,
        "Principes",
        [
            "• Multi-tenant : filtre cabinet_id partout",
            "• RBAC par rôle applicatif",
            "• Temps réel : WebSocket + Redis",
            "• E-mails OTP / alertes (domaine LexHub)",
            "• CI : GitHub Actions → images GHCR",
            "• HTTPS / TLS via Caddy",
            "",
            "URL : https://lexhub.space",
        ],
        body_size=13,
    )

    # —— 8 Pipeline ——
    s = cream()
    _title_bar(s, "6. Cœur métier — 5 étapes plaidoirie", "Ordre déployé (rail Étape X/5)")
    steps = [
        ("1", "Dossier & pièces", "Affaire, type, pièces"),
        ("2", "Dictée", "Micro / fichier arabe"),
        ("3", "Transcription", "Brut · Corriger · orange"),
        ("4", "Rédaction IA", "Structure · valider"),
        ("5", "Export", "Word · PDF · modèle"),
    ]
    for i, (n, t, d) in enumerate(steps):
        left = 0.35 + i * 2.55
        _card(s, left, 1.4, 2.4, 2.55)
        nb = s.shapes.add_textbox(PInches(left + 0.15), PInches(1.55), PInches(2.1), PInches(0.4))
        nr = nb.text_frame.paragraphs[0].add_run()
        _set_run(nr, n, size=22, bold=True, color=GOLD_RGB)
        tb = s.shapes.add_textbox(PInches(left + 0.12), PInches(2.15), PInches(2.15), PInches(1.4))
        tf = tb.text_frame
        tf.word_wrap = True
        r1 = tf.paragraphs[0].add_run()
        _set_run(r1, t, size=13, bold=True, color=NAVY_RGB)
        p2 = tf.add_paragraph()
        r2 = p2.add_run()
        _set_run(r2, d, size=12, color=DARK_RGB)
    _card_text(
        s,
        0.4,
        4.2,
        12.5,
        2.4,
        "Garde-fous IA",
        [
            "Correction de forme = orthographe / fusḥā — pas de résumé inventé. "
            "Composition : si un fait, article ou montant manque dans la dictée, il n'est pas inventé — manques signalés. "
            "Marques orange = substitutions STT à relire. Contrôle contradictions (dates, noms, montants).",
        ],
        body_size=14,
    )

    # —— 9 Maquette produit ——
    s = cream()
    _title_bar(s, "6bis. Aperçu produit", "Atelier plaidoirie & tableau de bord")
    img1 = MAQ / "14b-plaidoirie-workspace.png"
    img2 = MAQ / "10-tableau-de-bord.png"
    if img1.exists():
        _try_pic(s, img1, 0.35, 1.3, 6.2, 5.4)
    else:
        _card_text(s, 0.35, 1.3, 6.2, 5.4, "Workspace plaidoirie", ["(maquette 14b)"])
    if img2.exists():
        _try_pic(s, img2, 6.8, 1.3, 6.1, 5.4)
    else:
        _card_text(s, 6.8, 1.3, 6.1, 5.4, "Tableau de bord", ["(maquette 10)"])

    # —— 10 Cabinet ——
    s = cream()
    _title_bar(s, "7. Espace cabinet numérique", "Autour du cœur plaidoirie")
    _bullets(
        s,
        [
            "Menu latéral : Plaidoirie · Dossiers · Documents · Planning · Activité · Équipe (admin)",
            "En-tête : recherche Ctrl+K · notifications · abo (admin) · aide · thème · paramètres · FR/AR",
            "Dossiers : domaine juridique, filtre, pièces, clé de barre (fiche orale IA — pas un mot de passe)",
            "Documents : OCR + synthèse sourcée · Planning lié aux affaires · Journal d'activité",
            "Paramètres : Général · Cabinet · Plan & usage · Sécurité · Zone sensible",
        ],
        size=15,
        gap=10,
    )

    # —— 11 Collab / sécu ——
    s = cream()
    _title_bar(s, "8. Collaboration & sécurité")
    _card_text(
        s,
        0.4,
        1.35,
        6.15,
        5.3,
        "Collaboration",
        [
            "• Brouillon invisible pour l'assistant",
            "• Valider → visible cabinet",
            "• Assigner → notification ciblée",
            "  (+ validation auto si besoin)",
            "• Épingler (pin) sur pièce validée",
            "• WebSocket + e-mails transactionnels",
        ],
        body_size=13,
    )
    _card_text(
        s,
        6.75,
        1.35,
        6.15,
        5.3,
        "Sécurité",
        [
            "• JWT / sessions · rate limiting",
            "• Isolation cabinet_id (preuve : Rabat ≠ Atlas)",
            "• OTP inscription / e-mail",
            "• Audit des actions sensibles",
            "• Admin WV : suspendre / purger — sans lire dossiers",
            "• Zone sensible : avocat / assistant / admin cabinet",
        ],
        body_size=13,
    )

    # —— 12 Billing ——
    s = cream()
    _title_bar(s, "9. Abonnement & quotas (production)", "API /api/billing/plans — septembre 2026")
    plans_rows = [
        ("Découverte", "0 MAD", "3 / 50", "—"),
        ("Solo", "299 / mois", "35 / 600", "14 j"),
        ("Cabinet ★", "699 / mois", "120 / 2 000", "30 j"),
        ("Entreprise", "1 290 / mois", "350 / 5 000", "30 j"),
    ]
    headers = ("Plan", "Prix", "Plaidoiries / crédits IA", "Essai")
    for j, h in enumerate(headers):
        x = 0.45 + j * 3.15
        _card(s, x, 1.3, 3.05, 0.55, fill=NAVY_RGB)
        tb = s.shapes.add_textbox(PInches(x + 0.12), PInches(1.4), PInches(2.8), PInches(0.35))
        tr = tb.text_frame.paragraphs[0].add_run()
        _set_run(tr, h, size=12, bold=True, color=WHITE_RGB)
    for i, row in enumerate(plans_rows):
        for j, cell in enumerate(row):
            x = 0.45 + j * 3.15
            y = 1.95 + i * 0.7
            _card(s, x, y, 3.05, 0.6)
            tb = s.shapes.add_textbox(PInches(x + 0.12), PInches(y + 0.14), PInches(2.8), PInches(0.35))
            tr = tb.text_frame.paragraphs[0].add_run()
            _set_run(tr, cell, size=13, bold=(j == 0), color=NAVY_RGB if j == 0 else DARK_RGB)
    tip = s.shapes.add_textbox(PInches(0.5), PInches(4.9), PInches(12.3), PInches(1.8))
    tf = tip.text_frame
    tf.word_wrap = True
    for i, line in enumerate(
        [
            "Usage à la demande : OFF par défaut (~0,25 MAD / crédit hors forfait si activé) — indisponible sur Découverte.",
            "Paiement / changement de plan : admin cabinet uniquement. Environnement CMI / PayZone prêt ; activation opérateur en cours.",
            "Exemples crédits : rédaction ≈ 10 · révision ≈ 5 · clé de barre ≈ 8.",
        ]
    ):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = PPt(6)
        run = p.add_run()
        _set_run(run, "▸  " + line, size=13, color=DARK_RGB)

    # —— 13 Parrainage ——
    s = cream()
    _title_bar(s, "9bis. Parrainage cabinet → cabinet", "Croissance organique déployée")
    _bullets(
        s,
        [
            "Chaque cabinet a un code (ex. LH-…) et un lien d'inscription ?ref=CODE",
            "Visible dans Paramètres → Plan & usage (#parrainage) + section landing",
            "Filleul : +14 jours d'essai au démarrage Solo / Cabinet",
            "Parrain : +30 jours lorsque l'abonnement payant du filleul démarre après l'essai",
            "Anti-abus : pas d'auto-parrainage · plafond 12 / an",
            "Popup produit « Voir mon code » → /settings#parrainage",
        ],
        size=15,
        gap=10,
    )

    # —— 14 Tests / résultats ——
    s = cream()
    _title_bar(s, "10. Tests, déploiement, résultats")
    _card_text(
        s,
        0.4,
        1.35,
        6.15,
        5.3,
        "Validation",
        [
            "• OTP → cabinet actif immédiat",
            "• Pipeline 5 étapes bout-en-bout",
            "• Isolation multi-tenant (Rabat ≠ Atlas)",
            "• Assistant : brouillon invisible",
            "• Quotas / usage à la demande / parrainage",
            "• Zone sensible (avocat + assistant)",
            "• Tests auto : forme arabe, pipeline dictée",
        ],
        body_size=13,
    )
    _card_text(
        s,
        6.75,
        1.35,
        6.15,
        5.3,
        "Livré",
        [
            "• Prod : https://lexhub.space",
            "• Docker Compose + Caddy + TLS",
            "• CI → GHCR (frontend, backend, celery)",
            "• Guide tests + kits plaidoirie",
            "• Rapport PFA + livraison encadrant",
            "",
            "≠ démonstrateur hors-ligne :",
            "produit SaaS opérationnel.",
        ],
        body_size=13,
    )

    # —— 15 Perspectives ——
    s = cream()
    _title_bar(s, "Perspectives", "Évolution produit — pas l'outillage déjà en place")
    _bullets(
        s,
        [
            "Latence & précision STT arabe juridique (lexique cabinet, WER)",
            "Bibliothèque de modèles par domaine + historique de versions",
            "Indicateurs métier · lien planning ↔ audience ↔ plaidoirie",
            "Activer paiement opérateur CMI / PayZone (env. technique prêt)",
            "Confidentialité renforcée (rétention audio, politiques de purge)",
            "À plus long terme : signature électronique, échanges judiciaires si APIs",
        ],
        size=15,
        gap=10,
    )

    # —— 16 Closing ——
    s = navy()
    if LOGO.exists():
        s.shapes.add_picture(str(LOGO), PInches(5.6), PInches(1.15), width=PInches(2.1))
    box = s.shapes.add_textbox(PInches(0.8), PInches(3.2), PInches(11.7), PInches(3.2))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    _set_run(r, "Merci de votre attention", size=34, bold=True, color=WHITE_RGB)
    p2 = tf.add_paragraph()
    p2.alignment = PP_ALIGN.CENTER
    p2.space_before = PPt(14)
    r2 = p2.add_run()
    _set_run(r2, "Questions  ·  Démonstration sur https://lexhub.space", size=18, color=GOLD_RGB)
    p3 = tf.add_paragraph()
    p3.alignment = PP_ALIGN.CENTER
    p3.space_before = PPt(18)
    r3 = p3.add_run()
    _set_run(
        r3,
        "Douae El Assal  ·  ENSA Tétouan  ·  WEBVOICE  ·  LexHub",
        size=13,
        color=(160, 170, 190),
    )

    total = len(slides_meta)
    for i, slide in enumerate(slides_meta):
        # skip navy cover/closing heavy gold bar pages for footer style; still number cream slides
        if i == 0 or i == total - 1:
            continue
        _footer(slide, i + 1, total)

    path = OUT / "04_Soutenance_PFA_LexHub.pptx"
    try:
        prs.save(path)
    except PermissionError:
        alt = OUT / "04_Soutenance_PFA_LexHub_v2.pptx"
        prs.save(alt)
        return alt
    # copie Bureau (si possible)
    desk = Path.home() / "Desktop" / "04_Soutenance_PFA_LexHub.pptx"
    try:
        prs.save(str(desk))
    except Exception:
        pass
    return path


def main():
    import sys

    only_pptx = "--pptx" in sys.argv or "--soutenance" in sys.argv
    if only_pptx:
        print("OK", build_pptx())
        return
    paths = [
        build_rentabilisation(),
        build_guide(),
        build_captures_checklist(),
        build_pptx(),
    ]
    for p in paths:
        print("OK", p)


if __name__ == "__main__":
    main()
