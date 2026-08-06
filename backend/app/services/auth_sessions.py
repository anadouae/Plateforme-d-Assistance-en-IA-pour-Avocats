"""Sessions serveur pour refresh tokens (rotation + révocation)."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import AuthSession


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(
    db: Session,
    *,
    user_id: str,
    refresh_token: str,
    ip: str | None = None,
    user_agent: str | None = None,
) -> AuthSession:
    session = AuthSession(
        id=str(uuid.uuid4()),
        user_id=user_id,
        refresh_token_hash=hash_refresh_token(refresh_token),
        ip_address=ip,
        user_agent=(user_agent or "")[:255] or None,
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        created_at=datetime.now(timezone.utc),
        last_used_at=datetime.now(timezone.utc),
    )
    db.add(session)
    db.flush()
    return session


def get_valid_session(db: Session, refresh_token: str) -> AuthSession | None:
    row = (
        db.query(AuthSession)
        .filter(AuthSession.refresh_token_hash == hash_refresh_token(refresh_token))
        .first()
    )
    if not row or row.revoked_at:
        return None
    if row.expires_at < datetime.now(timezone.utc):
        return None
    return row


def rotate_session(
    db: Session,
    session: AuthSession,
    *,
    new_refresh_token: str,
    ip: str | None = None,
    user_agent: str | None = None,
) -> AuthSession:
    session.revoked_at = datetime.now(timezone.utc)
    return create_session(
        db,
        user_id=session.user_id,
        refresh_token=new_refresh_token,
        ip=ip,
        user_agent=user_agent,
    )


def revoke_session(db: Session, refresh_token: str) -> None:
    row = get_valid_session(db, refresh_token)
    if row:
        row.revoked_at = datetime.now(timezone.utc)
        db.flush()


def revoke_all_user_sessions(db: Session, user_id: str) -> None:
    now = datetime.now(timezone.utc)
    db.query(AuthSession).filter(
        AuthSession.user_id == user_id,
        AuthSession.revoked_at.is_(None),
    ).update({"revoked_at": now})
    db.flush()


def session_is_active(db: Session, session_id: str | None) -> bool:
    if not session_id:
        return True  # jetons legacy sans sid
    row = db.query(AuthSession).filter(AuthSession.id == session_id).first()
    if not row or row.revoked_at:
        return False
    return row.expires_at >= datetime.now(timezone.utc)
