"""Codes de récupération MFA à usage unique (hashés)."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import MfaRecoveryCode


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.strip().upper().encode("utf-8")).hexdigest()


def generate_recovery_codes(db: Session, user_id: str, count: int = 10) -> list[str]:
    """Remplace les anciens codes et retourne les codes en clair (affichage unique)."""
    db.query(MfaRecoveryCode).filter(MfaRecoveryCode.user_id == user_id).delete()
    plain: list[str] = []
    now = datetime.now(timezone.utc)
    for _ in range(count):
        raw = f"{secrets.token_hex(4)}-{secrets.token_hex(4)}".upper()
        plain.append(raw)
        db.add(
            MfaRecoveryCode(
                user_id=user_id,
                code_hash=_hash_code(raw),
                created_at=now,
            )
        )
    db.flush()
    return plain


def consume_recovery_code(db: Session, user_id: str, code: str) -> bool:
    if not code:
        return False
    row = (
        db.query(MfaRecoveryCode)
        .filter(
            MfaRecoveryCode.user_id == user_id,
            MfaRecoveryCode.code_hash == _hash_code(code),
            MfaRecoveryCode.used_at.is_(None),
        )
        .first()
    )
    if not row:
        return False
    row.used_at = datetime.now(timezone.utc)
    db.flush()
    return True
