"""Notifications cabinet — collab (plaidoirie validée, etc.)."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Cabinet, CabinetNotification, PlaidoirieDraft, User, UserRole

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class DigestEmailRequest(BaseModel):
    assistant_ids: list[str] | None = None


class NotificationOut(BaseModel):
    id: str
    type: str
    title: str
    body: str | None = None
    href: str | None = None
    read: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


def _visible_query(db: Session, user: User):
    q = db.query(CabinetNotification).filter(CabinetNotification.cabinet_id == user.cabinet_id)
    if user.role == UserRole.ASSISTANT:
        return q.filter(
            (CabinetNotification.user_id == user.id)
            | (CabinetNotification.role_target == UserRole.ASSISTANT.value)
        )
    if user.role in (UserRole.AVOCAT, UserRole.ADMIN_CABINET):
        return q.filter(
            (CabinetNotification.user_id == user.id)
            | (
                CabinetNotification.role_target.in_(
                    [UserRole.AVOCAT.value, UserRole.ADMIN_CABINET.value]
                )
            )
            | (
                (CabinetNotification.user_id.is_(None))
                & (CabinetNotification.role_target.is_(None))
            )
        )
    return q.filter(CabinetNotification.user_id == user.id)


@router.get("", response_model=list[NotificationOut])
def list_notifications(
    unread_only: bool = False,
    limit: int = 30,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = _visible_query(db, user)
    if unread_only:
        q = q.filter(CabinetNotification.read_at.is_(None))
    rows = q.order_by(CabinetNotification.created_at.desc()).limit(min(limit, 50)).all()
    return [
        NotificationOut(
            id=r.id,
            type=r.type,
            title=r.title,
            body=r.body,
            href=r.href,
            read=r.read_at is not None,
            created_at=r.created_at,
        )
        for r in rows
    ]


@router.get("/unread-count")
def unread_count(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    n = _visible_query(db, user).filter(CabinetNotification.read_at.is_(None)).count()
    return {"count": int(n)}


class DeleteNotificationsBody(BaseModel):
    ids: list[str] | None = None
    all: bool = False


@router.post("/delete")
def delete_notifications(
    data: DeleteNotificationsBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = _visible_query(db, user)
    if data.all:
        rows = q.all()
    elif data.ids:
        rows = q.filter(CabinetNotification.id.in_(data.ids)).all()
    else:
        rows = []
    n = len(rows)
    for row in rows:
        db.delete(row)
    db.commit()
    return {"ok": True, "count": n}


@router.post("/{notif_id}/read")
def mark_read(
    notif_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = _visible_query(db, user).filter(CabinetNotification.id == notif_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification introuvable")
    if row.read_at is None:
        row.read_at = datetime.now(timezone.utc)
        db.commit()
    return {"ok": True}


@router.post("/read-all")
def mark_all_read(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    rows = _visible_query(db, user).filter(CabinetNotification.read_at.is_(None)).all()
    for r in rows:
        r.read_at = now
    db.commit()
    return {"ok": True, "count": len(rows)}


@router.post("/digest-email")
def send_digest_email(
    data: DigestEmailRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Résumé email aux assistants sélectionnés : plaidoiries validées en attente."""
    if user.role not in (UserRole.AVOCAT, UserRole.ADMIN_CABINET):
        raise HTTPException(status_code=403, detail="Non autorisé")

    q = (
        db.query(User)
        .filter(
            User.cabinet_id == user.cabinet_id,
            User.role == UserRole.ASSISTANT,
            User.is_active.is_(True),
        )
    )
    wanted = [x.strip() for x in (data.assistant_ids or []) if x and x.strip()]
    if wanted:
        q = q.filter(User.id.in_(wanted))
    assistants = q.all()
    if wanted and not assistants:
        raise HTTPException(status_code=400, detail="Aucun assistant valide sélectionné")
    if not assistants:
        return {"ok": True, "sent": 0, "message": "Aucun assistant dans le cabinet."}
    pending = (
        db.query(PlaidoirieDraft)
        .filter(
            PlaidoirieDraft.cabinet_id == user.cabinet_id,
            PlaidoirieDraft.status == "validated",
        )
        .count()
    )
    if pending == 0:
        return {"ok": True, "sent": 0, "message": "Aucune plaidoirie validée à résumer."}

    sent = 0
    from app.services.email import send_digest_validated_pleas_email

    cabinet = db.query(Cabinet).filter(Cabinet.id == user.cabinet_id).first()
    cab_name = cabinet.name if cabinet else "Cabinet"
    for a in assistants:
        try:
            ok = send_digest_validated_pleas_email(
                a.email,
                assistant_name=a.full_name or a.email,
                pending_count=pending,
                cabinet_name=cab_name,
            )
            if ok:
                sent += 1
        except Exception:
            continue
    return {"ok": True, "sent": sent, "pending": pending}
