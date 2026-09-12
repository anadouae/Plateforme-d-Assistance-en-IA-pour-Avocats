"""Rétention SaaS LexHub — renouvellement, tips, win-back, digest, 2FA, sièges."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import (
    AgendaEvent,
    AuditLog,
    Cabinet,
    CabinetSubscription,
    Case,
    Document,
    PlaidoirieDraft,
    SubscriptionEvent,
    SubscriptionPlan,
    SubscriptionStatus,
    User,
    UserRole,
)
from app.services import billing as billing_svc
from app.services.email import (
    send_changelog_soft_email,
    send_inactivity_winback_email,
    send_onboarding_tip_email,
    send_payment_failed_email,
    send_renewal_reminder_email,
    send_seats_almost_full_email,
    send_twofa_nudge_email,
    send_upgrade_checklist_email,
    send_weekly_cabinet_digest_email,
)

logger = logging.getLogger(__name__)

CHANGELOG_ITEMS = [
    "Essai Cabinet 14 jours + rappels e-mail J-7 / J-3 / J-1",
    "Invitations équipe 100 % par e-mail (lien sécurisé)",
    "Bannière upgrade intelligente (essai, Découverte, quotas)",
    "Factures / reçus prêts pour CMI · PayZone",
    "Rappels agenda ~48 h pour toute l'équipe",
    "Clé de barre IA (quotas free en attendant OpenAI)",
]

_RENEWAL_THRESHOLDS = (7, 1)


def _now() -> datetime:
    return datetime.now(timezone.utc)


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


def _log(db: Session, cabinet_id: str, event_type: str, *, detail: str | None = None, plan_slug: str | None = None) -> None:
    billing_svc.log_subscription_event(
        db, cabinet_id, event_type, detail=detail, plan_slug=plan_slug
    )


def _aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _cabinet_age_days(cab: Cabinet) -> int:
    created = _aware(cab.created_at) or _now()
    return max(0, (_now() - created).days)


def _plea_count(db: Session, cabinet_id: str) -> int:
    return (
        db.query(func.count(PlaidoirieDraft.id))
        .filter(PlaidoirieDraft.cabinet_id == cabinet_id)
        .scalar()
        or 0
    )


def _last_activity_at(db: Session, cabinet_id: str) -> datetime | None:
    row = (
        db.query(func.max(AuditLog.created_at))
        .filter(AuditLog.cabinet_id == cabinet_id)
        .scalar()
    )
    return _aware(row)


# ─── Insights in-app (idées intelligentes) ───────────────────────────────────


def build_smart_insights(db: Session, cabinet_id: str, *, user: User | None = None) -> list[dict]:
    """Conseils contextuels pour maximiser l'usage (type Cursor tips)."""
    tips: list[dict] = []
    try:
        ent = billing_svc.get_entitlements(db, cabinet_id)
    except Exception:
        return tips

    plan = ent.plan
    cab = db.query(Cabinet).filter(Cabinet.id == cabinet_id).first()
    pleas = _plea_count(db, cabinet_id)
    age = _cabinet_age_days(cab) if cab else 0

    if ent.status == "trial" and ent.trial_days_left is not None:
        tips.append(
            {
                "id": "trial_countdown",
                "priority": 100 if ent.trial_days_left <= 3 else 70,
                "tone": "urgent" if ent.trial_days_left <= 3 else "info",
                "title": f"Essai {plan.name} — {ent.trial_days_left} j. restants",
                "body": "Choisissez Solo ou Cabinet avant la bascule Découverte.",
                "cta": "Choisir mon plan",
                "href": "/settings#abonnement",
            }
        )
    elif plan.slug == "free":
        tips.append(
            {
                "id": "free_upgrade",
                "priority": 90,
                "tone": "upgrade",
                "title": "Vous êtes sur Découverte",
                "body": "Solo 299 MAD ou Cabinet 699 MAD pour retrouver volume et équipe.",
                "cta": "Voir les plans",
                "href": "/tarifs",
            }
        )

    if pleas == 0 and age <= 14:
        tips.append(
            {
                "id": "first_plea",
                "priority": 55,
                "tone": "info",
                "title": "Pipeline plaidoirie",
                "body": "Dossier → pièces → dictée → rédaction → export Word. Quand vous êtes prêt.",
                "cta": "Voir l'atelier",
                "href": "/plaidoirie",
            }
        )

    lim = ent.plaidoiries_limit
    used = ent.plaidoiries_used
    if lim >= 0 and used / max(lim, 1) >= 0.8:
        tips.append(
            {
                "id": "quota_plea",
                "priority": 85,
                "tone": "warn",
                "title": f"Quota plaidoiries {used}/{lim}",
                "body": "Augmentez le plan pour éviter une coupure en audience.",
                "cta": "Augmenter",
                "href": "/settings#abonnement",
            }
        )

    av_lim, as_lim = plan.max_avocats, plan.max_assistants
    # Uniquement si capacité réelle (used ≤ limit). Ignore les comptes surpeuplés (seed / legacy).
    if (
        av_lim > 0
        and ent.avocats_used <= av_lim
        and ent.avocats_used / max(av_lim, 1) >= 0.8
    ):
        tips.append(
            {
                "id": "seats_avocat",
                "priority": 75,
                "tone": "warn",
                "title": f"Sièges avocats {ent.avocats_used}/{av_lim}",
                "body": "Presque plein — upgrader avant une invitation urgente.",
                "cta": "Gérer l'abonnement",
                "href": "/settings#abonnement",
            }
        )
    if (
        as_lim > 0
        and ent.assistants_used <= as_lim
        and ent.assistants_used / max(as_lim, 1) >= 0.8
    ):
        tips.append(
            {
                "id": "seats_assistant",
                "priority": 74,
                "tone": "warn",
                "title": f"Sièges assistants {ent.assistants_used}/{as_lim}",
                "body": "Passez au plan supérieur pour agrandir l'équipe.",
                "cta": "Voir les plans",
                "href": "/tarifs",
            }
        )
    elif plan.slug in ("solo", "pro", "enterprise") and ent.assistants_used == 0 and as_lim > 0:
        tips.append(
            {
                "id": "invite_assistant",
                "priority": 55,
                "tone": "tip",
                "title": "Invitez un assistant",
                "body": "Déléguez mise en forme et exports — inclus dans votre plan.",
                "cta": "Inviter",
                "href": "/team",
            }
        )

    if user and user.role == UserRole.ADMIN_CABINET and not user.totp_enabled and age >= 2:
        tips.append(
            {
                "id": "nudge_2fa",
                "priority": 60,
                "tone": "security",
                "title": "Activez la 2FA",
                "body": "2 minutes pour protéger dossiers et plaidoiries.",
                "cta": "Sécuriser",
                "href": "/settings#securite",
            }
        )

    period_end = ent.period_end
    if (
        ent.status == "active"
        and plan.slug != "free"
        and period_end
        and not ent.subscription.cancel_at_period_end
    ):
        days = max(0, (_aware(period_end) - _now()).days)  # type: ignore[operator]
        if days <= 7:
            tips.append(
                {
                    "id": "renewal_soon",
                    "priority": 80,
                    "tone": "info",
                    "title": f"Renouvellement dans {days} j.",
                    "body": f"Plan {plan.name} — vérifiez le moyen de paiement.",
                    "cta": "Voir l'abonnement",
                    "href": "/settings#abonnement",
                }
            )

    if ent.subscription.status == SubscriptionStatus.PAST_DUE:
        tips.append(
            {
                "id": "past_due",
                "priority": 110,
                "tone": "urgent",
                "title": "Paiement en échec",
                "body": "Régularisez pour éviter la restriction d'accès.",
                "cta": "Régulariser",
                "href": "/settings#abonnement",
            }
        )

    tips.sort(key=lambda t: -int(t.get("priority") or 0))
    return tips[:5]


# ─── Jobs ────────────────────────────────────────────────────────────────────


def process_renewal_reminders(db: Session) -> dict:
    sent = 0
    subs = (
        db.query(CabinetSubscription)
        .filter(
            CabinetSubscription.status == SubscriptionStatus.ACTIVE,
            CabinetSubscription.cancel_at_period_end.is_(False),
            CabinetSubscription.current_period_end.isnot(None),
        )
        .all()
    )
    for sub in subs:
        plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == sub.plan_id).first()
        if not plan or plan.slug == "free" or plan.price_mad_monthly <= 0:
            continue
        end = _aware(sub.current_period_end)
        if not end:
            continue
        days = (end - _now()).days
        if days < 0:
            continue
        admin = _admin_of_cabinet(db, sub.cabinet_id)
        cab = db.query(Cabinet).filter(Cabinet.id == sub.cabinet_id).first()
        if not admin or not cab:
            continue
        cycle = sub.billing_cycle.value if hasattr(sub.billing_cycle, "value") else str(sub.billing_cycle)
        amount = plan.price_mad_yearly if cycle == "yearly" else plan.price_mad_monthly
        for threshold in _RENEWAL_THRESHOLDS:
            if days > threshold:
                continue
            ym = end.strftime("%Y%m")
            ev = f"email_renewal_d{threshold}_{ym}"
            if _already_sent(db, sub.cabinet_id, ev):
                continue
            ok = send_renewal_reminder_email(
                admin.email,
                full_name=admin.full_name,
                cabinet_name=cab.name,
                plan_name=plan.name,
                days_left=max(days, 1) if threshold == 1 else days,
                amount_mad=amount,
                period_end_label=end.strftime("%d/%m/%Y"),
            )
            _log(db, sub.cabinet_id, ev, detail="sent" if ok else "fail", plan_slug=plan.slug)
            if ok:
                sent += 1
            break
    db.commit()
    return {"renewal_reminders": sent}


def process_onboarding_tips(db: Session) -> dict:
    sent = 0
    cabs = db.query(Cabinet).all()
    for cab in cabs:
        age = _cabinet_age_days(cab)
        if age not in (1, 2):
            continue
        # J+1 : skip si déjà une plaidoirie (activation OK)
        if age == 1 and _plea_count(db, cab.id) > 0:
            continue
        admin = _admin_of_cabinet(db, cab.id)
        if not admin:
            continue
        ev = f"email_tip_d{age}"
        if _already_sent(db, cab.id, ev):
            continue
        ok = send_onboarding_tip_email(
            admin.email,
            full_name=admin.full_name,
            cabinet_name=cab.name,
            day=age,
        )
        _log(db, cab.id, ev, detail="sent" if ok else "fail")
        if ok:
            sent += 1
    db.commit()
    return {"onboarding_tips": sent}


def process_inactivity_winback(db: Session) -> dict:
    sent = 0
    cutoff = _now() - timedelta(days=14)
    cabs = db.query(Cabinet).all()
    for cab in cabs:
        last = _last_activity_at(db, cab.id)
        created = _aware(cab.created_at)
        if created and created > cutoff:
            continue  # trop jeune
        if last and last > cutoff:
            continue
        # pas d'activité depuis 14 j (ou jamais d'audit)
        week = _now().strftime("%Y%W")
        ev = f"email_inactive_14d_{week}"
        if _already_sent(db, cab.id, ev):
            continue
        admin = _admin_of_cabinet(db, cab.id)
        if not admin:
            continue
        ok = send_inactivity_winback_email(
            admin.email,
            full_name=admin.full_name,
            cabinet_name=cab.name,
            days_inactive=14,
        )
        _log(db, cab.id, ev, detail="sent" if ok else "fail")
        if ok:
            sent += 1
    db.commit()
    return {"inactivity_winbacks": sent}


def process_twofa_nudges(db: Session) -> dict:
    sent = 0
    min_age = _now() - timedelta(days=3)
    admins = (
        db.query(User)
        .filter(
            User.role == UserRole.ADMIN_CABINET,
            User.is_active.is_(True),
            User.totp_enabled.is_(False),
            User.created_at <= min_age,
            ~User.email.like("%@deleted.lexhub.invalid"),
        )
        .all()
    )
    for admin in admins:
        if not admin.cabinet_id:
            continue
        month = _now().strftime("%Y%m")
        ev = f"email_2fa_nudge_{month}"
        if _already_sent(db, admin.cabinet_id, ev):
            continue
        ok = send_twofa_nudge_email(admin.email, full_name=admin.full_name)
        _log(db, admin.cabinet_id, ev, detail="sent" if ok else "fail")
        if ok:
            sent += 1
    db.commit()
    return {"twofa_nudges": sent}


def process_weekly_digests(db: Session) -> dict:
    sent = 0
    since = _now() - timedelta(days=7)
    week = _now().strftime("%Y%W")
    cabs = db.query(Cabinet).all()
    for cab in cabs:
        ev = f"email_weekly_digest_{week}"
        if _already_sent(db, cab.id, ev):
            continue
        admin = _admin_of_cabinet(db, cab.id)
        if not admin:
            continue
        cases_n = (
            db.query(func.count(Case.id))
            .filter(Case.cabinet_id == cab.id, Case.opened_at >= since)
            .scalar()
            or 0
        )
        pleas_n = (
            db.query(func.count(PlaidoirieDraft.id))
            .filter(PlaidoirieDraft.cabinet_id == cab.id, PlaidoirieDraft.created_at >= since)
            .scalar()
            or 0
        )
        docs_n = (
            db.query(func.count(Document.id))
            .filter(Document.cabinet_id == cab.id, Document.created_at >= since)
            .scalar()
            or 0
        )
        events_n = (
            db.query(func.count(AgendaEvent.id))
            .filter(AgendaEvent.cabinet_id == cab.id, AgendaEvent.created_at >= since)
            .scalar()
            or 0
        )
        if cases_n + pleas_n + docs_n + events_n == 0:
            continue  # silence si zéro activité
        ok = send_weekly_cabinet_digest_email(
            admin.email,
            full_name=admin.full_name,
            cabinet_name=cab.name,
            cases_n=cases_n,
            pleas_n=pleas_n,
            docs_n=docs_n,
            events_n=events_n,
        )
        _log(db, cab.id, ev, detail="sent" if ok else "fail")
        if ok:
            sent += 1
    db.commit()
    return {"weekly_digests": sent}


def process_changelog_soft(db: Session) -> dict:
    """1 e-mail changelog / mois pour admins de cabinets actifs payants ou trial."""
    sent = 0
    month = _now().strftime("%Y%m")
    subs = db.query(CabinetSubscription).filter(
        CabinetSubscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL])
    ).all()
    for sub in subs:
        plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == sub.plan_id).first()
        if not plan or plan.slug == "free":
            continue
        ev = f"email_changelog_{month}"
        if _already_sent(db, sub.cabinet_id, ev):
            continue
        admin = _admin_of_cabinet(db, sub.cabinet_id)
        if not admin:
            continue
        ok = send_changelog_soft_email(
            admin.email, full_name=admin.full_name, items=CHANGELOG_ITEMS
        )
        _log(db, sub.cabinet_id, ev, detail="sent" if ok else "fail", plan_slug=plan.slug)
        if ok:
            sent += 1
    db.commit()
    return {"changelogs": sent}


def maybe_send_seats_warning(db: Session, cabinet_id: str, role: str) -> bool:
    ent = billing_svc.get_entitlements(db, cabinet_id)
    if role in ("assistant", "assistant_juridique"):
        used, lim, label = ent.assistants_used, ent.plan.max_assistants, "assistants"
    else:
        used, lim, label = ent.avocats_used, ent.plan.max_avocats, "avocats"
    if lim <= 0 or used / max(lim, 1) < 0.8:
        return False
    ym = billing_svc._period_ym()  # noqa: SLF001
    ev = f"email_seats_{label}_{ym}"
    if _already_sent(db, cabinet_id, ev):
        return False
    cab = db.query(Cabinet).filter(Cabinet.id == cabinet_id).first()
    admin = _admin_of_cabinet(db, cabinet_id)
    if not cab or not admin:
        return False
    ok = send_seats_almost_full_email(
        admin.email,
        full_name=admin.full_name,
        cabinet_name=cab.name,
        role_label=label,
        used=used,
        limit=lim,
    )
    _log(db, cabinet_id, ev, detail=f"{used}/{lim}")
    return ok


def mark_payment_failed(db: Session, cabinet_id: str, *, amount_mad: int | None = None) -> bool:
    """Appelé par webhook CMI/PayZone (ou simulation admin)."""
    sub = billing_svc.ensure_subscription(db, cabinet_id)
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == sub.plan_id).first()
    sub.status = SubscriptionStatus.PAST_DUE
    db.flush()
    cab = db.query(Cabinet).filter(Cabinet.id == cabinet_id).first()
    admin = _admin_of_cabinet(db, cabinet_id)
    _log(db, cabinet_id, "payment_failed", plan_slug=plan.slug if plan else None)
    if not admin or not cab or not plan:
        return False
    day = _now().strftime("%Y%m%d")
    ev = f"email_payment_failed_{day}"
    if _already_sent(db, cabinet_id, ev):
        return False
    ok = send_payment_failed_email(
        admin.email,
        full_name=admin.full_name,
        cabinet_name=cab.name,
        plan_name=plan.name,
        amount_mad=amount_mad,
    )
    _log(db, cabinet_id, ev, detail="sent" if ok else "fail")
    return ok


def send_upgrade_checklist_for_cabinet(
    db: Session, cabinet_id: str, *, plan_name: str, admin: User, cabinet_name: str
) -> bool:
    ev = f"email_upgrade_checklist_{plan_name}_{_now().strftime('%Y%m')}"
    if _already_sent(db, cabinet_id, ev):
        return False
    ok = send_upgrade_checklist_email(
        admin.email,
        full_name=admin.full_name,
        cabinet_name=cabinet_name,
        plan_name=plan_name,
    )
    _log(db, cabinet_id, ev, detail="sent" if ok else "fail")
    return ok


def process_retention_daily(db: Session) -> dict:
    """Job quotidien 9h : renouvellement + tips + inactivité + 2FA + changelog mensuel."""
    out: dict = {}
    try:
        out.update(process_renewal_reminders(db))
    except Exception:
        logger.exception("renewal reminders failed")
        out["renewal_error"] = True
    try:
        out.update(process_onboarding_tips(db))
    except Exception:
        logger.exception("onboarding tips failed")
        out["tips_error"] = True
    try:
        out.update(process_inactivity_winback(db))
    except Exception:
        logger.exception("inactivity failed")
        out["inactive_error"] = True
    try:
        out.update(process_twofa_nudges(db))
    except Exception:
        logger.exception("2fa nudge failed")
        out["twofa_error"] = True
    # Changelog : 1er du mois seulement
    if _now().day == 1:
        try:
            out.update(process_changelog_soft(db))
        except Exception:
            logger.exception("changelog failed")
            out["changelog_error"] = True
    return out
