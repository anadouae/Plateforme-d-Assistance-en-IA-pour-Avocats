# -*- coding: utf-8 -*-
"""
Soutenance PFA LexHub — présentation professionnelle (prod https://lexhub.space).

  python docs/livraison-encadrant-2026/generate_soutenance_pfa.py
"""

from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt, Emu

OUT_DIR = Path(__file__).resolve().parent
ROOT = OUT_DIR.parents[1]
MAQ = ROOT / "docs" / "maquettes"
LOGO = OUT_DIR / "logo-lexhub.png"

NAVY = RGBColor(0x0A, 0x12, 0x28)
GOLD = RGBColor(0xC9, 0xA8, 0x4A)
CREAM = RGBColor(0xFA, 0xF8, 0xF3)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
DARK = RGBColor(0x1A, 0x24, 0x36)
MUTED = RGBColor(0x5A, 0x66, 0x7A)
LINE = RGBColor(0xD8, 0xD2, 0xC8)
SOFT = RGBColor(0xEE, 0xF2, 0xF8)
OK = RGBColor(0x1F, 0x6F, 0x54)

OUTPUTS = [
    OUT_DIR / "04_Soutenance_PFA_LexHub.pptx",
    OUT_DIR / "04_Soutenance_PFA_LexHub_NOUVEAU.pptx",
    ROOT / "docs" / "LexHub_Presentation_Soutenance.pptx",
    Path.home() / "Desktop" / "S9" / "PFA" / "final" / "04_Soutenance_PFA_LexHub.pptx",
    Path.home() / "Desktop" / "S9" / "PFA" / "04_Soutenance_PFA_LexHub.pptx",
]


def R(run, text, size=14, bold=False, color=NAVY, font="Calibri"):
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = font


def blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def bg(slide, color):
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    sh.fill.solid()
    sh.fill.fore_color.rgb = color
    sh.line.fill.background()
    sp = sh._element
    slide.shapes._spTree.remove(sp)
    slide.shapes._spTree.insert(2, sp)


def accent(slide):
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(0.1), Inches(7.5))
    sh.fill.solid()
    sh.fill.fore_color.rgb = GOLD
    sh.line.fill.background()


def header(slide, title, subtitle=None):
    accent(slide)
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.1), Inches(0), Inches(13.233), Inches(0.95 if not subtitle else 1.1))
    bar.fill.solid()
    bar.fill.fore_color.rgb = NAVY
    bar.line.fill.background()
    tb = slide.shapes.add_textbox(Inches(0.45), Inches(0.22), Inches(12.4), Inches(0.45))
    R(tb.text_frame.paragraphs[0].add_run(), title, size=22, bold=True, color=WHITE, font="Georgia")
    if subtitle:
        sb = slide.shapes.add_textbox(Inches(0.45), Inches(0.65), Inches(12.4), Inches(0.35))
        R(sb.text_frame.paragraphs[0].add_run(), subtitle, size=12, color=RGBColor(0xB8, 0xC2, 0xD4))
    return 1.25 if subtitle else 1.15


def footer(slide, n, total):
    box = slide.shapes.add_textbox(Inches(0.4), Inches(7.15), Inches(10.8), Inches(0.25))
    R(box.text_frame.paragraphs[0].add_run(), "LexHub · lexhub.space · ENSA Tétouan · WEBVOICE · PFA 2026", size=10, color=MUTED)
    num = slide.shapes.add_textbox(Inches(11.5), Inches(7.15), Inches(1.4), Inches(0.25))
    p = num.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.RIGHT
    R(p.add_run(), f"{n} / {total}", size=10, color=MUTED)


def cream(prs):
    s = blank(prs)
    bg(s, CREAM)
    return s


def navy_slide(prs):
    s = blank(prs)
    bg(s, NAVY)
    return s


def card(slide, left, top, w, h, fill=WHITE):
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(w), Inches(h))
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    sh.line.color.rgb = LINE
    sh.line.width = Pt(1)
    return sh


def card_title_body(slide, left, top, w, h, title, lines, ts=13, bs=12):
    card(slide, left, top, w, h)
    t = slide.shapes.add_textbox(Inches(left + 0.16), Inches(top + 0.12), Inches(w - 0.3), Inches(0.32))
    R(t.text_frame.paragraphs[0].add_run(), title, size=ts, bold=True, color=NAVY, font="Georgia")
    b = slide.shapes.add_textbox(Inches(left + 0.16), Inches(top + 0.46), Inches(w - 0.3), Inches(h - 0.58))
    tf = b.text_frame
    tf.word_wrap = True
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(3)
        R(p.add_run(), line, size=bs, color=DARK)


def bullets(slide, items, top, left=0.45, width=12.4, size=14, gap=7):
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(5.5))
    tf = box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(gap)
        R(p.add_run(), "▸  " + item, size=size, color=DARK)


def pic(slide, path: Path, left, top, w, h):
    card(slide, left - 0.04, top - 0.04, w + 0.08, h + 0.08)
    if path.exists():
        slide.shapes.add_picture(str(path), Inches(left), Inches(top), width=Inches(w), height=Inches(h))
    else:
        ph = slide.shapes.add_textbox(Inches(left), Inches(top + h / 2 - 0.15), Inches(w), Inches(0.3))
        ph.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
        R(ph.text_frame.paragraphs[0].add_run(), path.name, size=11, color=MUTED)


def icon_chip(slide, left, top, label, sub=""):
    card(slide, left, top, 2.35, 1.35, fill=SOFT)
    t = slide.shapes.add_textbox(Inches(left + 0.12), Inches(top + 0.28), Inches(2.1), Inches(0.45))
    R(t.text_frame.paragraphs[0].add_run(), label, size=13, bold=True, color=NAVY)
    if sub:
        s = slide.shapes.add_textbox(Inches(left + 0.12), Inches(top + 0.75), Inches(2.1), Inches(0.45))
        tf = s.text_frame
        tf.word_wrap = True
        R(tf.paragraphs[0].add_run(), sub, size=11, color=MUTED)


def build():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    slides = []

    def add(s):
        slides.append(s)
        return s

    # —— 1 Couverture ——
    s = add(navy_slide(prs))
    if LOGO.exists():
        s.shapes.add_picture(str(LOGO), Inches(5.55), Inches(0.55), width=Inches(2.2))
    box = s.shapes.add_textbox(Inches(0.7), Inches(2.5), Inches(11.9), Inches(3.8))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    R(p.add_run(), "SOUTENANCE — PROJET DE FIN D’ANNÉE", size=14, color=GOLD)
    p2 = tf.add_paragraph()
    p2.alignment = PP_ALIGN.CENTER
    p2.space_before = Pt(10)
    R(p2.add_run(), "LexHub", size=44, bold=True, color=WHITE, font="Georgia")
    p3 = tf.add_paragraph()
    p3.alignment = PP_ALIGN.CENTER
    p3.space_before = Pt(8)
    R(
        p3.add_run(),
        "SaaS d’assistance IA pour cabinets d’avocats au Maroc\n"
        "De la dictée et des pièces à la plaidoirie officielle — en production",
        size=15,
        color=RGBColor(0xC4, 0xCC, 0xD8),
    )
    for line, sz in (
        ("https://lexhub.space", 14),
        ("ENSA Tétouan  ·  WEBVOICE (Tanger)", 13),
        ("Douae El Assal  ·  Encadrant : M. Hatim Benhaddou  ·  Tuteur : M. Mohammed Al Achhab", 12),
    ):
        px = tf.add_paragraph()
        px.alignment = PP_ALIGN.CENTER
        px.space_before = Pt(6)
        R(px.add_run(), line, size=sz, color=RGBColor(0xA0, 0xAA, 0xBC))
    g = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(7.05), Inches(13.333), Inches(0.45))
    g.fill.solid()
    g.fill.fore_color.rgb = GOLD
    g.line.fill.background()

    # —— 2 Plan ——
    s = add(cream(prs))
    top = header(s, "Plan", "Une idée = une slide — produit réel déployé")
    plan = [
        ("01", "Contexte & problématique"),
        ("02", "Objectifs livrés"),
        ("03", "Positionnement LexHub"),
        ("04", "Cœur : aide IA à l’avocat"),
        ("05", "Dossier : données & utilité"),
        ("06", "Documents & synthèse"),
        ("07", "Équipe & accès"),
        ("08", "Architecture"),
        ("09", "Tarifs, essai, crédits"),
        ("10", "Packs, sièges, parrainage"),
        ("11", "Sécurité & déploiement"),
        ("12", "Bilan & perspectives"),
    ]
    for i, (num, title) in enumerate(plan):
        col, row = i % 3, i // 3
        left, y = 0.4 + col * 4.25, top + 0.15 + row * 1.35
        card(s, left, y, 4.05, 1.15)
        nb = s.shapes.add_textbox(Inches(left + 0.18), Inches(y + 0.32), Inches(0.7), Inches(0.4))
        R(nb.text_frame.paragraphs[0].add_run(), num, size=18, bold=True, color=GOLD, font="Georgia")
        tb = s.shapes.add_textbox(Inches(left + 0.95), Inches(y + 0.38), Inches(2.9), Inches(0.5))
        R(tb.text_frame.paragraphs[0].add_run(), title, size=13, bold=True, color=NAVY)

    # —— 3 Contexte ——
    s = add(cream(prs))
    top = header(s, "1. Contexte & problématique", "Barreau marocain · stage WEBVOICE · livrable live")
    card_title_body(
        s, 0.4, top, 6.2, 5.4, "Contexte",
        [
            "• Production écrite dense : plaidoiries, mémoires",
            "• Circuit artisanal : notes → ressaisie → Word",
            "• Bilinguisme arabe / français",
            "• Secret professionnel → isolation cabinet",
            "• ChatGPT générique : pas de dossiers, rôles,",
            "  pièces OCR, export officiel, quotas",
            "",
            "WEBVOICE (Tanger) : voix + web → LegalTech",
            "Livré : LexHub en production (lexhub.space)",
        ],
        bs=13,
    )
    card_title_body(
        s, 6.8, top, 6.1, 5.4, "Problématique",
        [
            "Comment déployer une SaaS multi-cabinets qui :",
            "",
            "1. transforme dictée + pièces en plaidoirie",
            "   structurée (Word/PDF officiel) ;",
            "2. complète les manques via questions ;",
            "3. collabore avec l’assistant sans exposer",
            "   les brouillons ;",
            "4. monétise (quotas, crédits, parrainage) ;",
            "5. sans inventer le fond juridique ?",
        ],
        bs=13,
    )

    # —— 4 Objectifs ——
    s = add(cream(prs))
    top = header(s, "2. Objectifs — tous en production")
    bullets(
        s,
        [
            "Pipeline voix + pièces → questions → rédaction → chat révision → export logo",
            "Espace cabinet : dossiers, documents, planning, activité, clé de barre",
            "Analyse documentaire (synthèse / Q&A) et analyse de dossier (overview)",
            "Équipe : invitations e-mail + code d’adhésion, sièges selon plan",
            "Freemium + essai plafonné + packs (actif payant) + sièges à la carte + PAYG",
            "Parrainage cabinet→cabinet (+14 j / +30 j) · isolation multi-tenant",
            "Prod TLS, OTP, WebSocket, CI/CD sur https://lexhub.space",
        ],
        top=top + 0.1,
        size=14,
        gap=8,
    )

    # —— 5 Positionnement ——
    s = add(cream(prs))
    top = header(s, "3. Positionnement", "Outil de cabinet — pas un chatbot libre")
    card_title_body(s, 0.4, top, 4.05, 5.4, "LexHub fait", [
        "• Dictée Web Speech API native",
        "• Transcription Fusha + surlignage",
        "• Contrôle déterministe contradictions",
        "• Révision par chat assisté",
        "• Export Word (.docx) unique + logo",
        "• Rôles RBAC, validation, équipe",
        "• Quotas, packs FIFO & parrainage",
    ], bs=12)
    card_title_body(s, 4.65, top, 4.05, 5.4, "LexHub ne fait pas", [
        "• Remplacer le conseil juridique",
        "• Inventer faits / articles / montants",
        "• ERP facturation du cabinet",
        "• Remplacer Mahakim",
        "• Lire les dossiers côté",
        "  admin plateforme",
    ], bs=12)
    card_title_body(s, 8.9, top, 4.0, 5.4, "Principe", [
        "L’avocat reste seul",
        "responsable du contenu.",
        "",
        "L’IA structure, propose,",
        "interroge — ne plaide pas",
        "à sa place.",
    ], bs=13)

    # —— 6 Cœur IA ——
    s = add(cream(prs))
    top = header(s, "4. Comment l’IA aide réellement l’avocat", "Parcours déployé — atelier plaidoirie")
    steps = [
        ("1", "Sources", "Dossier + pièces OCR\n+ dictée avocat"),
        ("2", "Analyse", "Manques détectés\narguments / faits"),
        ("3", "Questions", "QCM de clarification\n(max 5)"),
        ("4", "Rédaction", "Structure pro\nanti-invention"),
        ("5", "Chat", "Révision guidée\ncrédits visibles"),
        ("6", "Export", "Aperçu + Word/PDF\nlogo cabinet"),
    ]
    for i, (n, t, d) in enumerate(steps):
        left = 0.35 + i * 2.15
        card(s, left, top, 2.05, 2.55)
        nb = s.shapes.add_textbox(Inches(left + 0.12), Inches(top + 0.15), Inches(1.8), Inches(0.35))
        R(nb.text_frame.paragraphs[0].add_run(), n, size=20, bold=True, color=GOLD, font="Georgia")
        tt = s.shapes.add_textbox(Inches(left + 0.12), Inches(top + 0.55), Inches(1.8), Inches(0.35))
        R(tt.text_frame.paragraphs[0].add_run(), t, size=13, bold=True, color=NAVY)
        bb = s.shapes.add_textbox(Inches(left + 0.12), Inches(top + 1.05), Inches(1.8), Inches(1.3))
        tf = bb.text_frame
        tf.word_wrap = True
        for j, line in enumerate(d.split("\n")):
            p = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
            R(p.add_run(), line, size=11, color=DARK)
    card_title_body(
        s, 0.4, top + 2.8, 12.5, 2.15, "Règle métier",
        [
            "La dictée est la source primaire des faits. Les pièces jointes ancrent les preuves (OCR). "
            "Si une info manque, LexHub ne l’invente pas : il pose des questions, puis compose. "
            "L’avocat édite au chat, voit l’aperçu officiel, télécharge Word ou PDF avec le branding cabinet.",
        ],
        bs=13,
    )

    # —— 7 Maquette ——
    s = add(cream(prs))
    top = header(s, "4bis. Aperçu produit", "Atelier & tableau de bord")
    pic(s, MAQ / "14b-plaidoirie-workspace.png", 0.35, top, 6.2, 5.4)
    pic(s, MAQ / "14c-transcription-fusha.png", 6.8, top, 6.1, 5.4)

    # —— 8 Dossier ——
    s = add(cream(prs))
    top = header(s, "5. Création de dossier — données & utilité", "Identité juridique pour la plaidoirie")
    rows = [
        ("Client / parties", "Noms, rôles, qualités (physique / morale)"),
        ("Tribunal & ville", "Siège + type de juridiction marocaine"),
        ("N° RG / greffe", "Références citées dans l’acte"),
        ("Degré / chambre", "1ère instance, appel, référé…"),
        ("Audience", "1ère audience → planning lié"),
        ("Adversaire", "Partie adverse + domicile"),
    ]
    for i, (k, v) in enumerate(rows):
        y = top + i * 0.8
        card(s, 0.4, y, 12.5, 0.7)
        a = s.shapes.add_textbox(Inches(0.6), Inches(y + 0.18), Inches(3.2), Inches(0.4))
        R(a.text_frame.paragraphs[0].add_run(), k, size=13, bold=True, color=NAVY)
        b = s.shapes.add_textbox(Inches(4.0), Inches(y + 0.18), Inches(8.6), Inches(0.4))
        R(b.text_frame.paragraphs[0].add_run(), v, size=13, color=DARK)

    # —— 9 Documents ——
    s = add(cream(prs))
    top = header(s, "6. Documents & intelligence dossier", "Hors atelier plaidoirie — gain de temps quotidien")
    card_title_body(s, 0.4, top, 6.15, 5.4, "Pièces & module Documents", [
        "• Upload pièces (OCR asynchrone)",
        "• Synthèse sourcée d’un document",
        "  (pas d’affirmation sans ancrage)",
        "• Q&A sur une pièce (crédits ask)",
        "• Peut rattacher à un dossier ou",
        "  zone « Non classé »",
        "",
        "Utilité : lire vite un contrat,",
        "une requête, un PV sans tout",
        "relire manuellement.",
    ], bs=12)
    card_title_body(s, 6.75, top, 6.15, 5.4, "Vue d’ensemble du dossier", [
        "• Analyse de dossier (overview)",
        "  : synthèse transversale des pièces",
        "• Clé de barre : fiche orale IA",
        "  pour préparer l’audience",
        "  (≠ mot de passe)",
        "",
        "Utilité : l’avocat arrive à l’audience",
        "avec les points clés, sans inventer",
        "ce qui n’est pas dans le dossier.",
    ], bs=12)

    # —— 10 Équipe ——
    s = add(cream(prs))
    top = header(s, "7. Gestion d’équipe & accès", "Admin cabinet = avocat + responsable")
    card_title_body(s, 0.4, top, 6.15, 5.4, "Invitations", [
        "1. E-mail d’invitation (rôle choisi",
        "   avocat / assistant) — lien + code",
        "2. Code d’adhésion cabinet (durée",
        "   limitée, approvals contrôlés)",
        "3. Quotas de sièges selon le plan",
        "   (Solo 1+1 · Cabinet 5+3 · …)",
        "",
        "Page Équipe + Paramètres cabinet.",
    ], bs=12)
    card_title_body(s, 6.75, top, 6.15, 5.4, "Visibilité plaidoirie", [
        "• Brouillon : avocat / admin seulement",
        "• Valider → visible aux assistants",
        "• Assigner → notification ciblée",
        "• Épingler (pin) sur pièce validée",
        "",
        "Assistant : pas d’IA lourde ;",
        "peut quitter via Zone sensible.",
        "Admin plateforme : purge cabinets,",
        "sans lire les affaires.",
    ], bs=12)

    # —— 11 Architecture ——
    s = add(cream(prs))
    top = header(s, "8. Architecture technique", "Stack de production")
    card_title_body(s, 0.4, top, 6.15, 5.4, "Couches", [
        "Frontend — Next.js 14, TypeScript, FR/AR",
        "API — FastAPI (Python 3.11), JWT, Alembic",
        "Jobs — Celery + Redis (tâches lourdes)",
        "Données — PostgreSQL 15, MinIO (objets)",
        "Voix — Web Speech API W3C native",
        "IA — Prompts déterministes anti-hallucination",
        "Export — Word (.docx) avec armoiries royales",
        "Audit BDD — Adminer via tunnel SSH chiffré",
    ], bs=12)
    card_title_body(s, 6.75, top, 6.15, 5.4, "Garanties", [
        "• Isolation cabinet_id",
        "• RBAC par rôle",
        "• OTP e-mail",
        "• WebSocket temps réel",
        "• Audit actions sensibles",
        "• HTTPS / TLS",
        "",
        "URL : https://lexhub.space",
    ], bs=12)

    # —— 12 Billing ——
    s = add(cream(prs))
    top = header(s, "9. Tarifs, essai hybride & crédits IA", "API live /api/billing/plans")
    headers = ["Plan", "MAD/mois", "Sièges", "Plaidoiries", "Crédits", "Essai"]
    data = [
        ("Découverte", "0", "1", "3", "50", "—"),
        ("Solo", "299", "1+1", "35", "600", "14 j"),
        ("Cabinet ★", "699", "5+3", "120", "2 000", "30 j"),
        ("Entreprise", "1 290", "15+10", "350", "5 000", "30 j"),
    ]
    for j, h in enumerate(headers):
        x = 0.35 + j * 2.15
        card(s, x, top, 2.05, 0.48, fill=NAVY)
        tb = s.shapes.add_textbox(Inches(x + 0.08), Inches(top + 0.1), Inches(1.9), Inches(0.3))
        R(tb.text_frame.paragraphs[0].add_run(), h, size=11, bold=True, color=WHITE)
    for i, row in enumerate(data):
        for j, cell in enumerate(row):
            x = 0.35 + j * 2.15
            y = top + 0.58 + i * 0.62
            card(s, x, y, 2.05, 0.55)
            tb = s.shapes.add_textbox(Inches(x + 0.08), Inches(y + 0.12), Inches(1.9), Inches(0.35))
            R(tb.text_frame.paragraphs[0].add_run(), cell, size=12, bold=(j == 0), color=NAVY if j == 0 else DARK)
    tip = s.shapes.add_textbox(Inches(0.4), Inches(top + 3.25), Inches(12.5), Inches(2.3))
    tf = tip.text_frame
    tf.word_wrap = True
    for i, line in enumerate([
        "Essai hybride : 0 MAD + plafonds réduits (Solo 400/25 · Cabinet 1 000/60 · Entreprise 1 800/120) — pas le forfait plein",
        "Coûts crédits : polish 1 · ask 2 · clarify 3 · synthèse 4 · révision 5 · analyse / clé 8 · rédaction 10",
        "Ordre de conso : forfait du mois → packs FIFO (12 mois) → PAYG si ON (~0,25 MAD) → sinon blocage clair",
        "Paiement : admin cabinet · CMI/PayZone env. prêt · activation opérateur en cours",
    ]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(5)
        R(p.add_run(), "▸  " + line, size=12, color=DARK)

    # —— 13 Parrainage + rentabilisation ——
    s = add(cream(prs))
    top = header(s, "10. Packs, sièges & parrainage", "Trois objets de facturation + croissance organique")
    card_title_body(s, 0.4, top, 6.15, 5.4, "Packs & sièges (déployé)", [
        "• Packs : 500 / 110 · 1 000 / 200 · 2 500 / 450 MAD",
        "• Uniquement si abonnement ACTIF payant",
        "  (jamais pendant l’essai / Découverte)",
        "• Acheter → fenêtre carte → crédit après paiement",
        "• Expiration 12 mois par lot (FIFO)",
        "• Cabinet : +1 avocat = 99 MAD/mois (0–5 extra)",
        "• PAYG OFF par défaut · jamais silencieux",
    ], bs=12)
    card_title_body(s, 6.75, top, 6.15, 5.4, "Parrainage & logique éco.", [
        "• Code LH-… + lien ?ref=CODE",
        "• Filleul +14 j · parrain +30 j au paiement",
        "• Anti-abus : pas d’auto-ref · max 12/an",
        "• Découverte = acquisition (3/50)",
        "• Solo / Cabinet = cœur de revenus",
        "• Pack = recharge si forfait fini",
        "• Résiliation en fin de période payée",
    ], bs=12)

    # —— 14 Sécurité ——
    s = add(cream(prs))
    top = header(s, "11. Sécurité, tests, déploiement")
    card_title_body(s, 0.4, top, 6.15, 5.4, "Sécurité", [
        "• JWT / sessions · rate limiting",
        "• Multi-tenant (Rabat ≠ Atlas)",
        "• OTP inscription / sensible",
        "• Audit · Zone sensible comptes",
        "• Admin WV : suspendre / purger",
        "  sans ouvrir les dossiers",
    ], bs=12)
    card_title_body(s, 6.75, top, 6.15, 5.4, "Livré", [
        "• Prod : lexhub.space (Caddy TLS)",
        "• CI → images GHCR",
        "• Scénarios rôles + pipeline 5 étapes",
        "• Kits test commercial & famille",
        "• Rapport PFA + guide encadrant",
        "• ≠ démo hors-ligne : SaaS réel",
    ], bs=12)

    # —— 15 Perspectives ——
    s = add(cream(prs))
    top = header(s, "12. Perspectives", "Évolution produit — outillage déjà en place")
    bullets(
        s,
        [
            "Précision / latence STT arabe juridique (lexique cabinet)",
            "Modèles par domaine + historique de versions",
            "Indicateurs métier · planning ↔ audience ↔ plaidoirie",
            "Activer paiement opérateur CMI / PayZone (abo + packs)",
            "Qualifier les essais Entreprise · palier Sur mesure",
            "Rétention audio & politiques de purge renforcées",
        ],
        top=top + 0.15,
        size=15,
        gap=12,
    )

    # —— 16 Closing ——
    s = add(navy_slide(prs))
    if LOGO.exists():
        s.shapes.add_picture(str(LOGO), Inches(5.55), Inches(1.2), width=Inches(2.2))
    box = s.shapes.add_textbox(Inches(0.7), Inches(3.3), Inches(11.9), Inches(3))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    R(p.add_run(), "Merci de votre attention", size=34, bold=True, color=WHITE, font="Georgia")
    p2 = tf.add_paragraph()
    p2.alignment = PP_ALIGN.CENTER
    p2.space_before = Pt(14)
    R(p2.add_run(), "Questions  ·  Démonstration : https://lexhub.space", size=17, color=GOLD)
    p3 = tf.add_paragraph()
    p3.alignment = PP_ALIGN.CENTER
    p3.space_before = Pt(16)
    R(p3.add_run(), "Douae El Assal  ·  ENSA Tétouan  ·  WEBVOICE  ·  LexHub", size=13, color=RGBColor(0xA0, 0xAA, 0xBE))

    total = len(slides)
    for i, slide in enumerate(slides):
        if i in (0, total - 1):
            continue
        footer(slide, i + 1, total)

    saved = []
    for path in OUTPUTS:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            prs.save(str(path))
            saved.append(str(path))
        except Exception as e:
            saved.append(f"FAIL {path.name}: {e}")
    return total, saved


if __name__ == "__main__":
    n, paths = build()
    print(f"Slides: {n}")
    for p in paths:
        print(p)
