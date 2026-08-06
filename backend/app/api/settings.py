from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, log_audit, require_roles
from app.core.database import get_db
from app.core.security import hash_password, verify_password
from app.models import Cabinet, User, UserRole
from app.schemas import (
    CabinetSettingsResponse,
    CabinetSettingsUpdate,
    MessageResponse,
    PasswordChangeRequest,
)

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/cabinet", response_model=CabinetSettingsResponse)
def get_cabinet_settings(
    user: User = Depends(require_roles(UserRole.ADMIN_CABINET)),
    db: Session = Depends(get_db),
):
    cabinet = db.query(Cabinet).filter(Cabinet.id == user.cabinet_id).first()
    if not cabinet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cabinet introuvable")
    return CabinetSettingsResponse(
        id=cabinet.id,
        name=cabinet.name,
        city=cabinet.city,
        address=cabinet.address,
        barreau=cabinet.barreau,
        ice=cabinet.ice,
        status=cabinet.status.value,
    )


@router.patch("/cabinet", response_model=CabinetSettingsResponse)
def update_cabinet_settings(
    data: CabinetSettingsUpdate,
    request: Request,
    user: User = Depends(require_roles(UserRole.ADMIN_CABINET)),
    db: Session = Depends(get_db),
):
    cabinet = db.query(Cabinet).filter(Cabinet.id == user.cabinet_id).first()
    if not cabinet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cabinet introuvable")

    for field, value in data.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(cabinet, field, value)

    log_audit(db, "settings.cabinet_update", user=user, request=request)
    db.commit()
    db.refresh(cabinet)
    return CabinetSettingsResponse(
        id=cabinet.id,
        name=cabinet.name,
        city=cabinet.city,
        address=cabinet.address,
        barreau=cabinet.barreau,
        ice=cabinet.ice,
        status=cabinet.status.value,
    )


@router.post("/password/request-otp", response_model=MessageResponse)
def request_password_otp(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Envoie un code email avant changement de mot de passe (pas de 2FA téléphone)."""
    from app.core.rate_limit import check_rate_limit
    from app.services.email import send_otp_email
    from app.services.email_otp import PURPOSE_PASSWORD_CHANGE, create_otp

    check_rate_limit(request, key="settings.pwd_otp", limit=5, window_sec=60)
    code = create_otp(
        db, email=user.email, purpose=PURPOSE_PASSWORD_CHANGE, minutes=15, digits=True
    )
    db.commit()
    send_otp_email(user.email, code, "Changement de mot de passe")
    return MessageResponse(message="Un code a été envoyé à votre adresse email.")


@router.post("/password", response_model=MessageResponse)
def change_password(
    data: PasswordChangeRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.services.email_otp import PURPOSE_PASSWORD_CHANGE, consume_otp
    from app.services.auth_sessions import revoke_all_user_sessions

    if not consume_otp(
        db, email=user.email, purpose=PURPOSE_PASSWORD_CHANGE, code=data.email_otp
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code email invalide ou expiré.",
        )
    if data.current_password and not verify_password(
        data.current_password, user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mot de passe actuel incorrect.",
        )

    user.hashed_password = hash_password(data.new_password)
    revoke_all_user_sessions(db, user.id)
    log_audit(db, "settings.password_change", user=user, request=request)
    db.commit()

    return MessageResponse(message="Mot de passe modifié avec succès.")
