# -*- coding: utf-8 -*-
"""
Soutenance PFA LexHub — PPT 16:9 aligné sur Beamer / rapport (SI cabinet + MADI).

  python docs/livraison-encadrant-2026/generate_soutenance_pfa.py
"""

from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

OUT_DIR = Path(__file__).resolve().parent
ROOT = OUT_DIR.parents[1]
DESKTOP_OVERLEAF = Path.home() / "Desktop" / "Soutenance_PFA_LexHub_ENSA_Overleaf"
SHOTS = DESKTOP_OVERLEAF / "screenshots"
if not SHOTS.exists():
    SHOTS = ROOT / "docs" / "soutenance-pfa" / "screenshots"
MAQ = ROOT / "docs" / "maquettes"
LOGO = DESKTOP_OVERLEAF / "logo-lexhub.png"
if not LOGO.exists():
    LOGO = ROOT / "docs" / "soutenance-pfa" / "logo-lexhub.png"

NAVY = RGBColor(0x0A, 0x12, 0x28)
GOLD = RGBColor(0xC9, 0xA8, 0x4A)
CREAM = RGBColor(0xFA, 0xF8, 0xF3)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
DARK = RGBColor(0x1A, 0x24, 0x36)
MUTED = RGBColor(0x5A, 0x66, 0x7A)
LINE = RGBColor(0xD8, 0xD2, 0xC8)
SOFT = RGBColor(0xEE, 0xF2, 0xF8)
OK = RGBColor(0x1F, 0x6F, 0x54)
WARN = RGBColor(0xE0, 0x7B, 0x54)

OUTPUTS = [
    DESKTOP_OVERLEAF / "Soutenance_PFA_LexHub.pptx",
    OUT_DIR / "04_Soutenance_PFA_LexHub.pptx",
    OUT_DIR / "04_Soutenance_PFA_LexHub_NOUVEAU.pptx",
    ROOT / "docs" / "LexHub_Presentation_Soutenance.pptx",
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
    h = 0.95 if not subtitle else 1.1
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.1), Inches(0), Inches(13.233), Inches(h))
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
    R(box.text_frame.paragraphs[0].add_run(), "LexHub · SI cabinet · lexhub.space · ENSA Tétouan · WEBVOICE · PFA 2026", size=10, color=MUTED)
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


def find_shot(*names: str) -> Path:
    for n in names:
        for base in (SHOTS, MAQ, ROOT / "docs" / "soutenance-pfa" / "screenshots"):
            p = base / n
            if p.exists():
                return p
    return SHOTS / names[0]


def pic(slide, path: Path, left, top, w, h, caption: str | None = None):
    """Embed a screenshot; optional French caption under the image."""
    frame_h = h + (0.32 if caption else 0.0)
    card(slide, left - 0.04, top - 0.04, w + 0.08, frame_h + 0.08)
    if path.exists():
        slide.shapes.add_picture(str(path), Inches(left), Inches(top), width=Inches(w), height=Inches(h))
    else:
        ph = slide.shapes.add_textbox(Inches(left), Inches(top + h / 2 - 0.15), Inches(w), Inches(0.3))
        ph.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
        R(ph.text_frame.paragraphs[0].add_run(), path.name, size=11, color=MUTED)
    if caption:
        cap = slide.shapes.add_textbox(Inches(left), Inches(top + h + 0.02), Inches(w), Inches(0.28))
        p = cap.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        R(p.add_run(), caption, size=11, bold=True, color=NAVY)


def build():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    slides = []

    def add(s):
        slides.append(s)
        return s

    # 1 Couverture
    s = add(navy_slide(prs))
    if LOGO.exists():
        s.shapes.add_picture(str(LOGO), Inches(5.55), Inches(0.45), width=Inches(2.2))
    box = s.shapes.add_textbox(Inches(0.7), Inches(2.35), Inches(11.9), Inches(4.2))
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
        "Système d’information de cabinet & assistance IA\n"
        "Droit marocain — dossier + plaidoirie — en production",
        size=15,
        color=RGBColor(0xC4, 0xCC, 0xD8),
    )
    for line, sz in (
        ("https://lexhub.space", 14),
        ("ENSA Tétouan  ·  WEBVOICE (Tanger)", 13),
        ("EL ASSAL Douae  ·  Encadrant : M. Hatim BENHADDOU  ·  Tuteur : Prof. Mohammed AL ACHHAB", 12),
    ):
        px = tf.add_paragraph()
        px.alignment = PP_ALIGN.CENTER
        px.space_before = Pt(6)
        R(px.add_run(), line, size=sz, color=RGBColor(0xA0, 0xAA, 0xBC))
    g = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(7.05), Inches(13.333), Inches(0.45))
    g.fill.solid()
    g.fill.fore_color.rgb = GOLD
    g.line.fill.background()

    # 2 Plan
    s = add(cream(prs))
    top = header(s, "Plan de la soutenance", "Du besoin métier au SI déployé")
    plan = [
        ("01", "Cadrage & problématique"),
        ("02", "Positionnement marché"),
        ("03", "Objectifs PFA"),
        ("04", "Acteurs & RBAC"),
        ("05", "Atelier 5 étapes"),
        ("06", "Dictée & correction"),
        ("07", "Urbanisation MADI"),
        ("08", "Architecture & UML"),
        ("09", "Modèle économique"),
        ("10", "Production & CI/CD"),
        ("11", "Démonstration"),
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

    # 3 Contexte
    s = add(cream(prs))
    top = header(s, "1. Contexte métier", "La plaidoirie : acte oral préparé à l’écrit")
    card_title_body(s, 0.4, top, 6.2, 5.4, "Réalité terrain", [
        "• Circuit artisanal : notes → dictée → ressaisie Word",
        "• Bilinguisme arabe judiciaire / français d’affaires",
        "• Secret professionnel (loi 28-08, art. 30)",
        "• Besoin : un SI de cabinet, pas un chatbot",
        "",
        "Stage WEBVOICE (Tanger) · ENSA Tétouan",
        "1er juil. – 31 août 2026",
        "Livré : https://lexhub.space",
    ], bs=13)
    card_title_body(s, 6.8, top, 6.1, 5.4, "Problématique", [
        "Comment concevoir et mettre en production",
        "un SaaS multi-cabinets où :",
        "",
        "1. l’avocat mène un atelier en 5 étapes ;",
        "2. l’assistant ne voit que le validé ;",
        "3. l’abonnement est opérationnel ;",
        "4. l’IA n’invente aucun fait juridique ?",
    ], bs=13)

    # 4 Marché
    s = add(cream(prs))
    top = header(s, "2. Positionnement marché", "AS-IS → écart → TO-BE")
    for i, (lab, sub, fill) in enumerate([
        ("AS-IS", "Outils en silos", SOFT),
        ("ÉCART", "Process non uni", RGBColor(0xFD, 0xEE, 0xD9)),
        ("TO-BE", "SI LexHub", RGBColor(0xD8, 0xF3, 0xDC)),
    ]):
        left = 0.6 + i * 4.15
        card(s, left, top, 3.9, 1.35, fill=fill)
        t = s.shapes.add_textbox(Inches(left + 0.2), Inches(top + 0.25), Inches(3.5), Inches(0.4))
        R(t.text_frame.paragraphs[0].add_run(), lab, size=18, bold=True, color=NAVY, font="Georgia")
        u = s.shapes.add_textbox(Inches(left + 0.2), Inches(top + 0.75), Inches(3.5), Inches(0.4))
        R(u.text_frame.paragraphs[0].add_run(), sub, size=13, color=MUTED)
    rows = [
        ("Gestion cabinet", "Dossiers / calendrier", "Pas d’atelier voix → acte"),
        ("Dictée desktop", "Transcription", "Pas SaaS multi-tenant"),
        ("Chatbots IA", "Rédaction fluide", "Invention de faits, pas d’équipe"),
        ("LexHub", "Dossier + plaidoirie + rôles", "Déployé sur lexhub.space"),
    ]
    hy = top + 1.65
    for j, h in enumerate(["Famille", "Force", "Limite"]):
        x = 0.4 + j * 4.2
        card(s, x, hy, 4.05, 0.45, fill=NAVY)
        tb = s.shapes.add_textbox(Inches(x + 0.12), Inches(hy + 0.08), Inches(3.8), Inches(0.3))
        R(tb.text_frame.paragraphs[0].add_run(), h, size=12, bold=True, color=WHITE)
    for i, row in enumerate(rows):
        for j, cell in enumerate(row):
            x = 0.4 + j * 4.2
            y = hy + 0.55 + i * 0.72
            fill = RGBColor(0xFF, 0xF9, 0xC4) if i == 3 else WHITE
            card(s, x, y, 4.05, 0.65, fill=fill)
            tb = s.shapes.add_textbox(Inches(x + 0.12), Inches(y + 0.15), Inches(3.8), Inches(0.4))
            R(tb.text_frame.paragraphs[0].add_run(), cell, size=12, bold=(j == 0 or i == 3), color=NAVY if j == 0 else DARK)

    # 5 Objectifs
    s = add(cream(prs))
    top = header(s, "3. Objectifs du PFA", "Un SI de cabinet — l’IA est un service")
    card_title_body(s, 0.4, top, 7.4, 5.4, "Objectifs livrés", [
        "1. Atelier 5 étapes (dossier → export Word / PDF)",
        "2. Espace cabinet : dossiers, pièces, équipe, planning",
        "3. Rôles : avocat, assistant, admin cabinet, admin plateforme",
        "4. Validation = seuil de visibilité assistant",
        "5. Modèle d’abonnement + production réelle",
    ], bs=14)
    card_title_body(s, 8.0, top, 4.9, 5.4, "Règle d’or", [
        "Postgres = vérité métier",
        "",
        "LLM = proposition,",
        "jamais maître des faits",
        "",
        "L’avocat reste",
        "responsable du contenu",
    ], bs=14)

    # 6 RBAC
    s = add(cream(prs))
    top = header(s, "4. Acteurs & RBAC", "Quatre rôles — moindre privilège")
    roles = [
        ("Avocat", "Dicte, corrige, rédige, valide, exporte"),
        ("Assistant", "Uniquement plaidoiries validées / finalisées"),
        ("Admin cabinet", "Équipe, abonnement, identité visuelle"),
        ("Admin plateforme", "Cabinets / leads — sans lecture des affaires"),
    ]
    for i, (role, desc) in enumerate(roles):
        y = top + i * 1.2
        card(s, 0.4, y, 7.6, 1.05)
        a = s.shapes.add_textbox(Inches(0.6), Inches(y + 0.18), Inches(2.8), Inches(0.35))
        R(a.text_frame.paragraphs[0].add_run(), role, size=14, bold=True, color=NAVY)
        b = s.shapes.add_textbox(Inches(3.5), Inches(y + 0.18), Inches(4.3), Inches(0.7))
        tf = b.text_frame
        tf.word_wrap = True
        R(tf.paragraphs[0].add_run(), desc, size=13, color=DARK)
    card_title_body(s, 8.2, top, 4.7, 5.0, "Cycle de vie", [
        "Brouillon → invisible",
        "à l’assistant",
        "",
        "Validée → visible équipe",
        "(validation séparée)",
        "",
        "Export → finalisée",
        "(Word .docx / PDF)",
    ], bs=12)

    # 7 Pipeline 5 étapes
    s = add(cream(prs))
    top = header(s, "5. Cœur produit — cinq étapes", "Dossier → pièces → rédaction → livrable")
    steps = [
        ("1", "Dossier &\npièces"),
        ("2", "Dictée"),
        ("3", "Correction\nde forme"),
        ("4", "Rédaction\nassistée"),
        ("5", "Export\nWord / PDF"),
    ]
    for i, (n, lab) in enumerate(steps):
        left = 0.45 + i * 2.55
        card(s, left, top, 2.4, 2.2, fill=SOFT if i < 4 else RGBColor(0xD8, 0xF3, 0xDC))
        nb = s.shapes.add_textbox(Inches(left + 0.15), Inches(top + 0.25), Inches(2.1), Inches(0.4))
        R(nb.text_frame.paragraphs[0].add_run(), n, size=22, bold=True, color=GOLD, font="Georgia")
        tb = s.shapes.add_textbox(Inches(left + 0.15), Inches(top + 0.85), Inches(2.1), Inches(1.1))
        tf = tb.text_frame
        tf.word_wrap = True
        for j, line in enumerate(lab.split("\n")):
            p = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
            R(p.add_run(), line, size=13, bold=True, color=NAVY)
    card_title_body(s, 0.4, top + 2.5, 12.5, 2.7, "Points clés", [
        "• Étape 1 : identité des parties + pièces OCR ; domaine de plaidoirie lié au dossier",
        "• Étapes 2–3 : micro Web Speech ou Whisper (Firefox inclus) ; Corriger (fautes OK) ; QCM de clarification",
        "• Étapes 4–5 : rédaction ancrée + chat révision ; export Word .docx et PDF (armoiries, charte) ; finalisée après export",
    ], bs=13)

    # 8 Dictée
    s = add(cream(prs))
    top = header(s, "6. Dictée, clarification & révision", "Fidélité des faits · UX claire")
    card_title_body(s, 0.4, top, 6.15, 5.4, "Capture & correction", [
        "• Micro navigateur (Web Speech) ou Whisper (Firefox)",
        "• Fichier : WAV, MP3, OGG, M4A, WebM",
        "• Détection auto FR / AR (sans changer l’UI)",
        "• Bandeau d’écoute + boutons Terminé / Annuler",
        "",
        "Correction de forme (fusḥā)",
        "• Surlignage des substitutions",
        "• Fautes de frappe / STT approximées",
        "• Pas de faux « succès » sur du charabia",
    ], bs=12)
    card_title_body(s, 6.75, top, 6.15, 5.4, "Clarification & assistant", [
        "• QCM 0–5 : dossier anonymisé → LLM → avoc.",
        "• Chat révision : répond + met à jour le doc",
        "• Annuler / Modifier la requête",
        "• Remplit خامساً / لهذه الأسباب si vides",
        "",
        "Ce que l’IA ne fait pas",
        "• Inventer faits, articles, montants",
        "• Remplacer le jugement de l’avocat",
    ], bs=12)

    # 9 MADI
    s = add(cream(prs))
    top = header(s, "7. Urbanisation MADI", "LexHub = SI de cabinet, pas « une appli IA »")
    layers = [
        ("M — Métier", "Dossier → Pièces → Plaidoirie → Équipe → Abonnement"),
        ("A — Applications", "Cases · Documents · Rédaction · Billing · Admin · IA service"),
        ("D — Données", "Postgres (vérité) · MinIO (fichiers) · Redis (files)"),
        ("I — Infrastructure", "Docker / VPS · Caddy TLS · OpenAI (externe)"),
    ]
    for i, (title, body) in enumerate(layers):
        y = top + i * 1.25
        card(s, 0.5, y, 12.3, 1.1, fill=SOFT)
        t = s.shapes.add_textbox(Inches(0.75), Inches(y + 0.18), Inches(3.5), Inches(0.35))
        R(t.text_frame.paragraphs[0].add_run(), title, size=14, bold=True, color=NAVY, font="Georgia")
        b = s.shapes.add_textbox(Inches(4.4), Inches(y + 0.18), Inches(8.1), Inches(0.7))
        tf = b.text_frame
        tf.word_wrap = True
        R(tf.paragraphs[0].add_run(), body, size=13, color=DARK)

    # 10 Architecture
    s = add(cream(prs))
    top = header(s, "8. Architecture déployée", "SaaS multi-tenant — lexhub.space")
    arch = [
        ("Navigateur", "Next.js"),
        ("Caddy", "HTTPS / TLS"),
        ("FastAPI", "Métier + RBAC"),
        ("PostgreSQL", "Vérité métier"),
        ("Redis", "Files / temps réel"),
        ("MinIO", "Fichiers chiffrés"),
    ]
    for i, (a, b) in enumerate(arch):
        col, row = i % 3, i // 3
        left = 0.45 + col * 4.25
        y = top + row * 2.0
        card(s, left, y, 4.05, 1.7)
        t = s.shapes.add_textbox(Inches(left + 0.2), Inches(y + 0.35), Inches(3.6), Inches(0.4))
        R(t.text_frame.paragraphs[0].add_run(), a, size=16, bold=True, color=NAVY, font="Georgia")
        u = s.shapes.add_textbox(Inches(left + 0.2), Inches(y + 0.9), Inches(3.6), Inches(0.45))
        R(u.text_frame.paragraphs[0].add_run(), b, size=13, color=MUTED)
    tip = s.shapes.add_textbox(Inches(0.5), Inches(top + 4.2), Inches(12.3), Inches(1.0))
    tf = tip.text_frame
    tf.word_wrap = True
    R(tf.paragraphs[0].add_run(),
      "Isolation cabinet_id · RBAC (assistant ≠ brouillons) · Whisper ou Web Speech · ports BDD 127.0.0.1 · admin plateforme sans lecture des affaires",
      size=12, color=DARK)

    # 10bis Diagrammes clés (6 séquences principales)
    s = add(cream(prs))
    top = header(s, "8bis. Diagrammes clés", "Six séquences UML — sources PlantUML dans diagrams/")
    seqs = [
        ("Inscription OTP", "request → e-mail → verify → register (Cabinet ACTIVE + essai) → login"),
        ("Login + Turnstile", "captcha-config → login ; Turnstile après 3 échecs → JWT"),
        ("Dictée → rédaction", "STT → polish → clarify → compose → revise"),
        ("Validation / export", "validate / assign → WS ; export Word/PDF → finalized (UI)"),
        ("Documents OCR", "POST /upload → MinIO → extract → extracted_text"),
        ("Facturation", "plans / packs → history (amount > 0 MAD) → PDF facture"),
    ]
    for i, (title, body) in enumerate(seqs):
        col, row = i % 2, i // 2
        left = 0.4 + col * 6.45
        y = top + row * 1.55
        card(s, left, y, 6.25, 1.4, fill=SOFT)
        t = s.shapes.add_textbox(Inches(left + 0.2), Inches(y + 0.2), Inches(5.85), Inches(0.35))
        R(t.text_frame.paragraphs[0].add_run(), title, size=14, bold=True, color=NAVY, font="Georgia")
        b = s.shapes.add_textbox(Inches(left + 0.2), Inches(y + 0.65), Inches(5.85), Inches(0.55))
        tf = b.text_frame
        tf.word_wrap = True
        R(tf.paragraphs[0].add_run(), body, size=12, color=DARK)

    # 11 Économie
    s = add(cream(prs))
    top = header(s, "9. Modèle économique", "Essai hybride · plans · packs · sièges")
    headers = ["Formule", "Mensuel", "Essai", "Cible"]
    data = [
        ("Découverte", "0 MAD", "Permanent", "Découverte produit"),
        ("Solo", "299 MAD", "14 j", "Avocat indépendant"),
        ("Cabinet", "699 MAD", "30 j", "Petite structure"),
        ("Entreprise", "1 290 MAD", "7 j qualifié", "Cabinets structurés"),
    ]
    for j, h in enumerate(headers):
        x = 0.4 + j * 3.2
        card(s, x, top, 3.05, 0.48, fill=NAVY)
        tb = s.shapes.add_textbox(Inches(x + 0.1), Inches(top + 0.1), Inches(2.85), Inches(0.3))
        R(tb.text_frame.paragraphs[0].add_run(), h, size=12, bold=True, color=WHITE)
    for i, row in enumerate(data):
        for j, cell in enumerate(row):
            x = 0.4 + j * 3.2
            y = top + 0.58 + i * 0.7
            card(s, x, y, 3.05, 0.62)
            tb = s.shapes.add_textbox(Inches(x + 0.1), Inches(y + 0.15), Inches(2.85), Inches(0.35))
            R(tb.text_frame.paragraphs[0].add_run(), cell, size=12, bold=(j == 0), color=NAVY if j == 0 else DARK)
    card_title_body(s, 0.4, top + 3.55, 6.15, 2.0, "Garde-fous", [
        "Essai = durée + plafond crédits",
        "Repère IA du jour (continuer / demain)",
        "Factures listées si amount > 0 MAD",
    ], bs=12)
    card_title_body(s, 6.75, top + 3.55, 6.15, 2.0, "Croissance", [
        "Packs prépayés (abonnés actifs)",
        "Sièges Cabinet · Parrainage confraternel",
        "PDF facture téléchargeable",
    ], bs=12)

    # 12 Prod
    s = add(cream(prs))
    top = header(s, "10. Production & CI/CD", "https://lexhub.space")
    card_title_body(s, 0.4, top, 6.15, 5.4, "Infrastructure", [
        "• VPS · Docker Compose · Caddy TLS",
        "• Images frontend / backend / celery",
        "• GitHub Actions → GHCR",
        "• Sauvegardes PostgreSQL + fichiers",
        "",
        "Atout multi-support",
        "• Même SaaS desktop + mobile (pas d’app native)",
        "• Dock tactile · rôles conservés · ~360–430 px",
    ], bs=12)
    card_title_body(s, 6.75, top, 6.15, 5.4, "Sécurité", [
        "• JWT + OTP e-mail + Turnstile (après échecs)",
        "• Multi-tenant (cabinet_id) + RBAC",
        "• Noms masqués avant tout appel LLM",
        "• Admin plateforme : usage/plans, jamais les affaires",
        "• Dock mobile fixé ; marque LexHub (pas « Administration »)",
        "• Adminer via tunnel SSH seulement",
    ], bs=12)

    # 13 Demo — Accueil & connexion
    s = add(cream(prs))
    top = header(s, "11. Démonstration — Accueil & connexion")
    pic(s, find_shot("01-accueil.png"), 0.35, top, 6.2, 5.05, "Accueil LexHub (page publique)")
    pic(s, find_shot("02-connexion.png"), 6.8, top, 6.1, 5.05, "Connexion sécurisée")

    # 14 Demo — Tableau de bord & dossiers
    s = add(cream(prs))
    top = header(s, "11bis. Démonstration — Tableau de bord & dossiers")
    pic(s, find_shot("10-tableau-de-bord.png"), 0.35, top, 6.2, 5.05, "Tableau de bord — dossiers, documents, essai et crédits")
    pic(s, find_shot("11-dossiers.png"), 6.8, top, 6.1, 5.05, "Liste des dossiers du cabinet")

    # 15 Demo — Fiche dossier & documents
    s = add(cream(prs))
    top = header(s, "11ter. Démonstration — Dossier & documents")
    pic(s, find_shot("24-dossier-detail.png"), 0.35, top, 6.2, 5.05, "Fiche dossier — identité des parties et plaidoirie liée")
    pic(s, find_shot("13-documents.png"), 6.8, top, 6.1, 5.05, "Espace Documents — dépôt et statut d'extraction")

    # 16 Demo — Détail document & atelier
    s = add(cream(prs))
    top = header(s, "11quater. Démonstration — Document & atelier plaidoirie")
    pic(s, find_shot("13b-document-detail.png"), 0.35, top, 6.2, 5.05, "Détail document — extrait, synthèse IA et questions")
    pic(s, find_shot("14b-plaidoirie-workspace.png"), 6.8, top, 6.1, 5.05, "Atelier plaidoirie — étape 1 (dossier & pièces)")

    # 17 Demo — Transcription & export
    s = add(cream(prs))
    top = header(s, "11quinquies. Démonstration — Transcription & export")
    pic(s, find_shot("14c-transcription-fusha.png"), 0.35, top, 6.2, 5.05, "Transcription / correction (arabe fusḥā)")
    pic(s, find_shot("19-export-document.png"), 6.8, top, 6.1, 5.05, "Export Word (.docx) / PDF de la plaidoirie")

    # 18 Demo — Équipe, activité & admin
    s = add(cream(prs))
    top = header(s, "11sexies. Démonstration — Équipe, activité & admin")
    pic(s, find_shot("16-equipe.png"), 0.35, top, 4.1, 5.05, "Équipe — invitations et rôles")
    pic(s, find_shot("23-activite-cabinet.png"), 4.6, top, 4.1, 5.05, "Journal d'activité du cabinet")
    pic(s, find_shot("22a-admin-dashboard.png"), 8.85, top, 4.1, 5.05, "Admin plateforme — pilotage LexHub")

    # 16 Bilan
    s = add(cream(prs))
    top = header(s, "12. Bilan", "Objectifs PFA — conformité")
    rows = [
        ("Atelier 5 étapes", "Dossier → Word / PDF"),
        ("SI multi-tenant + RBAC", "Isolation + validation assistant"),
        ("Urbanisation MADI", "Process / apps / données / infra"),
        ("Modèle économique", "Essai, plans, packs ; factures > 0 MAD"),
        ("Production", "lexhub.space"),
    ]
    for i, (a, b) in enumerate(rows):
        y = top + i * 0.95
        card(s, 0.4, y, 10.2, 0.85)
        t = s.shapes.add_textbox(Inches(0.6), Inches(y + 0.22), Inches(4.5), Inches(0.4))
        R(t.text_frame.paragraphs[0].add_run(), a, size=14, bold=True, color=NAVY)
        u = s.shapes.add_textbox(Inches(5.3), Inches(y + 0.22), Inches(5.0), Inches(0.4))
        R(u.text_frame.paragraphs[0].add_run(), b, size=13, color=DARK)
        ok = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(11.0), Inches(y + 0.2), Inches(1.8), Inches(0.45))
        ok.fill.solid()
        ok.fill.fore_color.rgb = OK
        ok.line.fill.background()
        ot = s.shapes.add_textbox(Inches(11.15), Inches(y + 0.28), Inches(1.5), Inches(0.3))
        ot.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
        R(ot.text_frame.paragraphs[0].add_run(), "OK", size=12, bold=True, color=WHITE)

    # 17 Perspectives
    s = add(cream(prs))
    top = header(s, "Perspectives", "Évolution produit (hors périmètre déjà livré)")
    card_title_body(s, 0.4, top, 6.15, 5.4, "Court terme", [
        "• Encaissement réel (CMI / PayZone)",
        "• Qualité STT / relecture renforcée",
    ], bs=14)
    card_title_body(s, 6.75, top, 6.15, 5.4, "Moyen terme", [
        "• Continuité dossier → audience",
        "• Interopérabilités sans casser",
        "  les maîtres de donnée MADI",
    ], bs=14)

    # 18 Closing
    s = add(navy_slide(prs))
    if LOGO.exists():
        s.shapes.add_picture(str(LOGO), Inches(5.55), Inches(1.1), width=Inches(2.2))
    box = s.shapes.add_textbox(Inches(0.7), Inches(3.2), Inches(11.9), Inches(3.2))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    R(p.add_run(), "Merci pour votre attention", size=34, bold=True, color=WHITE, font="Georgia")
    p2 = tf.add_paragraph()
    p2.alignment = PP_ALIGN.CENTER
    p2.space_before = Pt(14)
    R(p2.add_run(), "Questions  ·  Démonstration : https://lexhub.space", size=17, color=GOLD)
    p3 = tf.add_paragraph()
    p3.alignment = PP_ALIGN.CENTER
    p3.space_before = Pt(16)
    R(p3.add_run(), "EL ASSAL Douae  ·  ENSA Tétouan  ·  WEBVOICE  ·  LexHub", size=13, color=RGBColor(0xA0, 0xAA, 0xBE))

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
