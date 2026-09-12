from pathlib import Path

path = Path(r"C:\Users\daurinia\Desktop\Avocat-AI-Assistance\backend\app\services\billing.py")
text = path.read_text(encoding="utf-8")
start = text.index("# ---------------------------------------------------------------------------\n# Quotas IA")
end = text.index("DEFAULT_PLANS: list[dict[str, Any]] = [")
new_block = '''# ---------------------------------------------------------------------------
# Quotas IA — SaaS attractif + marge protégée (anti-drain OpenAI)
# Poids ≈ coût relatif. Cible COGS ~10–20 % du prix en usage réel.
# Enterprise = fair-use chiffré (pas d'illimité abusif).
# ---------------------------------------------------------------------------
AI_ACTION_CREDITS: dict[str, int] = {
    "polish": 1,
    "ask": 2,
    "clarify": 3,
    "synthesis": 4,
    "summarize": 4,
    "revise": 5,
    "analyse": 8,
    "cle_de_barre": 8,
    "compose": 10,
}

AI_MONTHLY_LIMITS: dict[str, dict[str, int]] = {
    "free": {
        "ai_credits": 50,
        "synthesis": 3,
        "cle_de_barre": 1,
        "analyse": 1,
        "ask": 10,
        "revise": 8,
    },
    "solo": {
        "ai_credits": 600,
        "synthesis": 25,
        "cle_de_barre": 10,
        "analyse": 12,
        "ask": 100,
        "revise": 60,
    },
    "pro": {
        "ai_credits": 2000,
        "synthesis": 100,
        "cle_de_barre": 50,
        "analyse": 50,
        "ask": 400,
        "revise": 250,
    },
    "enterprise": {
        "ai_credits": 5000,
        "synthesis": 300,
        "cle_de_barre": 150,
        "analyse": 150,
        "ask": 1200,
        "revise": 600,
    },
}

AI_DAILY_CREDIT_CAPS: dict[str, int] = {
    "free": 12,
    "solo": 50,
    "pro": 180,
    "enterprise": 300,
}

AI_CONCURRENT_SLOTS: dict[str, int] = {
    "free": 1,
    "solo": 1,
    "pro": 2,
    "enterprise": 3,
}

HEAVY_AI_ACTIONS = frozenset({"compose", "revise", "analyse", "cle_de_barre"})


PAST_DUE_GRACE_DAYS = 7  # jours après échec avant restriction IA/plaidoirie


def ai_limit_for(plan_slug: str, action: str) -> int:
    return int(AI_MONTHLY_LIMITS.get(plan_slug, AI_MONTHLY_LIMITS["free"]).get(action, 0))


def ai_credit_cost(action: str) -> int:
    return int(AI_ACTION_CREDITS.get(action, 2))


def ai_daily_cap_for(plan_slug: str) -> int:
    return int(AI_DAILY_CREDIT_CAPS.get(plan_slug, AI_DAILY_CREDIT_CAPS["free"]))


def ai_concurrent_slots_for(plan_slug: str) -> int:
    return int(AI_CONCURRENT_SLOTS.get(plan_slug, 1))


def openai_model_for_plan(plan_slug: str, action: str) -> str:
    """Free / léger Solo → mini ; lourds + Pro/Enterprise → gpt-4o."""
    from app.core.config import settings

    premium = (settings.OPENAI_MODEL or "gpt-4o").strip() or "gpt-4o"
    mini = (getattr(settings, "OPENAI_MODEL_LIGHT", None) or "gpt-4o-mini").strip()
    slug = (plan_slug or "free").strip().lower()
    if slug == "free":
        return mini
    if slug == "solo" and action not in HEAVY_AI_ACTIONS:
        return mini
    return premium


'''
path.write_text(text[:start] + new_block + text[end:], encoding="utf-8")
print("OK quotas", start, end)

# Patch plan numbers + highlights via simple replaces
text = path.read_text(encoding="utf-8")
repls = [
    ('"max_plaidoiries_month": 5,\n        "features": [FEATURE_DICTATION, FEATURE_EXPORT_DOCX, FEATURE_SYNTHESIS, FEATURE_CLE_DE_BARRE, FEATURE_PII],\n        "is_public": True,\n        "is_recommended": False,\n        "sort_order": 10,\n        "trial_days": 0,\n        "highlights": [\n            "Gratuit pour toujours — quotas IA limités",\n            "1 avocat — 0 assistant",\n            "Jusqu\'à 5 dossiers · 5 plaidoiries / mois",\n            "100 crédits IA ChatGPT / mois",\n            "5 synthèses · 2 clés de barre · 15 révisions",\n            "Dictée arabe · Export Word",\n        ],\n        "highlights_ar": [\n            "مجاني دائماً — حصص ذكاء محدودة",\n            "محامٍ واحد — بدون مساعد",\n            "حتى 5 ملفات · 5 مرافعات / شهر",\n            "100 رصيد ذكاء ChatGPT / شهر",\n            "5 تلخيصات · مذكرتان · 15 تعديلاً",\n            "إملاء عربي · تصدير Word",\n        ],',
     '"max_plaidoiries_month": 3,\n        "features": [FEATURE_DICTATION, FEATURE_EXPORT_DOCX, FEATURE_SYNTHESIS, FEATURE_CLE_DE_BARRE, FEATURE_PII],\n        "is_public": True,\n        "is_recommended": False,\n        "sort_order": 10,\n        "trial_days": 0,\n        "highlights": [\n            "Gratuit pour toujours — idéal pour tester",\n            "3 plaidoiries · 50 crédits IA / mois",\n            "ChatGPT léger · Export Word",\n            "1 analyse · 8 révisions · plafond journalier",\n            "Passez à Solo dès que le cabinet démarre",\n        ],\n        "highlights_ar": [\n            "مجاني دائماً — للتجربة",\n            "3 مرافعات · 50 رصيد ذكاء / شهر",\n            "ChatGPT · تصدير Word",\n            "تحليل واحد · 8 تعديلات",\n            "الترقية إلى Solo عند الانطلاق",\n        ],'),
    ('"max_plaidoiries_month": 40,', '"max_plaidoiries_month": 35,'),
    ('"max_plaidoiries_month": 150,', '"max_plaidoiries_month": 120,'),
    ('"max_plaidoiries_month": 400,', '"max_plaidoiries_month": 350,'),
    ('"Dossiers illimités · 40 plaidoiries / mois",\n            "800 crédits IA ChatGPT / mois",\n            "30 synthèses · 12 clés · 80 révisions",',
     '"Dossiers illimités · 35 plaidoiries / mois",\n            "600 crédits IA / mois · gpt-4o sur rédaction",\n            "Plafond journalier anti-abus inclus",'),
    ('"Jusqu\'à 5 avocats + 3 assistants",\n            "150 plaidoiries · 3000 crédits IA / mois",\n            "Analyses dossier, révisions, chat pièces inclus",\n            "Clé de barre + ChatGPT gpt-4o",',
     '"Jusqu\'à 5 avocats + 3 assistants",\n            "120 plaidoiries · 2000 crédits IA / mois",\n            "Analyses, révisions, chat pièces · gpt-4o",\n            "Support prioritaire · anti-abus cabinet",'),
    ('"Jusqu\'à 15 avocats + 10 assistants",\n            "400 plaidoiries · crédits IA illimités*",\n            "Analyses & synthèses illimitées*",\n            "ChatGPT gpt-4o · branding cabinet",\n            "*usage raisonnable cabinet — anti-abus actif",',
     '"Jusqu\'à 15 avocats + 10 assistants",\n            "350 plaidoiries · 5000 crédits fair-use / mois",\n            "Plafond journalier + slots parallèles",\n            "ChatGPT gpt-4o · branding cabinet",\n            "Pas d\'illimité abusif — marge protégée",'),
]
for a, b in repls:
    if a not in text:
        print("MISS", a[:60])
    else:
        text = text.replace(a, b, 1)
        print("OK replace", a[:40])
path.write_text(text, encoding="utf-8")
print("done")
