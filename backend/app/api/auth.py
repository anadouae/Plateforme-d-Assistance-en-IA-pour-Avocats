from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, log_audit
from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models import Cabinet, CabinetStatus, TokenType, User, UserRole
from app.schemas import (
    EmailOnlyRequest,
    EmailOtpVerifyRequest,
    ForgotPasswordRequest,
    GoogleAuthRequest,
    LoginRequest,
    MessageResponse,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    TwoFactorEnableRequest,
    TwoFactorEnableResponse,
    TwoFactorSetupResponse,
    UserResponse,
)
from app.services.auth_sessions import (
    create_session,
    get_valid_session,
    hash_refresh_token,
    revoke_all_user_sessions,
    revoke_session,
    rotate_session,
)
from app.services.email import (
    send_lockout_email,
    send_otp_email,
    send_password_reset_email,
)
from app.services.email_otp import (
    PURPOSE_REGISTER,
    consume_otp,
    create_otp,
    otp_is_valid,
)
from app.services.recovery_codes import consume_recovery_code, generate_recovery_codes
from app.services.tokens import (
    consume_token,
    create_token,
    reset_password_hours,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _mfa_required_for(user: User) -> bool:
    # MFA obligatoire pour l admin plateforme LexHub
    return user.role == UserRole.ADMIN_WEBVOICE


_CABINET_PLACEHOLDER = "À compléter"


def _cabinet_profile_complete(cabinet: Cabinet | None) -> bool:
    """True si le cabinet a renseigné ses infos métier (hors inscription minimale)."""
    if not cabinet:
        return True
    marker = _CABINET_PLACEHOLDER.casefold()
    for raw in (cabinet.city, cabinet.address, cabinet.barreau):
        value = (raw or "").strip().casefold()
        if not value or value == marker:
            return False
    name = (cabinet.name or "").strip()
    if len(name) < 2 or name.casefold().startswith("cabinet temporaire"):
        return False
    return True


def _user_response(user: User, cabinet: Cabinet | None) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        full_name_ar=getattr(user, "full_name_ar", None),
        phone=getattr(user, "phone", None),
        role=user.role.value,
        cabinet_id=user.cabinet_id,
        cabinet_name=cabinet.name if cabinet else "",
        cabinet_name_ar=getattr(cabinet, "name_ar", None) if cabinet else None,
        cabinet_city=cabinet.city if cabinet else None,
        cabinet_barreau=cabinet.barreau if cabinet else None,
        cabinet_address=cabinet.address if cabinet else None,
        cabinet_has_logo=bool(getattr(cabinet, "logo_path", None)) if cabinet else False,
        cabinet_profile_complete=_cabinet_profile_complete(cabinet),
        totp_enabled=bool(user.totp_enabled),
        mfa_required=_mfa_required_for(user),
        has_seen_onboarding_tour=bool(getattr(user, "has_seen_onboarding_tour", False)),
    )


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    secure = settings.COOKIE_SECURE or settings.ENVIRONMENT == "production"
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/api/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        path="/api/auth",
    )
    if settings.REFRESH_COOKIE_NAME != "sanad_refresh":
        response.delete_cookie(
            key="sanad_refresh",
            path="/api/auth",
        )


def _issue_tokens(
    db: Session,
    user: User,
    cabinet: Cabinet | None,
    request: Request,
    response: Response,
    *,
    mfa_setup_required: bool = False,
) -> TokenResponse:
    # Placeholder refresh then bind session id into both tokens
    provisional = create_refresh_token({"sub": user.id})
    ua = request.headers.get("user-agent")
    ip = request.client.host if request.client else None
    session = create_session(
        db,
        user_id=user.id,
        refresh_token=provisional,
        ip=ip,
        user_agent=ua,
    )
    access = create_access_token({"sub": user.id}, session_id=session.id)
    refresh = create_refresh_token({"sub": user.id}, session_id=session.id)
    # Re-hash with final refresh (includes sid)
    session.refresh_token_hash = hash_refresh_token(refresh)
    db.flush()
    _set_refresh_cookie(response, refresh)
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        user=_user_response(user, cabinet),
        mfa_setup_required=mfa_setup_required,
    )


def _verify_mfa(db: Session, user: User, totp_code: str | None, recovery_code: str | None) -> None:
    if not user.totp_enabled:
        return
    if recovery_code:
        if consume_recovery_code(db, user.id, recovery_code):
            return
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Code de récupération invalide.",
        )
    if not totp_code:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="2FA_REQUIRED",
        )
    from app.services.totp import verify_totp

    if not verify_totp(user.totp_secret or "", totp_code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Code 2FA invalide.",
        )


@router.get("/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cabinet = db.query(Cabinet).filter(Cabinet.id == user.cabinet_id).first()
    return _user_response(user, cabinet)


@router.post("/onboarding-tour/complete", response_model=UserResponse)
def complete_onboarding_tour(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Marque le tour guidé comme vu (terminé ou passé)."""
    if not getattr(user, "has_seen_onboarding_tour", False):
        user.has_seen_onboarding_tour = True
        db.add(user)
        db.commit()
        db.refresh(user)
    cabinet = db.query(Cabinet).filter(Cabinet.id == user.cabinet_id).first()
    return _user_response(user, cabinet)


@router.get("/captcha-config")
def captcha_config():
    return {
        "enabled": bool(settings.TURNSTILE_SECRET_KEY and settings.TURNSTILE_SITE_KEY),
        "site_key": settings.TURNSTILE_SITE_KEY or "",
        "after_failures": settings.CAPTCHA_AFTER_FAILURES,
    }


@router.post("/request-register-otp", response_model=MessageResponse)
def request_register_otp(
    data: EmailOnlyRequest, request: Request, db: Session = Depends(get_db)
):
    """Étape 1 inscription : envoie un code à 6 chiffres pour prouver l'email."""
    from app.core.rate_limit import check_rate_limit

    check_rate_limit(request, key="auth.register_otp", limit=15, window_sec=60)
    existing = db.query(User).filter(User.email == data.email.lower()).first()
    if existing:
        # Même message (anti-énumération)
        return MessageResponse(
            message="Si cet email est disponible, un code de vérification a été envoyé."
        )
    code = create_otp(db, email=data.email, purpose=PURPOSE_REGISTER, minutes=15, digits=True)
    db.commit()
    if not send_otp_email(data.email, code, "Vérification de votre email"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service d'email indisponible. Réessayez plus tard.",
        )
    return MessageResponse(
        message="Si cet email est disponible, un code de vérification a été envoyé."
    )


@router.post("/verify-register-otp", response_model=MessageResponse)
def verify_register_otp(
    data: EmailOtpVerifyRequest, request: Request, db: Session = Depends(get_db)
):
    """Vérifie le code sans le consommer — consommation au moment du register."""
    from app.core.rate_limit import check_rate_limit
    from app.services.email_otp import otp_is_valid

    check_rate_limit(request, key="auth.verify_register_otp", limit=10, window_sec=60)
    from app.core.rate_limit import check_named_rate_limit, count_failures, record_failure

    email_key = (data.email or "").strip().lower()
    # Max 5 échecs / 15 min par e-mail (anti brute-force OTP)
    fails = count_failures(request, key=f"otp_fail:{email_key}", window_sec=900)
    if fails >= 5:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Trop de tentatives. Demandez un nouveau code.",
        )
    check_named_rate_limit(name=f"otp_verify:{email_key}", limit=8, window_sec=60)
    if not otp_is_valid(
        db, email=data.email, purpose=PURPOSE_REGISTER, code=data.code
    ):
        record_failure(request, key=f"otp_fail:{email_key}", window_sec=900)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code invalide ou expiré.",
        )
    return MessageResponse(message="Email vérifié. Vous pouvez continuer l'inscription.")


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    from app.core.rate_limit import check_rate_limit
    from app.services.hibp import is_password_breached

    check_rate_limit(request, key="auth.register", limit=5, window_sec=60)
    if not consume_otp(
        db, email=data.email, purpose=PURPOSE_REGISTER, code=data.email_otp
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code email invalide ou expiré. Demandez un nouveau code.",
        )
    if await is_password_breached(data.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce mot de passe apparaît dans des fuites connues. Choisissez-en un autre.",
        )

    existing = db.query(User).filter(User.email == data.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Une erreur est survenue. Veuillez réessayer.",
        )

    email_local = (data.email or "").split("@")[0].replace(".", " ").replace("_", " ").strip()
    manager_name = (data.manager_name or "").strip() or (email_local.title() if email_local else "Administrateur")
    cabinet_name = (data.cabinet_name or "").strip() or f"Cabinet temporaire — {email_local or 'LexHub'}"
    city = (data.city or "").strip() or _CABINET_PLACEHOLDER
    address = (data.address or "").strip() or _CABINET_PLACEHOLDER
    barreau = (data.barreau or "").strip() or _CABINET_PLACEHOLDER

    cabinet = Cabinet(
        name=cabinet_name,
        city=city,
        address=address,
        barreau=barreau,
        ice=data.ice,
        status=CabinetStatus.ACTIVE,
    )
    db.add(cabinet)
    db.flush()
    from app.services.join_code import assign_unique_join_code

    assign_unique_join_code(db, cabinet, cabinet_name)

    user = User(
        email=data.email.lower(),
        hashed_password=hash_password(data.password),
        full_name=manager_name,
        phone=data.phone,
        role=UserRole.ADMIN_CABINET,
        is_active=True,
        is_verified=True,
        cabinet_id=cabinet.id,
    )
    db.add(user)
    db.flush()

    from app.services.billing import start_free_for_cabinet

    start_free_for_cabinet(db, cabinet.id)

    if getattr(data, "referral_code", None):
        from app.services.referral import attach_referral_on_register

        try:
            attach_referral_on_register(
                db, new_cabinet_id=cabinet.id, referral_code=data.referral_code
            )
        except HTTPException:
            raise
        except Exception:
            pass

    log_audit(db, "cabinet.register", user=user, request=request, details=cabinet.name)
    db.commit()

    try:
        from app.services.email import send_welcome_free_email

        send_welcome_free_email(
            user.email,
            full_name=user.full_name,
            cabinet_name=cabinet.name,
        )
    except Exception:
        pass

    return MessageResponse(
        message=(
            "Inscription réussie. Votre cabinet est sur le plan Découverte (gratuit). "
            "Complétez les informations du cabinet dans Paramètres après connexion."
        )
    )


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(data: ForgotPasswordRequest, request: Request, db: Session = Depends(get_db)):
    from app.core.rate_limit import check_rate_limit

    check_rate_limit(request, key="auth.forgot", limit=8, window_sec=60)
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if user:
        raw = create_token(db, user, TokenType.RESET_PASSWORD, reset_password_hours())
        log_audit(db, "auth.forgot_password", user=user, request=request)
        db.commit()
        if not send_password_reset_email(user.email, raw):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service d'email indisponible. Réessayez plus tard.",
            )

    return MessageResponse(
        message="Si un compte existe avec cette adresse, un email sera envoyé."
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    data: ResetPasswordRequest, request: Request, db: Session = Depends(get_db)
):
    from app.core.rate_limit import check_rate_limit
    from app.services.hibp import is_password_breached

    check_rate_limit(request, key="auth.reset", limit=8, window_sec=60)
    if await is_password_breached(data.new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce mot de passe apparaît dans des fuites connues. Choisissez-en un autre.",
        )

    user = consume_token(db, data.token, TokenType.RESET_PASSWORD)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lien invalide ou expiré.",
        )

    user.hashed_password = hash_password(data.new_password)
    user.failed_login_attempts = 0
    user.locked_until = None
    revoke_all_user_sessions(db, user.id)
    # Sécurité : un compte désactivé ne se réactive PAS via reset MDP
    if not user.is_active:
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte désactivé — contactez l'admin de votre cabinet pour réactivation.",
        )
    db.commit()

    return MessageResponse(message="Mot de passe réinitialisé avec succès.")


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    request: Request,
    response: Response,
    data: RefreshTokenRequest = Body(default_factory=RefreshTokenRequest),
    db: Session = Depends(get_db),
):
    from app.core.rate_limit import check_rate_limit

    check_rate_limit(request, key="auth.refresh", limit=30, window_sec=60)
    raw = (
        data.refresh_token
        or request.cookies.get(settings.REFRESH_COOKIE_NAME)
        or request.cookies.get("sanad_refresh")
    )
    if not raw:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide")

    payload = decode_token(raw)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide")

    session = get_valid_session(db, raw)
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session révoquée")

    user = db.query(User).filter(User.id == payload.get("sub")).first()
    if not user or not user.is_active or user.id != session.user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expirée")

    cabinet = db.query(Cabinet).filter(Cabinet.id == user.cabinet_id).first()
    new_session = rotate_session(
        db,
        session,
        new_refresh_token=create_refresh_token({"sub": user.id}),
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    access = create_access_token({"sub": user.id}, session_id=new_session.id)
    final_refresh = create_refresh_token({"sub": user.id}, session_id=new_session.id)
    new_session.refresh_token_hash = hash_refresh_token(final_refresh)
    db.commit()
    _set_refresh_cookie(response, final_refresh)
    return TokenResponse(
        access_token=access,
        refresh_token=final_refresh,
        user=_user_response(user, cabinet),
        mfa_setup_required=_mfa_required_for(user),
    )


@router.post("/logout", response_model=MessageResponse)
def logout(
    request: Request,
    response: Response,
    data: RefreshTokenRequest = Body(default_factory=RefreshTokenRequest),
    db: Session = Depends(get_db),
):
    raw = (
        data.refresh_token
        or request.cookies.get(settings.REFRESH_COOKIE_NAME)
        or request.cookies.get("sanad_refresh")
    )
    if raw:
        revoke_session(db, raw)
        db.commit()
    _clear_refresh_cookie(response)
    return MessageResponse(message="Déconnecté.")


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    from app.core.password_policy import DUMMY_PASSWORD_HASH
    from app.core.rate_limit import check_rate_limit, count_failures, record_failure
    from app.services.captcha import verify_turnstile

    check_rate_limit(
        request,
        key="auth.login",
        limit=settings.LOGIN_RATE_LIMIT,
        window_sec=settings.LOGIN_RATE_WINDOW_SEC,
    )

    failures = count_failures(request, key="auth.login_fail", window_sec=settings.LOGIN_RATE_WINDOW_SEC)
    captcha_needed = failures >= settings.CAPTCHA_AFTER_FAILURES and bool(
        settings.TURNSTILE_SECRET_KEY
    )
    if captcha_needed:
        ok = await verify_turnstile(
            data.captcha_token,
            request.client.host if request.client else None,
        )
        if not ok:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CAPTCHA_REQUIRED",
            )

    from app.services.join_code import find_pending_join_block

    if find_pending_join_block(db, data.email, data.password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="JOIN_PENDING",
        )

    user = db.query(User).filter(User.email == data.email.lower()).first()

    if not user:
        verify_password(data.password, DUMMY_PASSWORD_HASH)
        record_failure(request, key="auth.login_fail", window_sec=settings.LOGIN_RATE_WINDOW_SEC)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants incorrects")

    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Compte temporairement bloqué. Réessayez plus tard.",
        )

    if not verify_password(data.password, user.hashed_password):
        user.failed_login_attempts += 1
        record_failure(request, key="auth.login_fail", window_sec=settings.LOGIN_RATE_WINDOW_SEC)
        if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
            user.locked_until = datetime.now(timezone.utc) + timedelta(
                minutes=settings.LOCKOUT_MINUTES
            )
            send_lockout_email(user.email, settings.LOCKOUT_MINUTES)
        log_audit(db, "auth.login_failed", user=user, request=request)
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants incorrects")

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Veuillez vérifier votre adresse email avant de vous connecter.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte inactif. Votre cabinet est en attente d'activation.",
        )

    cabinet = db.query(Cabinet).filter(Cabinet.id == user.cabinet_id).first()
    if cabinet and cabinet.status == CabinetStatus.SUSPENDED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cabinet suspendu. Contactez le support.",
        )

    if cabinet and cabinet.status == CabinetStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cabinet en attente de validation par l'administrateur WebVoice.",
        )

    try:
        _verify_mfa(db, user, data.totp_code, data.recovery_code)
    except HTTPException as exc:
        if exc.status_code == 401:
            log_audit(db, "auth.2fa_failed", user=user, request=request)
            db.commit()
        raise

    user.failed_login_attempts = 0
    user.locked_until = None
    log_audit(db, "auth.login_success", user=user, request=request)

    mfa_setup = _mfa_required_for(user)
    tokens = _issue_tokens(
        db, user, cabinet, request, response, mfa_setup_required=mfa_setup
    )
    db.commit()
    return tokens


@router.post("/google", response_model=TokenResponse)
async def google_login(
    data: GoogleAuthRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    from app.core.rate_limit import check_rate_limit
    from app.services.google_oauth import verify_google_id_token

    check_rate_limit(request, key="auth.google", limit=15, window_sec=60)
    info = await verify_google_id_token(data.id_token)
    if not info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token Google invalide ou Google OAuth non configuré.",
        )

    user = db.query(User).filter(User.email == info["email"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun compte associé à cet email Google. Inscrivez votre cabinet d'abord.",
        )

    if not user.is_active or not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte inactif ou non vérifié.",
        )

    cabinet = db.query(Cabinet).filter(Cabinet.id == user.cabinet_id).first()
    if cabinet and cabinet.status in (CabinetStatus.SUSPENDED, CabinetStatus.PENDING):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cabinet suspendu ou en attente de validation.",
        )

    try:
        _verify_mfa(db, user, data.totp_code, data.recovery_code)
    except HTTPException as exc:
        if exc.status_code == 401:
            log_audit(db, "auth.google_2fa_failed", user=user, request=request)
            db.commit()
        raise

    user.google_id = info["google_id"]
    log_audit(db, "auth.google_login", user=user, request=request)
    mfa_setup = _mfa_required_for(user)
    tokens = _issue_tokens(
        db, user, cabinet, request, response, mfa_setup_required=mfa_setup
    )
    db.commit()
    return tokens


@router.get("/2fa/setup", response_model=TwoFactorSetupResponse)
def setup_2fa(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.services.totp import generate_totp_secret, get_totp_uri, qr_code_base64

    secret = generate_totp_secret()
    user.totp_secret = secret
    user.totp_enabled = False
    db.commit()

    uri = get_totp_uri(secret, user.email)
    return TwoFactorSetupResponse(
        secret=secret,
        qr_code_base64=qr_code_base64(uri),
        provisioning_uri=uri,
    )


@router.post("/2fa/enable", response_model=TwoFactorEnableResponse)
def enable_2fa(
    data: TwoFactorEnableRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.services.totp import verify_totp

    if not user.totp_secret:
        raise HTTPException(status_code=400, detail="Configurez d'abord la 2FA.")
    if not verify_totp(user.totp_secret, data.code):
        raise HTTPException(status_code=400, detail="Code invalide.")
    user.totp_enabled = True
    codes = generate_recovery_codes(db, user.id)
    log_audit(db, "auth.2fa_enabled", user=user, request=request)
    db.commit()
    return TwoFactorEnableResponse(
        message="Authentification à deux facteurs activée. Conservez vos codes de récupération.",
        recovery_codes=codes,
    )


@router.post("/2fa/disable", response_model=MessageResponse)
def disable_2fa(
    data: TwoFactorEnableRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.services.totp import verify_totp
    from app.models import MfaRecoveryCode

    if user.role == UserRole.ADMIN_WEBVOICE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La 2FA est obligatoire pour les comptes administrateur plateforme.",
        )
    if not user.totp_enabled or not user.totp_secret:
        raise HTTPException(status_code=400, detail="2FA non active.")
    if not verify_totp(user.totp_secret, data.code):
        raise HTTPException(status_code=400, detail="Code invalide.")
    user.totp_enabled = False
    user.totp_secret = None
    db.query(MfaRecoveryCode).filter(MfaRecoveryCode.user_id == user.id).delete()
    log_audit(db, "auth.2fa_disabled", user=user, request=request)
    db.commit()
    return MessageResponse(message="Authentification à deux facteurs désactivée.")
