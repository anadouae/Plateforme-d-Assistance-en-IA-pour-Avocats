"""Settings cabinet — branding (logo, name_ar) + profil avocat."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, log_audit, require_roles
from app.core.database import get_db
from app.models import Cabinet, User, UserRole
from app.schemas import (
    AccountDeleteRequest,
    CabinetSettingsResponse,
    CabinetSettingsUpdate,
    EmailChangeConfirm,
    EmailChangeRequestOtp,
    MessageResponse,
    PasswordChangeRequest,
    ProfileNameUpdate,
    UserResponse,
)
from app.services.object_storage import read_file, save_file

router = APIRouter(prefix="/api/settings", tags=["settings"])

_ALLOWED_LOGO = {".png", ".jpg", ".jpeg", ".webp"}
_MAX_LOGO = 1_500_000  # ~1.5 Mo


def _cabinet_payload(cabinet: Cabinet) -> CabinetSettingsResponse:
    return CabinetSettingsResponse(
        id=cabinet.id,
        name=cabinet.name,
        name_ar=getattr(cabinet, "name_ar", None),
        city=cabinet.city,
        address=cabinet.address,
        barreau=cabinet.barreau,
        ice=cabinet.ice,
        status=cabinet.status.value,
        has_logo=bool(getattr(cabinet, "logo_path", None)),
    )


@router.get("/cabinet", response_model=CabinetSettingsResponse)
def get_cabinet_settings(
    user: User = Depends(require_roles(UserRole.ADMIN_CABINET)),
    db: Session = Depends(get_db),
):
    cabinet = db.query(Cabinet).filter(Cabinet.id == user.cabinet_id).first()
    if not cabinet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cabinet introuvable")
    return _cabinet_payload(cabinet)


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
    return _cabinet_payload(cabinet)


@router.post("/cabinet/logo", response_model=CabinetSettingsResponse)
async def upload_cabinet_logo(
    request: Request,
    file: UploadFile = File(...),
    user: User = Depends(require_roles(UserRole.ADMIN_CABINET)),
    db: Session = Depends(get_db),
):
    from app.core.rate_limit import check_rate_limit

    check_rate_limit(
        request,
        key=f"settings.cabinet_logo:{user.id}",
        limit=10,
        window_sec=60,
    )
    cabinet = db.query(Cabinet).filter(Cabinet.id == user.cabinet_id).first()
    if not cabinet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cabinet introuvable")

    name = (file.filename or "logo.png").lower()
    ext = "." + name.rsplit(".", 1)[-1] if "." in name else ".png"
    if ext not in _ALLOWED_LOGO:
        raise HTTPException(
            status_code=400,
            detail="Formats acceptés : PNG, JPG, WEBP",
        )
    raw = await file.read()
    if not raw or len(raw) > _MAX_LOGO:
        raise HTTPException(status_code=400, detail="Logo trop volumineux (max 1,5 Mo)")
    from app.services.file_sniff import sniff_allowed_upload

    sniff_err = sniff_allowed_upload(raw, ext)
    if sniff_err:
        raise HTTPException(status_code=400, detail=sniff_err)

    path = save_file(raw, user.cabinet_id, "_branding", ext)
    cabinet.logo_path = path
    log_audit(db, "settings.cabinet_logo", user=user, request=request)
    db.commit()
    db.refresh(cabinet)
    return _cabinet_payload(cabinet)


@router.get("/cabinet/logo")
def get_cabinet_logo(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Logo cabinet — accessible à tous les membres du cabinet (exports)."""
    cabinet = db.query(Cabinet).filter(Cabinet.id == user.cabinet_id).first()
    if not cabinet or not getattr(cabinet, "logo_path", None):
        raise HTTPException(status_code=404, detail="Aucun logo")
    try:
        data = read_file(cabinet.logo_path)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Logo introuvable") from exc
    media = "image/png"
    if cabinet.logo_path.endswith(".jpg") or cabinet.logo_path.endswith(".jpeg"):
        media = "image/jpeg"
    elif cabinet.logo_path.endswith(".webp"):
        media = "image/webp"
    return Response(content=data, media_type=media, headers={"Cache-Control": "private, max-age=300"})


@router.delete("/cabinet/logo", response_model=MessageResponse)
def delete_cabinet_logo(
    request: Request,
    user: User = Depends(require_roles(UserRole.ADMIN_CABINET)),
    db: Session = Depends(get_db),
):
    cabinet = db.query(Cabinet).filter(Cabinet.id == user.cabinet_id).first()
    if not cabinet:
        raise HTTPException(status_code=404, detail="Cabinet introuvable")
    cabinet.logo_path = None
    log_audit(db, "settings.cabinet_logo_delete", user=user, request=request)
    db.commit()
    return MessageResponse(message="Logo retiré.")


@router.patch("/profile", response_model=UserResponse)
def update_profile_names(
    data: ProfileNameUpdate,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.api.auth import _user_response

    if data.full_name is not None:
        user.full_name = data.full_name.strip()
    if data.full_name_ar is not None:
        user.full_name_ar = data.full_name_ar.strip() or None
    if data.phone is not None:
        user.phone = data.phone.strip() or None
    cabinet = db.query(Cabinet).filter(Cabinet.id == user.cabinet_id).first()
    log_audit(db, "settings.profile_names", user=user, request=request)
    db.commit()
    db.refresh(user)
    return _user_response(user, cabinet)


@router.post("/email/request-otp", response_model=MessageResponse)
def request_email_change_otp(
    data: EmailChangeRequestOtp,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Envoie un code à la NOUVELLE adresse avant de changer l'email du compte."""
    from app.core.rate_limit import check_rate_limit
    from app.services.email import send_otp_email
    from app.services.email_otp import PURPOSE_EMAIL_CHANGE, create_otp

    check_rate_limit(request, key="settings.email_otp", limit=5, window_sec=120)
    new_email = str(data.new_email).strip().lower()
    if new_email == (user.email or "").strip().lower():
        raise HTTPException(status_code=400, detail="C'est déjà votre adresse email.")
    taken = db.query(User).filter(User.email == new_email, User.id != user.id).first()
    if taken:
        raise HTTPException(status_code=400, detail="Cette adresse email est déjà utilisée.")
    code = create_otp(db, email=new_email, purpose=PURPOSE_EMAIL_CHANGE, minutes=15, digits=True)
    db.commit()
    if not send_otp_email(new_email, code, "Changement d'adresse email"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service d'email indisponible. Réessayez plus tard.",
        )
    return MessageResponse(message="Un code a été envoyé à la nouvelle adresse email.")


@router.post("/email/confirm", response_model=UserResponse)
def confirm_email_change(
    data: EmailChangeConfirm,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.api.auth import _user_response
    from app.core.security import verify_password
    from app.services.email import send_email_changed_notice
    from app.services.email_otp import PURPOSE_EMAIL_CHANGE, consume_otp

    new_email = str(data.new_email).strip().lower()
    if new_email == (user.email or "").strip().lower():
        raise HTTPException(status_code=400, detail="C'est déjà votre adresse email.")
    if not verify_password(data.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect.")
    if not consume_otp(db, email=new_email, purpose=PURPOSE_EMAIL_CHANGE, code=data.email_otp):
        raise HTTPException(status_code=400, detail="Code email invalide ou expiré.")
    taken = db.query(User).filter(User.email == new_email, User.id != user.id).first()
    if taken:
        raise HTTPException(status_code=400, detail="Cette adresse email est déjà utilisée.")

    old_email = user.email
    user.email = new_email
    cabinet = db.query(Cabinet).filter(Cabinet.id == user.cabinet_id).first()
    log_audit(db, "settings.email_change", user=user, request=request, details=old_email)
    db.commit()
    db.refresh(user)
    try:
        send_email_changed_notice(
            old_email=old_email,
            new_email=new_email,
            full_name=user.full_name or new_email,
        )
    except Exception:
        pass
    return _user_response(user, cabinet)


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
    if not send_otp_email(user.email, code, "Changement de mot de passe"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service d'email indisponible. Réessayez plus tard.",
        )
    return MessageResponse(message="Un code a été envoyé à votre adresse email.")


@router.post("/password", response_model=MessageResponse)
def change_password(
    data: PasswordChangeRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.core.security import hash_password, verify_password
    from app.services.auth_sessions import revoke_all_user_sessions
    from app.services.email_otp import PURPOSE_PASSWORD_CHANGE, consume_otp

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
    try:
        from app.services.email import send_password_changed_email

        send_password_changed_email(user.email, full_name=user.full_name or user.email)
    except Exception:
        pass

    return MessageResponse(message="Mot de passe modifié avec succès.")


@router.post("/account/delete-otp", response_model=MessageResponse)
def request_account_delete_otp(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Envoie un code email avant suppression définitive du compte."""
    from app.core.rate_limit import check_rate_limit
    from app.services.email import send_otp_email
    from app.services.email_otp import PURPOSE_ACCOUNT_DELETE, create_otp

    if user.role == UserRole.ADMIN_WEBVOICE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Les comptes administrateur plateforme ne peuvent pas être auto-supprimés. Contactez contact@lexhub.space.",
        )
    check_rate_limit(request, key="settings.account_delete_otp", limit=3, window_sec=120)
    code = create_otp(
        db, email=user.email, purpose=PURPOSE_ACCOUNT_DELETE, minutes=15, digits=True
    )
    db.commit()
    if not send_otp_email(user.email, code, "Suppression de compte LexHub"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service d'email indisponible. Réessayez plus tard.",
        )
    return MessageResponse(message="Un code de confirmation a été envoyé à votre adresse email.")


@router.post("/account/delete", response_model=MessageResponse)
def delete_account(
    data: AccountDeleteRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Suppression de compte type grandes apps :
    - mot de passe + OTP email + phrase SUPPRIMER
    - anonymisation (soft-delete) pour préserver l'intégrité des dossiers / audit
    - révocation de toutes les sessions
    """
    import secrets
    import uuid as uuid_mod

    from app.core.security import hash_password, verify_password
    from app.models import AuthSession, MfaRecoveryCode, PlaidoirieDraft
    from app.services.auth_sessions import revoke_all_user_sessions
    from app.services.email import send_account_deleted_email
    from app.services.email_otp import PURPOSE_ACCOUNT_DELETE, consume_otp

    if user.role == UserRole.ADMIN_WEBVOICE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Les comptes administrateur plateforme ne peuvent pas être auto-supprimés.",
        )

    conf = (data.confirmation or "").strip().upper()
    if conf not in {"SUPPRIMER", "DELETE", "حذف"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Saisissez SUPPRIMER pour confirmer (ou DELETE / حذف).',
        )

    # Compte OTP / Google sans mot de passe : OTP + phrase suffisent
    if user.hashed_password:
        if not (data.password or "").strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mot de passe requis.",
            )
        if not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mot de passe incorrect.",
            )

    if not consume_otp(
        db, email=user.email, purpose=PURPOSE_ACCOUNT_DELETE, code=data.email_otp
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code email invalide ou expiré.",
        )

    cabinet_closed = False
    cabinet_id = user.cabinet_id

    # Admin cabinet seul → fermeture du cabinet (droit du responsable)
    if user.role == UserRole.ADMIN_CABINET:
        other_admins = (
            db.query(User)
            .filter(
                User.cabinet_id == user.cabinet_id,
                User.role == UserRole.ADMIN_CABINET,
                User.is_active.is_(True),
                User.id != user.id,
            )
            .count()
        )
        if other_admins == 0:
            from app.models import Cabinet, CabinetStatus

            cabinet = db.query(Cabinet).filter(Cabinet.id == user.cabinet_id).first()
            if cabinet:
                cabinet.status = CabinetStatus.SUSPENDED
                cabinet.join_code = None
            members = (
                db.query(User)
                .filter(User.cabinet_id == user.cabinet_id, User.is_active.is_(True))
                .all()
            )
            for member in members:
                if member.id == user.id:
                    continue
                member.is_active = False
                revoke_all_user_sessions(db, member.id)
                db.query(AuthSession).filter(AuthSession.user_id == member.id).delete(
                    synchronize_session=False
                )
            cabinet_closed = True
            log_audit(
                db,
                "cabinet.self_close",
                user=user,
                request=request,
                details=cabinet.name if cabinet else cabinet_id,
            )

    original_email = user.email
    original_name = user.full_name or user.email
    uid = user.id

    # Détacher assignations plaidoirie
    db.query(PlaidoirieDraft).filter(PlaidoirieDraft.assigned_to_user_id == uid).update(
        {"assigned_to_user_id": None}, synchronize_session=False
    )

    # Anonymiser (soft-delete) — conserve les FK dossiers / audit
    tombstone = f"deleted+{uid[:8]}-{uuid_mod.uuid4().hex[:8]}@deleted.lexhub.invalid"
    user.email = tombstone
    user.full_name = "Compte supprimé"
    user.full_name_ar = None
    user.phone = None
    user.hashed_password = hash_password(secrets.token_urlsafe(48))
    user.is_active = False
    user.is_verified = False
    user.totp_secret = None
    user.totp_enabled = False
    user.google_id = None
    user.failed_login_attempts = 0
    user.locked_until = None

    db.query(MfaRecoveryCode).filter(MfaRecoveryCode.user_id == uid).delete(
        synchronize_session=False
    )
    revoke_all_user_sessions(db, uid)
    # Nettoyage sessions orphelines éventuelles
    db.query(AuthSession).filter(AuthSession.user_id == uid).delete(synchronize_session=False)

    log_audit(
        db,
        "settings.account_delete",
        user=user,
        request=request,
        details=f"anonymized former={original_email[:3]}***",
    )
    db.commit()

    background_tasks.add_task(
        send_account_deleted_email, original_email, full_name=original_name
    )
    if cabinet_closed:
        return MessageResponse(
            message=(
                "Cabinet fermé et compte supprimé. "
                "Tous les accès du cabinet ont été désactivés."
            )
        )
    return MessageResponse(
        message="Compte supprimé. Vos sessions ont été fermées et vos données personnelles anonymisées."
    )

