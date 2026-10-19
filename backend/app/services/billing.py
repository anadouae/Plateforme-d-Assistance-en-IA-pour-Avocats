"""Plans LexHub, entitlements, quotas et abonnements (paiement réel = phase 2)."""

from __future__ import annotations

import html
import json
import uuid
from calendar import monthrange
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import (
    BillingCreditPackPurchase,
    BillingCycle,
    BillingInvoice,
    Cabinet,
    CabinetSubscription,
    Case,
    SubscriptionEvent,
    SubscriptionPlan,
    SubscriptionStatus,
    UsageCounter,
    User,
    UserRole,
)

FEATURE_DICTATION = "dictation"
FEATURE_EXPORT_DOCX = "export_docx"
FEATURE_EXPORT_PDF = "export_pdf"
FEATURE_PII = "pii_anonymization"
FEATURE_CLE_DE_BARRE = "cle_de_barre"
FEATURE_OPENAI = "openai_premium"
FEATURE_BRANDING = "custom_branding"
FEATURE_TEAM = "team_invites"
FEATURE_SYNTHESIS = "ai_synthesis"
FEATURE_PRIORITY = "priority_support"

# ---------------------------------------------------------------------------
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

# Essai hybride « durée + plafond » (stratégie rentabilisation) —
# quotas d'essai < forfait payant. Sièges inchangés (équipe peut tester).
# Solo ~67 %, Cabinet ★ 50 %, Entreprise ~36 %.
TRIAL_USAGE_CAPS: dict[str, dict[str, int]] = {
    "solo": {
        "ai_credits": 400,
        "plaidoiries": 25,
        "synthesis": 17,
        "cle_de_barre": 7,
        "analyse": 8,
        "ask": 70,
        "revise": 40,
        "daily_credits": 35,
    },
    "pro": {
        "ai_credits": 1000,
        "plaidoiries": 60,
        "synthesis": 50,
        "cle_de_barre": 25,
        "analyse": 25,
        "ask": 200,
        "revise": 125,
        "daily_credits": 90,
    },
    "enterprise": {
        "ai_credits": 1800,
        "plaidoiries": 120,
        "synthesis": 105,
        "cle_de_barre": 50,
        "analyse": 50,
        "ask": 420,
        "revise": 210,
        "daily_credits": 105,
    },
}

AI_CONCURRENT_SLOTS: dict[str, int] = {
    "free": 1,
    "solo": 1,
    "pro": 2,
    "enterprise": 3,
}

HEAVY_AI_ACTIONS = frozenset({"compose", "revise", "analyse", "cle_de_barre", "polish"})

# Dépassement facturé (plans payants) — prix public clair MAD / crédit IA
AI_OVERAGE_MAD_PER_CREDIT = 0.25

# Packs prépayés (légèrement dégressifs vs 0,25 MAD / crédit à la demande)
CREDIT_PACKS: list[dict[str, Any]] = [
    {
        "id": "pack_500",
        "credits": 500,
        "price_mad": 110,
        "label": "500 crédits",
        "label_ar": "500 رصيد",
        "unit_mad": 0.22,
    },
    {
        "id": "pack_1000",
        "credits": 1000,
        "price_mad": 200,
        "label": "1 000 crédits",
        "label_ar": "1 000 رصيد",
        "unit_mad": 0.20,
    },
    {
        "id": "pack_2500",
        "credits": 2500,
        "price_mad": 450,
        "label": "2 500 crédits",
        "label_ar": "2 500 رصيد",
        "unit_mad": 0.18,
    },
]

PACK_EXPIRY_MONTHS = 12
PACK_BANNER_USAGE_RATIO = 0.80  # bannière « besoin de crédits » si forfait ≥ 80 %
PACK_UPGRADE_NUDGE_MIN_PURCHASES = 2  # sur 3 mois glissants

# Sièges avocat supplémentaires — Cabinet (pro) uniquement
EXTRA_AVOCAT_SEAT_MAD_MONTHLY = 99
MAX_EXTRA_AVOCAT_SEATS_PRO = 5  # 5 inclus + 5 = 10 max avant Entreprise

PAST_DUE_GRACE_DAYS = 7  # jours après échec avant restriction IA/plaidoirie


def is_active_paying(ent: "Entitlements") -> bool:
    """Abonnement réel payant — pas Découverte, pas essai."""
    slug = (ent.plan.slug or "free").lower()
    return slug != "free" and (ent.status or "") == SubscriptionStatus.ACTIVE.value


def is_trial_status(ent: "Entitlements") -> bool:
    return (ent.status or "") in (SubscriptionStatus.TRIAL.value, "trial")


def ai_limit_for(plan_slug: str, action: str) -> int:
    return int(AI_MONTHLY_LIMITS.get(plan_slug, AI_MONTHLY_LIMITS["free"]).get(action, 0))


def plan_ai_credits_limit(plan: SubscriptionPlan) -> int:
    """Crédits IA mensuels : colonne plan (éditable admin) sinon grille code."""
    raw = getattr(plan, "max_ai_credits_month", None)
    if raw is not None and int(raw) >= 0:
        return int(raw)
    return ai_limit_for(plan.slug, "ai_credits")


def trial_usage_cap(plan_slug: str, key: str) -> int | None:
    """Plafond d'essai pour une clé (ai_credits, plaidoiries, …). None = pas de plafond dédié."""
    caps = TRIAL_USAGE_CAPS.get((plan_slug or "").strip().lower())
    if not caps:
        return None
    if key not in caps:
        return None
    return int(caps[key])


def apply_trial_cap(plan_slug: str, key: str, paid_limit: int, *, in_trial: bool) -> int:
    """Pendant l'essai : min(forfait payant, plafond essai). Hors essai : forfait payant."""
    if not in_trial or paid_limit < 0:
        return paid_limit
    capped = trial_usage_cap(plan_slug, key)
    if capped is None:
        return paid_limit
    return min(int(paid_limit), int(capped))


def ai_credit_cost(action: str) -> int:
    return int(AI_ACTION_CREDITS.get(action, 2))


def ai_daily_cap_for(plan_slug: str, *, in_trial: bool = False) -> int:
    paid = int(AI_DAILY_CREDIT_CAPS.get(plan_slug, AI_DAILY_CREDIT_CAPS["free"]))
    return apply_trial_cap(plan_slug, "daily_credits", paid, in_trial=in_trial)


def _ai_daily_used(cabinet_id: str | None) -> int:
    if not cabinet_id:
        return 0
    try:
        from app.core.rate_limit import get_cabinet_ai_daily_used

        return int(get_cabinet_ai_daily_used(cabinet_id) or 0)
    except Exception:
        return 0


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


DEFAULT_PLANS: list[dict[str, Any]] = [
    {
        "slug": "free",
        "name": "Découverte",
        "name_ar": "اكتشاف",
        "description": "Gratuit pour toujours — attractif, limité par quotas pour découvrir LexHub.",
        "price_mad_monthly": 0,
        "price_mad_yearly": 0,
        "max_avocats": 1,
        "max_assistants": 0,
        "max_cases": 5,
        "max_plaidoiries_month": 3,
        "features": [FEATURE_DICTATION, FEATURE_EXPORT_DOCX, FEATURE_SYNTHESIS, FEATURE_CLE_DE_BARRE, FEATURE_PII],
        "is_public": True,
        "is_recommended": False,
        "sort_order": 10,
        "trial_days": 0,
        "highlights": [
            "Gratuit pour toujours — idéal pour tester",
            "3 plaidoiries · 50 crédits IA / mois",
            "ChatGPT léger · Export Word",
            "1 analyse · 8 révisions · plafond journalier",
            "Passez à Solo dès que le cabinet démarre",
        ],
        "highlights_ar": [
            "مجاني دائماً — للتجربة",
            "3 مرافعات · 50 رصيد ذكاء / شهر",
            "ChatGPT · تصدير Word",
            "تحليل واحد · 8 تعديلات",
            "الترقية إلى Solo عند الانطلاق",
        ],
    },
    {
        "slug": "solo",
        "name": "Solo",
        "name_ar": "فردي",
        "description": "Pour l'avocat indépendant qui veut un assistant et des exports complets.",
        "price_mad_monthly": 299,
        "price_mad_yearly": 2990,
        "max_avocats": 1,
        "max_assistants": 1,
        "max_cases": -1,
        "max_plaidoiries_month": 35,
        "features": [
            FEATURE_DICTATION,
            FEATURE_EXPORT_DOCX,
            FEATURE_EXPORT_PDF,
            FEATURE_PII,
            FEATURE_BRANDING,
            FEATURE_TEAM,
            FEATURE_SYNTHESIS,
            FEATURE_CLE_DE_BARRE,
        ],
        "is_public": True,
        "is_recommended": False,
        "sort_order": 20,
        "trial_days": 14,
        "highlights": [
            "Essai 14 jours avec carte (annulable)",
            "Pendant l'essai : 400 crédits IA · 25 plaidoiries (puis 600 · 35 en payant)",
            "1 avocat + 1 assistant (2 personnes max)",
            "Dossiers illimités · export Word + PDF · logo cabinet",
            "Plafond journalier anti-abus inclus",
        ],
        "highlights_ar": [
            "محامٍ + مساعد واحد",
            "ملفات غير محدودة · 40 مرافعة / شهر",
            "800 رصيد ذكاء ChatGPT / شهر",
            "30 تلخيصاً · 12 مذكرة · 80 تعديلاً",
            "تصدير Word + PDF + شعار",
        ],
    },
    {
        "slug": "pro",
        "name": "Cabinet",
        "name_ar": "مكتب",
        "description": "Le plan des cabinets en croissance — équipe élargie et IA ChatGPT complète.",
        "price_mad_monthly": 699,
        "price_mad_yearly": 6990,
        "max_avocats": 5,
        "max_assistants": 3,
        "max_cases": -1,
        "max_plaidoiries_month": 120,
        "features": [
            FEATURE_DICTATION,
            FEATURE_EXPORT_DOCX,
            FEATURE_EXPORT_PDF,
            FEATURE_PII,
            FEATURE_CLE_DE_BARRE,
            FEATURE_OPENAI,
            FEATURE_BRANDING,
            FEATURE_TEAM,
            FEATURE_SYNTHESIS,
            FEATURE_PRIORITY,
        ],
        "is_public": True,
        "is_recommended": True,
        "sort_order": 30,
        "trial_days": 30,
        "highlights": [
            "Essai 30 jours avec carte (annulable)",
            "Pendant l'essai : 1 000 crédits · 60 plaidoiries (puis 2 000 · 120)",
            "Jusqu'à 5 avocats + 3 assistants",
            "Analyses, révisions, chat pièces · gpt-4o",
            "Support prioritaire · anti-abus cabinet",
        ],
        "highlights_ar": [
            "حتى 5 محامين + 3 مساعدين",
            "150 مرافعة · 3000 رصيد ذكاء / شهر",
            "تحليل ملفات وتعديلات ودردشة الوثائق",
            "مذكرة مرافعة + ChatGPT",
            "دعم ذو أولوية",
        ],
    },
    {
        "slug": "enterprise",
        "name": "Entreprise",
        "name_ar": "مؤسسة",
        "description": "Grands cabinets — sièges élevés, IA ChatGPT illimitée (usage raisonnable).",
        "price_mad_monthly": 1290,
        "price_mad_yearly": 12900,
        "max_avocats": 15,
        "max_assistants": 10,
        "max_cases": -1,
        "max_plaidoiries_month": 350,
        "features": [
            FEATURE_DICTATION,
            FEATURE_EXPORT_DOCX,
            FEATURE_EXPORT_PDF,
            FEATURE_PII,
            FEATURE_CLE_DE_BARRE,
            FEATURE_OPENAI,
            FEATURE_BRANDING,
            FEATURE_TEAM,
            FEATURE_SYNTHESIS,
            FEATURE_PRIORITY,
        ],
        "is_public": True,
        "is_recommended": False,
        "sort_order": 40,
        "trial_days": 30,
        "highlights": [
            "Essai 30 jours avec carte (annulable)",
            "Pendant l'essai : 1 800 crédits · 120 plaidoiries (puis 5 000 · 350)",
            "Jusqu'à 15 avocats + 10 assistants",
            "ChatGPT gpt-4o · branding cabinet",
            "Pas d'illimité abusif — marge protégée",
        ],
        "highlights_ar": [
            "حتى 15 محامياً + 10 مساعدين",
            "400 مرافعة · أرصدة ذكاء غير محدودة*",
            "تحليل وتلخيص غير محدود*",
            "ChatGPT · شعار المكتب",
            "*استخدام معقول — حماية من الإفراط",
        ],
    },
]

# Features never shown on public pricing (internal quality/privacy)
PUBLIC_HIDDEN_FEATURES = {FEATURE_PII}

MOROCCO_PAYMENT_METHODS = [
    {
        "id": "cmi",
        "name": "Carte bancaire (CMI)",
        "name_ar": "بطاقة بنكية (CMI)",
        "status": "env_ready",
        "blurb": "Environnement prêt — activation opérateur CMI (merchant ID).",
    },
    {
        "id": "payzone",
        "name": "PayZone",
        "name_ar": "PayZone",
        "status": "env_ready",
        "blurb": "Environnement prêt — activation opérateur PayZone.",
    },
    {
        "id": "stripe",
        "name": "Carte internationale",
        "name_ar": "بطاقة دولية",
        "status": "coming_soon",
        "blurb": "Visa / Mastercard — cabinets multi-pays.",
    },
]

CANCEL_REASON_CODES = [
    ("too_expensive", "Trop cher pour notre cabinet"),
    ("missing_features", "Fonctionnalités manquantes"),
    ("switching", "On change d'outil"),
    ("temporary", "Pause temporaire"),
    ("hard_to_use", "Trop complexe à utiliser"),
    ("other", "Autre raison"),
]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _period_ym(dt: datetime | None = None) -> str:
    d = dt or _now()
    return f"{d.year:04d}-{d.month:02d}"


def _add_months(dt: datetime, months: int = 1) -> datetime:
    y, m = dt.year, dt.month + months
    while m > 12:
        m -= 12
        y += 1
    day = min(dt.day, monthrange(y, m)[1])
    return dt.replace(year=y, month=m, day=day)


def features_of(plan: SubscriptionPlan) -> list[str]:
    raw = plan.features_json or "[]"
    try:
        data = json.loads(raw)
        return [str(x) for x in data] if isinstance(data, list) else []
    except Exception:
        return []


def plan_to_dict(plan: SubscriptionPlan, *, public: bool = False) -> dict[str, Any]:
    feats = features_of(plan)
    if public:
        feats = [f for f in feats if f not in PUBLIC_HIDDEN_FEATURES]
    spec = next((p for p in DEFAULT_PLANS if p["slug"] == plan.slug), {})
    return {
        "id": plan.id,
        "slug": plan.slug,
        "name": plan.name,
        "name_ar": plan.name_ar,
        "description": plan.description,
        "price_mad_monthly": plan.price_mad_monthly,
        "price_mad_yearly": plan.price_mad_yearly,
        "max_avocats": plan.max_avocats,
        "max_assistants": plan.max_assistants,
        "max_cases": plan.max_cases,
        "max_plaidoiries_month": plan.max_plaidoiries_month,
        "max_ai_credits_month": plan_ai_credits_limit(plan),
        "features": feats,
        "highlights": list(spec.get("highlights") or []),
        "highlights_ar": list(spec.get("highlights_ar") or []),
        "is_public": plan.is_public,
        "is_recommended": plan.is_recommended,
        "is_active": plan.is_active,
        "sort_order": plan.sort_order,
        "trial_days": plan.trial_days,
    }


def ensure_default_plans(db: Session) -> None:
    """Idempotent seed + sync prices/copy for the 4 recommended plans."""
    for spec in DEFAULT_PLANS:
        existing = db.query(SubscriptionPlan).filter(SubscriptionPlan.slug == spec["slug"]).first()
        feats = json.dumps(spec["features"], ensure_ascii=False)
        if existing:
            # Seed only missing AI credits; do not wipe admin price/quota edits
            credits_default = int(
                AI_MONTHLY_LIMITS.get(spec["slug"], AI_MONTHLY_LIMITS["free"]).get("ai_credits", 50)
            )
            if getattr(existing, "max_ai_credits_month", None) in (None, 0):
                existing.max_ai_credits_month = credits_default
            existing.updated_at = _now()
            continue
        plan = SubscriptionPlan(
            id=str(uuid.uuid4()),
            slug=spec["slug"],
            name=spec["name"],
            name_ar=spec.get("name_ar"),
            description=spec.get("description"),
            price_mad_monthly=spec["price_mad_monthly"],
            price_mad_yearly=spec["price_mad_yearly"],
            max_avocats=spec["max_avocats"],
            max_assistants=spec["max_assistants"],
            max_cases=spec["max_cases"],
            max_plaidoiries_month=spec["max_plaidoiries_month"],
            max_ai_credits_month=int(
                AI_MONTHLY_LIMITS.get(spec["slug"], AI_MONTHLY_LIMITS["free"]).get("ai_credits", 50)
            ),
            features_json=feats,
            is_public=spec["is_public"],
            is_recommended=spec["is_recommended"],
            is_active=True,
            sort_order=spec["sort_order"],
            trial_days=spec["trial_days"],
        )
        db.add(plan)
    db.flush()


def log_subscription_event(
    db: Session,
    cabinet_id: str,
    event_type: str,
    *,
    plan_slug: str | None = None,
    detail: str | None = None,
    created_by: str | None = None,
) -> None:
    db.add(
        SubscriptionEvent(
            id=str(uuid.uuid4()),
            cabinet_id=cabinet_id,
            event_type=event_type,
            plan_slug=plan_slug,
            detail=detail,
            created_by=created_by,
        )
    )
    db.flush()


def get_plan_by_slug(db: Session, slug: str) -> SubscriptionPlan | None:
    ensure_default_plans(db)
    return db.query(SubscriptionPlan).filter(SubscriptionPlan.slug == slug).first()


def start_free_for_cabinet(db: Session, cabinet_id: str) -> CabinetSubscription:
    """Inscription Coursera-like : plan Découverte actif, sans essai payant."""
    ensure_default_plans(db)
    free = get_plan_by_slug(db, "free")
    if not free:
        raise RuntimeError("Plan free manquant")
    existing = (
        db.query(CabinetSubscription).filter(CabinetSubscription.cabinet_id == cabinet_id).first()
    )
    if existing:
        return existing
    now = _now()
    sub = CabinetSubscription(
        id=str(uuid.uuid4()),
        cabinet_id=cabinet_id,
        plan_id=free.id,
        status=SubscriptionStatus.ACTIVE,
        billing_cycle=BillingCycle.MONTHLY,
        trial_ends_at=None,
        current_period_start=now,
        current_period_end=_add_months(now, 1),
        payment_provider="none",
        notes="Découverte (gratuit) à l'inscription",
    )
    db.add(sub)
    db.flush()
    log_subscription_event(db, cabinet_id, "free_started", plan_slug=free.slug, detail="register")
    return sub


def start_trial_for_cabinet(db: Session, cabinet_id: str, *, days: int = 14) -> CabinetSubscription:
    """Legacy — inscription = Découverte (plus d'essai Cabinet auto)."""
    return start_free_for_cabinet(db, cabinet_id)


def start_paid_trial(
    db: Session,
    cabinet_id: str,
    plan_slug: str,
    *,
    billing_cycle: str = "monthly",
    card_last4: str,
    card_brand: str = "card",
) -> CabinetSubscription:
    """Essai payant (Solo/Cabinet/Entreprise) après carte — modèle Coursera."""
    ensure_default_plans(db)
    plan = get_plan_by_slug(db, plan_slug)
    if not plan or not plan.is_active:
        raise HTTPException(status_code=404, detail="Plan introuvable")
    if int(plan.price_mad_monthly or 0) <= 0:
        raise HTTPException(status_code=400, detail="Ce plan n'a pas d'essai payant")

    days = int(plan.trial_days or 0) or 30
    sub = ensure_subscription(db, cabinet_id)
    now = _now()
    cycle = BillingCycle.YEARLY if billing_cycle == "yearly" else BillingCycle.MONTHLY
    sub.plan_id = plan.id
    sub.status = SubscriptionStatus.TRIAL
    sub.billing_cycle = cycle
    sub.trial_ends_at = now + timedelta(days=days)
    sub.current_period_start = now
    sub.current_period_end = sub.trial_ends_at
    sub.payment_provider = f"card_mock:{card_brand}:{card_last4}"
    sub.cancel_at_period_end = False
    sub.cancel_reason_code = None
    sub.cancel_reason_text = None
    sub.cancel_requested_at = None
    try:
        from app.services.referral import apply_referee_trial_bonus

        bonus = apply_referee_trial_bonus(db, cabinet_id, sub)
        if bonus:
            days = days + bonus
    except Exception:
        pass
    sub.notes = f"Essai {days}j {plan.slug} carte ****{card_last4}"
    db.flush()
    log_subscription_event(
        db,
        cabinet_id,
        "paid_trial_started",
        plan_slug=plan.slug,
        detail=f"{days}j:{cycle.value}:****{card_last4}",
    )
    return sub


def ensure_subscription(db: Session, cabinet_id: str) -> CabinetSubscription:
    """Garantit une souscription (backfill → Découverte)."""
    ensure_default_plans(db)
    sub = (
        db.query(CabinetSubscription).filter(CabinetSubscription.cabinet_id == cabinet_id).first()
    )
    if sub:
        return refresh_subscription_status(db, sub)
    return start_free_for_cabinet(db, cabinet_id)


def refresh_subscription_status(db: Session, sub: CabinetSubscription) -> CabinetSubscription:
    """Fin d'essai : carte + pas d'annulation → ACTIVE payant ; sinon → Découverte."""
    now = _now()
    if sub.status == SubscriptionStatus.TRIAL and sub.trial_ends_at:
        end = sub.trial_ends_at
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        if now >= end:
            has_card = str(sub.payment_provider or "").startswith("card_mock")
            if has_card and not sub.cancel_at_period_end:
                cycle = sub.billing_cycle
                sub.status = SubscriptionStatus.ACTIVE
                sub.trial_ends_at = None
                sub.current_period_start = now
                sub.current_period_end = _add_months(
                    now, 12 if cycle == BillingCycle.YEARLY else 1
                )
                sub.notes = (sub.notes or "") + " | Essai terminé → facturation auto"
                db.flush()
                plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == sub.plan_id).first()
                log_subscription_event(
                    db,
                    sub.cabinet_id,
                    "trial_converted_paid",
                    plan_slug=plan.slug if plan else None,
                    detail=str(sub.payment_provider),
                )
                try:
                    from app.services.referral import apply_referrer_reward_on_paid

                    apply_referrer_reward_on_paid(db, sub.cabinet_id)
                except Exception:
                    pass
            else:
                free = get_plan_by_slug(db, "free")
                if free:
                    sub.plan_id = free.id
                    sub.status = SubscriptionStatus.ACTIVE
                    sub.trial_ends_at = None
                    sub.current_period_start = now
                    sub.current_period_end = _add_months(now, 1)
                    sub.cancel_at_period_end = False
                    sub.notes = (sub.notes or "") + " | Essai expiré / annulé → Découverte"
                    db.flush()
                    log_subscription_event(
                        db, sub.cabinet_id, "trial_ended_free", plan_slug="free"
                    )
    return sub


@dataclass
class Entitlements:
    plan: SubscriptionPlan
    subscription: CabinetSubscription
    features: list[str]
    status: str
    trial_days_left: int | None
    period_end: datetime | None
    plaidoiries_used: int
    plaidoiries_limit: int
    avocats_used: int
    assistants_used: int
    cases_used: int
    cle_de_barre_used: int = 0
    cle_de_barre_limit: int = 0
    synthesis_used: int = 0
    synthesis_limit: int = 0
    ai_credits_used: int = 0
    ai_credits_limit: int = 0
    analyse_used: int = 0
    analyse_limit: int = 0
    ask_used: int = 0
    ask_limit: int = 0
    revise_used: int = 0
    revise_limit: int = 0
    on_demand_enabled: bool = False
    on_demand_mad_limit: int | None = None  # None = illimité si enabled ; 0+ = plafond MAD
    ai_overage_credits: int = 0
    payment_mock: bool = True
    past_due_days: int | None = None
    access_restricted: bool = False
    trial_usage_capped: bool = False
    paid_ai_credits_limit: int | None = None
    paid_plaidoiries_limit: int | None = None
    prepaid_ai_credits: int = 0
    extra_avocat_seats: int = 0
    avocats_limit: int = 1
    extra_seat_mad_monthly: int = EXTRA_AVOCAT_SEAT_MAD_MONTHLY
    seats_addon_available: bool = False

    def has(self, feature: str) -> bool:
        return feature in self.features

    @property
    def overage_mad_estimate(self) -> float:
        return round(float(self.ai_overage_credits or 0) * AI_OVERAGE_MAD_PER_CREDIT, 2)

    def to_dict(self) -> dict[str, Any]:
        in_trial = self.status in (
            SubscriptionStatus.TRIAL.value,
            "trial",
        )
        return {
            "plan": plan_to_dict(self.plan),
            "status": self.status,
            "billing_cycle": self.subscription.billing_cycle.value
            if hasattr(self.subscription.billing_cycle, "value")
            else str(self.subscription.billing_cycle),
            "trial_ends_at": self.subscription.trial_ends_at.isoformat()
            if self.subscription.trial_ends_at
            else None,
            "trial_days_left": self.trial_days_left,
            "trial_usage_capped": bool(self.trial_usage_capped),
            "current_period_start": self.subscription.current_period_start.isoformat()
            if self.subscription.current_period_start
            else None,
            "current_period_end": self.period_end.isoformat() if self.period_end else None,
            "cancel_at_period_end": self.subscription.cancel_at_period_end,
            "payment_provider": self.subscription.payment_provider,
            "payment_mock": self.payment_mock,
            "features": self.features,
            "past_due_days": self.past_due_days,
            "access_restricted": self.access_restricted,
            "ai_credit_costs": dict(AI_ACTION_CREDITS),
            "ai_daily_limit": ai_daily_cap_for(self.plan.slug, in_trial=in_trial),
            "ai_daily_used": _ai_daily_used(getattr(self.subscription, "cabinet_id", None)),
            "ai_concurrent_slots": ai_concurrent_slots_for(self.plan.slug),
            "on_demand_enabled": bool(self.on_demand_enabled),
            "on_demand_mad_limit": self.on_demand_mad_limit,
            "on_demand_mad_per_credit": AI_OVERAGE_MAD_PER_CREDIT,
            "on_demand_available": (self.plan.slug or "") != "free",
            "prepaid_ai_credits": int(self.prepaid_ai_credits or 0),
            "extra_avocat_seats": int(self.extra_avocat_seats or 0),
            "extra_seat_mad_monthly": int(self.extra_seat_mad_monthly),
            "seats_addon_available": bool(self.seats_addon_available),
            "credit_packs_available": is_active_paying(self),
            "is_active_paying": is_active_paying(self),
            "is_trial": is_trial_status(self),
            # Catalogue toujours visible (achat uniquement si abonnement payant actif)
            "credit_packs": list(CREDIT_PACKS),
            "usage": {
                "plaidoiries_used": self.plaidoiries_used,
                "plaidoiries_limit": self.plaidoiries_limit,
                "avocats_used": self.avocats_used,
                "avocats_limit": self.avocats_limit,
                "assistants_used": self.assistants_used,
                "assistants_limit": self.plan.max_assistants,
                "cases_used": self.cases_used,
                "cases_limit": self.plan.max_cases,
                "cle_de_barre_used": self.cle_de_barre_used,
                "cle_de_barre_limit": self.cle_de_barre_limit,
                "synthesis_used": self.synthesis_used,
                "synthesis_limit": self.synthesis_limit,
                "ai_credits_used": self.ai_credits_used,
                "ai_credits_limit": self.ai_credits_limit,
                "analyse_used": self.analyse_used,
                "analyse_limit": self.analyse_limit,
                "ask_used": self.ask_used,
                "ask_limit": self.ask_limit,
                "revise_used": self.revise_used,
                "revise_limit": self.revise_limit,
                "ai_overage_credits": self.ai_overage_credits,
                "ai_overage_mad_estimate": self.overage_mad_estimate,
                "paid_ai_credits_limit": self.paid_ai_credits_limit,
                "paid_plaidoiries_limit": self.paid_plaidoiries_limit,
                "prepaid_ai_credits": int(self.prepaid_ai_credits or 0),
            },
        }


def _seat_counts(db: Session, cabinet_id: str) -> tuple[int, int]:
    users = db.query(User).filter(User.cabinet_id == cabinet_id, User.is_active.is_(True)).all()
    avocats = sum(
        1
        for u in users
        if u.role in (UserRole.AVOCAT, UserRole.ADMIN_CABINET)
        and u.role != UserRole.ADMIN_WEBVOICE
    )
    assistants = sum(1 for u in users if u.role == UserRole.ASSISTANT)
    return avocats, assistants


def get_or_create_usage(db: Session, cabinet_id: str) -> UsageCounter:
    ym = _period_ym()
    row = (
        db.query(UsageCounter)
        .filter(UsageCounter.cabinet_id == cabinet_id, UsageCounter.period_ym == ym)
        .first()
    )
    if row:
        return row
    row = UsageCounter(
        id=str(uuid.uuid4()),
        cabinet_id=cabinet_id,
        period_ym=ym,
        plaidoiries_count=0,
        cle_de_barre_count=0,
        synthesis_count=0,
        ai_credits_used=0,
        analyse_count=0,
        ask_count=0,
        revise_count=0,
        ai_overage_credits=0,
    )
    db.add(row)
    db.flush()
    return row


def get_entitlements(db: Session, cabinet_id: str) -> Entitlements:
    cab = db.query(Cabinet).filter(Cabinet.id == cabinet_id).first()
    if not cab:
        raise HTTPException(status_code=404, detail="Cabinet introuvable")
    sub = ensure_subscription(db, cabinet_id)
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == sub.plan_id).first()
    if not plan:
        raise HTTPException(status_code=500, detail="Plan introuvable")
    usage = get_or_create_usage(db, cabinet_id)
    avocats, assistants = _seat_counts(db, cabinet_id)
    cases_used = db.query(Case).filter(Case.cabinet_id == cabinet_id).count()
    trial_left = None
    if sub.status == SubscriptionStatus.TRIAL and sub.trial_ends_at:
        end = sub.trial_ends_at
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        trial_left = max(0, (end - _now()).days)
    period_end = sub.current_period_end or sub.trial_ends_at
    past_due_days = None
    access_restricted = False
    status_val = sub.status.value if hasattr(sub.status, "value") else str(sub.status)
    if status_val == SubscriptionStatus.PAST_DUE.value:
        from app.models import SubscriptionEvent

        ev = (
            db.query(SubscriptionEvent)
            .filter(
                SubscriptionEvent.cabinet_id == cabinet_id,
                SubscriptionEvent.event_type == "payment_failed",
            )
            .order_by(SubscriptionEvent.created_at.desc())
            .first()
        )
        since = ev.created_at if ev else getattr(sub, "updated_at", None) or _now()
        if since.tzinfo is None:
            since = since.replace(tzinfo=timezone.utc)
        past_due_days = max(0, (_now() - since).days)
        access_restricted = past_due_days >= PAST_DUE_GRACE_DAYS

    in_trial = status_val in (SubscriptionStatus.TRIAL.value, "trial")
    slug = plan.slug or "free"
    paid_credits = plan_ai_credits_limit(plan)
    paid_pleas = int(plan.max_plaidoiries_month)
    trial_capped = bool(in_trial and slug in TRIAL_USAGE_CAPS)
    extra_seats = max(0, int(getattr(sub, "extra_avocat_seats", 0) or 0))
    # Solde packs = somme des lots (pas un mélange avec forfait / PAYG)
    try:
        prepaid = pack_balance_total(db, cabinet_id)
        sub.prepaid_ai_credits = prepaid
    except Exception:
        prepaid = max(0, int(getattr(sub, "prepaid_ai_credits", 0) or 0))
    avocats_limit = int(plan.max_avocats) + (extra_seats if slug == "pro" else 0)

    return Entitlements(
        plan=plan,
        subscription=sub,
        features=features_of(plan),
        status=status_val,
        trial_days_left=trial_left,
        period_end=period_end,
        plaidoiries_used=usage.plaidoiries_count,
        plaidoiries_limit=apply_trial_cap(slug, "plaidoiries", paid_pleas, in_trial=in_trial),
        avocats_used=avocats,
        assistants_used=assistants,
        cases_used=cases_used,
        cle_de_barre_used=int(usage.cle_de_barre_count or 0),
        cle_de_barre_limit=apply_trial_cap(
            slug, "cle_de_barre", ai_limit_for(slug, "cle_de_barre"), in_trial=in_trial
        ),
        synthesis_used=int(getattr(usage, "synthesis_count", 0) or 0),
        synthesis_limit=apply_trial_cap(
            slug, "synthesis", ai_limit_for(slug, "synthesis"), in_trial=in_trial
        ),
        ai_credits_used=int(getattr(usage, "ai_credits_used", 0) or 0),
        ai_credits_limit=apply_trial_cap(slug, "ai_credits", paid_credits, in_trial=in_trial),
        analyse_used=int(getattr(usage, "analyse_count", 0) or 0),
        analyse_limit=apply_trial_cap(
            slug, "analyse", ai_limit_for(slug, "analyse"), in_trial=in_trial
        ),
        ask_used=int(getattr(usage, "ask_count", 0) or 0),
        ask_limit=apply_trial_cap(slug, "ask", ai_limit_for(slug, "ask"), in_trial=in_trial),
        revise_used=int(getattr(usage, "revise_count", 0) or 0),
        revise_limit=apply_trial_cap(
            slug, "revise", ai_limit_for(slug, "revise"), in_trial=in_trial
        ),
        on_demand_enabled=bool(getattr(sub, "on_demand_enabled", False)),
        on_demand_mad_limit=getattr(sub, "on_demand_mad_limit", None),
        ai_overage_credits=int(getattr(usage, "ai_overage_credits", 0) or 0),
        payment_mock=True,
        past_due_days=past_due_days,
        access_restricted=access_restricted,
        trial_usage_capped=trial_capped,
        paid_ai_credits_limit=paid_credits if trial_capped else None,
        paid_plaidoiries_limit=paid_pleas if trial_capped else None,
        prepaid_ai_credits=prepaid,
        extra_avocat_seats=extra_seats if slug == "pro" else 0,
        avocats_limit=avocats_limit,
        extra_seat_mad_monthly=EXTRA_AVOCAT_SEAT_MAD_MONTHLY,
        seats_addon_available=slug == "pro",
    )


def require_feature(db: Session, cabinet_id: str, feature: str) -> Entitlements:
    ent = get_entitlements(db, cabinet_id)
    if not ent.has(feature):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Fonctionnalité réservée à un plan supérieur ({feature}). Passez à Cabinet Pro.",
        )
    return ent


def assert_can_invite(db: Session, cabinet_id: str, role: str) -> None:
    ent = get_entitlements(db, cabinet_id)
    if not ent.has(FEATURE_TEAM) and role != "unused":
        # Free : pas d'invites assistants ; on bloque toute invite sauf si Pro/Solo
        if ent.plan.slug == "free":
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Le plan Découverte n'autorise pas d'invitations. Passez à Solo ou Pro.",
            )
    role_n = (role or "avocat").strip()
    if role_n == "assistant_juridique" or role_n == "assistant":
        if ent.assistants_used >= ent.plan.max_assistants:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=(
                    f"Limite d'assistants atteinte ({ent.plan.max_assistants}). "
                    "Passez au plan supérieur."
                ),
            )
    else:
        lim = int(getattr(ent, "avocats_limit", None) or ent.plan.max_avocats)
        if ent.avocats_used >= lim:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=(
                    f"Limite d'avocats atteinte ({lim}). "
                    + (
                        "Ajoutez des sièges à la carte dans Paramètres → Plan & usage, "
                        "ou passez à Entreprise."
                        if (ent.plan.slug or "") == "pro"
                        else "Passez au plan Cabinet Pro ou Entreprise."
                    )
                ),
            )


def assert_can_create_case(db: Session, cabinet_id: str) -> None:
    ent = get_entitlements(db, cabinet_id)
    lim = ent.plan.max_cases
    if lim >= 0 and ent.cases_used >= lim:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Limite de dossiers atteinte ({lim}). Passez à Solo ou Pro.",
        )


def assert_can_use_plaidoirie(db: Session, cabinet_id: str) -> Entitlements:
    ent = get_entitlements(db, cabinet_id)
    _raise_if_restricted(ent)
    lim = ent.plaidoiries_limit
    if lim >= 0 and ent.plaidoiries_used >= lim:
        _raise_quota_or_allow_overage(
            ent,
            "compose",
            label="plaidoiries",
            used=ent.plaidoiries_used,
            limit=lim,
        )
    _assert_ai_credits(ent, "compose", db)
    return ent


def assert_can_use_cle_de_barre(db: Session, cabinet_id: str) -> Entitlements:
    ent = get_entitlements(db, cabinet_id)
    _raise_if_restricted(ent)
    lim = ent.cle_de_barre_limit
    if lim >= 0 and ent.cle_de_barre_used >= lim:
        _raise_quota_or_allow_overage(
            ent,
            "cle_de_barre",
            label="clés de barre",
            used=ent.cle_de_barre_used,
            limit=lim,
        )
    _assert_ai_credits(ent, "cle_de_barre", db)
    return ent


def assert_can_use_synthesis(db: Session, cabinet_id: str) -> Entitlements:
    ent = get_entitlements(db, cabinet_id)
    _raise_if_restricted(ent)
    lim = ent.synthesis_limit
    if lim >= 0 and ent.synthesis_used >= lim:
        _raise_quota_or_allow_overage(
            ent,
            "synthesis",
            label="synthèses IA",
            used=ent.synthesis_used,
            limit=lim,
        )
    _assert_ai_credits(ent, "synthesis", db)
    return ent


def assert_can_use_ai_action(db: Session, cabinet_id: str, action: str) -> Entitlements:
    """
    Gate unifié pour toute action IA ChatGPT.
    Vérifie : impayé, crédits mensuels, plafond produit (revise/analyse/ask…).
    Plans payants : si quota dépassé et usage à la demande ACTIVÉ → autorise (facturé).
    """
    ent = get_entitlements(db, cabinet_id)
    _raise_if_restricted(ent)
    _assert_ai_credits(ent, action, db)
    product_key = {
        "revise": ("revise_used", "revise_limit", "révisions IA"),
        "analyse": ("analyse_used", "analyse_limit", "analyses de dossier"),
        "ask": ("ask_used", "ask_limit", "questions sur pièces"),
        "clarify": None,
        "polish": None,
        "summarize": ("synthesis_used", "synthesis_limit", "synthèses IA"),
        "synthesis": ("synthesis_used", "synthesis_limit", "synthèses IA"),
        "compose": ("plaidoiries_used", "plaidoiries_limit", "plaidoiries"),
        "cle_de_barre": ("cle_de_barre_used", "cle_de_barre_limit", "clés de barre"),
    }.get(action)
    if product_key:
        used_attr, lim_attr, label = product_key
        used = int(getattr(ent, used_attr, 0) or 0)
        lim = int(getattr(ent, lim_attr, 0) or 0)
        if lim >= 0 and used >= lim:
            _raise_quota_or_allow_overage(
                ent,
                action,
                label=label,
                used=used,
                limit=lim,
            )
    return ent


def _raise_if_restricted(ent: Entitlements) -> None:
    if ent.access_restricted:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(
                "Accès IA restreint : paiement en échec depuis "
                f"{ent.past_due_days or PAST_DUE_GRACE_DAYS} j. Régularisez l'abonnement."
            ),
        )


def _raise_quota_or_allow_overage(
    ent: Entitlements,
    action: str,
    *,
    label: str,
    used: int,
    limit: int,
) -> None:
    """Bloque ou autorise le dépassement facturé selon on_demand."""
    if is_trial_status(ent):
        end = ent.period_end or getattr(ent.subscription, "trial_ends_at", None)
        end_label = end.strftime("%d/%m/%Y") if end else "—"
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "code": "trial_quota_reached",
                "message": (
                    f"Forfait d’essai « {label} » épuisé ({used}/{limit}). "
                    f"Pendant l’essai : pas d’achat de packs. "
                    f"Attendez la fin d’essai ({end_label}) ou souscrivez à un plan pour continuer."
                ),
                "trial": True,
                "trial_ends_label": end_label,
                "actions": ["upgrade"],
            },
        )
    cost = ai_credit_cost(action)
    if _can_use_on_demand(ent, extra_credits=cost):
        return
    slug = (ent.plan.slug or "free").lower()
    actions: list[str] = []
    if slug != "free":
        if not ent.on_demand_enabled:
            actions.append("enable_on_demand")
        if is_active_paying(ent):
            actions.append("buy_pack")
        actions.append("upgrade")
    else:
        actions.append("upgrade")
    raise HTTPException(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        detail={
            "code": "product_quota_reached",
            "message": (
                f"Quota {label} du mois atteint ({used}/{limit}). "
                + (
                    "Activez l’usage à la demande, achetez un pack, ou passez au plan supérieur."
                    if slug != "free"
                    else "Passez à Solo / Cabinet pour continuer."
                )
            ),
            "trial": False,
            "actions": actions,
            "label": label,
            "used": used,
            "limit": limit,
        },
    )


def _can_use_on_demand(ent: Entitlements, *, extra_credits: int) -> bool:
    slug = (ent.plan.slug or "free").lower()
    if slug == "free":
        return False
    if not ent.on_demand_enabled:
        return False
    mad_lim = ent.on_demand_mad_limit
    if mad_lim is not None and mad_lim >= 0:
        projected = ent.overage_mad_estimate + extra_credits * AI_OVERAGE_MAD_PER_CREDIT
        if projected > float(mad_lim) + 1e-6:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=(
                    f"Plafond d’usage à la demande atteint ({mad_lim} MAD ce mois). "
                    "Augmentez le plafond ou désactivez/attendez le prochain mois "
                    "dans Paramètres → Abonnement."
                ),
            )
    return True


def _raise_credits_block(
    ent: Entitlements,
    *,
    action: str,
    cost: int,
    used: int,
    lim: int,
    pack_balance: int,
) -> None:
    """Écran de résolution structuré (jamais une erreur technique seule)."""
    if is_trial_status(ent):
        end = ent.period_end or getattr(ent.subscription, "trial_ends_at", None)
        end_label = end.strftime("%d/%m/%Y") if end else "—"
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "code": "trial_quota_reached",
                "message": (
                    f"Forfait d’essai épuisé ({used}/{lim} crédits). "
                    f"Pas d’achat de packs pendant l’essai. "
                    f"Attendez la fin d’essai ({end_label}) ou souscrivez pour continuer."
                ),
                "trial": True,
                "trial_ends_label": end_label,
                "actions": ["upgrade"],
            },
        )
    actions: list[str] = []
    if (ent.plan.slug or "") != "free":
        if not ent.on_demand_enabled:
            actions.append("enable_on_demand")
        if is_active_paying(ent):
            actions.append("buy_pack")
        actions.append("upgrade")
    else:
        actions.append("upgrade")
    raise HTTPException(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        detail={
            "code": "credits_exhausted",
            "message": (
                f"Forfait du mois épuisé pour « {action} » "
                f"({used}/{lim} crédits inclus, packs {pack_balance}, "
                f"usage à la demande "
                f"{'activé' if ent.on_demand_enabled else 'désactivé'}). "
                "Choisissez une option ci-dessous pour continuer."
            ),
            "trial": False,
            "actions": actions,
            "cost": cost,
            "included_used": used,
            "included_limit": lim,
            "pack_balance": pack_balance,
            "on_demand_enabled": bool(ent.on_demand_enabled),
        },
    )


def expire_credit_pack_lots(db: Session, cabinet_id: str) -> int:
    """Passe en expired les lots dont expires_at est dépassé. Retourne le nb touché."""
    now = _now()
    rows = (
        db.query(BillingCreditPackPurchase)
        .filter(
            BillingCreditPackPurchase.cabinet_id == cabinet_id,
            BillingCreditPackPurchase.status == "paid",
            BillingCreditPackPurchase.expires_at.isnot(None),
            BillingCreditPackPurchase.expires_at < now,
        )
        .all()
    )
    n = 0
    for row in rows:
        row.status = "expired"
        row.credits_remaining = 0
        n += 1
    if n:
        db.flush()
        sync_prepaid_balance_cache(db, cabinet_id)
    return n


def active_pack_lots(
    db: Session, cabinet_id: str, *, for_update: bool = False
) -> list[BillingCreditPackPurchase]:
    """Lots payés, non expirés, avec solde — FIFO (expires_at croissant)."""
    expire_credit_pack_lots(db, cabinet_id)
    now = _now()
    q = (
        db.query(BillingCreditPackPurchase)
        .filter(
            BillingCreditPackPurchase.cabinet_id == cabinet_id,
            BillingCreditPackPurchase.status == "paid",
            BillingCreditPackPurchase.credits_remaining > 0,
            BillingCreditPackPurchase.expires_at.isnot(None),
            BillingCreditPackPurchase.expires_at >= now,
        )
        .order_by(
            BillingCreditPackPurchase.expires_at.asc(),
            BillingCreditPackPurchase.paid_at.asc(),
            BillingCreditPackPurchase.created_at.asc(),
        )
    )
    if for_update:
        q = q.with_for_update()
    return q.all()


def pack_balance_total(db: Session, cabinet_id: str) -> int:
    lots = active_pack_lots(db, cabinet_id, for_update=False)
    return sum(int(l.credits_remaining or 0) for l in lots)


def sync_prepaid_balance_cache(db: Session, cabinet_id: str) -> int:
    """Cache dénormalisé sur subscription (affichage) — source de vérité = lots."""
    sub = ensure_subscription(db, cabinet_id)
    # recalcul sans for_update pour éviter deadlock si déjà locké
    now = _now()
    total = (
        db.query(BillingCreditPackPurchase)
        .filter(
            BillingCreditPackPurchase.cabinet_id == cabinet_id,
            BillingCreditPackPurchase.status == "paid",
            BillingCreditPackPurchase.credits_remaining > 0,
            BillingCreditPackPurchase.expires_at.isnot(None),
            BillingCreditPackPurchase.expires_at >= now,
        )
        .all()
    )
    bal = sum(int(r.credits_remaining or 0) for r in total)
    sub.prepaid_ai_credits = bal
    db.flush()
    return bal


def pack_purchases_last_months(db: Session, cabinet_id: str, *, months: int = 3) -> int:
    since = _now() - timedelta(days=31 * months)
    return (
        db.query(BillingCreditPackPurchase)
        .filter(
            BillingCreditPackPurchase.cabinet_id == cabinet_id,
            BillingCreditPackPurchase.status == "paid",
            BillingCreditPackPurchase.paid_at.isnot(None),
            BillingCreditPackPurchase.paid_at >= since,
        )
        .count()
    )


@dataclass
class CreditConsumeResult:
    from_included: int = 0
    from_packs: int = 0
    from_overage: int = 0
    pack_lot_ids: list[str] | None = None


def can_cover_ai_credits(db: Session, cabinet_id: str, cost: int, ent: Entitlements) -> bool:
    """Même ordre que consume — sans écrire."""
    lim = ent.ai_credits_limit
    used = ent.ai_credits_used
    if lim < 0:
        return True
    room = max(0, lim - used)
    need = max(0, cost - room)
    if need <= 0:
        return True
    packs = pack_balance_total(db, cabinet_id)
    if need <= packs:
        return True
    need_od = need - packs
    try:
        return _can_use_on_demand(ent, extra_credits=need_od)
    except HTTPException:
        return False


def consume_ai_credits(
    db: Session,
    cabinet_id: str,
    cost: int,
    *,
    action: str,
    ent: Entitlements,
    usage: UsageCounter,
    sub: CabinetSubscription | None,
) -> CreditConsumeResult:
    """
    UNIQUE point de décrément crédits IA (règle produit) :
    1) forfait mensuel inclus  2) packs FIFO  3) PAYG si ON  4) blocage.
    """
    if cost <= 0:
        return CreditConsumeResult()
    lim = ent.ai_credits_limit
    used = int(getattr(usage, "ai_credits_used", 0) or 0)
    result = CreditConsumeResult(pack_lot_ids=[])

    if lim < 0:
        usage.ai_credits_used = used + cost
        result.from_included = cost
        db.flush()
        return result

    room = max(0, lim - used)
    from_included = min(cost, room)
    need = cost - from_included
    result.from_included = from_included

    from_packs = 0
    if need > 0:
        lots = active_pack_lots(db, cabinet_id, for_update=True)
        for lot in lots:
            if need <= 0:
                break
            take = min(need, int(lot.credits_remaining or 0))
            if take <= 0:
                continue
            lot.credits_remaining = int(lot.credits_remaining or 0) - take
            need -= take
            from_packs += take
            result.pack_lot_ids.append(lot.id)
            if lot.credits_remaining <= 0:
                lot.credits_remaining = 0
        result.from_packs = from_packs
        if from_packs > 0 and sub is not None:
            sync_prepaid_balance_cache(db, cabinet_id)

    from_overage = need
    if from_overage > 0:
        if not _can_use_on_demand(ent, extra_credits=from_overage):
            from app.core.rate_limit import refund_cabinet_ai_daily

            refund_cabinet_ai_daily(cabinet_id, cost)
            _raise_credits_block(
                ent,
                action=action,
                cost=cost,
                used=used,
                lim=lim,
                pack_balance=pack_balance_total(db, cabinet_id),
            )
        usage.ai_overage_credits = int(getattr(usage, "ai_overage_credits", 0) or 0) + from_overage
        result.from_overage = from_overage

    usage.ai_credits_used = used + cost
    db.flush()
    if result.from_packs or result.from_overage:
        log_subscription_event(
            db,
            cabinet_id,
            "ai_credits_consumed",
            plan_slug=ent.plan.slug,
            detail=(
                f"action={action}:incl={result.from_included}:"
                f"pack={result.from_packs}:payg={result.from_overage}"
            ),
        )
    return result


def _assert_ai_credits(ent: Entitlements, action: str, db: Session | None = None) -> None:
    cost = ai_credit_cost(action)
    lim = ent.ai_credits_limit
    if lim < 0:
        return
    if ent.ai_credits_used + cost <= lim:
        return
    pack_bal = int(getattr(ent, "prepaid_ai_credits", 0) or 0)
    if db is not None:
        pack_bal = pack_balance_total(db, ent.subscription.cabinet_id)
    need_extra = ent.ai_credits_used + cost - lim
    if need_extra <= pack_bal:
        return
    need_od = need_extra - pack_bal
    try:
        if _can_use_on_demand(ent, extra_credits=need_od):
            return
    except HTTPException:
        pass
    _raise_credits_block(
        ent,
        action=action,
        cost=cost,
        used=ent.ai_credits_used,
        lim=lim,
        pack_balance=pack_bal,
    )


def spend_ai_action(db: Session, cabinet_id: str, action: str) -> None:
    """Incrémente compteurs produit ; crédits via consume_ai_credits uniquement."""
    ym = _period_ym()
    usage = (
        db.query(UsageCounter)
        .filter(UsageCounter.cabinet_id == cabinet_id, UsageCounter.period_ym == ym)
        .with_for_update()
        .first()
    )
    if not usage:
        usage = get_or_create_usage(db, cabinet_id)
        usage = (
            db.query(UsageCounter)
            .filter(UsageCounter.id == usage.id)
            .with_for_update()
            .first()
        )
    sub = (
        db.query(CabinetSubscription)
        .filter(CabinetSubscription.cabinet_id == cabinet_id)
        .with_for_update()
        .first()
    )
    ent = get_entitlements(db, cabinet_id)
    cost = ai_credit_cost(action)
    consume_ai_credits(db, cabinet_id, cost, action=action, ent=ent, usage=usage, sub=sub)
    if action == "compose":
        usage.plaidoiries_count = int(usage.plaidoiries_count or 0) + 1
    elif action == "revise":
        usage.revise_count = int(getattr(usage, "revise_count", 0) or 0) + 1
    elif action == "analyse":
        usage.analyse_count = int(getattr(usage, "analyse_count", 0) or 0) + 1
    elif action == "ask":
        usage.ask_count = int(getattr(usage, "ask_count", 0) or 0) + 1
    elif action in ("synthesis", "summarize"):
        usage.synthesis_count = int(getattr(usage, "synthesis_count", 0) or 0) + 1
    elif action == "cle_de_barre":
        usage.cle_de_barre_count = int(usage.cle_de_barre_count or 0) + 1
    db.flush()
    if action == "compose":
        try:
            from app.services.trial_lifecycle import maybe_send_quota_warning

            maybe_send_quota_warning(db, cabinet_id)
        except Exception:
            pass


def set_on_demand_settings(
    db: Session,
    cabinet_id: str,
    *,
    enabled: bool,
    mad_limit: int | None = None,
) -> Entitlements:
    """Active/désactive l’usage à la demande (admin cabinet)."""
    sub = ensure_subscription(db, cabinet_id)
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == sub.plan_id).first()
    if not plan or plan.slug == "free":
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="L’usage à la demande n’est disponible que sur Solo, Cabinet ou Entreprise.",
        )
    sub.on_demand_enabled = bool(enabled)
    if mad_limit is not None:
        # -1 = illimité ; 0+ = plafond MAD
        sub.on_demand_mad_limit = None if mad_limit < 0 else int(mad_limit)
    db.flush()
    log_subscription_event(
        db,
        cabinet_id,
        "on_demand_updated",
        plan_slug=plan.slug,
        detail=f"enabled={enabled}:mad_limit={sub.on_demand_mad_limit}",
    )
    return get_entitlements(db, cabinet_id)


def list_billing_addons(db: Session, cabinet_id: str) -> dict[str, Any]:
    ent = get_entitlements(db, cabinet_id)
    expire_credit_pack_lots(db, cabinet_id)
    bal = sync_prepaid_balance_cache(db, cabinet_id)
    packs_ok = is_active_paying(ent)
    lim = int(ent.ai_credits_limit or 0)
    used = int(ent.ai_credits_used or 0)
    usage_ratio = (used / lim) if lim > 0 else 0.0
    show_banner = packs_ok and usage_ratio >= PACK_BANNER_USAGE_RATIO
    purchases_3m = pack_purchases_last_months(db, cabinet_id, months=3) if packs_ok else 0
    nudge_upgrade = packs_ok and purchases_3m >= PACK_UPGRADE_NUDGE_MIN_PURCHASES
    lots = []
    if packs_ok or bal > 0:
        now = _now()
        for row in (
            db.query(BillingCreditPackPurchase)
            .filter(
                BillingCreditPackPurchase.cabinet_id == cabinet_id,
                BillingCreditPackPurchase.status == "paid",
                BillingCreditPackPurchase.credits_remaining > 0,
            )
            .order_by(BillingCreditPackPurchase.expires_at.asc())
            .all()
        ):
            if row.expires_at and row.expires_at < now:
                continue
            lots.append(
                {
                    "id": row.id,
                    "pack_id": row.pack_id,
                    "credits_remaining": int(row.credits_remaining or 0),
                    "credits": int(row.credits or 0),
                    "expires_at": row.expires_at.isoformat() if row.expires_at else None,
                    "paid_at": row.paid_at.isoformat() if row.paid_at else None,
                    "amount_mad": int(row.amount_mad or 0),
                }
            )
    packs_with_expiry = []
    for p in CREDIT_PACKS:
        exp = (_now() + timedelta(days=365)).strftime("%d/%m/%Y")
        packs_with_expiry.append(
            {
                **p,
                "expires_after_months": PACK_EXPIRY_MONTHS,
                "expires_hint": exp,
            }
        )
    slug = (ent.plan.slug or "free").lower()
    return {
        "currency": "MAD",
        "on_demand_mad_per_credit": AI_OVERAGE_MAD_PER_CREDIT,
        "status": ent.status,
        "is_active_paying": packs_ok,
        "is_trial": is_trial_status(ent),
        "prepaid_ai_credits": bal,
        "credit_packs_available": packs_ok,
        "credit_packs": packs_with_expiry if packs_ok else [],
        "pack_lots": lots,
        "show_pack_banner": show_banner,
        "pack_usage_ratio": round(usage_ratio, 3),
        "pack_purchases_last_3_months": purchases_3m,
        "nudge_upgrade_before_pack": nudge_upgrade,
        "seats_addon_available": slug == "pro" and not is_trial_status(ent),
        "extra_avocat_seats": int(ent.extra_avocat_seats or 0),
        "extra_seat_mad_monthly": EXTRA_AVOCAT_SEAT_MAD_MONTHLY,
        "max_extra_avocat_seats": MAX_EXTRA_AVOCAT_SEATS_PRO if slug == "pro" else 0,
        "avocats_limit": int(ent.avocats_limit),
        "avocats_included": int(ent.plan.max_avocats),
    }


def _require_active_paying_for_packs(ent: Entitlements) -> None:
    if is_trial_status(ent):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "packs_forbidden_trial",
                "message": "Les packs prépayés ne sont pas disponibles pendant l’essai.",
            },
        )
    if not is_active_paying(ent):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "packs_forbidden_status",
                "message": "Les packs sont réservés aux abonnements actifs payants (Solo / Cabinet / Entreprise).",
            },
        )


def start_credit_pack_checkout(
    db: Session,
    cabinet_id: str,
    pack_id: str,
    *,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Étape 1 : crée un achat pending — ne crédite AUCUN crédit."""
    ent = get_entitlements(db, cabinet_id)
    _require_active_paying_for_packs(ent)
    pack = next((p for p in CREDIT_PACKS if p["id"] == pack_id), None)
    if not pack:
        raise HTTPException(status_code=400, detail="Pack introuvable.")
    purchase = BillingCreditPackPurchase(
        id=str(uuid.uuid4()),
        cabinet_id=cabinet_id,
        pack_id=pack_id,
        credits=int(pack["credits"]),
        credits_remaining=0,
        amount_mad=int(pack["price_mad"]),
        unit_price_mad=float(pack["unit_mad"]),
        status="pending_payment",
        created_by=user_id,
    )
    db.add(purchase)
    log_subscription_event(
        db,
        cabinet_id,
        "credit_pack_checkout_started",
        plan_slug=ent.plan.slug,
        detail=f"{pack_id}:{pack['price_mad']}MAD",
        created_by=user_id,
    )
    db.flush()
    expires_hint = (_now() + timedelta(days=365)).strftime("%d/%m/%Y")
    return {
        "purchase_id": purchase.id,
        "pack_id": pack_id,
        "credits": int(pack["credits"]),
        "amount_mad": int(pack["price_mad"]),
        "unit_mad": float(pack["unit_mad"]),
        "label": pack["label"],
        "expires_after_months": PACK_EXPIRY_MONTHS,
        "expires_hint": expires_hint,
        "status": "pending_payment",
        "payment_required": True,
    }


def confirm_credit_pack_payment(
    db: Session,
    cabinet_id: str,
    purchase_id: str,
    *,
    card_name: str,
    card_number: str,
    card_exp: str | None = None,
    card_cvc: str | None = None,
    user_id: str | None = None,
    cabinet_name: str = "Cabinet",
) -> Entitlements:
    """
    Étape 2 : après fenêtre de paiement réussie → crédite le lot + facture.
    Même modèle carte que l'abonnement (mock opérateur) ; webhook CMI pourra
    appeler la même finalisation plus tard.
    """
    from app.core.config import settings

    ent = get_entitlements(db, cabinet_id)
    _require_active_paying_for_packs(ent)
    purchase = (
        db.query(BillingCreditPackPurchase)
        .filter(
            BillingCreditPackPurchase.id == purchase_id,
            BillingCreditPackPurchase.cabinet_id == cabinet_id,
        )
        .with_for_update()
        .first()
    )
    if not purchase:
        raise HTTPException(status_code=404, detail="Achat introuvable.")
    if purchase.status == "paid":
        return get_entitlements(db, cabinet_id)
    if purchase.status != "pending_payment":
        raise HTTPException(status_code=400, detail="Cet achat n’est plus en attente de paiement.")

    digits = "".join(c for c in (card_number or "") if c.isdigit())
    if len(digits) < 13 or not (card_name or "").strip():
        raise HTTPException(status_code=400, detail="Carte invalide — vérifiez le numéro et le titulaire.")

    # Prod réel sans PSP : ne pas créditer (règle 9)
    payment_mock = bool(getattr(settings, "BILLING_PAYMENT_MOCK", True))
    if not payment_mock and not (
        getattr(settings, "CMI_ENABLED", False) or getattr(settings, "PAYZONE_ENABLED", False)
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "payment_provider_unavailable",
                "message": (
                    "Paiement packs indisponible : prestataire CMI/PayZone non activé. "
                    "Aucun crédit n’a été ajouté."
                ),
            },
        )

    now = _now()
    last4 = digits[-4:]
    purchase.status = "paid"
    purchase.credits_remaining = int(purchase.credits)
    purchase.paid_at = now
    purchase.expires_at = now + timedelta(days=365)
    purchase.payment_provider = f"card_mock:pack:{last4}" if payment_mock else "card"
    purchase.card_last4 = last4

    pack = next((p for p in CREDIT_PACKS if p["id"] == purchase.pack_id), None)
    label = pack["label"] if pack else purchase.pack_id
    exp_label = purchase.expires_at.strftime("%d/%m/%Y")
    pack_number = f"PACK-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    pack_status = "paid_mock" if payment_mock else "paid"
    inv = BillingInvoice(
        id=str(uuid.uuid4()),
        cabinet_id=cabinet_id,
        number=pack_number,
        plan_slug=ent.plan.slug,
        plan_name=f"Pack crédits IA · {label}",
        amount_mad=int(purchase.amount_mad),
        currency="MAD",
        billing_cycle="one_shot",
        status=pack_status,
        period_label=f"{purchase.credits} crédits · expire {exp_label}",
        issued_at=now,
        pdf_html=render_cursor_invoice_html(
            number=pack_number,
            issued_at=now,
            cabinet_name=cabinet_name,
            plan_name=f"Pack crédits IA · {label}",
            period_label=f"{purchase.credits} crédits · expire {exp_label}",
            amount_mad=int(purchase.amount_mad),
            billing_cycle="one_shot",
            status=pack_status,
            card_last4=last4,
            description=f"Pack crédits IA · {label} ({purchase.credits} crédits)",
        ),
    )
    db.add(inv)
    purchase.invoice_id = inv.id
    sync_prepaid_balance_cache(db, cabinet_id)
    log_subscription_event(
        db,
        cabinet_id,
        "credit_pack_paid",
        plan_slug=ent.plan.slug,
        detail=f"{purchase.pack_id}:{purchase.credits}:exp={exp_label}",
        created_by=user_id,
    )
    db.flush()
    return get_entitlements(db, cabinet_id)


def purchase_credit_pack(
    db: Session,
    cabinet_id: str,
    pack_id: str,
    *,
    user_id: str | None = None,
    cabinet_name: str = "Cabinet",
) -> Entitlements:
    """DEPRECATED — ne plus créditer au clic. Utiliser checkout + confirm."""
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
            "code": "pack_payment_required",
            "message": "Utilisez la fenêtre de paiement (checkout puis confirmation).",
        },
    )


def set_extra_avocat_seats(
    db: Session,
    cabinet_id: str,
    quantity: int,
    *,
    user_id: str | None = None,
) -> Entitlements:
    """Règle le nombre de sièges avocat add-on (Cabinet / pro uniquement)."""
    qty = int(quantity)
    if qty < 0 or qty > MAX_EXTRA_AVOCAT_SEATS_PRO:
        raise HTTPException(
            status_code=400,
            detail=f"Nombre de sièges extra invalide (0–{MAX_EXTRA_AVOCAT_SEATS_PRO}).",
        )
    ent = get_entitlements(db, cabinet_id)
    if (ent.plan.slug or "") != "pro":
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Les sièges à la carte sont disponibles sur le plan Cabinet uniquement.",
        )
    included = int(ent.plan.max_avocats)
    new_limit = included + qty
    if ent.avocats_used > new_limit:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Impossible : {ent.avocats_used} avocats actifs, "
                f"le nouveau plafond serait {new_limit}. "
                "Retirez d’abord des membres de l’équipe."
            ),
        )
    sub = ensure_subscription(db, cabinet_id)
    sub.extra_avocat_seats = qty
    monthly_addon = qty * EXTRA_AVOCAT_SEAT_MAD_MONTHLY
    log_subscription_event(
        db,
        cabinet_id,
        "extra_seats_updated",
        plan_slug="pro",
        detail=f"extra={qty}:addon_mad={monthly_addon}",
        created_by=user_id,
    )
    db.flush()
    return get_entitlements(db, cabinet_id)


def increment_plaidoirie_usage(db: Session, cabinet_id: str) -> None:
    spend_ai_action(db, cabinet_id, "compose")


def increment_cle_usage(db: Session, cabinet_id: str) -> None:
    spend_ai_action(db, cabinet_id, "cle_de_barre")


def increment_synthesis_usage(db: Session, cabinet_id: str) -> None:
    spend_ai_action(db, cabinet_id, "synthesis")


def begin_ai_action(
    db: Session,
    cabinet_id: str,
    action: str,
    *,
    request=None,
    acknowledge_daily_overage: bool | None = None,
) -> tuple[Entitlements, str | None]:
    """
    Prépare une action IA : quotas + daily + slot concurrent.
    Retourne (entitlements, slot_token). Toujours appeler finish_ai_action.

    Plafond du jour : si dépassé sans acknowledgement → DAILY_CAP_CHOICE (popup choix).
    Header X-LexHub-Daily-Overage: 1 = le client a choisi de continuer.
    """
    from app.core.rate_limit import acquire_cabinet_ai_slot, check_cabinet_ai_daily

    ent = assert_can_use_ai_action(db, cabinet_id, action)
    in_trial = ent.status in (SubscriptionStatus.TRIAL.value, "trial")
    ack = bool(acknowledge_daily_overage)
    if acknowledge_daily_overage is None and request is not None:
        try:
            raw = (request.headers.get("x-lexhub-daily-overage") or "").strip().lower()
            ack = raw in ("1", "true", "yes")
        except Exception:
            ack = False
    try:
        check_cabinet_ai_daily(
            cabinet_id,
            ai_credit_cost(action),
            ai_daily_cap_for(ent.plan.slug, in_trial=in_trial),
            acknowledge_overage=ack,
        )
    except HTTPException as exc:
        detail = getattr(exc, "detail", None)
        if isinstance(detail, dict) and detail.get("code") == "DAILY_CAP_CHOICE":
            plan_name = getattr(ent.plan, "name", None) or ent.plan.slug
            detail = {
                **detail,
                "is_trial": bool(in_trial),
                "plan_slug": ent.plan.slug,
                "plan_name": plan_name,
                "message": (
                    (
                        f"Pendant votre essai « {plan_name} », "
                        if in_trial
                        else f"Avec votre abonnement « {plan_name} », "
                    )
                    + f"le repère du jour est {detail.get('daily_limit')} crédits IA. "
                    "Même logique pour tous les plans (essai ou payant) : "
                    "ce n’est pas un impayé. "
                    "Choisissez d’attendre demain, ou de continuer "
                    "(crédits du mois / de l’essai débités)."
                ),
            }
            raise HTTPException(
                status_code=exc.status_code,
                detail=detail,
                headers=getattr(exc, "headers", None),
            ) from exc
        raise
    token = acquire_cabinet_ai_slot(
        cabinet_id,
        ai_concurrent_slots_for(ent.plan.slug),
        ttl_sec=240 if action in HEAVY_AI_ACTIONS else 120,
    )
    return ent, token


def finish_ai_action(
    db: Session,
    cabinet_id: str,
    action: str,
    *,
    slot_token: str | None,
    success: bool,
) -> None:
    """Debite si succès ; libère le slot ; rembourse le daily si échec."""
    from app.core.rate_limit import release_cabinet_ai_slot, refund_cabinet_ai_daily

    try:
        if success:
            spend_ai_action(db, cabinet_id, action)
        else:
            refund_cabinet_ai_daily(cabinet_id, ai_credit_cost(action))
    finally:
        release_cabinet_ai_slot(cabinet_id, slot_token)



def select_plan_mock(
    db: Session,
    cabinet_id: str,
    plan_slug: str,
    *,
    billing_cycle: str = "monthly",
    allow_paid_without_payment: bool | None = None,
) -> CabinetSubscription:
    """Bascule de plan. Plans payants bloqués si BILLING_PAYMENT_MOCK=False."""
    from app.core.config import settings

    ensure_default_plans(db)
    plan = get_plan_by_slug(db, plan_slug)
    if not plan or not plan.is_active:
        raise HTTPException(status_code=404, detail="Plan introuvable")

    is_paid = int(plan.price_mad_monthly or 0) > 0 or int(plan.price_mad_yearly or 0) > 0
    if allow_paid_without_payment is None:
        allow_paid_without_payment = bool(getattr(settings, "BILLING_PAYMENT_MOCK", True))
    if is_paid and not allow_paid_without_payment:
        log_subscription_event(
            db,
            cabinet_id,
            "upgrade_requested",
            plan_slug=plan.slug,
            detail=billing_cycle,
        )
        raise HTTPException(
            status_code=402,
            detail=(
                "Paiement requis. Contactez contact@lexhub.space ou effectuez un virement — "
                "WEBVOICE activera votre plan sous 24–48 h."
            ),
        )

    sub = ensure_subscription(db, cabinet_id)
    now = _now()
    cycle = BillingCycle.YEARLY if billing_cycle == "yearly" else BillingCycle.MONTHLY
    sub.plan_id = plan.id
    sub.status = SubscriptionStatus.ACTIVE
    sub.billing_cycle = cycle
    sub.trial_ends_at = None
    sub.current_period_start = now
    sub.current_period_end = _add_months(now, 12 if cycle == BillingCycle.YEARLY else 1)
    sub.payment_provider = "manual"
    sub.cancel_at_period_end = False
    sub.cancel_reason_code = None
    sub.cancel_reason_text = None
    sub.cancel_requested_at = None
    sub.notes = f"Sélection {plan.slug} ({cycle.value}) mock={allow_paid_without_payment}"
    db.flush()
    log_subscription_event(
        db, cabinet_id, "plan_selected", plan_slug=plan.slug, detail=cycle.value
    )
    if is_paid:
        try:
            from app.services.referral import apply_referrer_reward_on_paid

            apply_referrer_reward_on_paid(db, cabinet_id)
        except Exception:
            pass
    return sub


def request_cancellation(
    db: Session,
    cabinet_id: str,
    *,
    reason_code: str,
    reason_text: str | None = None,
    user_id: str | None = None,
) -> CabinetSubscription:
    valid = {c for c, _ in CANCEL_REASON_CODES}
    if reason_code not in valid:
        raise HTTPException(status_code=400, detail="Motif de résiliation invalide")
    sub = ensure_subscription(db, cabinet_id)
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == sub.plan_id).first()
    now = _now()
    sub.cancel_at_period_end = True
    sub.cancel_reason_code = reason_code
    sub.cancel_reason_text = (reason_text or "").strip()[:2000] or None
    sub.cancel_requested_at = now
    db.flush()
    log_subscription_event(
        db,
        cabinet_id,
        "cancel_requested",
        plan_slug=plan.slug if plan else None,
        detail=f"{reason_code}: {sub.cancel_reason_text or ''}",
        created_by=user_id,
    )
    return sub


def undo_cancellation(db: Session, cabinet_id: str, *, user_id: str | None = None) -> CabinetSubscription:
    sub = ensure_subscription(db, cabinet_id)
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == sub.plan_id).first()
    sub.cancel_at_period_end = False
    sub.cancel_reason_code = None
    sub.cancel_reason_text = None
    sub.cancel_requested_at = None
    db.flush()
    log_subscription_event(
        db,
        cabinet_id,
        "cancel_undone",
        plan_slug=plan.slug if plan else None,
        created_by=user_id,
    )
    return sub


def list_events(db: Session, cabinet_id: str, *, limit: int = 50) -> list[SubscriptionEvent]:
    return (
        db.query(SubscriptionEvent)
        .filter(SubscriptionEvent.cabinet_id == cabinet_id)
        .order_by(SubscriptionEvent.created_at.desc())
        .limit(limit)
        .all()
    )


LEXHUB_INVOICE_LOGO_URL = "https://lexhub.space/logo-lexhub-cube.png?v=cube-3"


def is_paid_invoice_row(*, amount_mad: int | float | None, status: str | None) -> bool:
    """Factures listées : montant > 0 MAD (pas les reçus d'essai à 0)."""
    if int(amount_mad or 0) <= 0:
        return False
    st = (status or "").lower()
    if "trial" in st or "essai" in st:
        return False
    return True


def _invoice_logo_path() -> "Path | None":
    from pathlib import Path

    here = Path(__file__).resolve()
    candidates = [
        here.parents[1] / "assets" / "logo-lexhub-cube.png",
        here.parents[3] / "frontend" / "public" / "logo-lexhub-cube.png",
        Path("/opt/sanad/frontend/public/logo-lexhub-cube.png"),
        Path("/opt/sanad/backend/app/assets/logo-lexhub-cube.png"),
    ]
    for p in candidates:
        if p.is_file():
            return p
    return None


def _fmt_mad(amount: int | float | None) -> str:
    n = int(amount or 0)
    return f"{n:,}".replace(",", " ") + " MAD"


def _cycle_label(cycle: str | None) -> str:
    c = (cycle or "").lower()
    if c == "yearly":
        return "Annuel"
    if c == "monthly":
        return "Mensuel"
    if c == "one_shot":
        return "Paiement unique"
    return cycle or "—"


def _status_paid_label(status: str | None) -> str:
    st = (status or "").lower()
    if "paid" in st or st in {"payee", "payée", "issued", "issued_mock"}:
        return "Payée"
    return status or "—"


def render_cursor_invoice_html(
    *,
    number: str,
    issued_at: datetime | None,
    cabinet_name: str,
    address: str = "",
    city: str = "",
    plan_name: str,
    period_label: str = "",
    amount_mad: int | float,
    billing_cycle: str = "",
    status: str = "",
    card_last4: str = "",
    description: str | None = None,
) -> str:
    """Facture style SaaS (type Cursor) — aperçu navigateur."""
    safe_num = html.escape(number or "")
    safe_name = html.escape(cabinet_name or "—")
    safe_addr = html.escape(address or "")
    safe_city = html.escape(city or "")
    safe_plan = html.escape(plan_name or "Abonnement LexHub")
    safe_period = html.escape(period_label or "—")
    amount = int(amount_mad or 0)
    amount_s = _fmt_mad(amount)
    date_s = issued_at.strftime("%d %b %Y") if issued_at else "—"
    cycle_s = html.escape(_cycle_label(billing_cycle))
    status_s = html.escape(_status_paid_label(status))
    desc = html.escape(
        description
        or f"{plan_name or 'Abonnement LexHub'} — {_cycle_label(billing_cycle)}"
    )
    bill_lines = safe_name
    if safe_addr:
        bill_lines += f"<br/>{safe_addr}"
    if safe_city:
        bill_lines += f"<br/>{safe_city}"
    card_row = ""
    if card_last4:
        card_row = (
            f'<div class="row"><span class="k">Moyen de paiement</span>'
            f'<span class="v">Carte ···· {html.escape(card_last4)}</span></div>'
        )
    return f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"/>
<title>Facture {safe_num}</title>
<style>
  :root {{ --ink:#0f172a; --muted:#64748b; --line:#e2e8f0; --soft:#f8fafc; --brand:#0B1A4D; }}
  * {{ box-sizing:border-box; }}
  body {{
    margin:0; padding:48px 24px; background:#f1f5f9;
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    color:var(--ink); -webkit-font-smoothing:antialiased;
  }}
  .sheet {{
    max-width:680px; margin:0 auto; background:#fff; border:1px solid var(--line);
    border-radius:12px; padding:40px 44px 36px; box-shadow:0 1px 2px rgba(15,23,42,.04);
  }}
  .top {{ display:flex; justify-content:space-between; align-items:flex-start; gap:24px; }}
  .brand {{ display:flex; align-items:center; gap:12px; }}
  .brand img {{
    width:44px; height:44px; border-radius:10px; object-fit:contain;
    background:linear-gradient(155deg,#1a2a55,#0A1228); padding:5px;
  }}
  .brand .name {{ font-size:20px; font-weight:700; letter-spacing:-.02em; color:var(--brand); }}
  .brand .sub {{ font-size:12px; color:var(--muted); margin-top:2px; }}
  .inv-meta {{ text-align:right; }}
  .inv-meta .lbl {{ font-size:11px; font-weight:600; letter-spacing:.08em; text-transform:uppercase; color:var(--muted); }}
  .inv-meta .num {{ font-size:18px; font-weight:700; margin-top:4px; color:var(--ink); }}
  .inv-meta .date {{ font-size:13px; color:var(--muted); margin-top:6px; }}
  .amount-due {{
    margin-top:28px; padding:18px 20px; background:var(--soft); border:1px solid var(--line);
    border-radius:10px; display:flex; justify-content:space-between; align-items:center;
  }}
  .amount-due .lbl {{ font-size:13px; color:var(--muted); }}
  .amount-due .val {{ font-size:28px; font-weight:700; letter-spacing:-.03em; color:var(--brand); }}
  .cols {{ display:grid; grid-template-columns:1fr 1fr; gap:28px; margin-top:28px; }}
  .cols h3 {{ margin:0 0 8px; font-size:11px; font-weight:600; letter-spacing:.08em; text-transform:uppercase; color:var(--muted); }}
  .cols p {{ margin:0; font-size:14px; line-height:1.55; }}
  table {{ width:100%; border-collapse:collapse; margin-top:32px; }}
  thead th {{
    text-align:left; font-size:11px; font-weight:600; letter-spacing:.06em;
    text-transform:uppercase; color:var(--muted); padding:0 0 10px; border-bottom:1px solid var(--line);
  }}
  thead th:last-child, tbody td:last-child {{ text-align:right; }}
  tbody td {{ padding:16px 0; border-bottom:1px solid var(--line); font-size:14px; vertical-align:top; }}
  tbody td .muted {{ color:var(--muted); font-size:12px; margin-top:4px; }}
  .totals {{ margin-top:8px; margin-left:auto; width:260px; }}
  .totals .row {{ display:flex; justify-content:space-between; padding:8px 0; font-size:14px; }}
  .totals .row.total {{ border-top:1px solid var(--line); margin-top:4px; padding-top:12px; font-weight:700; font-size:15px; }}
  .pay {{ margin-top:28px; padding-top:20px; border-top:1px solid var(--line); }}
  .pay .row {{ display:flex; justify-content:space-between; gap:16px; padding:6px 0; font-size:13px; }}
  .pay .k {{ color:var(--muted); }}
  .pay .v {{ font-weight:600; }}
  .foot {{ margin-top:28px; font-size:11px; color:#94a3b8; line-height:1.5; }}
  @media print {{
    body {{ background:#fff; padding:0; }}
    .sheet {{ box-shadow:none; border:none; max-width:none; border-radius:0; }}
  }}
</style></head><body>
<div class="sheet">
  <div class="top">
    <div class="brand lexhub-brand">
      <img src="{LEXHUB_INVOICE_LOGO_URL}" alt="LexHub" width="44" height="44"/>
      <div>
        <div class="name">LexHub</div>
        <div class="sub">WEBVOICE · LegalTech Maroc</div>
      </div>
    </div>
    <div class="inv-meta">
      <div class="lbl">Facture</div>
      <div class="num">{safe_num}</div>
      <div class="date">{date_s}</div>
    </div>
  </div>
  <div class="amount-due">
    <div>
      <div class="lbl">Montant</div>
      <div style="font-size:12px;color:var(--muted);margin-top:4px">Statut · {status_s}</div>
    </div>
    <div class="val">{amount_s}</div>
  </div>
  <div class="cols">
    <div>
      <h3>Facturé à</h3>
      <p>{bill_lines}</p>
    </div>
    <div>
      <h3>Émetteur</h3>
      <p>LexHub by WEBVOICE<br/>Tanger, Maroc<br/>lexhub.space</p>
    </div>
  </div>
  <table>
    <thead><tr><th>Description</th><th>Période</th><th>Montant</th></tr></thead>
    <tbody>
      <tr>
        <td>{desc}<div class="muted">Cycle · {cycle_s}</div></td>
        <td>{safe_period}</td>
        <td>{amount_s}</td>
      </tr>
    </tbody>
  </table>
  <div class="totals">
    <div class="row"><span>Sous-total</span><span>{amount_s}</span></div>
    <div class="row total"><span>Total</span><span>{amount_s}</span></div>
  </div>
  <div class="pay">
    <div class="row"><span class="k">Statut</span><span class="v">{status_s}</span></div>
    {card_row}
  </div>
  <p class="foot">Document généré automatiquement par LexHub. Paiement électronique (CMI / PayZone). Merci de votre confiance.</p>
</div>
</body></html>"""


def brand_invoice_html(raw: str | None) -> str:
    """Compat : anciennes factures → style Cursor + logo si absents."""
    doc = (raw or "").strip()
    if not doc:
        return render_cursor_invoice_html(
            number="—",
            issued_at=None,
            cabinet_name="—",
            plan_name="LexHub",
            amount_mad=0,
            status="—",
        )
    if "amount-due" in doc and "logo-lexhub-cube" in doc:
        return doc
    # Si déjà un HTML LexHub basique, on le remplace pas — on injecte juste le header
    if "logo-lexhub-cube" in doc or "lexhub-brand" in doc:
        return doc
    lower = doc.lower()
    body_idx = lower.find("<body")
    if body_idx >= 0:
        gt = doc.find(">", body_idx)
        if gt >= 0:
            header = (
                f'<div class="lexhub-brand" style="display:flex;align-items:center;gap:12px;'
                f'margin:24px auto 0;max-width:680px;padding:0 44px">'
                f'<img src="{LEXHUB_INVOICE_LOGO_URL}" alt="LexHub" width="44" height="44" '
                f'style="width:44px;height:44px;border-radius:10px;object-fit:contain;'
                f'background:linear-gradient(155deg,#1a2a55,#0A1228);padding:5px"/>'
                f'<div style="font-size:20px;font-weight:700;color:#0B1A4D">LexHub</div></div>'
            )
            return doc[: gt + 1] + header + doc[gt + 1 :]
    return render_cursor_invoice_html(
        number="—",
        issued_at=None,
        cabinet_name="—",
        plan_name="LexHub",
        amount_mad=0,
        status="—",
        description="Document facture",
    )


def invoice_html_from_row(
    inv: BillingInvoice,
    *,
    cabinet_name: str = "",
    address: str = "",
    city: str = "",
    card_last4: str = "",
) -> str:
    """Toujours régénérer le HTML Cursor à partir des champs métier (aperçu cohérent)."""
    return render_cursor_invoice_html(
        number=inv.number or "",
        issued_at=inv.issued_at,
        cabinet_name=cabinet_name or "Cabinet",
        address=address,
        city=city,
        plan_name=inv.plan_name or "LexHub",
        period_label=inv.period_label or "",
        amount_mad=int(inv.amount_mad or 0),
        billing_cycle=inv.billing_cycle or "",
        status=inv.status or "",
        card_last4=card_last4,
    )


def build_invoice_pdf_bytes(
    *,
    number: str,
    issued_at: datetime | None,
    cabinet_name: str,
    address: str = "",
    city: str = "",
    plan_name: str,
    period_label: str = "",
    amount_mad: int | float,
    billing_cycle: str = "",
    status: str = "",
    card_last4: str = "",
) -> bytes:
    """Vrai PDF (PyMuPDF) — téléchargement navigateur, pas boîte Imprimer."""
    import fitz

    amount = int(amount_mad or 0)
    amount_s = _fmt_mad(amount)
    date_s = issued_at.strftime("%d/%m/%Y") if issued_at else "—"
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4
    ink = (15 / 255, 23 / 255, 42 / 255)
    muted = (100 / 255, 116 / 255, 139 / 255)
    brand = (11 / 255, 26 / 255, 77 / 255)
    line = (226 / 255, 232 / 255, 240 / 255)
    soft = (248 / 255, 250 / 255, 252 / 255)

    margin = 48
    y = margin

    logo = _invoice_logo_path()
    if logo:
        try:
            page.insert_image(
                fitz.Rect(margin, y, margin + 42, y + 42),
                filename=str(logo),
                keep_proportion=True,
            )
        except Exception:
            pass
    page.insert_text((margin + 54, y + 18), "LexHub", fontsize=16, fontname="helv", color=brand)
    page.insert_text(
        (margin + 54, y + 34),
        "WEBVOICE · LegalTech Maroc",
        fontsize=8,
        fontname="helv",
        color=muted,
    )
    page.insert_text((420, y + 14), "FACTURE", fontsize=9, fontname="helv", color=muted)
    page.insert_text((420, y + 30), number or "—", fontsize=12, fontname="helv", color=ink)
    page.insert_text((420, y + 46), date_s, fontsize=9, fontname="helv", color=muted)

    y += 70
    # Amount box
    box = fitz.Rect(margin, y, 595 - margin, y + 56)
    page.draw_rect(box, color=line, fill=soft, width=0.6)
    page.insert_text((margin + 14, y + 22), "Montant", fontsize=9, fontname="helv", color=muted)
    page.insert_text(
        (margin + 14, y + 40),
        f"Statut · {_status_paid_label(status)}",
        fontsize=8,
        fontname="helv",
        color=muted,
    )
    page.insert_text((595 - margin - 140, y + 34), amount_s, fontsize=18, fontname="helv", color=brand)

    y += 78
    page.insert_text((margin, y), "FACTURÉ À", fontsize=8, fontname="helv", color=muted)
    page.insert_text((300, y), "ÉMETTEUR", fontsize=8, fontname="helv", color=muted)
    y += 16
    page.insert_text((margin, y), cabinet_name or "—", fontsize=11, fontname="helv", color=ink)
    page.insert_text((300, y), "LexHub by WEBVOICE", fontsize=11, fontname="helv", color=ink)
    y += 14
    if address:
        page.insert_text((margin, y), address, fontsize=9, fontname="helv", color=muted)
    page.insert_text((300, y), "Tanger, Maroc", fontsize=9, fontname="helv", color=muted)
    y += 14
    if city:
        page.insert_text((margin, y), city, fontsize=9, fontname="helv", color=muted)
    page.insert_text((300, y), "lexhub.space", fontsize=9, fontname="helv", color=muted)

    y += 28
    page.draw_line(fitz.Point(margin, y), fitz.Point(595 - margin, y), color=line, width=0.7)
    y += 14
    page.insert_text((margin, y), "DESCRIPTION", fontsize=8, fontname="helv", color=muted)
    page.insert_text((340, y), "PÉRIODE", fontsize=8, fontname="helv", color=muted)
    page.insert_text((480, y), "MONTANT", fontsize=8, fontname="helv", color=muted)
    y += 10
    page.draw_line(fitz.Point(margin, y), fitz.Point(595 - margin, y), color=line, width=0.7)
    y += 18
    desc = f"{plan_name or 'Abonnement LexHub'} — {_cycle_label(billing_cycle)}"
    page.insert_text((margin, y), desc[:58], fontsize=10, fontname="helv", color=ink)
    page.insert_text((340, y), (period_label or "—")[:28], fontsize=9, fontname="helv", color=muted)
    page.insert_text((480, y), amount_s, fontsize=10, fontname="helv", color=ink)

    y += 36
    page.draw_line(fitz.Point(340, y), fitz.Point(595 - margin, y), color=line, width=0.7)
    y += 16
    page.insert_text((340, y), "Sous-total", fontsize=10, fontname="helv", color=muted)
    page.insert_text((480, y), amount_s, fontsize=10, fontname="helv", color=ink)
    y += 18
    page.insert_text((340, y), "Total", fontsize=11, fontname="helv", color=ink)
    page.insert_text((480, y), amount_s, fontsize=11, fontname="helv", color=brand)

    y += 40
    page.draw_line(fitz.Point(margin, y), fitz.Point(595 - margin, y), color=line, width=0.7)
    y += 18
    page.insert_text(
        (margin, y),
        f"Statut : {_status_paid_label(status)}",
        fontsize=9,
        fontname="helv",
        color=ink,
    )
    if card_last4:
        y += 14
        page.insert_text(
            (margin, y),
            f"Moyen de paiement : Carte ···· {card_last4}",
            fontsize=9,
            fontname="helv",
            color=ink,
        )
    y += 28
    page.insert_text(
        (margin, y),
        "Document généré automatiquement par LexHub. Paiement électronique (CMI / PayZone).",
        fontsize=8,
        fontname="helv",
        color=muted,
    )

    data = doc.tobytes()
    doc.close()
    return data


def generate_invoice(
    db: Session,
    cabinet_id: str,
    *,
    cabinet_name: str,
    city: str = "",
    address: str = "",
) -> BillingInvoice:
    sub = ensure_subscription(db, cabinet_id)
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == sub.plan_id).first()
    if not plan:
        raise HTTPException(status_code=500, detail="Plan introuvable")
    cycle = sub.billing_cycle.value if hasattr(sub.billing_cycle, "value") else str(sub.billing_cycle)
    is_trial = sub.status == SubscriptionStatus.TRIAL
    amount = 0 if is_trial else (
        plan.price_mad_yearly if cycle == "yearly" else plan.price_mad_monthly
    )
    now = _now()
    number = f"LH-{now.strftime('%Y%m')}-{cabinet_id[:6].upper()}-{uuid.uuid4().hex[:4].upper()}"
    period = (
        f"{sub.current_period_start.date().isoformat() if sub.current_period_start else '—'} → "
        f"{sub.current_period_end.date().isoformat() if sub.current_period_end else '—'}"
    )
    desc = (
        f"Confirmation d’essai {plan.name or ''} — 0 MAD aujourd’hui"
        if is_trial
        else f"Abonnement {plan.name or ''}"
    )
    html_doc = render_cursor_invoice_html(
        number=number,
        issued_at=now,
        cabinet_name=cabinet_name or "",
        address=address or "",
        city=city or "",
        plan_name=plan.name or "LexHub",
        period_label=period,
        amount_mad=amount,
        billing_cycle=cycle,
        status="issued_mock" if not is_trial else "trial_mock",
        description=desc,
    )
    inv = BillingInvoice(
        id=str(uuid.uuid4()),
        cabinet_id=cabinet_id,
        number=number,
        plan_slug=plan.slug,
        plan_name=plan.name,
        amount_mad=amount,
        currency="MAD",
        billing_cycle=cycle,
        status="issued_mock",
        period_label=period,
        issued_at=now,
        pdf_html=html_doc,
    )
    db.add(inv)
    db.flush()
    log_subscription_event(
        db, cabinet_id, "invoice_generated", plan_slug=plan.slug, detail=number
    )
    return inv


def generate_trial_confirmation_invoice(
    db: Session,
    cabinet_id: str,
    *,
    cabinet_name: str,
    plan: SubscriptionPlan,
    billing_cycle: str,
    card_last4: str,
    trial_days: int,
    cardholder_name: str = "",
    billing_address: str = "",
    billing_city: str = "",
) -> BillingInvoice:
    """Reçu d'essai 0 MAD — style confirmation Cursor (simulation)."""
    now = _now()
    number = f"LH-TRIAL-{now.strftime('%Y%m')}-{cabinet_id[:6].upper()}-{uuid.uuid4().hex[:4].upper()}"
    cycle = billing_cycle
    future_amount = (
        int(plan.price_mad_yearly or 0)
        if cycle == "yearly"
        else int(plan.price_mad_monthly or 0)
    )
    trial_end = (now + timedelta(days=trial_days)).strftime("%d/%m/%Y")
    safe_name = html.escape(cabinet_name or "")
    safe_holder = html.escape(cardholder_name or "—")
    safe_addr = html.escape(billing_address or "")
    safe_city = html.escape(billing_city or "")
    safe_plan = html.escape(plan.name or "")
    invoice_html = f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"/><title>Reçu {number}</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#0A1228;max-width:680px;margin:32px auto;padding:32px;background:#F7F8FC}}
.card{{background:#fff;border:1px solid #e2e8f0;border-radius:16px;padding:28px;box-shadow:0 8px 32px -12px rgba(10,18,40,.12)}}
.brand{{font-size:22px;font-weight:700;color:#1B3F9C;letter-spacing:.02em}}
.badge{{display:inline-block;background:#ecfdf5;color:#047857;font-size:11px;font-weight:700;padding:4px 10px;border-radius:999px;margin-top:8px}}
.muted{{color:#64748b;font-size:13px;line-height:1.5}}
.row{{display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid #f1f5f9;font-size:14px}}
.row:last-child{{border-bottom:none}}
.total{{font-size:22px;font-weight:700;color:#0A1228;margin-top:16px}}
.stamp{{margin-top:24px;padding-top:16px;border-top:1px dashed #cbd5e1;font-size:11px;color:#94a3b8}}
@media print{{body{{background:#fff;margin:0}} .card{{box-shadow:none}}}}
</style></head><body>
<div class="card">
<div class="brand">LexHub</div>
<div class="badge">✓ Essai activé — simulation</div>
<p class="muted" style="margin-top:12px">Reçu de confirmation · WEBVOICE LegalTech</p>
<p style="margin-top:20px"><strong>{number}</strong><br/><span class="muted">Émis le {now.strftime('%d/%m/%Y à %H:%M')}</span></p>
<div style="margin-top:20px">
<div class="row"><span>Cabinet</span><strong>{safe_name}</strong></div>
<div class="row"><span>Adresse</span><span>{safe_addr or '—'}{', ' + safe_city if safe_city else ''}</span></div>
<div class="row"><span>Plan</span><strong>{safe_plan}</strong></div>
<div class="row"><span>Cycle</span><span>{'Annuel' if cycle == 'yearly' else 'Mensuel'}</span></div>
<div class="row"><span>Essai gratuit</span><strong>{trial_days} jours</strong></div>
<div class="row"><span>Fin essai (sans résiliation)</span><span>{trial_end}</span></div>
<div class="row"><span>Carte</span><span>**** **** **** {card_last4} · {safe_holder}</span></div>
<div class="row"><span>Montant aujourd'hui</span><strong style="color:#047857">0 MAD</strong></div>
<div class="row"><span>Après l'essai</span><span>{future_amount} MAD / {'an' if cycle == 'yearly' else 'mois'}</span></div>
</div>
<p class="total">Total payé aujourd'hui : 0 MAD</p>
</div>
<p class="stamp">Document généré automatiquement par LexHub (environnement de simulation).
La facturation fiscale définitive sera émise lors de l'activation du paiement CMI / PayZone.</p>
</body></html>"""
    inv = BillingInvoice(
        id=str(uuid.uuid4()),
        cabinet_id=cabinet_id,
        number=number,
        plan_slug=plan.slug,
        plan_name=plan.name,
        amount_mad=0,
        currency="MAD",
        billing_cycle=cycle,
        status="trial_mock",
        period_label=f"Essai {trial_days}j jusqu'au {trial_end}",
        issued_at=now,
        pdf_html=invoice_html,
    )
    db.add(inv)
    db.flush()
    log_subscription_event(
        db, cabinet_id, "trial_receipt_issued", plan_slug=plan.slug, detail=number
    )
    return inv


def analyze_cancel_reasons(db: Session) -> dict[str, Any]:
    """Agrège les motifs de résiliation pour l'admin (+ suggestion IA légère)."""
    rows = (
        db.query(CabinetSubscription)
        .filter(CabinetSubscription.cancel_reason_code.isnot(None))
        .all()
    )
    counts: dict[str, int] = {}
    samples: list[dict[str, str]] = []
    for r in rows:
        code = r.cancel_reason_code or "other"
        counts[code] = counts.get(code, 0) + 1
        if r.cancel_reason_text and len(samples) < 20:
            samples.append({"code": code, "text": r.cancel_reason_text[:280]})
    label_map = dict(CANCEL_REASON_CODES)
    ranked = sorted(counts.items(), key=lambda x: -x[1])
    top = ranked[0][0] if ranked else None
    suggestion = None
    if top == "too_expensive":
        suggestion = (
            "Le prix est le motif n°1. Envisager une promo Solo, un pack annuel plus visible, "
            "ou un freemium plus généreux avant upsell."
        )
    elif top == "missing_features":
        suggestion = (
            "Prioriser la roadmap produit (clé de barre, exports, équipe) d'après les commentaires."
        )
    elif top == "hard_to_use":
        suggestion = "Améliorer l'onboarding et raccourcir le parcours plaidoirie."
    elif top:
        suggestion = f"Motif dominant : {label_map.get(top, top)}. Analyser les commentaires libres."
    return {
        "total": len(rows),
        "by_reason": [
            {"code": c, "label": label_map.get(c, c), "count": n} for c, n in ranked
        ],
        "samples": samples,
        "ai_suggestion": suggestion,
    }