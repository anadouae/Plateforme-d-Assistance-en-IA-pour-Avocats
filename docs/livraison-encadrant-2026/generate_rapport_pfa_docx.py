# -*- coding: utf-8 -*-
"""Rapport PFA LexHub — Version Word professionnelle et exhaustive.

Alignée rigoureusement sur les sources LaTeX (docs/rapport-pfa/) et la version déployée en production (https://lexhub.space).
Projet de Fin d'Année — ENSA Tétouan / Entreprise d'accueil WEBVOICE (Tanger)
Étudiante : EL ASSAL Douae
Encadrant entreprise : M. Hatim Benhaddou
Tuteur pédagogique : Prof. Mohammed Al Achhab
Période : 01/07/2026 au 31/08/2026
"""

from pathlib import Path
import sys

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

REPO = Path(__file__).resolve().parents[2]
OUT_REPO = Path(__file__).resolve().parent
DESKTOP = Path.home() / "Desktop"
OUT_PFA = DESKTOP / "S9" / "PFA"

LOGO_LEXHUB = OUT_REPO / "logo-lexhub.png"
LOGO_ENSA = REPO / "docs" / "rapport-pfa" / "assets" / "logo-ensa.png"
LOGO_WEBVOICE = REPO / "docs" / "rapport-pfa" / "assets" / "logo-webvoice.png"
MAQUETTES = REPO / "docs" / "rapport-pfa" / "maquettes"

NAVY = RGBColor(0x0B, 0x1A, 0x4D)
GOLD = RGBColor(0xC4, 0x97, 0x3F)
MUTED = RGBColor(0x4A, 0x55, 0x68)
DARK = RGBColor(0x1F, 0x29, 0x37)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)


def set_run_font(run, name="Calibri", size=11, bold=False, italic=False, color=None):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color is not None:
        run.font.color.rgb = color


def add_para(doc, text, *, bold=False, italic=False, size=11, space_after=6, space_before=0, color=None, align=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    if align is not None:
        p.alignment = align
    r = p.add_run(text)
    set_run_font(r, size=size, bold=bold, italic=italic, color=color or MUTED)
    return p


def heading(doc, text, level=1):
    p = doc.add_heading(text, level=level)
    p.paragraph_format.keep_with_next = True
    if level == 1:
        p.paragraph_format.space_before = Pt(16)
        p.paragraph_format.space_after = Pt(8)
        for run in p.runs:
            set_run_font(run, size=16, bold=True, color=NAVY)
    elif level == 2:
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(5)
        for run in p.runs:
            set_run_font(run, size=13, bold=True, color=NAVY)
    elif level == 3:
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(4)
        for run in p.runs:
            set_run_font(run, size=11.5, bold=True, color=GOLD)
    return p


def shade(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), hex_color)
    shd.set(qn("w:val"), "clear")
    tcPr.append(shd)


def table(doc, headers, rows, col_widths=None):
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.style = "Table Grid"
    for i, h in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell.text = ""
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.space_before = Pt(3)
        r = p.add_run(h)
        set_run_font(r, bold=True, size=9.5, color=WHITE)
        shade(cell, "0B1A4D")
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            cell = t.rows[ri + 1].cells[ci]
            cell.text = ""
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.space_before = Pt(3)
            r = p.add_run(str(val))
            set_run_font(r, size=9, color=DARK)
            if ri % 2:
                shade(cell, "F8FAFC")
    if col_widths and len(col_widths) == len(headers):
        for row in t.rows:
            for ci, w in enumerate(col_widths):
                row.cells[ci].width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    return t


def bullet(doc, text, size=10.5, space_after=3):
    p = doc.add_paragraph(style="List Bullet")
    for run in list(p.runs):
        run.text = ""
    r = p.add_run(text)
    set_run_font(r, size=size, color=MUTED)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    return p


def numbered(doc, text, size=10.5, space_after=3):
    p = doc.add_paragraph(style="List Number")
    for run in list(p.runs):
        run.text = ""
    r = p.add_run(text)
    set_run_font(r, size=size, color=MUTED)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    return p


def add_figure(doc, img_path, caption_text, width_cm=14.0):
    if img_path.exists():
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(3)
        run = p.add_run()
        run.add_picture(str(img_path), width=Cm(width_cm))

        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.paragraph_format.space_after = Pt(8)
        r = cap.add_run(f"Figure — {caption_text}")
        set_run_font(r, size=9.5, italic=True, color=MUTED)


def set_cell_margins(section):
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(2.2)
    section.left_margin = Cm(2.2)
    section.right_margin = Cm(2.0)


def add_page_number(section):
    footer = section.footer
    footer.is_linked_to_previous = False
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r0 = p.add_run("LexHub  ·  Rapport PFA  ·  ENSA Tétouan / WEBVOICE  ·  ")
    set_run_font(r0, size=8.5, color=MUTED)
    fld1 = OxmlElement("w:fldChar")
    fld1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    fld2 = OxmlElement("w:fldChar")
    fld2.set(qn("w:fldCharType"), "end")
    r = p.add_run()
    r._r.append(fld1)
    r._r.append(instr)
    r._r.append(fld2)
    set_run_font(r, size=8.5, bold=True, color=NAVY)


def cover(doc):
    p = add_para(doc, "UNIVERSITÉ ABDELMALEK ESSAÂDI", bold=True, size=13, align=WD_ALIGN_PARAGRAPH.CENTER, color=NAVY)
    p.paragraph_format.space_before = Pt(10)
    add_para(
        doc,
        "École Nationale des Sciences Appliquées de Tétouan",
        size=11.5,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        color=NAVY,
    )
    add_para(doc, "Cycle Ingénieur — Génie Informatique (2e année)", size=10.5, align=WD_ALIGN_PARAGRAPH.CENTER)
    add_para(doc, "Année Universitaire 2025–2026", size=10.5, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=12)

    # Logos row
    t_logos = doc.add_table(rows=1, cols=2)
    t_logos.alignment = WD_TABLE_ALIGNMENT.CENTER
    if LOGO_ENSA.exists():
        p_ensa = t_logos.rows[0].cells[0].paragraphs[0]
        p_ensa.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_ensa.add_run().add_picture(str(LOGO_ENSA), width=Cm(3.8))
    if LOGO_WEBVOICE.exists():
        p_wv = t_logos.rows[0].cells[1].paragraphs[0]
        p_wv.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_wv.add_run().add_picture(str(LOGO_WEBVOICE), width=Cm(3.8))

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    add_para(doc, "PROJET DE FIN D'ANNÉE (PFA)", bold=True, size=15, align=WD_ALIGN_PARAGRAPH.CENTER, color=NAVY)
    add_para(doc, "LexHub", bold=True, size=28, align=WD_ALIGN_PARAGRAPH.CENTER, color=NAVY, space_after=4)

    if LOGO_LEXHUB.exists():
        p_lh = doc.add_paragraph()
        p_lh.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_lh.paragraph_format.space_after = Pt(6)
        p_lh.add_run().add_picture(str(LOGO_LEXHUB), width=Cm(2.6))

    add_para(
        doc,
        "Mise en place d'une plateforme d'assistance IA pour avocats",
        size=13.5,
        bold=True,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        color=GOLD,
        space_after=14,
    )

    table(
        doc,
        ["Paramètre", "Détail officiel"],
        [
            ["Réalisé par", "EL ASSAL Douae"],
            ["Entreprise d'accueil", "WEBVOICE — 29, rue Amr Ibn Ass, étage 3, n°26, Tanger (https://webvoice.pro)"],
            ["Gérant entreprise", "M. Khalid MERINI LAAROSSI"],
            ["Encadrant entreprise", "M. Hatim BENHADDOU"],
            ["Tuteur pédagogique", "Prof. Mohammed AL ACHHAB (ENSA Tétouan)"],
            ["Période de stage", "Du 01 juillet 2026 au 31 août 2026 (2 mois)"],
            ["Plateforme livrée", "LexHub en production — https://lexhub.space"],
        ],
        col_widths=[5.0, 11.0],
    )

    add_para(
        doc,
        "Document officiel d'ingénierie logicielle aligné sur la version déployée en production (Web Speech API, Word .docx unique, Adminer sécurisé SSH, modèle économique qualifié).",
        italic=True,
        size=9.5,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_before=10,
    )
    doc.add_page_break()


def build():
    doc = Document()
    set_cell_margins(doc.sections[0])
    add_page_number(doc.sections[0])
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)
    style.font.color.rgb = MUTED

    cover(doc)

    # -------------------------------------------------------------
    # Liminaires
    # -------------------------------------------------------------
    heading(doc, "Dédicace", 1)
    add_para(doc, "À mes très chers parents, pour leurs sacrifices constants, leur soutien indéfectible et leur amour bienveillant tout au long de mon cursus universitaire.")
    add_para(doc, "À mes professeurs de l'ENSA Tétouan, qui m'ont inculqué l'esprit d'analyse, l'éthique professionnelle et la rigueur scientifique de l'ingénieur.")
    add_para(doc, "À l'équipe WEBVOICE, pour son encadrement bienveillant, ses conseils méthodologiques et la confiance accordée sur un projet d'ingénierie d'envergure.")

    heading(doc, "Remerciements", 1)
    add_para(
        doc,
        "Je tiens à adresser mes remerciements les plus sincères à Monsieur Khalid Merini Laarossi, gérant de WEBVOICE, "
        "pour m'avoir accueillie au sein de son entreprise et pour m'avoir offert l'opportunité de travailler sur un projet concret "
        "à fort impact technologique et métier.",
    )
    add_para(
        doc,
        "J'exprime ma profonde gratitude à Monsieur Hatim Benhaddou, mon encadrant en entreprise, pour sa disponibilité constante, "
        "la qualité de son suivi technique quotidien, ses exigences de production et ses précieux arbitrages tout au long de ce stage.",
    )
    add_para(
        doc,
        "Je remercie tout particulièrement mon tuteur pédagogique, le Professeur Mohammed Al Achhab, pour son écoute, ses orientations "
        "académiques éclairées et ses conseils précieux lors des séances de suivi à l'ENSA Tétouan.",
    )
    add_para(doc, "Enfin, j'adresse mes remerciements chaleureux à mes proches et camarades pour leurs encouragements constants.")

    heading(doc, "Résumé", 1)
    add_para(doc, "Mots-clés : LegalTech, SaaS, intelligence artificielle, plaidoirie vocale, Web Speech API, Word (.docx), multi-tenant, secret professionnel, Maroc.", italic=True)
    add_para(
        doc,
        "Ce rapport présente l'étude, la conception, la réalisation et la mise en production de LexHub (https://lexhub.space), "
        "plateforme logicielle SaaS (Software as a Service) d'assistance par intelligence artificielle destinée aux cabinets d'avocats marocains.",
    )
    add_para(
        doc,
        "Partant du constat d'une forte perte de productivité lors de la transition orale-écrite des arguments de plaidoirie, LexHub "
        "met en place un atelier en cinq étapes : rattachement du dossier et des pièces justificatives, dictée vocale temps réel "
        "via la Web Speech API native du navigateur (respectant la confidentialité locale sans coût serveur), transcription avec détection "
        "visuelle des corrections et détection déterministe des contradictions matérielles, rédaction assistée structurée selon les "
        "usages des juridictions marocaines, et export final exclusif au format Microsoft Word (.docx) 100 % éditable, orné de l'en-tête officiel "
        "du cabinet et des armoiries du Royaume du Maroc.",
    )
    add_para(
        doc,
        "L'architecture logicielle repose sur une isolation stricte des données par cabinet (multi-tenant), un contrôle d'accès fondé sur "
        "les rôles (RBAC) protégeant le secret des brouillons vis-à-vis des collaborateurs assistants, et un système d'administration de "
        "base de données conteneurisé (Adminer) dont l'accès public Web est totalement neutralisé pour garantir la conformité avec l'article 30 "
        "de la loi n° 28-08 régissant la profession d'avocat au Maroc. La viabilité économique est assurée par un modèle hybride associant "
        "essai gratuit encadré par un plafond Fair-Use, forfaits mensuels, recharges de crédits prépayés FIFO, et une qualification commerciale "
        "stricte pour les grands comptes Entreprise.",
    )

    heading(doc, "Abstract", 1)
    add_para(doc, "Keywords: LegalTech, SaaS, Artificial Intelligence, Speech-to-Text, Web Speech API, Word (.docx), Multi-tenant, Professional Secrecy, Morocco.", italic=True)
    add_para(
        doc,
        "This engineering report documents the specification, architecture, implementation, and cloud deployment of LexHub "
        "(https://lexhub.space), a specialized multi-tenant LegalTech SaaS platform providing AI-powered workflow assistance for Moroccan law firms.",
    )
    add_para(
        doc,
        "Addressing the productivity bottleneck between oral courtroom argumentation and formal legal drafting, LexHub delivers a guided "
        "five-step pipeline: case matter and exhibits assignment, real-time voice dictation leveraging the browser-native Web Speech API "
        "(eliminating backend audio transport overhead and safeguarding on-device privacy), Arabic transcription with visual typographical "
        "highlights and deterministic contradiction auditing, AI-assisted structuring strictly grounded on dictated facts, and export to "
        "fully editable Microsoft Word (.docx) documents formatted with official royal emblems and cabinet headers.",
    )

    doc.add_page_break()

    # -------------------------------------------------------------
    # Chapitre 1 — Introduction générale
    # -------------------------------------------------------------
    heading(doc, "Chapitre 1 — Introduction générale", 1)

    heading(doc, "1.1 Contexte et motivation", 2)
    add_para(
        doc,
        "La pratique quotidienne des cabinets d'avocats au Maroc se caractérise par une charge rédactionnelle particulièrement intense : "
        "requêtes introductives d'instance, mémoires en réponse, conclusions récapitulatives et notes de plaidoirie orales destinées aux tribunaux. "
        "Dans la grande majorité des cabinets, la chaîne de production documentaire demeure artisanale : prise de notes manuscrites à l'audience, "
        "dictée informelle sur dictaphone ou messagerie instantanée, ressaisie fastidieuse par un collaborateur ou un secrétaire, puis mise en page "
        "tardive sur traitement de texte. Ce processus est chronophage, sujet à des erreurs de transcription matérielle (noms, dates, montants en dirhams, "
        "références d'actes) et dépourvu de traçabilité centralisée.",
    )
    add_para(
        doc,
        "Le besoin métier exprimé n'est pas celui d'un agent conversationnel grand public (« chatbot ») générant des avis juridiques abstraits, "
        "mais d'un outil de productivité professionnelle sur mesure, capable d'accélérer la conversion fidèle de la parole de l'avocat en un document "
        "judiciaire immédiatement exploitable, tout en préservant le secret professionnel le plus rigoureux.",
    )

    heading(doc, "1.2 L'entreprise d'accueil — WEBVOICE", 2)
    add_para(
        doc,
        "WEBVOICE (https://webvoice.pro), société sise à Tanger (29, rue Amr Ibn Ass, n°26), est une entreprise spécialisée dans les technologies "
        "de la voix sur IP (VoIP), les systèmes de télécommunication d'entreprise, les plateformes web dynamiques et le développement applicatif mobile. "
        "Le projet LexHub s'inscrit au cœur de cette synergie technologique en combinant le traitement vocal bilingue (arabe standard / français) et "
        "l'ingénierie logicielle Cloud multi-locataires.",
    )

    heading(doc, "1.3 Problématique", 2)
    add_para(
        doc,
        "Comment concevoir, sécuriser et déployer une plateforme logicielle SaaS multi-cabinets permettant à un avocat marocain de dicter sa plaidoirie "
        "en arabe, d'obtenir une transcription instantanée sans latence réseau, de structurer ses moyens de fait et de droit sans risque d'hallucination "
        "juridique, de collaborer de manière étanche avec ses assistants sans divulguer ses brouillons non validés, et d'exporter directement un document "
        "officiel Microsoft Word (.docx) 100 % éditable, prêt pour l'audience ?",
    )

    heading(doc, "1.4 Objectifs assignés", 2)
    numbered(doc, "Mettre en œuvre un pipeline vocal en 5 étapes guidées (Dossier & pièces, Dictée, Transcription, Rédaction IA, Export Word .docx).")
    numbered(doc, "Garantir la reconnaissance vocale en temps réel via la Web Speech API native du navigateur, sans frais serveur récurrents.")
    numbered(doc, "Assurer l'intégrité déontologique de la rédaction IA : interdiction absolue d'inventer des faits, des articles de loi ou des montants.")
    numbered(doc, "Concevoir une isolation multi-tenant stricte au niveau de la base relationnelle et du stockage objet.")
    numbered(doc, "Définir un système de permissions à 4 rôles (avocat, assistant juridique, admin cabinet, admin plateforme WebVoice).")
    numbered(doc, "Sécuriser les outils d'audit technique (Adminer) par tunnel SSH chiffré, sans aucune exposition sur le web public.")
    numbered(doc, "Construire un modèle économique viable associant freemium, essai hybride encadré, packs de crédits prépayés et qualification Entreprise.")
    numbered(doc, "Déployer la solution en production sur un serveur VPS sécurisé sous HTTPS (https://lexhub.space).")

    heading(doc, "1.5 Démarche méthodologique", 2)
    add_para(
        doc,
        "Le projet a été conduit selon une méthodologie agile itérative, rythmée par des cycles hebdomadaires de développement, de validation "
        "auprès des encadrants et de déploiement continu sur l'environnement de production. Chaque incrément a été éprouvé sur des cas réels "
        "de dossiers judiciaires marocains (droit civil, commercial, droit de la famille).",
    )

    # -------------------------------------------------------------
    # Chapitre 2 — Étude de l'existant et benchmark
    # -------------------------------------------------------------
    heading(doc, "Chapitre 2 — Étude de l'existant et état de l'art", 1)
    add_para(
        doc,
        "Une étude comparative approfondie des solutions logicielles destinées aux cabinets d'avocats a été menée au Maroc et à l'international, "
        "selon quatre critères d'évaluation : le cœur métier vocal (dictée et structuration de plaidoirie), la gestion de cabinet, "
        "l'architecture SaaS multi-tenant et la conformité aux spécificités procédurales marocaines.",
    )

    table(
        doc,
        ["Solution", "Périmètre fonctionnel", "Limites constatées face aux besoins"],
        [
            ["SmartAvocat (smartavocat.ma)", "Gestion de cabinet, suivi des dossiers, facturation", "Aucun module de dictée vocale ni de génération de plaidoirie"],
            ["Avocato (avocato.ma)", "Gestion des affaires, synchronisation portail Mahakim", "Orientation administrative ; absence de pipeline rédactionnel IA"],
            ["AvocatPro (avocatpro.ma)", "Suivi procédural, agenda des audiences", "Pas d'assistance vocale ni de traitement du langage juridique"],
            ["Legaliq (legaliq.ma)", "Moteur de recherche et Q&A juridique/fiscal", "Outil d'information générale ; pas de gestion de dossiers ni d'équipe"],
            ["Kanoun (kanoun.com)", "Consultation des textes de loi marocains et OHADA", "Base documentaire statique ; pas de production de plaidoiries sur mesure"],
            ["Adala.ai (adala.ai)", "Génération de contrats et modèles types", "Généraliste ; absence d'isolation multi-cabinets et d'export Word annoté"],
            ["Diskod / Dragon Legal", "Dictée vocale pour logiciel bureautique desktop", "Solution lourde, coûteuse par poste, sans intégration web ni dossiers"],
            ["LexHub (lexhub.space)", "Dictée vocale Web Speech API, structuration IA fidèle, collaboration sécurisée, export Word .docx officiel", "Solution complète, collaborative et souveraine déployée en production"],
        ],
        col_widths=[4.5, 6.0, 5.5],
    )

    add_para(
        doc,
        "Positionnement stratégique de LexHub : LexHub ne se positionne pas comme une IA de substitution (« robot-avocat »), mais comme une IA d'assistance "
        "au service de l'avocat (« copilote »). Le système applique le principe d'ancrage factuel strict : l'IA structure, formule et met en forme dans un arabe "
        "juridique châtié (Fusha), mais n'a pas le droit d'extrapoler ou d'ajouter le moindre fait non énoncé par le praticien.",
    )

    # -------------------------------------------------------------
    # Chapitre 3 — Analyse des besoins et modélisation fonctionnelle
    # -------------------------------------------------------------
    heading(doc, "Chapitre 3 — Analyse des besoins et modélisation fonctionnelle", 1)

    heading(doc, "3.1 Acteurs du système", 2)
    table(
        doc,
        ["Acteur", "Nature", "Rôle et périmètre d'action"],
        [
            ["Avocat titulaire / associé", "Humain (métier)", "Dicte les plaidoiries, vérifie les transcriptions, valide les projets, assigne les tâches aux assistants et exporte les documents Word."],
            ["Stagiaire / Assistant juridique", "Humain (métier)", "Consulte les dossiers rattachés et les plaidoiries explicitement validées ou assignées ; n'a aucun accès aux brouillons privés."],
            ["Avocat administrateur cabinet", "Humain (gestion)", "Dispose de toutes les prérogatives avocat, plus la gestion de l'équipe (invitations, rôles), la personnalisation de la charte graphique et la facturation."],
            ["Administrateur plateforme WebVoice", "Humain (supervision)", "Supervise les indicateurs globaux de production, active ou suspend les cabinets, sans jamais pouvoir consulter le contenu confidentiel des dossiers judiciaires."],
        ],
        col_widths=[4.5, 3.5, 8.0],
    )

    heading(doc, "3.2 Spécifications fonctionnelles prioritaires", 2)
    table(
        doc,
        ["Code", "Module", "Description de l'exigence fonctionnelle"],
        [
            ["EF-1", "Authentification", "Inscription sécurisée avec vérification par e-mail (code OTP à 6 chiffres), création immédiate de l'espace cabinet."],
            ["EF-2", "Dossiers judiciaires", "Création et gestion des dossiers (numéro d'ordre, tribunal, ville, juridiction, parties adverses, historique)."],
            ["EF-3", "Dictée vocale", "Capture micro temps réel dans le navigateur (Web Speech API) avec affichage continu et reprise à tout instant."],
            ["EF-4", "Transcription Fusha", "Nettoyage typographique, correction de forme en arabe juridique avec mise en évidence visuelle orange des termes corrigés."],
            ["EF-5", "Contrôle contradictions", "Vérification algorithmique déterministe des dates, numéros de pièces, montants en MAD et identités."],
            ["EF-6", "Rédaction assistée", "Génération de la plaidoirie en sections normalisées (En-tête, Faits constants, Moyens de droit, Prétentions chiffrées)."],
            ["EF-7", "Assistant interactif", "Module de révision guidée permettant à l'avocat d'affiner le texte ou de compléter une section par dialogue."],
            ["EF-8", "Export Word (.docx)", "Génération du document officiel téléchargeable au format .docx, prêt pour impression ou dépôt au greffe."],
            ["EF-9", "Collaboration étanche", "Masquage rigoureux des brouillons (draft) aux assistants ; accès réservé aux états validés (validated)."],
            ["EF-10", "Planning & Audiences", "Gestion de l'agenda des audiences, synchronisation avec le dossier et rappels à J-2 (48h)."],
            ["EF-11", "Fil d'activité", "Journalisation transparente des actions sensibles au sein du cabinet pour l'audit interne."],
            ["EF-12", "Modèle économique", "Gestion des forfaits (Découverte, Solo, Cabinet, Entreprise), des crédits et de la période d'essai encadrée."],
        ],
        col_widths=[2.5, 4.0, 9.5],
    )

    heading(doc, "3.3 Spécifications non fonctionnelles", 2)
    bullet(doc, "Sécurité et secret professionnel (ENF-1) : Isolation étanche multi-tenant assurée par cabinet_id au niveau de la couche ORM SQLAlchemy. Hash des mots de passe en bcrypt avec salage individuel.")
    bullet(doc, "Confidentialité locale (ENF-2) : Utilisation prioritaire de la Web Speech API native du navigateur évitant le transfert permanent de flux audio bruts vers des serveurs tiers.")
    bullet(doc, "Disponibilité et résilience (ENF-3) : Déploiement multi-conteneurs Docker orchestré, avec redémarrage automatique en cas de panne et reverse-proxy TLS Caddy.")
    bullet(doc, "Intégrité déontologique (ENF-4) : Prompts LLM verrouillés avec pénalités de créativité (température basse 0.2) et garde-fous stricts interdisant toute invention de faits.")
    bullet(doc, "Performance (ENF-5) : Temps de réponse API inférieur à 200 ms sur les endpoints transactionnels et limitation du débit (Rate Limiting) sur l'authentification.")

    heading(doc, "3.4 Règles de gestion de la collaboration au cabinet", 2)
    numbered(doc, "Règle 1 (Isolement du brouillon) : Tout nouveau projet de plaidoirie créé par un avocat reçoit le statut draft. Il est strictement invisible aux assistants du cabinet.")
    numbered(doc, "Règle 2 (Validation explicite) : L'action de validation par l'avocat fait passer le statut à validated et le rend consultable par les collaborateurs désignés.")
    numbered(doc, "Règle 3 (Finalisation par l'export) : Le téléchargement du fichier Word (.docx) fait passer la plaidoirie au statut finalized, archivant le texte pour l'audience.")
    numbered(doc, "Règle 4 (Assignation ciblée) : L'avocat peut assigner un projet spécifique à un assistant juridique, déclenchant une notification interne temps réel.")

    # -------------------------------------------------------------
    # Chapitre 4 — Conception architecturale et technique
    # -------------------------------------------------------------
    heading(doc, "Chapitre 4 — Conception architecturale et technique", 1)

    heading(doc, "4.1 Architecture logique multi-niveaux", 2)
    add_para(
        doc,
        "L'application LexHub adopte une architecture découplée trois tiers conteneurisée, assurant une séparation nette entre l'interface utilisateur, "
        "la logique métier transactionnelle et les services de persistance :",
    )
    bullet(doc, "Niveau Présentation : Application Single Page Next.js 14 (React, TypeScript, Tailwind CSS) optimisée pour le bilinguisme français/arabe (direction RTL).")
    bullet(doc, "Niveau Logique & Traitement : API RESTful haute performance développée sous FastAPI (Python 3.11), intégrant la validation Pydantic, l'authentification JWT et la gestion asynchrone.")
    bullet(doc, "Niveau Traitement Asynchrone : File de messages Redis associée à des workers Celery pour les tâches d'arrière-plan (génération de documents lourds, rappels e-mail).")
    bullet(doc, "Niveau Persistance : SGBD relationnel PostgreSQL 15 hébergeant les schémas relationnels avec migrations versionnées Alembic, et stockage objet MinIO / S3 pour les pièces jointes.")

    heading(doc, "4.2 Architecture des données et modèle relationnel", 2)
    add_para(
        doc,
        "Le modèle de données est structuré autour du concept central de Cabinet (locataire SaaS). Chaque table applicative (users, cases, plaidoirie_drafts, "
        "documents, agenda_events, cabinet_notifications) intègre une clé étrangère cabinet_id indexée, garantissant l'étanchéité des requêtes SQL.",
    )

    heading(doc, "4.3 Audit et administration de la base de données : choix d'Adminer sécurisé", 2)
    add_para(
        doc,
        "Dans une optique de maintenance opérationnelle et d'audit des données lors des phases de tests et de recette, une interface d'administration "
        "de la base de données était requise. Les outils bureautiques lourds (ex. pgAdmin local imposant une installation sur chaque poste client) "
        "ont été écartés au profit d'Adminer (image officielle adminer:latest) déployé directement au sein du réseau Docker du VPS.",
    )
    add_para(
        doc,
        "Sécurisation déontologique absolue (Article 30 de la loi n° 28-08) : La profession d'avocat étant soumise au secret professionnel le plus rigoureux, "
        "il était formellement exclu d'exposer une interface d'administration de base de données sur le réseau Internet public. L'accès externe direct sur "
        "le port 8080 a été intégralement bloqué par le pare-feu du serveur et neutralisé au niveau du reverse-proxy Caddy (retournant une erreur HTTP 404/308). "
        "L'accès est réservé exclusivement aux ingénieurs autorisés à travers un tunnel SSH chiffré de bout en bout, activé en un clic via le script scripté "
        "Ouvrir_Adminer.bat (mappant localement le port 8088 vers le conteneur interne).",
    )

    heading(doc, "4.4 Pipeline de plaidoirie en cinq étapes", 2)
    add_para(
        doc,
        "L'atelier de plaidoirie constitue le cœur d'innovation de LexHub. Il guide l'avocat à travers cinq phases méthodologiques progressives :",
    )
    numbered(doc, "Étape 1 — Dossier et pièces : Sélection du dossier judiciaire cible, consultation des pièces annexées (contrats, PV d'huissier, factures) et définition du type de procédure.")
    numbered(doc, "Étape 2 — Dictée vocale : Enregistrement de la parole de l'avocat en arabe via la Web Speech API native du navigateur, avec indicateur de flux et transcription instantanée.")
    numbered(doc, "Étape 3 — Transcription et correction de forme : Nettoyage automatique en arabe standard juridique (Fusha) ; mise en évidence des corrections par surlignage orange ; détection des contradictions matérielles.")
    numbered(doc, "Étape 4 — Rédaction assistée : Structuration du texte selon les normes procédurales marocaines (En-tête de cour, Faits constants, Réfutation des prétentions adverses, Dispositif légal) ; affinement par dialogue interactif avec l'IA.")
    numbered(doc, "Étape 5 — Export officiel Word (.docx) : Téléchargement du document 100 % éditable, comprenant les armoiries officielles du Royaume du Maroc, l'en-tête du cabinet et la typographie Noto Naskh Arabic. Le document est alors classé comme finalisé.")

    # -------------------------------------------------------------
    # Chapitre 5 — Modèle de rentabilisation et viabilité économique
    # -------------------------------------------------------------
    heading(doc, "Chapitre 5 — Modèle de rentabilisation et viabilité économique", 1)

    heading(doc, "5.1 Principes méthodologiques appliqués", 2)
    add_para(
        doc,
        "Pour assurer la pérennité financière de la plateforme en production tout en maîtrisant les coûts variables liés aux modèles de langage (LLM), "
        "une stratégie économique rigoureuse a été conçue, articulée autour de six piliers :",
    )
    bullet(doc, "Product-Led Growth (PLG) & Freemium : Accès immédiat au plan Découverte gratuit pour faire éprouver la valeur du produit sans barrière à l'entrée.")
    bullet(doc, "Good–Better–Best Pricing : Échelonnement clair des formules d'abonnement adaptées aux différentes tailles de cabinets marocains.")
    bullet(doc, "Essai hybride (Hybrid Trial) : Association d'une durée d'essai calendaire et d'un plafond strict de consommation pour éviter toute consommation abusive sans intention d'achat.")
    bullet(doc, "Fair-Use Soft-Cap (Repère journalier) : Système préventif informant l'utilisateur de sa cadence quotidienne sans blocage brutal.")
    bullet(doc, "Packs de crédits prépayés FIFO : Possibilité pour les abonnés actifs de recharger leur solde avec des packs valables 12 mois.")
    bullet(doc, "Qualification commerciale grands comptes : Protection spécifique de l'offre Entreprise pour prévenir la création de faux comptes volumineux.")

    heading(doc, "5.2 Grille tarifaire des forfaits LexHub", 2)
    table(
        doc,
        ["Formule", "Tarif mensuel", "Tarif annuel (-15%)", "Essai offert", "Forfait mensuel inclus", "Cible prioritaire"],
        [
            ["Découverte", "0 MAD", "0 MAD", "Permanent", "3 plaidoiries / 50 crédits", "Avocat stagiaire, test initial"],
            ["Solo", "299 MAD / mois", "2 990 MAD / an", "14 jours", "35 plaidoiries / 600 crédits", "Avocat individuel indépendant"],
            ["Cabinet (Recommandé)", "699 MAD / mois", "6 990 MAD / an", "30 jours", "120 plaidoiries / 2 000 crédits", "Cabinet de 2 à 5 collaborateurs"],
            ["Entreprise", "1 290 MAD / mois", "12 900 MAD / an", "7 jours (qualifié)", "350 plaidoiries / 5 000 crédits", "Grand cabinet d'affaires structuré"],
            ["Sur mesure", "Sur devis", "Devis annuel", "Sur cadrage", "Illimité / Sur mesure", "Structures > 15 avocats, réseaux"],
        ],
        col_widths=[2.8, 2.4, 2.4, 2.4, 3.5, 3.5],
    )

    heading(doc, "5.3 Analyse détaillée de chaque plan de la grille", 2)
    add_para(doc, "Chaque formule tarifaire a été modélisée pour répondre précisément aux besoins organisationnels et économiques des différentes catégories de praticiens marocains :")
    
    bullet(doc, "Plan Découverte (0 MAD — Freemium d'acquisition) : Conçu pour lever tous les freins à l'adoption, ce forfait offre 1 compte utilisateur, 3 dossiers, 3 plaidoiries complètes et 50 crédits d'accueil. Il permet à l'avocat d'éprouver immédiatement la qualité de la reconnaissance vocale et de la mise en page Word sans engagement et sans carte bancaire (repère journalier de 12 crédits/jour).")
    bullet(doc, "Plan Solo (299 MAD HT/mois ou 2 990 MAD/an) : Dédié à l'avocat exerçant en individuel, il inclut 1 siège avocat + 1 siège assistant juridique offert (2 utilisateurs), 35 plaidoiries et 600 crédits par mois. L'essai hybride de 14 jours (400 crédits) permet de valider le produit sur des dossiers réels avec un repère de confort de 35 crédits/jour en essai, passant à 50 crédits/jour en formule payante.")
    bullet(doc, "Plan Cabinet (699 MAD HT/mois ou 6 990 MAD/an — Formule recommandée) : Cœur de cible du marché, il comprend 5 sièges avocats + 3 sièges assistants (8 collaborateurs inclus), 120 plaidoiries et 2 000 crédits mensuels. L'essai de 30 jours est plafonné à 1 000 crédits (repère journalier de 90 cr./j en essai, 180 cr./j en payé). Il offre la possibilité exclusive d'ajouter jusqu'à 5 sièges avocats à 99 MAD/mois par collaborateur.")
    bullet(doc, "Plan Entreprise (1 290 MAD HT/mois ou 12 900 MAD/an) : Adapté aux cabinets d'affaires de premier plan, il inclut 15 sièges avocats + 10 sièges assistants (25 collaborateurs inclus), 350 plaidoiries et 5 000 crédits mensuels (repère de 105 cr./j en essai et 300 cr./j en payé). Son accès fait l'objet d'un processus commercial qualifié strict.")
    bullet(doc, "Palier Sur mesure (Sur devis) : Pour les structures dépassant 15 avocats, proposant un hébergement souverain isolé (Single-Tenant), des connecteurs ERP personnalisés et un support d'astreinte 24/7.")

    heading(doc, "5.4 Qualification commerciale Entreprise et Deux Piliers anti-fraude", 2)
    add_para(
        doc,
        "L'expérience des plateformes SaaS d'IA montre que les forfaits à haute capacité (5 000 crédits) sont la cible privilégiée d'abus et de faux comptes "
        "éphémères. Pour LexHub, la souscription directe en libre-service web à l'offre Entreprise a été délibérément supprimée :",
    )
    bullet(doc, "Rupture du libre-service (Self-Service) : Tout clic sur l'offre Entreprise redirige obligatoirement vers /commercial?intent=enterprise, imposant la saisie de 7 informations de qualification vérifiables (Nom, email pro, téléphone direct, cabinet, ville et barreau, nombre d'avocats, cadrage du besoin). La demande est enregistrée dans la table PostgreSQL commercial_leads.")
    bullet(doc, "Pilier 1 — KYC léger déontologique : Conformément à la loi n° 28-08 régissant la profession d'avocat au Maroc, l'équipe commerciale vérifie l'inscription effective du demandeur au tableau officiel de l'Ordre des Avocats du Barreau déclaré. Tout demandeur fictif est immédiatement écarté.")
    bullet(doc, "Pilier 2 — Double Verrou (Durée & Plafond) : L'essai pilote est resserré à 7 jours seulement (créant une dynamique d'évaluation active sur 2-3 dossiers réels), et son plafond d'utilisation est strictement bridé à 1 800 crédits (au lieu des 5 000 crédits du forfait payant actif), protégeant l'entreprise d'accueil contre des coûts LLM disproportionnés.")

    heading(doc, "5.5 Stratégie de croissance globale (Growth Plan) et Unit Economics", 2)
    add_para(
        doc,
        "La viabilité commerciale de LexHub s'appuie sur une mécanique de croissance en trois temps articulée avec une rentabilité unitaire élevée :",
    )
    bullet(doc, "Entonnoir Product-Led Growth (PLG) : L'expérience utilisateur immédiate (Time-to-Value < 3 minutes) convertit les visiteurs en utilisateurs Découverte, qui découvrent naturellement la valeur sur un cas concret avant de basculer vers un essai Solo ou Cabinet.")
    bullet(doc, "Expansion du panier moyen (Land & Expand) : Les abonnés actifs augmentent leur valeur vie (LTV) par l'achat de packs prépayés FIFO valables 12 mois (500 crédits à 110 MAD, 1 000 à 200 MAD, 2 500 à 450 MAD) et par l'ajout de sièges collaborateurs à la carte (99 MAD / mois).")
    bullet(doc, "Moteur viral de parrainage confraternel : Grâce à un code unique par cabinet (ex. LH-CAS-8842), le filleul bénéficie de +14 jours d'essai offerts, et le parrain reçoit +30 jours d'abonnement gratuit crédités automatiquement au premier paiement du filleul (plafond de 12 parrainages/an).")
    bullet(doc, "Maîtrise des COGS et marge brute de 80% : Grâce à la reconnaissance vocale Web Speech API locale (zéro coût serveur) et à l'optimisation des prompts LLM, le coût direct d'une plaidoirie complète est inférieur à 0,70 MAD, garantissant une marge brute de plus de 80% pour l'entreprise d'accueil WEBVOICE dès quelques dizaines de cabinets abonnés.")

    # -------------------------------------------------------------
    # Chapitre 6 — Réalisation et aspects techniques
    # -------------------------------------------------------------
    heading(doc, "Chapitre 6 — Réalisation et aspects techniques", 1)

    heading(doc, "6.1 Stack technologique mise en œuvre", 2)
    table(
        doc,
        ["Composant", "Technologie retenue", "Rôle et justification technique"],
        [
            ["Frontend", "Next.js 14, React, TypeScript", "Rendu réactif, typage statique, gestion optimisée des formulaires complexes et du RTL."],
            ["Design & UI", "Tailwind CSS, Lucide Icons", "Composants ergonomiques modernes, palette sobre adaptée au secteur juridique."],
            ["Backend API", "FastAPI, Python 3.11, Pydantic", "Performance asynchrone élevée, documentation OpenAPI native, typage strict."],
            ["ORM & BDD", "SQLAlchemy 2, PostgreSQL 15", "Modélisation relationnelle robuste, transactions ACID, migrations versionnées Alembic."],
            ["Voix & Audio", "Web Speech API (W3C standard)", "Reconnaissance vocale temps réel sans latence, respect de la confidentialité locale, zéro coût serveur."],
            ["IA & Traitement", "Routeur LLM, Prompts anti-hallucination", "Correction linguistique en Fusha, structuration juridique et révision interactive."],
            ["Export documentaire", "python-docx natif", "Production de fichiers Word (.docx) 100 % éditables, avec typographie Noto Naskh Arabic."],
            ["Conteneurisation", "Docker, Docker Compose", "Isolation complète des microservices, reproductibilité des déploiements."],
            ["Reverse-Proxy & TLS", "Caddy 2 Server", "Certificats HTTPS/TLS automatiques (Let's Encrypt), compression HTTP/2 et HTTP/3."],
        ],
        col_widths=[3.5, 4.5, 8.0],
    )

    heading(doc, "6.2 Sécurité et conformité déontologique", 2)
    add_para(
        doc,
        "La sécurité des données juridiques a été intégrée dès la conception (« Privacy by Design ») :",
    )
    bullet(doc, "Chiffrement systématique : Toutes les communications externes transitent impérativement sous HTTPS avec chiffrement TLS 1.3.")
    bullet(doc, "Cloisonnement multi-tenant : Les requêtes en base de données injectent systématiquement le filtre WHERE cabinet_id = :current_cabinet, interdisant toute fuite d'information inter-cabinets.")
    bullet(doc, "Neutralisation des ports sensibles : La base de données PostgreSQL (port 5432) et le conteneur Adminer (port 8080) sont confinés au réseau Docker interne et inaccessibles depuis Internet.")
    bullet(doc, "Auditabilité complète : Chaque action critique (connexion, création de dossier, export de plaidoirie, modification d'utilisateur) est inscrite dans un journal d'audit non modifiable.")

    # -------------------------------------------------------------
    # Chapitre 7 — Tests, validation et déploiement
    # -------------------------------------------------------------
    heading(doc, "Chapitre 7 — Tests, validation et déploiement", 1)

    heading(doc, "7.1 Stratégie de tests et scénarios de validation", 2)
    add_para(
        doc,
        "Une campagne complète de tests fonctionnels, d'intégration et de sécurité a été menée pour valider la robustesse de LexHub en conditions réelles :",
    )

    table(
        doc,
        ["Scénario de test", "Procédure exécutée", "Résultat obtenu", "Statut"],
        [
            ["1. Inscription OTP", "Création de compte, envoi du code à 6 chiffres, saisie et validation", "Compte et cabinet créés immédiatement, session ouverte", "Conforme"],
            ["2. Isolation brouillon", "Création d'une plaidoirie par l'avocat ; connexion sous profil assistant", "La plaidoirie en brouillon n'apparaît pas dans la liste assistant", "Conforme"],
            ["3. Validation avocat", "Validation de la plaidoirie par l'avocat ; consultation sous profil assistant", "La plaidoirie devient immédiatement consultable par l'assistant", "Conforme"],
            ["4. Export Word (.docx)", "Téléchargement du document depuis l'étape 5 de l'atelier", "Fichier .docx propre, armoiries présentes, police Noto Naskh RTL", "Conforme"],
            ["5. Étanchéité multi-tenant", "Tentative d'accès par URL directe à une ressource d'un autre cabinet", "Code HTTP 404/403 renvoyé, aucune donnée exposée", "Conforme"],
            ["6. Verrouillage packs essai", "Tentative d'achat d'un pack de crédits en période d'essai", "Section masquée dans l'UI et rejet HTTP 403 par l'API", "Conforme"],
            ["7. Repère IA journalier", "Atteinte du seuil préventif de requêtes d'assistance IA", "Affichage de la modale de choix (Continuer / Attendre demain)", "Conforme"],
            ["8. Audit BDD sécurisé", "Tentative de connexion HTTP directe sur Adminer ; ouverture via SSH", "Rejet public 404/308 ; connexion réussie via tunnel localhost:8088", "Conforme"],
            ["9. Qualification Entreprise", "Demande d'essai Entreprise sur la page des tarifs", "Redirection sur /commercial?intent=enterprise et enregistrement lead", "Conforme"],
            ["10. Parrainage cabinet", "Création de compte filleul avec code de parrainage", "+14 jours d'essai appliqués au filleul, bonus parrain prêt", "Conforme"],
        ],
        col_widths=[3.5, 5.5, 5.5, 1.8],
    )

    heading(doc, "7.2 Déploiement en production sur VPS", 2)
    add_para(
        doc,
        "La plateforme est déployée et activement maintenue sur un serveur VPS dédié (adresse IP : 51.38.78.23) sous le nom de domaine "
        "hautement disponible https://lexhub.space. Le pipeline de déploiement s'appuie sur GitHub Actions pour la construction automatisée "
        "des images Docker (frontend, backend, celery) publiées sur le registre GitHub Packages (GHCR), garantissant une reproductibilité sans faille.",
    )

    heading(doc, "7.3 Risques identifiés et mesures palliatives", 2)
    bullet(doc, "Variabilité de la qualité micro : Un environnement très bruyant peut altérer la reconnaissance vocale. Mesure palliative : affichage visuel du volume sonore et possibilité de reprise textuelle manuelle directe.")
    bullet(doc, "Secret médical et pièces sensibles : Certaines affaires pénales ou familiales comportent des éléments hautement confidentiels. Mesure palliative : chiffrement au repos des documents sur le stockage objet et masquage automatique des données sensibles.")

    # -------------------------------------------------------------
    # Chapitre 8 — Conclusion et perspectives
    # -------------------------------------------------------------
    heading(doc, "Chapitre 8 — Conclusion et perspectives", 1)

    heading(doc, "8.1 Bilan du projet de fin d'année", 2)
    add_para(
        doc,
        "Le projet de fin d'année LexHub, réalisé au sein de la société WEBVOICE, a permis d'atteindre l'intégralité des objectifs fixés au cahier des charges. "
        "En deux mois intensifs de travail d'ingénierie logicielle, une solution SaaS complète et prête pour la commercialisation a été conçue, développée "
        "et mise en production sur https://lexhub.space.",
    )
    add_para(
        doc,
        "Ce projet a constitué une opportunité exceptionnelle d'appliquer les compétences acquises au cours des deux années du cycle ingénieur en Génie "
        "Informatique à l'ENSA Tétouan : modélisation logicielle avancée, développement full-stack moderne (Next.js, FastAPI, PostgreSQL), intégration "
        "d'algorithmes d'intelligence artificielle ancrés sur la réalité métier, sécurité des systèmes d'information et devops.",
    )

    heading(doc, "8.2 Perspectives d'évolution produit", 2)
    numbered(doc, "Enrichissement du lexique juridique personnalisé : Possibilité pour chaque cabinet de définir son dictionnaire d'abréviations et de formules procédurales récurrentes.")
    numbered(doc, "Connecteur direct Mahakim : Automatisation de la synchronisation des dates d'audience directement depuis le portail du Ministère de la Justice marocain.")
    numbered(doc, "Finalisation de l'agrément bancaire CMI / PayZone : Intégration du paiement par carte bancaire marocaine pour l'activation instantanée des abonnements payants.")
    numbered(doc, "Application mobile complémentaire : Extension mobile (iOS / Android) dédiée exclusivement à la dictée nomade en sortie de salle d'audience.")

    # -------------------------------------------------------------
    # Bibliographie / Webographie
    # -------------------------------------------------------------
    heading(doc, "Bibliographie et Webographie", 1)
    numbered(doc, "Royaume du Maroc — Dahir n° 1-08-101 du 20 chaoual 1429 (20 octobre 2008) portant promulgation de la loi n° 28-08 organisant la profession d'avocat au Maroc. Bulletin Officiel n° 5680.")
    numbered(doc, "Royaume du Maroc — Dahir n° 1-74-447 du 11 ramadan 1394 (28 septembre 1974) approuvant le texte du Code de procédure civile marocain.")
    numbered(doc, "W3C — Web Speech API Specification, W3C Community Group. https://wicg.github.io/speech-api/")
    numbered(doc, "Next.js Documentation — React Framework for the Web, Vercel. https://nextjs.org/docs")
    numbered(doc, "FastAPI Documentation — Modern, fast (high-performance), web framework for building APIs with Python. https://fastapi.tiangolo.com")
    numbered(doc, "SQLAlchemy Documentation — The Database Toolkit for Python. https://docs.sqlalchemy.org")
    numbered(doc, "PostgreSQL Global Development Group — PostgreSQL 15 Documentation. https://www.postgresql.org/docs/15/")
    numbered(doc, "Docker Inc. — Docker Engine & Compose Documentation. https://docs.docker.com")
    numbered(doc, "WEBVOICE — Solutions informatiques, VoIP, web et mobile. Siège : Tanger. https://webvoice.pro")
    numbered(doc, "LexHub — Plateforme d'assistance IA pour avocats en production. https://lexhub.space")
    numbered(doc, "Dépôt GitHub du projet — https://github.com/anadouae/Plateforme-d-Assistance-en-IA-pour-Avocats")

    # -------------------------------------------------------------
    # Annexes — Cahier des captures d'écran réelles
    # -------------------------------------------------------------
    doc.add_page_break()
    heading(doc, "Annexes — Captures d'écran de la version en production", 1)
    add_para(
        doc,
        "Les figures suivantes illustrent le parcours utilisateur réel au sein de la plateforme LexHub déployée sur https://lexhub.space, "
        "démontrant la concrétisation fonctionnelle de l'ensemble des modules d'ingénierie logicielle décrits dans ce rapport.",
        italic=True,
    )

    screens = [
        ("01-accueil.png", "Écran d'accueil public et proposition de valeur LexHub (https://lexhub.space)"),
        ("02-connexion.png", "Formulaire de connexion sécurisée avec authentification par session et JWT"),
        ("10-tableau-de-bord.png", "Tableau de bord principal du cabinet : métriques d'activité et accès rapide"),
        ("11-dossiers.png", "Gestionnaire des dossiers judiciaires avec filtres et recherche instantanée"),
        ("14b-plaidoirie-workspace.png", "Atelier de plaidoirie : navigation guidée à travers les cinq étapes métier"),
        ("14c-transcription-fusha.png", "Module de transcription : texte arabe nettoyé avec surlignage orange des corrections"),
        ("19-export-document.png", "Aperçu du document officiel et bouton d'export Microsoft Word (.docx) 100 % éditable"),
        ("15-planning.png", "Module de planning : agenda visuel des audiences et rappels automatiques"),
        ("23-activite-cabinet.png", "Fil d'activité collaboratif du cabinet pour la traçabilité des opérations"),
        ("16-equipe.png", "Gestion de l'équipe du cabinet : attribution des rôles et invitation d'assistants"),
        ("22a-admin-dashboard.png", "Tableau de bord de supervision de la plateforme (administration WebVoice)"),
    ]

    for fname, caption in screens:
        img_path = MAQUETTES / fname
        if img_path.exists():
            add_figure(doc, img_path, caption, width_cm=14.5)

    # -------------------------------------------------------------
    # Sauvegardes multiples
    # -------------------------------------------------------------
    name = "01_Rapport_PFA_LexHub.docx"
    paths = [
        OUT_REPO / name,
        OUT_PFA / name,
        OUT_PFA / "final" / name,
        DESKTOP / name,
        REPO / "docs" / "rapport-pfa" / "livrables" / "00_Rapport_PFA_LexHub.docx",
    ]

    saved = []
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            doc.save(str(path))
            saved.append(str(path))
            print(f"[OK] Sauvegardé avec succès : {path}")
        except PermissionError:
            print(f"[VERROUILLÉ] Fichier ouvert par un autre programme : {path}")
        except Exception as e:
            print(f"[ERREUR] Impossible de sauvegarder {path} : {e}")

    return saved


if __name__ == "__main__":
    res = build()
    print(f"\nTerminé ! {len(res)} copies du Rapport PFA générées.")
