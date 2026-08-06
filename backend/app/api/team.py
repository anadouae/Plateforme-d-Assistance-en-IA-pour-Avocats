import secrets
import string

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, log_audit, require_roles
from app.core.config import settings
from app.core.database import get_db
from app.core.security import hash_password
from app.models import TokenType, User, UserRole
from app.services.email import send_team_invite_email
from app.services.tokens import create_token, invite_hours
from app.schemas import MessageResponse, TeamInviteRequest, TeamInviteResponse, TeamMemberResponse, TeamUpdateRequest

router = APIRouter(prefix="/api/team", tags=["team"])


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


@router.post("/invite", response_model=TeamInviteResponse, status_code=status.HTTP_201_CREATED)
def invite_member(
    data: TeamInviteRequest,
    request: Request,
    user: User = Depends(require_roles(UserRole.ADMIN_CABINET)),
    db: Session = Depends(get_db),
):
    email = data.email.lower().strip()
    existing = db.query(User).filter(User.email == email).first()

    role_map = {
        "avocat": UserRole.AVOCAT,
        "assistant_juridique": UserRole.ASSISTANT,
        "admin_cabinet": UserRole.ADMIN_CABINET,
    }

    if existing:
        if existing.cabinet_id != user.cabinet_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cet email est déjà utilisé par un autre cabinet.",
            )
        if existing.is_active and existing.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ce collaborateur est déjà actif. Utilisez « Réactiver » si besoin.",
            )
        existing.full_name = data.full_name
        existing.role = role_map[data.role]
        existing.is_active = False
        existing.is_verified = False
        new_user = existing
        db.flush()
        raw_token = create_token(db, new_user, TokenType.RESET_PASSWORD, invite_hours())
    else:
        temp_password = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))
        new_user = User(
            email=email,
            hashed_password=hash_password(temp_password),
            full_name=data.full_name,
            role=role_map[data.role],
            is_active=False,
            is_verified=False,
            cabinet_id=user.cabinet_id,
        )
        db.add(new_user)
        db.flush()
        raw_token = create_token(db, new_user, TokenType.RESET_PASSWORD, invite_hours())

    cabinet = user.cabinet
    log_audit(db, "team.invite", user=user, request=request, details=email)
    db.commit()

    email_sent = send_team_invite_email(
        email,
        raw_token,
        cabinet.name if cabinet else "Sanad",
        user.full_name,
    )

    invite_url = f"{settings.FRONTEND_URL.rstrip('/')}/activate?token={raw_token}"
    is_dev_mail = settings.SMTP_HOST in ("mailhog", "localhost") or settings.SMTP_PORT == 1025
    dev_mail = "http://localhost:8025" if is_dev_mail else None

    if email_sent:
        msg = f"Invitation envoyée à {email}."
    else:
        msg = f"Invitation créée pour {email}. L'email n'a pas pu être envoyé — partagez le lien manuellement."

    return TeamInviteResponse(
        message=msg,
        invite_url=invite_url,
        email=email,
        email_sent=email_sent,
        dev_mail_url=dev_mail,
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
        role_map = {
            "avocat": UserRole.AVOCAT,
            "assistant_juridique": UserRole.ASSISTANT,
            "admin_cabinet": UserRole.ADMIN_CABINET,
        }
        member.role = role_map[data.role]

    if data.is_active is not None:
        member.is_active = data.is_active

    log_audit(db, "team.update", user=user, request=request, details=member.email)
    db.commit()
    db.refresh(member)
    return _member_response(member)
