#!/usr/bin/env python3
"""Génère les diagrammes PNG Sanad pour docs + présentation."""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "diagrammes"
OUT.mkdir(parents=True, exist_ok=True)

NAVY = "#0B1F4A"
GOLD = "#D2B589"
CREAM = "#F5F0E8"
WHITE = "#FFFFFF"
MUTED = "#4A5568"
GREEN = "#1a3a2a"
LIGHT = "#E8EEF7"


def _fig(w=14, h=8):
    fig, ax = plt.subplots(figsize=(w, h), dpi=160)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    fig.patch.set_facecolor(CREAM)
    ax.set_facecolor(CREAM)
    return fig, ax


def box(ax, x, y, w, h, text, fc=WHITE, ec=NAVY, tc=NAVY, fs=10, lw=1.6, bold=False):
    p = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.3,rounding_size=1.2",
        facecolor=fc, edgecolor=ec, linewidth=lw, zorder=2,
    )
    ax.add_patch(p)
    ax.text(
        x + w / 2, y + h / 2, text,
        ha="center", va="center", fontsize=fs,
        color=tc, fontfamily="DejaVu Sans",
        fontweight="bold" if bold else "normal",
        zorder=3, wrap=True,
    )


def arrow(ax, x1, y1, x2, y2, color=NAVY):
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle="-|>", color=color, lw=1.8),
        zorder=1,
    )


def title(ax, text, y=94):
    ax.text(50, y, text, ha="center", va="center", fontsize=18,
            color=NAVY, fontfamily="DejaVu Sans", fontweight="bold")
    ax.add_patch(Rectangle((20, y - 3.2), 60, 0.35, facecolor=GOLD, edgecolor="none"))


def save(fig, name):
    path = OUT / name
    fig.savefig(path, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"OK → {path}")


def diagram_architecture():
    fig, ax = _fig(14, 8.2)
    title(ax, "Sanad — Architecture principale")

    # Client
    box(ax, 3, 72, 18, 14, "Navigateur\n(Avocat / Assistant)\nlocalhost:3000", fc=NAVY, tc=GOLD, fs=9, bold=True)

    # Frontend
    box(ax, 28, 72, 20, 14, "Frontend\nNext.js · TypeScript\nTailwind CSS", fc=WHITE, fs=10, bold=True)

    # Backend
    box(ax, 56, 68, 22, 18, "Backend API\nFastAPI · Python\nJWT · Multi-tenant\n:8001", fc=NAVY, tc=GOLD, fs=10, bold=True)

    # Data layer
    box(ax, 8, 28, 16, 14, "PostgreSQL\nDonnées métier\n:5432", fc=LIGHT, fs=9, bold=True)
    box(ax, 28, 28, 16, 14, "MinIO\nFichiers docs\n:9000", fc=LIGHT, fs=9, bold=True)
    box(ax, 48, 28, 16, 14, "Redis\nCache / Celery\n:6379", fc=LIGHT, fs=9, bold=True)
    box(ax, 68, 28, 16, 14, "Ollama / LLM\nCorrection IA\n:11434", fc=LIGHT, fs=9, bold=True)
    box(ax, 40, 8, 20, 12, "ChromaDB\nIndex & corpus juridique", fc=LIGHT, fs=9, bold=True)

    # Flow banner
    box(ax, 8, 50, 84, 10,
        "Flux cœur :  Dicter  →  Transcrire & corriger  →  Modifier  →  Export PDF / DOC  →  Classer dossier",
        fc=GREEN, tc=WHITE, fs=10, bold=True)

    arrow(ax, 21, 79, 28, 79)
    arrow(ax, 48, 79, 56, 79)
    arrow(ax, 67, 68, 16, 42)
    arrow(ax, 67, 68, 36, 42)
    arrow(ax, 67, 68, 56, 42)
    arrow(ax, 67, 68, 76, 42)
    arrow(ax, 67, 68, 50, 20)

    ax.text(50, 2, "Isolation par cabinet_id · Rôles : avocat / assistant / admin_cabinet",
            ha="center", fontsize=9, color=MUTED)
    save(fig, "01-architecture-principale.png")


def diagram_parcours_plaidoirie():
    fig, ax = _fig(14, 7.5)
    title(ax, "Cœur métier — Parcours plaidoirie")

    steps = [
        (4, "1. Dicter", "Micro arabe\nou saisie"),
        (23, "2. Transcrire\n& corriger", "IA : texte propre\nsans inventer"),
        (42, "3. Modifier", "Vérifier · ajouter\néditer librement"),
        (61, "4. Exporter", "PDF / Imprimer\nou fichier DOC"),
        (80, "5. Classer", "Dossier précis\ndu cabinet"),
    ]
    for i, (x, t, d) in enumerate(steps):
        fc = NAVY if i % 2 == 0 else WHITE
        tc = GOLD if i % 2 == 0 else NAVY
        box(ax, x, 45, 16, 28, f"{t}\n\n{d}", fc=fc, tc=tc, fs=10, bold=True)
        if i < len(steps) - 1:
            arrow(ax, x + 16.2, 59, steps[i + 1][0] - 0.4, 59, GOLD)

    box(ax, 10, 18, 80, 16,
        "Avocat : dicte, corrige, modifie, exporte, classe\n"
        "Assistant : consulte les plaidoiries réalisées · export PDF / DOC (sans dictée)",
        fc=CREAM, ec=GOLD, fs=11, bold=True)
    ax.text(50, 8, "Sanad · « Deux gestes. Tout le reste suit. »",
            ha="center", fontsize=11, color=MUTED, style="italic")
    save(fig, "02-parcours-plaidoirie.png")


def diagram_roles():
    fig, ax = _fig(13, 7.2)
    title(ax, "Rôles et espaces")

    box(ax, 5, 35, 28, 45,
        "AVOCAT\n\n• Dicter la plaidoirie\n• Voir texte corrigé\n• Modifier / vérifier\n• Export PDF ou DOC\n• Classer au dossier\n• Piloter la stratégie",
        fc=NAVY, tc=WHITE, fs=10, bold=True)
    box(ax, 36, 35, 28, 45,
        "ASSISTANT\n\n• Consulter plaidoiries\n• Export PDF / DOC\n• Préparer les pièces\n• Alimenter le dossier\n• Suivre le planning\n• Pas de dictée",
        fc=WHITE, tc=NAVY, fs=10, bold=True)
    box(ax, 67, 35, 28, 45,
        "ADMIN CABINET\n\n• Gérer l’équipe\n• Paramètres cabinet\n• Accès modules\n  métier\n• Invitations\n• Rôles membres",
        fc=GREEN, tc=WHITE, fs=10, bold=True)
    ax.text(50, 18, "Chaque utilisateur appartient à un cabinet (multi-tenant).",
            ha="center", fontsize=11, color=MUTED)
    ax.text(50, 12, "Isolation applicative par cabinet_id sur toutes les requêtes.",
            ha="center", fontsize=10, color=MUTED)
    save(fig, "03-roles.png")


def diagram_er():
    fig, ax = _fig(14, 9)
    title(ax, "Modèle de données — vue d’ensemble", y=96)

    tables = [
        (5, 70, 22, 18, "cabinets\nid · name · city\nstatus · barreau"),
        (35, 70, 22, 18, "users\nid · email · role\ncabinet_id · 2FA"),
        (65, 70, 22, 18, "cases\nid · reference\nclient · status\ncabinet_id"),
        (5, 38, 22, 18, "documents\nfile · OCR text\ncase_id\ncabinet_id"),
        (35, 38, 22, 18, "agenda_events\ntitle · type\nstarts_at\ncase_id?"),
        (65, 38, 22, 18, "case_tasks\ntitle · status\ndue_at\ncase_id?"),
        (20, 8, 22, 16, "case_notes\ntitle · body\ncase_id?"),
        (50, 8, 22, 16, "audit_logs\naction · ip\ncabinet_id"),
        (78, 8, 18, 16, "email_tokens\nhash · type\nexpires"),
    ]
    for x, y, w, h, t in tables:
        box(ax, x, y, w, h, t, fc=WHITE, fs=8.5, bold=True)

    # relation hints
    arrow(ax, 27, 79, 35, 79)
    arrow(ax, 57, 79, 65, 79)
    arrow(ax, 76, 70, 76, 56)
    arrow(ax, 46, 70, 46, 56)
    arrow(ax, 16, 70, 16, 56)

    ax.text(50, 2, "11 tables PostgreSQL · Fichiers binaires dans MinIO (chemin cabinet/dossier/fichier)",
            ha="center", fontsize=9, color=MUTED)
    save(fig, "04-modele-donnees.png")


def diagram_stack():
    fig, ax = _fig(12, 7)
    title(ax, "Couches techniques")
    layers = [
        (78, "Présentation", "Next.js · React · Tailwind · FR / AR / EN", NAVY, GOLD),
        (58, "API métier", "FastAPI · Auth JWT · Rôles · Validation", WHITE, NAVY),
        (38, "Services", "Dictée/IA · OCR · Synthèse · Celery", LIGHT, NAVY),
        (18, "Persistance", "PostgreSQL · MinIO · Redis · ChromaDB", GREEN, WHITE),
    ]
    for y, name, detail, fc, tc in layers:
        box(ax, 15, y, 70, 14, f"{name}\n{detail}", fc=fc, tc=tc, fs=12, bold=True)
    save(fig, "05-couches-techniques.png")


if __name__ == "__main__":
    diagram_architecture()
    diagram_parcours_plaidoirie()
    diagram_roles()
    diagram_er()
    diagram_stack()
    print(f"\nDiagrammes → {OUT}")
