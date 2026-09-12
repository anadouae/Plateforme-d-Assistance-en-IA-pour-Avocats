"""Rappels fin d'essai + e-mails lifecycle (rétention SaaS)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import (
    Cabinet,
    CabinetSubscription,
    SubscriptionEvent,
    SubscriptionPlan,
    SubscriptionStatus,
    User,
    UserRole,
)
from app.services import billing as billing_svc
from app.services.email import (
    send_quota_warning_email,
    send_trial_converted_email,
    send_trial_ended_email,
    send_trial_reminder_email,
)

logger = logging.getLogger(__name__)

# Jours restants → envoi (comme Cursor / Notion : D-7, D-3, D-1)
_REMINDER_THRESHOLDS = (7, 3, 1)


def _admin_of_cabinet(db: Session, cabinet_id: str) -> User | None:
    return (
        db.query(User)
        .filter(
            User.cabinet_id == cabinet_id,
            User.role == UserRole.ADMIN_CABINET,
            User.is_active.is_(True),
            ~User.email.like("%@deleted.lexhub.invalid"),
        )
        .order_by(User.created_at.asc())
        .first()
    )


def _already_sent(db: Session, cabinet_id: str, event_type: str) -> bool:
    return (
        db.query(SubscriptionEvent)
        .filter(
            SubscriptionEvent.cabinet_id == cabinet_id,
            SubscriptionEvent.event_type == event_type,
        )
        .first()
        is not None
    )


def _days_left(sub: CabinetSubscription) -> int | None:
    if sub.status != SubscriptionStatus.TRIAL or not sub.trial_ends_at:
        return None
    end = sub.trial_ends_at
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    delta = end - datetime.now(timezone.utc)
    return max(0, delta.days)


def process_trial_lifecycle(db: Session) -> dict:
    """À lancer périodiquement (Celery beat) : rappels + fin d'essai."""
    sent_reminders = 0
    ended = 0
    errors = 0

    subs = (
        db.query(CabinetSubscription)
        .filter(CabinetSubscription.status == SubscriptionStatus.TRIAL)
        .all()
    )
    for sub in list(subs):
        try:
            cab = db.query(Cabinet).filter(Cabinet.id == sub.cabinet_id).first()
            admin = _admin_of_cabinet(db, sub.cabinet_id)
            if not cab or not admin:
                continue

            days = _days_left(sub)
            if days is None:
                continue

            # Fin d'essai → refresh : carte + pas d'annulation → ACTIVE payant ; sinon Découverte
            before_plan = sub.plan_id
            before_status = sub.status
            before_provider = str(sub.payment_provider or "")
            billing_svc.refresh_subscription_status(db, sub)
            if before_status == SubscriptionStatus.TRIAL and sub.status != SubscriptionStatus.TRIAL:
                converted = (
                    sub.status == SubscriptionStatus.ACTIVE
                    and before_plan == sub.plan_id
                    and before_provider.startswith("card_mock")
                )
                if converted:
                    ev = "email_trial_converted"
                    if not _already_sent(db, sub.cabinet_id, ev):
                        plan = (
                            db.query(SubscriptionPlan)
                            .filter(SubscriptionPlan.id == sub.plan_id)
                            .first()
                        )
                        cycle = (
                            sub.billing_cycle.value
                            if hasattr(sub.billing_cycle, "value")
                            else str(sub.billing_cycle)
                        )
                        ok = send_trial_converted_email(
                            admin.email,
                            full_name=admin.full_name,
                            cabinet_name=cab.name,
                            plan_name=plan.name if plan else "LexHub",
                            billing_cycle=cycle,
                        )
                        billing_svc.log_subscription_event(
                            db,
                            sub.cabinet_id,
                            ev,
                            plan_slug=plan.slug if plan else None,
                            detail="sent" if ok else "send_failed",
                        )
                        if ok:
                            ended += 1
                else:
                    ev = "email_trial_ended"
                    if not _already_sent(db, sub.cabinet_id, ev):
                        ok = send_trial_ended_email(
                            admin.email,
                            full_name=admin.full_name,
                            cabinet_name=cab.name,
                        )
                        billing_svc.log_subscription_event(
                            db,
                            sub.cabinet_id,
                            ev,
                            plan_slug="free",
                            detail="sent" if ok else "send_failed",
                        )
                        if ok:
                            ended += 1
                continue

            if days <= 0:
                continue

            # Catch-up : si le job a raté le jour exact, on envoie le seuil le plus bas non envoyé
            for threshold in _REMINDER_THRESHOLDS:
                if days > threshold:
                    continue
                ev = f"email_trial_d{threshold}"
                if _already_sent(db, sub.cabinet_id, ev):
                    continue
                ok = send_trial_reminder_email(
                    admin.email,
                    full_name=admin.full_name,
                    cabinet_name=cab.name,
                    days_left=days,
                )
                billing_svc.log_subscription_event(
                    db,
                    sub.cabinet_id,
                    ev,
                    detail="sent" if ok else "send_failed",
                )
                if ok:
                    sent_reminders += 1
                break
        except Exception:
            errors += 1
            logger.exception("trial lifecycle failed for sub %s", getattr(sub, "id", "?"))

    db.commit()
    return {
        "reminders_sent": sent_reminders,
        "trials_ended_emailed": ended,
        "errors": errors,
        "checked": len(subs),
    }


def maybe_send_quota_warning(db: Session, cabinet_id: str) -> bool:
    """Envoie 1 e-mail à ~80% du quota plaidoiries / mois."""
    ent = billing_svc.get_entitlements(db, cabinet_id)
    lim = ent.plaidoiries_limit
    used = ent.plaidoiries_used
    if lim < 0 or used < max(1, int(lim * 0.8)):
        return False
    ym = billing_svc._period_ym()  # noqa: SLF001
    ev = f"email_quota_warn_{ym}"
    if _already_sent(db, cabinet_id, ev):
        return False
    cab = db.query(Cabinet).filter(Cabinet.id == cabinet_id).first()
    admin = _admin_of_cabinet(db, cabinet_id)
    if not cab or not admin:
        return False
    ok = send_quota_warning_email(
        admin.email,
        full_name=admin.full_name,
        cabinet_name=cab.name,
        used=used,
        limit=lim,
    )
    billing_svc.log_subscription_event(
        db, cabinet_id, ev, detail=f"{used}/{lim}" + ("" if ok else " fail")
    )
    return ok
