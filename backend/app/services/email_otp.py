"""OTP / magic-link email (hashés, usage unique, expiration courte)."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models import EmailOtp

PURPOSE_REGISTER = "register"
PURPOSE_MAGIC_LOGIN = "magic_login"
PURPOSE_PASSWORD_CHANGE = "password_change"
PURPOSE_ACCOUNT_DELETE = "account_delete"
PURPOSE_EMAIL_CHANGE = "email_change"


def _hash(value: str) -> str:
    return hashlib.sha256(value.strip().encode("utf-8")).hexdigest()


def create_otp(
    db: Session,
    *,
    email: str,
    purpose: str,
    minutes: int = 15,
    digits: bool = True,
) -> str:
    """Crée un OTP ; invalide les précédents non utilisés pour (email, purpose)."""
    email = email.strip().lower()
    now = datetime.now(timezone.utc)
    db.query(EmailOtp).filter(
        EmailOtp.email == email,
        EmailOtp.purpose == purpose,
        EmailOtp.used_at.is_(None),
    ).update({"used_at": now})

    raw = f"{secrets.randbelow(1_000_000):06d}" if digits else secrets.token_urlsafe(32)
    row = EmailOtp(
        id=str(uuid.uuid4()),
        email=email,
        purpose=purpose,
        code_hash=_hash(raw),
        expires_at=now + timedelta(minutes=minutes),
        created_at=now,
    )
    db.add(row)
    db.flush()
    return raw


def otp_is_valid(
    db: Session,
    *,
    email: str,
    purpose: str,
    code: str,
) -> bool:
    """Vérifie sans consommer (pour débloquer le formulaire d'inscription)."""
    email = email.strip().lower()
    row = (
        db.query(EmailOtp)
        .filter(
            EmailOtp.email == email,
            EmailOtp.purpose == purpose,
            EmailOtp.code_hash == _hash(code),
            EmailOtp.used_at.is_(None),
        )
        .first()
    )
    if not row:
        return False
    return row.expires_at >= datetime.now(timezone.utc)


def consume_otp(
    db: Session,
    *,
    email: str,
    purpose: str,
    code: str,
) -> bool:
    email = email.strip().lower()
    row = (
        db.query(EmailOtp)
        .filter(
            EmailOtp.email == email,
            EmailOtp.purpose == purpose,
            EmailOtp.code_hash == _hash(code),
            EmailOtp.used_at.is_(None),
        )
        .first()
    )
    if not row:
        return False
    if row.expires_at < datetime.now(timezone.utc):
        return False
    row.used_at = datetime.now(timezone.utc)
    db.flush()
    return True


def create_magic_token(db: Session, email: str, minutes: int = 15) -> str:
    return create_otp(
        db, email=email, purpose=PURPOSE_MAGIC_LOGIN, minutes=minutes, digits=False
    )


def consume_magic_token(db: Session, token: str) -> str | None:
    """Retourne l'email si le magic token est valide."""
    row = (
        db.query(EmailOtp)
        .filter(
            EmailOtp.purpose == PURPOSE_MAGIC_LOGIN,
            EmailOtp.code_hash == _hash(token),
            EmailOtp.used_at.is_(None),
        )
        .first()
    )
    if not row or row.expires_at < datetime.now(timezone.utc):
        return None
    row.used_at = datetime.now(timezone.utc)
    db.flush()
    return row.email
