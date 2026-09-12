"""Codes d'invitation cabinet — formats variés, haute entropie, difficiles à deviner."""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings

# Alphabet lisible (sans 0/O/1/I/L) + minuscules pour plus d'entropie visuelle
_ALPH_UP = "ABCDEFGHJKLMNPQRSTUVWXYZ"
_ALPH_NUM = "23456789"
_ALPH_LOW = "abcdefghjkmnpqrstuvwxyz"
_ALPH_MIX = _ALPH_UP + _ALPH_LOW + _ALPH_NUM


def _expire_days() -> int:
    return max(1, min(90, int(getattr(settings, "JOIN_CODE_EXPIRE_DAYS", 14) or 14)))


def max_approvals() -> int:
    return max(1, min(50, int(getattr(settings, "JOIN_CODE_MAX_APPROVALS", 1) or 1)))


def _rand(n: int, alphabet: str = _ALPH_MIX) -> str:
    return "".join(secrets.choice(alphabet) for _ in range(n))


def generate_join_code(prefix: str | None = None) -> str:
    """
    Formats aléatoires (jamais une seule forme fixe) — très durs à brute-forcer.
    Exemples :
      LX7k-9mQp-2nXr
      4F8a.K2m9.Vx7Q
      INV_a9Kx7mQp2n
      9mQp2n-LEX-7kXr
    """
    style = secrets.randbelow(5)
    if style == 0:
        # Triple blocs mixtes
        return f"{_rand(4)}-{_rand(4)}-{_rand(4)}"
    if style == 1:
        # Points (style licence)
        return f"{_rand(4)}.{_rand(4)}.{_rand(4)}"
    if style == 2:
        # Préfixe INV_ + corps long
        return f"INV_{_rand(10)}"
    if style == 3:
        # Suffixe LEX au milieu
        return f"{_rand(6)}-LEX-{_rand(4)}"
    # Style 4 : préfixe cabinet court + long token url-safe-ish
    clean = "".join(c for c in (prefix or "LX").upper() if c in _ALPH_UP + _ALPH_NUM)
    head = (clean[:3] or "LX") + _rand(2, _ALPH_NUM)
    return f"{head}_{_rand(8)}"


def normalize_join_code(raw: str) -> str:
    # Conserve la casse mixte ; retire espaces seulement
    return (raw or "").strip().replace(" ", "")


def _code_taken(db: Session, code: str, exclude_cabinet_id: str | None = None) -> bool:
    from app.models import Cabinet, CabinetInvite

    q = db.query(Cabinet.id).filter(Cabinet.join_code == code)
    if exclude_cabinet_id:
        q = q.filter(Cabinet.id != exclude_cabinet_id)
    if q.first():
        return True
    # Comparaison exacte (codes mixtes)
    if db.query(CabinetInvite.id).filter(CabinetInvite.code == code).first():
        return True
    # Aussi case-insensitive pour éviter collisions proches
    return (
        db.query(CabinetInvite.id)
        .filter(CabinetInvite.code.ilike(code))
        .first()
        is not None
    )


def assign_unique_join_code(db: Session, cabinet: Any, prefix: str | None = None) -> str:
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=_expire_days())

    for _ in range(32):
        code = generate_join_code(prefix or getattr(cabinet, "name", None))
        if not _code_taken(db, code, exclude_cabinet_id=cabinet.id):
            cabinet.join_code = code
            cabinet.join_code_regenerated_at = now
            cabinet.join_code_expires_at = expires
            cabinet.join_code_approved_count = 0
            return code

    code = f"X{_rand(14)}"
    cabinet.join_code = code
    cabinet.join_code_regenerated_at = now
    cabinet.join_code_expires_at = expires
    cabinet.join_code_approved_count = 0
    return code


def create_personal_invite(
    db: Session,
    cabinet: Any,
    *,
    email: str,
    created_by: str | None,
    role: str = "avocat",
    recipient_name: str | None = None,
) -> Any:
    from app.models import CabinetInvite

    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=_expire_days())
    code = None
    for _ in range(32):
        candidate = generate_join_code(getattr(cabinet, "name", None))
        if not _code_taken(db, candidate):
            code = candidate
            break
    if not code:
        code = f"INV_{secrets.token_urlsafe(9)}"

    invite = CabinetInvite(
        id=str(uuid.uuid4()),
        cabinet_id=cabinet.id,
        email=email.lower().strip(),
        code=code,
        role=(role or "avocat").strip() or "avocat",
        recipient_name=(recipient_name or "").strip() or None,
        created_by=created_by,
        expires_at=expires,
        consumed_at=None,
        created_at=now,
    )
    db.add(invite)
    db.flush()
    return invite


def find_active_invite(db: Session, code: str) -> Any | None:
    """Invite non consommée et non expirée pour le code donné."""
    from app.models import CabinetInvite

    normalized = normalize_join_code(code)
    if not normalized or len(normalized) < 8:
        return None
    invite = (
        db.query(CabinetInvite)
        .filter(
            CabinetInvite.code == normalized,
            CabinetInvite.consumed_at.is_(None),
        )
        .first()
    )
    if not invite:
        # fallback case-insensitive
        invite = (
            db.query(CabinetInvite)
            .filter(
                CabinetInvite.code.ilike(normalized),
                CabinetInvite.consumed_at.is_(None),
            )
            .first()
        )
    if not invite:
        return None
    now = datetime.now(timezone.utc)
    exp = invite.expires_at
    if exp is not None:
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp <= now:
            return None
    return invite


def join_code_status(cabinet: Any) -> dict[str, Any]:
    code = (getattr(cabinet, "join_code", None) or "").strip()
    now = datetime.now(timezone.utc)
    expires_at = getattr(cabinet, "join_code_expires_at", None)
    approved = int(getattr(cabinet, "join_code_approved_count", 0) or 0)
    cap = max_approvals()
    expired = False
    if expires_at is not None:
        exp = expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        expired = exp <= now
    exhausted = approved >= cap
    active = bool(code) and not expired and not exhausted
    return {
        "join_code": code,
        "regenerated_at": getattr(cabinet, "join_code_regenerated_at", None),
        "expires_at": expires_at,
        "approved_count": approved,
        "max_approvals": cap,
        "remaining_approvals": max(0, cap - approved),
        "is_expired": expired,
        "is_exhausted": exhausted,
        "is_active": active,
    }


def is_join_code_accepting(cabinet: Any) -> bool:
    return bool(join_code_status(cabinet)["is_active"])


def record_join_approval(db: Session, cabinet: Any) -> None:
    n = int(getattr(cabinet, "join_code_approved_count", 0) or 0) + 1
    cabinet.join_code_approved_count = n
    if n >= max_approvals():
        assign_unique_join_code(db, cabinet)


def find_pending_join_block(db: Session, email: str, password: str) -> bool:
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
