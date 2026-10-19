"""Équipe cabinet — invitations e-mail (admin cabinet) et acceptation par lien."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import log_audit, require_password_set, require_roles
from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import check_named_rate_limit, check_rate_limit
from app.core.security import hash_password
from app.models import (
    Cabinet,
    CabinetInvite,
    CabinetStatus,
    User,
    UserRole,
)
from app.schemas import (
    AcceptInviteRequest,
    CabinetInviteItem,
    InvitePreviewResponse,
    JoinCodeResponse,
    JoinCodeValidateRequest,
    JoinCodeValidateResponse,
    JoinRequestCreate,
    MessageResponse,
    TeamInviteEmailRequest,
    TeamMemberResponse,
    TeamUpdateRequest,
)
from app.services.join_code import (
    assign_unique_join_code,
    create_personal_invite,
    find_active_invite,
    is_join_code_accepting,
    join_code_status,
    normalize_join_code,
)

router = APIRouter(prefix="/api/team", tags=["team"])

ROLE_MAP = {
    "avocat": UserRole.AVOCAT,
    "assistant_juridique": UserRole.ASSISTANT,
    "admin_cabinet": UserRole.ADMIN_CABINET,
}


def _invite_email_status(db: Session, email: str, cabinet_id: str) -> str:
    """Statut visible admin : new | already_member_same | already_on_lexhub."""
    u = db.query(User).filter(User.email == (email or "").lower().strip()).first()
    if not u:
        return "new"
    if u.cabinet_id == cabinet_id:
        return "already_member_same"
    return "already_on_lexhub"


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
    """Garantit un code actif — régénère auto si expiré ou épuisé."""
    if cabinet.join_code:
        st = join_code_status(cabinet)
        if st["is_active"]:
            return cabinet.join_code
        return assign_unique_join_code(db, cabinet, cabinet.name)
    return assign_unique_join_code(db, cabinet, cabinet.name)


def _join_code_response(cabinet: Cabinet) -> JoinCodeResponse:
    st = join_code_status(cabinet)
    return JoinCodeResponse(
        join_code=st["join_code"] or "",
        regenerated_at=st["regenerated_at"],
        expires_at=st["expires_at"],
        approved_count=st["approved_count"],
        max_approvals=st["max_approvals"],
        remaining_approvals=st["remaining_approvals"],
        is_expired=st["is_expired"],
        is_exhausted=st["is_exhausted"],
        is_active=st["is_active"],
    )


def _rate_limit_join_attempt(request: Request, code: str) -> None:
    check_rate_limit(
        request,
        key="team.join_attempt_ip",
        limit=settings.JOIN_VALIDATE_RATE_LIMIT,
        window_sec=60,
    )
    if code:
        check_named_rate_limit(
            name=f"team.join_code:{code}",
            limit=settings.JOIN_CODE_ATTEMPT_RATE_LIMIT,
            window_sec=settings.JOIN_CODE_ATTEMPT_WINDOW_SEC,
        )
        check_rate_limit(
            request,
            key="team.join_attempt_code",
            limit=settings.JOIN_CODE_ATTEMPT_RATE_LIMIT,
            window_sec=settings.JOIN_CODE_ATTEMPT_WINDOW_SEC,
            subject=code,
        )


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


@router.get("/assistants", response_model=list[TeamMemberResponse])
def list_assistants(
    user: User = Depends(require_roles(UserRole.AVOCAT, UserRole.ADMIN_CABINET)),
    db: Session = Depends(get_db),
):
    """Liste des assistants du cabinet (pour assignation plaidoirie)."""
    members = (
        db.query(User)
        .filter(
            User.cabinet_id == user.cabinet_id,
            User.role == UserRole.ASSISTANT,
            User.is_active.is_(True),
        )
        .order_by(User.full_name.asc())
        .all()
    )
    return [_member_response(m) for m in members]


@router.get("/join-code", response_model=JoinCodeResponse)
def get_join_code(
    user: User = Depends(require_roles(UserRole.ADMIN_CABINET)),
    db: Session = Depends(get_db),
):
    """Ancien code cabinet partagé — remplacé par l'invitation e-mail."""
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="JOIN_CODE_DISABLED",
    )


@router.post("/join-code/regenerate", response_model=JoinCodeResponse)
def regenerate_join_code(
    request: Request,
    user: User = Depends(require_roles(UserRole.ADMIN_CABINET)),
    db: Session = Depends(get_db),
):
    """Ancien code cabinet partagé — remplacé par l'invitation e-mail."""
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="JOIN_CODE_DISABLED",
    )


@router.post("/invite-email", response_model=MessageResponse)
def send_team_invite_email(
    data: TeamInviteEmailRequest,
    request: Request,
    user: User = Depends(require_roles(UserRole.ADMIN_CABINET)),
    _pwd: User = Depends(require_password_set),
    db: Session = Depends(get_db),
):
    """Crée un code one-time pour l’email et l’envoie (invitation personnelle)."""
    check_named_rate_limit(name=f"invite_email:{user.id}", limit=12, window_sec=3600)
    cabinet = db.query(Cabinet).filter(Cabinet.id == user.cabinet_id).first()
    if not cabinet:
        raise HTTPException(status_code=404, detail="Cabinet introuvable")
    email = str(data.email).strip().lower()
    role = (data.role or "avocat").strip()
    if role not in ROLE_MAP:
        role = "avocat"
    from app.services.billing import assert_can_invite

    assert_can_invite(db, user.cabinet_id, role)
    try:
        from app.services.retention_lifecycle import maybe_send_seats_warning

        maybe_send_seats_warning(db, user.cabinet_id, role)
    except Exception:
        pass

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        if existing.cabinet_id == user.cabinet_id:
            raise HTTPException(
                status_code=400,
                detail="EMAIL_EXISTS_SAME_CABINET",
            )
        # Autre cabinet : on envoie quand même le lien pour informer, mais l'accept échouera.
        # L'admin voit le statut dans la liste des invitations.
        pass

    invite = create_personal_invite(
        db,
        cabinet,
        email=email,
        created_by=user.id,
        role=role,
        recipient_name=data.recipient_name,
    )
    from app.services.email import send_join_invite_email

    ok = send_join_invite_email(
        email,
        cabinet_name=cabinet.name,
        join_code=invite.code,
        inviter_name=user.full_name,
        recipient_name=data.recipient_name,
        role=role,
    )
    if not ok:
        raise HTTPException(status_code=502, detail="Envoi email impossible (config email)")
    log_audit(
        db,
        "team.invite_email",
        user=user,
        request=request,
        details=f"{email} code={invite.code}",
    )
    db.commit()
    if existing and existing.cabinet_id != user.cabinet_id:
        return MessageResponse(
            message=(
                f"Invitation envoyée à {email} — attention : cet email a déjà un compte LexHub "
                "dans un autre cabinet. La personne ne pourra pas créer un second compte ; "
                "un transfert manuel (support) sera nécessaire."
            )
        )
    return MessageResponse(message=f"Invitation envoyée à {email}")


@router.get("/invites", response_model=list[CabinetInviteItem])
def list_pending_invites(
    user: User = Depends(require_roles(UserRole.ADMIN_CABINET)),
    db: Session = Depends(get_db),
):
    """Invitations personnelles en attente (non consommées, non expirées)."""
    now = datetime.now(timezone.utc)
    rows = (
        db.query(CabinetInvite)
        .filter(
            CabinetInvite.cabinet_id == user.cabinet_id,
            CabinetInvite.consumed_at.is_(None),
            CabinetInvite.expires_at > now,
        )
        .order_by(CabinetInvite.created_at.desc())
        .all()
    )
    return [
        CabinetInviteItem(
            id=r.id,
            email=r.email,
            code=r.code,
            role=getattr(r, "role", None) or "avocat",
            expires_at=r.expires_at,
            created_at=r.created_at,
            email_status=_invite_email_status(db, r.email, user.cabinet_id),
        )
        for r in rows
    ]


@router.post("/join/validate", response_model=JoinCodeValidateResponse)
def validate_join_code(
    data: JoinCodeValidateRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Ne révèle jamais le nom du cabinet (anti-énumération)."""
    code = normalize_join_code(data.code)
    _rate_limit_join_attempt(request, code)
    if len(code) < 8:
        return JoinCodeValidateResponse(valid=False)

    invite = find_active_invite(db, code)
    if invite:
        cab = (
            db.query(Cabinet)
            .filter(Cabinet.id == invite.cabinet_id, Cabinet.status == CabinetStatus.ACTIVE)
            .first()
        )
        if cab:
            return JoinCodeValidateResponse(valid=True)
        return JoinCodeValidateResponse(valid=False)

    cab = (
        db.query(Cabinet)
        .filter(
            Cabinet.join_code == code,
            Cabinet.status == CabinetStatus.ACTIVE,
        )
        .first()
    )
    # Code cabinet général désactivé — invitations admin uniquement
    if cab and is_join_code_accepting(cab):
        return JoinCodeValidateResponse(valid=False)
    return JoinCodeValidateResponse(valid=False)


@router.get("/join/invite-preview", response_model=InvitePreviewResponse)
def invite_preview(
    code: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """Aperçu invitation personnelle (lien email admin)."""
    normalized = normalize_join_code(code)
    _rate_limit_join_attempt(request, normalized)
    invite = find_active_invite(db, normalized)
    if not invite:
        return InvitePreviewResponse(
            valid=False,
            email="",
            cabinet_name="",
        )
    cab = (
        db.query(Cabinet)
        .filter(Cabinet.id == invite.cabinet_id, Cabinet.status == CabinetStatus.ACTIVE)
        .first()
    )
    if not cab:
        return InvitePreviewResponse(valid=False, email="", cabinet_name="")
    existing = db.query(User).filter(User.email == invite.email.lower().strip()).first()
    return InvitePreviewResponse(
        valid=True,
        email=invite.email,
        cabinet_name=cab.name,
        recipient_name=getattr(invite, "recipient_name", None),
        role=getattr(invite, "role", None) or "avocat",
        email_already_registered=bool(existing),
        email_same_cabinet=bool(existing and existing.cabinet_id == cab.id),
    )


@router.post("/join/accept-invite", response_model=MessageResponse)
async def accept_invite(
    data: AcceptInviteRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Accepte une invitation admin — compte actif immédiatement (sans approbation)."""
    from app.services.email import send_join_approved_email
    from app.services.hibp import is_password_breached

    code = normalize_join_code(data.code)
    _rate_limit_join_attempt(request, code)
    check_rate_limit(
        request,
        key="team.accept_invite",
        limit=settings.JOIN_REQUEST_RATE_LIMIT,
        window_sec=60,
    )

    invite = find_active_invite(db, code)
    if not invite:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="INVITE_INVALID",
        )

    cabinet = (
        db.query(Cabinet)
        .filter(Cabinet.id == invite.cabinet_id, Cabinet.status == CabinetStatus.ACTIVE)
        .first()
    )
    if not cabinet:
        raise HTTPException(status_code=400, detail="INVITE_INVALID")

    email = invite.email.lower().strip()
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        if existing.cabinet_id == cabinet.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="EMAIL_EXISTS_SAME_CABINET",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="EMAIL_EXISTS_OTHER_CABINET",
        )

    if await is_password_breached(data.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mot de passe compromis (Have I Been Pwned). Choisissez-en un autre.",
        )

    role_key = getattr(invite, "role", None) or "avocat"
    if role_key == "admin_cabinet":
        # Évite l'escalade de privilèges via invitation
        role_key = "avocat"
    from app.services.billing import assert_can_invite

    assert_can_invite(db, cabinet.id, role_key)
    role = ROLE_MAP.get(role_key, UserRole.AVOCAT)
    full_name = data.full_name.strip() or (getattr(invite, "recipient_name", None) or email)

    new_user = User(
        email=email,
        hashed_password=hash_password(data.password),
        full_name=full_name,
        role=role,
        is_active=True,
        is_verified=True,
        cabinet_id=cabinet.id,
    )
    db.add(new_user)
    invite.consumed_at = datetime.now(timezone.utc)

    log_audit(
        db,
        "team.invite_accept",
        user=None,
        request=request,
        details=f"{email} → cabinet {cabinet.id} role={role.value}",
    )
    db.commit()

    try:
        send_join_approved_email(
            email,
            cabinet_name=cabinet.name,
            applicant_name=full_name,
        )
    except Exception:
        pass

    try:
        from app.services.email import send_invite_accepted_admin_email

        admin = (
            db.query(User)
            .filter(
                User.cabinet_id == cabinet.id,
                User.role == UserRole.ADMIN_CABINET,
                User.is_active.is_(True),
            )
            .order_by(User.created_at.asc())
            .first()
        )
        if admin:
            role_labels = {
                "avocat": "Avocat",
                "assistant": "Assistant",
                "admin_cabinet": "Admin cabinet",
            }
            send_invite_accepted_admin_email(
                admin.email,
                admin_name=admin.full_name,
                member_name=full_name,
                member_email=email,
                cabinet_name=cabinet.name,
                role_label=role_labels.get(role_key, role_key),
            )
    except Exception:
        pass

    return MessageResponse(message="Compte créé — vous pouvez vous connecter.")


@router.post("/join/request", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def submit_join_request(
    data: JoinRequestCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Désactivé — utiliser le lien d'invitation reçu par email (admin cabinet)."""
    code = normalize_join_code(data.code)
    _rate_limit_join_attempt(request, code)

    invite = find_active_invite(db, code)
    if invite:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="INVITE_USE_LINK",
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="JOIN_ADMIN_ONLY",
    )


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
