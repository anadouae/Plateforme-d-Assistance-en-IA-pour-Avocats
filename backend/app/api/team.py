"""Équipe cabinet — code d'invitation + approbation (منسّق = admin_cabinet)."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import log_audit, require_roles
from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import check_rate_limit
from app.core.security import hash_password
from app.models import (
    Cabinet,
    CabinetStatus,
    MembershipRequest,
    MembershipRequestStatus,
    User,
    UserRole,
)
from app.schemas import (
    JoinCodeResponse,
    JoinCodeValidateRequest,
    JoinCodeValidateResponse,
    JoinRequestCreate,
    MembershipApproveRequest,
    MembershipRequestResponse,
    MessageResponse,
    TeamMemberResponse,
    TeamUpdateRequest,
)
from app.services.join_code import assign_unique_join_code, normalize_join_code

router = APIRouter(prefix="/api/team", tags=["team"])

ROLE_MAP = {
    "avocat": UserRole.AVOCAT,
    "assistant_juridique": UserRole.ASSISTANT,
    "admin_cabinet": UserRole.ADMIN_CABINET,
}


def _member_response(user: User) -> TeamMemberResponse:
    return TeamMemberResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
    )


def _ensure_join_code(db: Session, cabinet: Cabinet) -> str:
    if cabinet.join_code:
        return cabinet.join_code
    return assign_unique_join_code(db, cabinet, cabinet.name)


@router.get("", response_model=list[TeamMemberResponse])
def list_team(
    user: User = Depends(require_roles(UserRole.ADMIN_CABINET)),
    db: Session = Depends(get_db),
):
    members = (
        db.query(User)
        .filter(User.cabinet_id == user.cabinet_id)
        .order_by(User.created_at.desc())
        .all()
    )
    return [_member_response(m) for m in members]


@router.get("/join-code", response_model=JoinCodeResponse)
def get_join_code(
    user: User = Depends(require_roles(UserRole.ADMIN_CABINET)),
    db: Session = Depends(get_db),
):
    cabinet = db.query(Cabinet).filter(Cabinet.id == user.cabinet_id).first()
    if not cabinet:
        raise HTTPException(status_code=404, detail="Cabinet introuvable")
    code = _ensure_join_code(db, cabinet)
    db.commit()
    return JoinCodeResponse(
        join_code=code,
        regenerated_at=cabinet.join_code_regenerated_at,
    )


@router.post("/join-code/regenerate", response_model=JoinCodeResponse)
def regenerate_join_code(
    request: Request,
    user: User = Depends(require_roles(UserRole.ADMIN_CABINET)),
    db: Session = Depends(get_db),
):
    cabinet = db.query(Cabinet).filter(Cabinet.id == user.cabinet_id).first()
    if not cabinet:
        raise HTTPException(status_code=404, detail="Cabinet introuvable")
    code = assign_unique_join_code(db, cabinet, cabinet.name)
    log_audit(db, "team.join_code_regenerate", user=user, request=request, details=code)
    db.commit()
    return JoinCodeResponse(
        join_code=code,
        regenerated_at=cabinet.join_code_regenerated_at,
    )


@router.post("/join/validate", response_model=JoinCodeValidateResponse)
def validate_join_code(
    data: JoinCodeValidateRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Ne révèle jamais le nom du cabinet (anti-énumération)."""
    check_rate_limit(
        request,
        key="team.join_validate",
        limit=settings.JOIN_VALIDATE_RATE_LIMIT,
        window_sec=60,
    )
    code = normalize_join_code(data.code)
    if len(code) < 6:
        return JoinCodeValidateResponse(valid=False)
    cab = (
        db.query(Cabinet.id)
        .filter(
            Cabinet.join_code == code,
            Cabinet.status == CabinetStatus.ACTIVE,
        )
        .first()
    )
    return JoinCodeValidateResponse(valid=cab is not None)


@router.post("/join/request", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def submit_join_request(
    data: JoinRequestCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    from app.services.hibp import is_password_breached

    check_rate_limit(
        request,
        key="team.join_request",
        limit=settings.JOIN_REQUEST_RATE_LIMIT,
        window_sec=60,
    )
    code = normalize_join_code(data.code)
    cabinet = (
        db.query(Cabinet)
        .filter(Cabinet.join_code == code, Cabinet.status == CabinetStatus.ACTIVE)
        .first()
    )
    # Réponse générique si code invalide
    if not cabinet:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="رمز غير صالح.",
        )

    email = data.email.lower().strip()
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="تعذر إتمام الطلب. تحقق من بياناتك أو اتصل بالمنسّق.",
        )

    pending = (
        db.query(MembershipRequest)
        .filter(
            MembershipRequest.email == email,
            MembershipRequest.status == MembershipRequestStatus.PENDING.value,
        )
        .first()
    )
    if pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="لديك بالفعل طلب قيد المراجعة.",
        )

    if await is_password_breached(data.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="كلمة المرور غير آمنة. اختر كلمة أخرى.",
        )

    req = MembershipRequest(
        cabinet_id=cabinet.id,
        full_name=data.full_name.strip(),
        email=email,
        hashed_password=hash_password(data.password),
        status=MembershipRequestStatus.PENDING,
    )
    db.add(req)
    log_audit(
        db,
        "team.join_request",
        user=None,
        request=request,
        details=f"{email} → cabinet {cabinet.id}",
    )
    db.commit()
    return MessageResponse(message="طلبك قيد المراجعة")


@router.get("/requests", response_model=list[MembershipRequestResponse])
def list_join_requests(
    user: User = Depends(require_roles(UserRole.ADMIN_CABINET)),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(MembershipRequest)
        .filter(
            MembershipRequest.cabinet_id == user.cabinet_id,
            MembershipRequest.status == MembershipRequestStatus.PENDING.value,
        )
        .order_by(MembershipRequest.requested_at.desc())
        .all()
    )
    return [
        MembershipRequestResponse(
            id=r.id,
            full_name=r.full_name,
            email=r.email,
            status=r.status.value,
            requested_at=r.requested_at,
            resolved_at=r.resolved_at,
        )
        for r in rows
    ]


@router.post("/requests/{request_id}/approve", response_model=TeamMemberResponse)
def approve_join_request(
    request_id: str,
    data: MembershipApproveRequest,
    request: Request,
    user: User = Depends(require_roles(UserRole.ADMIN_CABINET)),
    db: Session = Depends(get_db),
):
    req = (
        db.query(MembershipRequest)
        .filter(
            MembershipRequest.id == request_id,
            MembershipRequest.cabinet_id == user.cabinet_id,
            MembershipRequest.status == MembershipRequestStatus.PENDING.value,
        )
        .first()
    )
    if not req:
        raise HTTPException(status_code=404, detail="الطلب غير موجود")

    if db.query(User).filter(User.email == req.email).first():
        req.status = MembershipRequestStatus.REJECTED
        req.resolved_at = datetime.now(timezone.utc)
        req.resolved_by = user.id
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="هذا البريد مستخدم بالفعل.",
        )

    role = ROLE_MAP[data.role]
    new_user = User(
        email=req.email,
        hashed_password=req.hashed_password,
        full_name=req.full_name,
        role=role,
        is_active=True,
        is_verified=True,
        cabinet_id=user.cabinet_id,
    )
    db.add(new_user)
    req.status = MembershipRequestStatus.APPROVED
    req.resolved_at = datetime.now(timezone.utc)
    req.resolved_by = user.id
    log_audit(
        db,
        "team.join_approve",
        user=user,
        request=request,
        details=f"{req.email} → {data.role}",
    )
    db.commit()
    db.refresh(new_user)
    return _member_response(new_user)


@router.post("/requests/{request_id}/reject", response_model=MessageResponse)
def reject_join_request(
    request_id: str,
    request: Request,
    user: User = Depends(require_roles(UserRole.ADMIN_CABINET)),
    db: Session = Depends(get_db),
):
    req = (
        db.query(MembershipRequest)
        .filter(
            MembershipRequest.id == request_id,
            MembershipRequest.cabinet_id == user.cabinet_id,
            MembershipRequest.status == MembershipRequestStatus.PENDING.value,
        )
        .first()
    )
    if not req:
        raise HTTPException(status_code=404, detail="الطلب غير موجود")

    req.status = MembershipRequestStatus.REJECTED
    req.resolved_at = datetime.now(timezone.utc)
    req.resolved_by = user.id
    log_audit(
        db,
        "team.join_reject",
        user=user,
        request=request,
        details=req.email,
    )
    db.commit()
    return MessageResponse(message="تم رفض الطلب")


@router.patch("/{member_id}", response_model=TeamMemberResponse)
def update_member(
    member_id: str,
    data: TeamUpdateRequest,
    request: Request,
    user: User = Depends(require_roles(UserRole.ADMIN_CABINET)),
    db: Session = Depends(get_db),
):
    member = (
        db.query(User)
        .filter(User.id == member_id, User.cabinet_id == user.cabinet_id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")

    if member.id == user.id and data.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous ne pouvez pas suspendre votre propre compte.",
        )

    if data.role:
        member.role = ROLE_MAP[data.role]

    if data.is_active is not None:
        member.is_active = data.is_active

    log_audit(db, "team.update", user=user, request=request, details=member.email)
    db.commit()
    db.refresh(member)
    return _member_response(member)
