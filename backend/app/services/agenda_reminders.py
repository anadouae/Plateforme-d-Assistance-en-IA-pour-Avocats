"""Rappels agenda J-7 / J-2 / J-1."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.models import AgendaEvent, Cabinet, CabinetNotification, Case, User

logger = logging.getLogger(__name__)

_CASABLANCA = ZoneInfo("Africa/Casablanca")

_EVENT_TYPE_LABELS = {
    "audience": "Audience",
    "deadline": "Délai",
    "rdv": "Rendez-vous",
    "notification": "Notification",
    "recours": "Délai de recours",
    "expertise": "Expertise",
    "mediation": "Médiation",
    "other": "Événement",
}

# (attr_sent_at, hours_before_center, window_half_hours, label)
_REMINDER_WINDOWS = (
    ("reminder_7d_sent_at", 7 * 24, 6, "J-7"),
    ("reminder_2d_sent_at", 2 * 24, 4, "J-2"),
    ("reminder_1d_sent_at", 24, 3, "J-1"),
)


def _format_starts_at(starts_at: datetime) -> str:
    dt = starts_at
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    local = dt.astimezone(_CASABLANCA)
    return local.strftime("%d/%m/%Y à %H:%M")


def _event_type_label(event_type: str | None) -> str:
    key = (event_type or "other").strip().lower()
    return _EVENT_TYPE_LABELS.get(key, "Événement")


def _active_cabinet_members(db: Session, cabinet_id: str) -> list[User]:
    q = db.query(User).filter(User.cabinet_id == cabinet_id)
    if hasattr(User, "is_active"):
        q = q.filter(User.is_active.is_(True))
    return q.all()


def _notify_event(db: Session, event: AgendaEvent, when_label: str) -> tuple[int, int]:
    cabinet = db.query(Cabinet).filter(Cabinet.id == event.cabinet_id).first()
    cabinet_name = cabinet.name if cabinet else "Cabinet"
    case_ref = None
    if event.case_id:
        case = (
            db.query(Case)
            .filter(Case.id == event.case_id, Case.cabinet_id == event.cabinet_id)
            .first()
        )
        case_ref = case.reference if case else None

    type_label = _event_type_label(event.event_type)
    when = _format_starts_at(event.starts_at)
    title = f"Rappel {when_label} — {type_label}"
    body = f"{event.title} · {when}"
    if case_ref:
        body += f" · dossier {case_ref}"
    if event.city or event.location:
        body += f" · {event.location or ''} {event.city or ''}".strip()

    notified = 0
    emails = 0
    for member in _active_cabinet_members(db, event.cabinet_id):
        notif = CabinetNotification(
            cabinet_id=event.cabinet_id,
            user_id=member.id,
            type=f"agenda.reminder_{when_label.lower().replace('-', '')}",
            title=title,
            body=body,
            href=f"/agenda" + (f"?case={event.case_id}" if event.case_id else ""),
        )
        db.add(notif)
        notified += 1
        try:
            from app.services.email import send_agenda_reminder_email

            if send_agenda_reminder_email(
                member.email,
                full_name=member.full_name,
                cabinet_name=cabinet_name,
                event_title=event.title,
                starts_at_label=when,
                event_type_label=f'{type_label} ({when_label})',
                case_reference=case_ref,
                reminder_label=when_label,
            ):
                emails += 1
        except Exception:
            logger.debug("agenda email skip for %s", member.email, exc_info=True)
    return notified, emails


def send_due_agenda_reminders(db: Session) -> dict:
    """Rappels J-7, J-2, J-1 (fenêtres tolérantes pour polling 15 min)."""
    now = datetime.now(timezone.utc)
    processed = 0
    notified_users = 0
    emails_sent = 0
    errors = 0

    for attr, center_h, half_h, label in _REMINDER_WINDOWS:
        if not hasattr(AgendaEvent, attr):
            continue
        window_start = now + timedelta(hours=center_h - half_h)
        window_end = now + timedelta(hours=center_h + half_h)
        col = getattr(AgendaEvent, attr)
        events = (
            db.query(AgendaEvent)
            .filter(
                AgendaEvent.starts_at >= window_start,
                AgendaEvent.starts_at <= window_end,
                col.is_(None),
            )
            .order_by(AgendaEvent.starts_at.asc())
            .limit(120)
            .all()
        )
        for event in events:
            try:
                n, e = _notify_event(db, event, label)
                setattr(event, attr, now)
                notified_users += n
                emails_sent += e
                processed += 1
            except Exception:
                logger.exception("agenda reminder failed %s", event.id)
                errors += 1

    if processed:
        db.commit()
    return {
        "processed": processed,
        "notified_users": notified_users,
        "emails_sent": emails_sent,
        "errors": errors,
    }
