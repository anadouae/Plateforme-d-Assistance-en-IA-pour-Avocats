"""Codes d'invitation cabinet (lisibles, sans caractères ambigus)."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone

from sqlalchemy.orm import Session

# Pas de 0/O, 1/I/L
_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def generate_join_code(prefix: str | None = None) -> str:
    """Format lisible : PREFIX-XXXX (ex. ATLAS-7F2K)."""
    clean = "".join(c for c in (prefix or "SANAD").upper() if c in _ALPHABET)
    if len(clean) < 3:
        clean = "SANAD"
    head = clean[:5]
    tail = "".join(secrets.choice(_ALPHABET) for _ in range(4))
    return f"{head}-{tail}"


def normalize_join_code(raw: str) -> str:
    return (raw or "").strip().upper().replace(" ", "")


def assign_unique_join_code(db: Session, cabinet, prefix: str | None = None) -> str:
    from app.models import Cabinet

    for _ in range(24):
        code = generate_join_code(prefix or cabinet.name)
        exists = (
            db.query(Cabinet.id)
            .filter(Cabinet.join_code == code, Cabinet.id != cabinet.id)
            .first()
        )
        if not exists:
            cabinet.join_code = code
            cabinet.join_code_regenerated_at = datetime.now(timezone.utc)
            return code
    # fallback ultra rare
    code = generate_join_code("X" + secrets.token_hex(2).upper())
    cabinet.join_code = code
    cabinet.join_code_regenerated_at = datetime.now(timezone.utc)
    return code


def find_pending_join_block(db: Session, email: str, password: str) -> bool:
    """True si email+mdp correspondent à une demande pending."""
    from app.core.security import verify_password
    from app.models import MembershipRequest, MembershipRequestStatus

    req = (
        db.query(MembershipRequest)
        .filter(
            MembershipRequest.email == email.lower().strip(),
            MembershipRequest.status == MembershipRequestStatus.PENDING.value,
        )
        .first()
    )
    if not req:
        return False
    return verify_password(password, req.hashed_password)
