"""Archive journal d'audit plateforme (>90 j) en Excel — conservation longue durée."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models import AdminAuditArchive, AuditLog, Cabinet, User
from app.services.activity_archive import build_xlsx_bytes
from app.services.object_storage import read_file, save_file

RETENTION_DAYS = 90
PLATFORM_SCOPE = "platform"


def maybe_archive_old_admin_audit(db: Session, *, force: bool = False) -> AdminAuditArchive | None:
    """Archive les logs plateforme > 90 j (min 50 lignes sauf force)."""
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=RETENTION_DAYS)
    logs = (
        db.query(AuditLog)
        .filter(AuditLog.created_at < cutoff)
        .order_by(AuditLog.created_at.asc())
        .limit(5000)
        .all()
    )
    if not logs:
        return None
    if not force and len(logs) < 50:
        return None

    user_ids = {l.user_id for l in logs if l.user_id}
    cabinet_ids = {l.cabinet_id for l in logs if l.cabinet_id}
    names: dict[str, str] = {}
    emails: dict[str, str] = {}
    if user_ids:
        for u in db.query(User).filter(User.id.in_(user_ids)).all():
            names[u.id] = u.full_name or ""
            emails[u.id] = u.email or ""
    cab_names: dict[str, str] = {}
    if cabinet_ids:
        for c in db.query(Cabinet).filter(Cabinet.id.in_(cabinet_ids)).all():
            cab_names[c.id] = c.name

    headers = ["Date (UTC)", "Action", "Utilisateur", "Email", "Cabinet", "IP", "Détails"]
    rows = [
        [
            (l.created_at.isoformat() if l.created_at else ""),
            l.action or "",
            names.get(l.user_id, "") if l.user_id else "",
            emails.get(l.user_id, "") if l.user_id else "",
            cab_names.get(l.cabinet_id, "") if l.cabinet_id else "",
            l.ip_address or "",
            (l.details or "")[:2000],
        ]
        for l in logs
    ]
    period_start = logs[0].created_at or cutoff
    period_end = logs[-1].created_at or cutoff
    stamp = now.strftime("%Y%m%d_%H%M")
    filename = f"audit_plateforme_{stamp}.xlsx"
    payload = build_xlsx_bytes(headers, rows)
    storage_path = save_file(payload, PLATFORM_SCOPE, "_audit_archives", ".xlsx")

    archive = AdminAuditArchive(
        filename=filename,
        storage_path=storage_path,
        period_start=period_start,
        period_end=period_end,
        row_count=len(logs),
        created_at=now,
    )
    db.add(archive)
    for l in logs:
        db.delete(l)
    db.commit()
    db.refresh(archive)
    return archive


def admin_audit_archive_bytes(archive: AdminAuditArchive) -> bytes:
    return read_file(archive.storage_path)
