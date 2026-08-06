import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import EmailToken, TokenType, User


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def create_token(
    db: Session,
    user: User,
    token_type: TokenType,
    hours: int,
) -> str:
    raw = secrets.token_urlsafe(32)
    token = EmailToken(
        user_id=user.id,
        token_hash=_hash_token(raw),
        token_type=token_type,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=hours),
    )
    db.add(token)
    db.flush()
    return raw


def consume_token(db: Session, raw: str, token_type: TokenType) -> User | None:
    hashed = _hash_token(raw)
    record = (
        db.query(EmailToken)
        .filter(
            EmailToken.token_hash == hashed,
            EmailToken.token_type == token_type,
            EmailToken.used_at.is_(None),
        )
        .first()
    )
    if not record:
        return None
    if record.expires_at < datetime.now(timezone.utc):
        return None
    user = db.query(User).filter(User.id == record.user_id).first()
    if not user:
        return None
    record.used_at = datetime.now(timezone.utc)
    return user


def verify_email_hours() -> int:
    return settings.EMAIL_VERIFY_EXPIRE_HOURS


def reset_password_hours() -> int:
    return settings.PASSWORD_RESET_EXPIRE_HOURS


def invite_hours() -> int:
    return settings.INVITE_EXPIRE_HOURS
