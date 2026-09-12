"""Parrainage cabinet → cabinet (LexHub)."""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Cabinet, CabinetReferral, CabinetSubscription, SubscriptionStatus

REFEREE_BONUS_DAYS = 14
REFERRER_REWARD_DAYS = 30
MAX_ACTIVE_REFERRALS_PER_YEAR = 12


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _slug_code(name: str) -> str:
    """Code opaque (pas le nom du cabinet) — limite l'énumération."""
    del name  # volontaire : le nom ne doit pas figurer dans le code
    return f"LH-{secrets.token_hex(8).upper()}"


def ensure_referral_code(db: Session, cabinet_id: str) -> str:
    cab = db.query(Cabinet).filter(Cabinet.id == cabinet_id).first()
    if not cab:
        raise HTTPException(status_code=404, detail="Cabinet introuvable")
    if cab.referral_code:
        return cab.referral_code
    for _ in range(12):
        code = _slug_code(cab.name)
        exists = db.query(Cabinet).filter(Cabinet.referral_code == code).first()
        if not exists:
            cab.referral_code = code
            db.flush()
            return code
    cab.referral_code = f"LH-{secrets.token_hex(4).upper()}"
    db.flush()
    return cab.referral_code


def get_referral_overview(db: Session, cabinet_id: str) -> dict:
    code = ensure_referral_code(db, cabinet_id)
    rows = (
        db.query(CabinetReferral)
        .filter(CabinetReferral.referrer_cabinet_id == cabinet_id)
        .order_by(CabinetReferral.created_at.desc())
        .limit(40)
        .all()
    )
    pending = sum(1 for r in rows if r.status == "pending")
    rewarded = sum(1 for r in rows if r.referrer_reward_applied)
    return {
        "code": code,
        "share_path": f"/login?tab=register&ref={code}",
        "referee_bonus_days": REFEREE_BONUS_DAYS,
        "referrer_reward_days": REFERRER_REWARD_DAYS,
        "rules_fr": (
            "Partagez le lien d’inscription de votre cabinet (ou le code affiché). "
            "Le cabinet qui s’inscrit avec ce lien reçoit +14 jours d’essai "
            "quand il démarre Solo ou Cabinet. Vous recevez +1 mois offert "
            "lorsque son abonnement payant commence (après l’essai, sans résiliation). "
            "Ce code n’ouvre aucun accès à vos dossiers : il ne sert qu’au parrainage."
        ),
        "rules_ar": (
            "شاركوا رمزكم. يحصل المكتب المدعو على +14 يوماً من التجربة عند بدء Solo/Cabinet. "
            "تحصلون على شهر إضافي عند بدء اشتراكه المدفوع بعد التجربة."
        ),
        "stats": {
            "invites": len(rows),
            "pending": pending,
            "rewarded": rewarded,
        },
        "recent": [
            {
                "status": r.status,
                "code_used": r.code_used,
                "referee_bonus_applied": r.referee_bonus_applied,
                "referrer_reward_applied": r.referrer_reward_applied,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows[:8]
        ],
    }


def attach_referral_on_register(
    db: Session,
    *,
    new_cabinet_id: str,
    referral_code: str | None,
) -> CabinetReferral | None:
    code = (referral_code or "").strip().upper()
    if not code:
        return None
    referrer = db.query(Cabinet).filter(Cabinet.referral_code == code).first()
    if not referrer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code de parrainage invalide.",
        )
    if referrer.id == new_cabinet_id:
        raise HTTPException(status_code=400, detail="Auto-parrainage interdit.")

    year_ago = _now() - timedelta(days=365)
    count = (
        db.query(CabinetReferral)
        .filter(
            CabinetReferral.referrer_cabinet_id == referrer.id,
            CabinetReferral.created_at >= year_ago,
        )
        .count()
    )
    if count >= MAX_ACTIVE_REFERRALS_PER_YEAR:
        raise HTTPException(
            status_code=400,
            detail="Ce code a atteint la limite annuelle de parrainages.",
        )

    new_cab = db.query(Cabinet).filter(Cabinet.id == new_cabinet_id).first()
    if not new_cab:
        return None
    new_cab.referred_by_cabinet_id = referrer.id

    row = CabinetReferral(
        id=str(uuid.uuid4()),
        referrer_cabinet_id=referrer.id,
        referee_cabinet_id=new_cabinet_id,
        code_used=code,
        status="pending",
        referee_bonus_days=REFEREE_BONUS_DAYS,
    )
    db.add(row)
    db.flush()
    return row


def apply_referee_trial_bonus(db: Session, cabinet_id: str, sub: CabinetSubscription) -> int:
    """Ajoute +14 j d’essai au filleul (une fois)."""
    row = (
        db.query(CabinetReferral)
        .filter(CabinetReferral.referee_cabinet_id == cabinet_id)
        .first()
    )
    if not row or row.referee_bonus_applied:
        return 0
    days = int(row.referee_bonus_days or REFEREE_BONUS_DAYS)
    if sub.trial_ends_at:
        end = sub.trial_ends_at
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        sub.trial_ends_at = end + timedelta(days=days)
        sub.current_period_end = sub.trial_ends_at
    row.referee_bonus_applied = True
    row.status = "bonus_applied"
    db.flush()
    try:
        from app.services.billing import log_subscription_event

        log_subscription_event(
            db,
            cabinet_id,
            "referral_bonus_trial",
            detail=f"+{days}j:code={row.code_used}",
        )
    except Exception:
        pass
    return days


def apply_referrer_reward_on_paid(db: Session, referee_cabinet_id: str) -> bool:
    """Quand le filleul passe en abonnement payant actif → +30 j au parrain."""
    row = (
        db.query(CabinetReferral)
        .filter(CabinetReferral.referee_cabinet_id == referee_cabinet_id)
        .first()
    )
    if not row or row.referrer_reward_applied:
        return False

    from app.services.billing import ensure_subscription, log_subscription_event

    referrer_sub = ensure_subscription(db, row.referrer_cabinet_id)
    now = _now()
    base = referrer_sub.current_period_end or now
    if base.tzinfo is None:
        base = base.replace(tzinfo=timezone.utc)
    if base < now:
        base = now
    # +1 mois ≈ reward
    referrer_sub.current_period_end = base + timedelta(days=REFERRER_REWARD_DAYS)
    if referrer_sub.status == SubscriptionStatus.EXPIRED:
        referrer_sub.status = SubscriptionStatus.ACTIVE
    row.referrer_reward_applied = True
    row.status = "rewarded"
    row.qualified_at = now
    db.flush()
    log_subscription_event(
        db,
        row.referrer_cabinet_id,
        "referral_reward",
        detail=f"+{REFERRER_REWARD_DAYS}j:from={referee_cabinet_id}",
    )
    return True
