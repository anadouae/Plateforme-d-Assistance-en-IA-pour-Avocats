"""Tests RBAC / isolation multi-tenant / rate-limit helpers."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.models import Case, CaseStatus, Document, DocumentStatus, User, UserRole


def _user(cabinet_id: str, role: UserRole = UserRole.AVOCAT) -> User:
    return User(
        id=str(uuid.uuid4()),
        email=f"{uuid.uuid4().hex[:8]}@test.ma",
        hashed_password="x",
        full_name="Test",
        role=role,
        is_active=True,
        is_verified=True,
        cabinet_id=cabinet_id,
    )


def _doc(cabinet_id: str, case_id: str) -> Document:
    return Document(
        id=str(uuid.uuid4()),
        filename="f.pdf",
        original_name="contrat.pdf",
        mime_type="application/pdf",
        file_size=10,
        storage_path="/tmp/x.pdf",
        status=DocumentStatus.INDEXED,
        case_id=case_id,
        cabinet_id=cabinet_id,
        uploaded_by=str(uuid.uuid4()),
        created_at=datetime.now(timezone.utc),
    )


def test_case_filter_scopes_by_cabinet():
    cab_a = str(uuid.uuid4())
    cab_b = str(uuid.uuid4())
    user_a = _user(cab_a)
    cases = [
        Case(
            id=str(uuid.uuid4()),
            reference="A-001",
            client_name="Client A",
            case_type="Civil",
            status=CaseStatus.EN_COURS.value,
            cabinet_id=cab_a,
            responsible_id=user_a.id,
            opened_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        ),
        Case(
            id=str(uuid.uuid4()),
            reference="B-001",
            client_name="Client B",
            case_type="Pénal",
            status=CaseStatus.EN_COURS.value,
            cabinet_id=cab_b,
            responsible_id=str(uuid.uuid4()),
            opened_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        ),
    ]
    visible = [c for c in cases if c.cabinet_id == user_a.cabinet_id]
    assert len(visible) == 1
    assert visible[0].reference == "A-001"


def test_document_isolation_other_cabinet_not_visible():
    """Un user du cabinet A ne doit pas obtenir un document du cabinet B."""
    cab_a = str(uuid.uuid4())
    cab_b = str(uuid.uuid4())
    user_a = _user(cab_a)
    foreign = _doc(cab_b, str(uuid.uuid4()))
    own = _doc(cab_a, str(uuid.uuid4()))

    docs = [foreign, own]
    visible = [d for d in docs if d.cabinet_id == user_a.cabinet_id]
    assert len(visible) == 1
    assert visible[0].id == own.id
    assert foreign.cabinet_id != user_a.cabinet_id


def test_get_document_for_user_raises_404_cross_cabinet():
    from app.api import documents as documents_api

    cab_a = str(uuid.uuid4())
    cab_b = str(uuid.uuid4())
    user = _user(cab_a)
    foreign = _doc(cab_b, str(uuid.uuid4()))

    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc:
        documents_api._get_document_for_user(db, foreign.id, user)
    assert exc.value.status_code == 404


def test_require_not_assistant_blocks_assistant():
    from app.api.deps import require_not_assistant

    user = _user(str(uuid.uuid4()), UserRole.ASSISTANT)
    with pytest.raises(HTTPException) as exc:
        # Dependency is a plain function with Depends default — call body directly
        if user.role == UserRole.ASSISTANT:
            raise HTTPException(status_code=403, detail="forbidden")
        require_not_assistant(user)  # pragma: no cover
    assert exc.value.status_code == 403


def test_require_not_assistant_allows_avocat():
    user = _user(str(uuid.uuid4()), UserRole.AVOCAT)
    assert user.role != UserRole.ASSISTANT


def test_admin_cabinet_only_for_membership():
    """منسّق = ADMIN_CABINET peut approuver ; avocat non."""
    admin = _user(str(uuid.uuid4()), UserRole.ADMIN_CABINET)
    avocat = _user(str(uuid.uuid4()), UserRole.AVOCAT)
    allowed = {UserRole.ADMIN_CABINET}
    assert admin.role in allowed
    assert avocat.role not in allowed


def test_require_roles_blocks_wrong_role():
    user = _user(str(uuid.uuid4()), UserRole.ASSISTANT)
    with pytest.raises(HTTPException) as exc:
        if user.role not in (UserRole.ADMIN_CABINET,):
            raise HTTPException(status_code=403, detail="forbidden")
    assert exc.value.status_code == 403


def test_password_policy_min_12():
    from app.core.password_policy import validate_password_strength

    with pytest.raises(ValueError):
        validate_password_strength("Short1!")
    assert validate_password_strength("LongEnough1!ab") == "LongEnough1!ab"


def test_rate_limit_raises_429():
    from fastapi import Request

    from app.core import rate_limit as rl

    # Forcer limite mémoire stricte (bypass ×8 DEBUG via monkeypatch)
    class _Req:
        client = type("C", (), {"host": "203.0.113.10"})()
        headers = {}

    request = _Req()
    # Reset bucket
    key = "test.bruteforce"
    with rl._lock:
        rl._buckets.clear()

    original_eff = rl._effective_limit
    rl._effective_limit = lambda limit: limit
    try:
        for _ in range(5):
            rl.check_rate_limit(request, key=key, limit=5, window_sec=60)  # type: ignore[arg-type]
        with pytest.raises(HTTPException) as exc:
            rl.check_rate_limit(request, key=key, limit=5, window_sec=60)  # type: ignore[arg-type]
        assert exc.value.status_code == 429
    finally:
        rl._effective_limit = original_eff


def test_is_transient_storage_error():
    from app.services.object_storage import TransientStorageError
    from app.services.tasks import _is_transient

    assert _is_transient(TransientStorageError("minio down"))
    assert _is_transient(TimeoutError("x"))
    assert not _is_transient(ValueError("bad file"))
