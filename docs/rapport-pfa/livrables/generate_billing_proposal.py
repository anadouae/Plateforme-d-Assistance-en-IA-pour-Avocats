# -*- coding: utf-8 -*-
"""Génère la proposition commerciale LexHub (étude de marché + plans) pour WEBVOICE."""

from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

OUT = Path(__file__).resolve().parent


def set_run_font(run, name="Calibri", size=11, bold=False, italic=False):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic


def add_para(doc, text, *, bold=False, italic=False, size=11, align=None, space_after=6):
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    r = p.add_run(text)
    set_run_font(r, size=size, bold=bold, italic=italic)
    return p


def heading(doc, text, level=1):
    p = doc.add_heading(text, level=level)
    for run in p.runs:
        run.font.color.rgb = RGBColor(0x1A, 0x36, 0x5D)
    return p


def shade(cell, hex_color):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), hex_color)
    shd.set(qn("w:val"), "clear")
    tcPr.append(shd)


def table(doc, headers, rows, widths=None):
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell.text = ""
        p = cell.paragraphs[0]
        r = p.add_run(h)
        set_run_font(r, bold=True, size=9)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        shade(cell, "1A365D")
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            cell = t.rows[ri + 1].cells[ci]
            cell.text = ""
            p = cell.paragraphs[0]
            r = p.add_run(val)
            set_run_font(r, size=8)
            if ri % 2:
                shade(cell, "F0F4F8")
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Cm(w)
    doc.add_paragraph()
    return t


def setup(title, subtitle):
    doc = Document()
    s = doc.sections[0]
    s.top_margin = Cm(1.8)
    s.bottom_margin = Cm(1.8)
    s.left_margin = Cm(2)
    s.right_margin = Cm(2)
    hp = s.header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    hr = hp.add_run("LexHub — Proposition commerciale — WEBVOICE / ENSA")
    set_run_font(hr, size=8, italic=True)
    add_para(doc, "LexHub — Plateforme LegalTech pour cabinets marocains", bold=True, size=12, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
    add_para(doc, "Destinataire : Hatim Benhaddou (WEBVOICE) — Stagiaire : Douae EL ASSAL", size=10, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
    add_para(doc, title, bold=True, size=16, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=4)
    add_para(doc, subtitle, italic=True, size=10, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=12)
    return doc


def build_market_study():
    doc = setup(
        "Étude de marché & proposition de plans tarifaires",
        "Document de cadrage rentabilité LexHub — août 2026 — sans engagement de paiement réel (phase préparation)",
    )

    heading(doc, "1. Synthèse exécutive")
    add_para(
        doc,
        "LexHub se positionne comme un SaaS B2B pour cabinets d'avocats marocains, centré sur la "
        "transformation voix → plaidoirie (arabe), la gestion de dossier et bientôt la génération "
        "d'une clé de barre à partir des pièces. Le marché LegalTech marocain est encore peu saturé "
        "sur la plaidoirie vocale ; les acteurs locaux facturent typiquement entre 99 et 3 490 MAD/mois "
        "selon le positionnement (assistant IA, risque juridique, gestion).",
    )
    add_para(
        doc,
        "Recommandation : modèle freemium + essai Pro 14 jours + 4 plans publics, prix en MAD, "
        "limites par sièges (avocats / assistants) et par usage IA (plaidoiries / mois). "
        "Paiement Stripe (ou CMI / PayZone) en phase 2 — l'environnement produit (plans, quotas, UI, admin) "
        "est livré maintenant en mode démonstration.",
        bold=True,
    )

    heading(doc, "2. Étude de marché (Maroc & références mondiales)")
    heading(doc, "2.1 Concurrentes / adjacentes au Maroc", 2)
    table(
        doc,
        ["Acteur", "Positionnement", "Fourchette observée", "Leçon pour LexHub"],
        [
            ["Kateb.ma", "Rédaction IA juridique", "≈ 490–790 MAD/mois / user", "Prix d'entrée ~500 MAD crédible"],
            ["ADALA", "Assistant juridique multi-usages", "0 → 749 MAD/mois + crédits", "Freemium + packs de crédits"],
            ["Litigo.ma", "Risk / veille tribunaux", "490 → 3 490 MAD/mois", "Tier Business élevé acceptable"],
            ["LegalPlus", "Juridique + admin entreprise", "200 → 890 MAD + essai 14 j", "Essai 14 j = standard marché"],
            ["Beveron / SLC", "Case mgmt corporate", "Éditions par taille d'équipe", "Tarification par sièges"],
        ],
        [3.2, 3.8, 3.8, 4.5],
    )

    heading(doc, "2.2 Références internationales (psychologie d'offre)", 2)
    add_para(
        doc,
        "Cursor, Notion, Clio, Harvey.ai et Doctrine utilisent tous une échelle : essai gratuit du plan "
        "« Pro », un plan Free volontairement limité (hook), un plan Pro mis en avant (« Recommandé »), "
        "un plan Enterprise sur devis. LexHub reprend ce pattern pour maximiser l'upgrade sans agressivité.",
    )
    add_para(
        doc,
        "Métriques d'usage visibles (jours d'essai restants, barre « 12/40 plaidoiries ») créent l'urgence "
        "douce et la transparence — comme dans Cursor.",
    )

    heading(doc, "2.3 Persona & willingness-to-pay", 2)
    add_para(
        doc,
        "Cible primaire : avocat solo / cabinet 2–8 personnes à Casablanca, Rabat, Tanger, Fès, Marrakech. "
        "Pain : ressaisie des plaidoiries, perte de temps, risque de fuite de noms clients vers des IA grand public. "
        "Willingness-to-pay estimée : 400–1 200 MAD/mois pour un outil qui livre une plaidoirie exportable "
        "conforme aux usages marocains, avec confidentialité (anonymisation avant envoi LLM).",
    )

    heading(doc, "3. Proposition de plans recommandés (à valider)")
    add_para(doc, "Devise : MAD HT. Facturation mensuelle ou annuelle (−17 %). Paiement réel : phase 2.", italic=True, size=10)

    table(
        doc,
        ["Plan", "Prix / mois", "Sièges", "Plaidoiries IA / mois", "Différenciateur"],
        [
            ["Découverte (Free)", "0", "1 avocat · 0 assistant", "5", "Hook — découverte produit"],
            ["Solo", "490", "1 avocat · 1 assistant", "40", "Indépendant / petite étude"],
            ["Cabinet Pro ★", "990", "5 avocats · 3 assistants", "200", "Clé de barre + ChatGPT-class + PII"],
            ["Entreprise", "2 490+", "20 · 10 (ou custom)", "Illimité soft", "SLA, onboarding, facture"],
        ],
        [3.2, 2.5, 4.0, 3.5, 4.0],
    )

    heading(doc, "3.1 Détail des entitlements", 2)
    table(
        doc,
        ["Capacité", "Free", "Solo", "Pro", "Entreprise"],
        [
            ["Dossiers", "3", "Illimité", "Illimité", "Illimité"],
            ["Dictée arabe → fusḥā", "Oui", "Oui", "Oui", "Oui"],
            ["Export Word / PDF", "Word seul", "Word+PDF", "Word+PDF", "Word+PDF"],
            ["Anonymisation PII avant IA", "Non", "Oui", "Oui", "Oui"],
            ["Clé de barre depuis pièces", "Non", "Non", "Oui", "Oui"],
            ["Modèle IA premium (OpenAI)", "Non", "Non", "Oui", "Oui"],
            ["Branding cabinet (logo)", "Non", "Oui", "Oui", "Oui"],
            ["Support", "Communauté", "E-mail", "Prioritaire", "Dédié"],
            ["Essai Pro 14 jours", "À l'inscription", "—", "Inclus (cible essai)", "Sur devis"],
        ],
        [4.5, 2.5, 2.5, 2.8, 3.0],
    )

    heading(doc, "3.2 Psychologie d'upsell (pourquoi ces chiffres)", 2)
    add_para(
        doc,
        "• Free trop généreux tue la conversion : 5 plaidoiries + 0 assistant = frustration contrôlée.\n"
        "• Solo à 490 MAD aligne Kateb Essentiel / Litigo Starter — prix « sérieux » sans freiner.\n"
        "• Pro à 990 MAD (≈ 2× Solo) est le sweet spot cabinet : sièges + clé de barre + OpenAI — badge Recommandé.\n"
        "• Entreprise ancre le haut de gamme et rend Pro « raisonnable » (effet d'ancrage).",
    )

    heading(doc, "4. Parcours commercial produit (sans paiement réel pour l'instant)")
    add_para(
        doc,
        "1) Inscription cabinet → essai Cabinet Pro 14 jours automatique.\n"
        "2) Bannière jours restants + barre d'usage dans l'app.\n"
        "3) Page /tarifs publique + Paramètres → Abonnement.\n"
        "4) Bouton « Choisir ce plan » = bascule mock (provider=manual) — prêt pour brancher Stripe/CMI.\n"
        "5) Fin d'essai sans choix → bascule Découverte (Free) avec quotas réduits.\n"
        "6) Admin WebVoice peut créer / éditer / désactiver les plans et assigner un plan à un cabinet.",
    )

    heading(doc, "5. Roadmap technique liée à la rentabilité")
    table(
        doc,
        ["Phase", "Livrable", "Statut proposé"],
        [
            ["P0 (maintenant)", "Plans, essai, quotas, UI billing, admin plans", "À livrer"],
            ["P0", "Provider OpenAI + masquage PII (noms → tokens)", "À livrer (socle)"],
            ["P1", "Clé de barre IA à partir des pièces du dossier", "Socle + itération"],
            ["P1", "Paiement réel (Stripe Checkout ou CMI Maroc)", "Préparé, non branché"],
            ["P2", "Factures PDF, TVA, renouvellement auto, webhooks", "Après validation WEBVOICE"],
        ],
        [3.0, 8.0, 4.0],
    )

    heading(doc, "6. Projection revenus (hypothèse prudente)")
    add_para(
        doc,
        "Hypothèse année 1 : 40 cabinets payants (25 Solo + 12 Pro + 3 Entreprise) après acquisition "
        "pilotée WEBVOICE / barreaux partenaires.\n"
        "MRR ≈ 25×490 + 12×990 + 3×2490 = 12 250 + 11 880 + 7 470 = 31 600 MAD/mois "
        "(≈ 379 kMAD ARR) avant coûts LLM.\n"
        "Coût IA (ordre de grandeur) : 5–15 % du MRR si quotas respectés et anonymisation + cache.\n"
        "Point mort : ~15–20 Solo équivalents si coûts infra VPS + LLM maîtrisés.",
        size=10,
    )

    heading(doc, "7. Décisions demandées à l'encadrement WEBVOICE")
    add_para(
        doc,
        "1. Valider (ou ajuster) les 4 prix et les quotas sièges / plaidoiries.\n"
        "2. Confirmer l'essai Pro 14 jours à l'inscription.\n"
        "3. Fournir la clé API OpenAI / ChatGPT Pro pour le plan Pro+.\n"
        "4. Choisir le PSP phase 2 : Stripe international vs CMI / PayZone Maroc.\n"
        "5. Autoriser le mode mock « Choisir un plan » en production jusqu'au go-live paiement.",
    )

    heading(doc, "8. Conclusion")
    add_para(
        doc,
        "Cette grille place LexHub dans la fourchette LegalTech marocaine tout en différenciant "
        "par la plaidoirie vocale, la conformité de forme marocaine, la confidentialité (PII) et "
        "la clé de barre. L'implémentation produit suit immédiatement ce document : "
        "environnement billing opérationnel, sans encaissement réel.",
    )

    path = OUT / "05_Etude_marche_et_proposition_plans_LexHub.docx"
    doc.save(path)
    return path


def build_roadmap_tech():
    doc = setup(
        "Cadrage technique post-suivi — LexHub niveau international",
        "Anonymisation PII · OpenAI · Clé de barre · Billing · Admin — août 2026",
    )

    heading(doc, "1. Vision produit (après suivi entreprise)")
    add_para(
        doc,
        "L'avocat dépose les pièces du dossier → LexHub extrait les faits / parties → anonymise les noms "
        "avant tout appel LLM → génère une clé de barre puis une plaidoirie conforme aux usages marocains "
        "→ réinjecte les vrais noms uniquement côté cabinet. Monetisation par abonnements à paliers.",
    )

    heading(doc, "2. Architecture confidentialité (PII)")
    add_para(
        doc,
        "Technique : détection heuristique + liste des parties du dossier (client, adversaire, témoins) "
        "→ remplacement par jetons stables (PARTIE_A, PARTIE_B, TEMOIN_1). "
        "Le mapping reste en base cabinet (jamais envoyé au LLM). Après réponse IA, démasquage local. "
        "Aligné sur le principe minimisation / privacy-by-design (RGPD-like / Loi 09-08).",
    )

    heading(doc, "3. Pipeline clé de barre")
    add_para(
        doc,
        "1. Collecte des textes extraits (OCR) des documents du dossier.\n"
        "2. Anonymisation.\n"
        "3. Prompt métier marocain (faits, moyens, demandes, jurisprudence citée avec prudence).\n"
        "4. Appel modèle premium (OpenAI) si plan Pro+.\n"
        "5. Démasquage + structuration éditable dans l'atelier plaidoirie.\n"
        "6. L'avocat reste responsable du fond (disclaimer déontologique).",
    )

    heading(doc, "4. Billing (mode préparation)")
    add_para(
        doc,
        "Tables subscription_plans + cabinet_subscriptions + usage_counters. "
        "UI type Cursor : jours restants, barre d'usage, comparaison de plans, CTA upgrade. "
        "Admin WebVoice : CRUD plans + assignation manuelle. "
        "Champs external_customer_id / external_subscription_id prêts pour Stripe.",
    )

    heading(doc, "5. Critères « niveau mondial » déjà ciblés")
    add_para(
        doc,
        "• Multi-tenant strict · audit logs · MFA · invitations admin-only\n"
        "• Quotas visibles · essai · plans éditables admin\n"
        "• PII masking avant cloud LLM\n"
        "• Export Word/PDF institutionnel\n"
        "• Temps réel (notifications) · déploiement TLS lexhub.space\n"
        "À venir : paiement réel, facturation, SLA Entreprise, monitoring usage LLM par cabinet",
    )

    path = OUT / "06_Cadrage_technique_billing_PII_cle_de_barre.docx"
    doc.save(path)
    return path


if __name__ == "__main__":
    for p in (build_market_study(), build_roadmap_tech()):
        print(p, p.stat().st_size)
