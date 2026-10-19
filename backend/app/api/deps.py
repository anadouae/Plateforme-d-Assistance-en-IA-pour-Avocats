from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models import AuditLog, User, UserRole
from app.services.auth_sessions import session_is_active

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Non authentifié",
        )
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
        )
    if not session_is_active(db, payload.get("sid")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session révoquée",
        )
    user = db.query(User).filter(User.id == payload.get("sub")).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Compte inactif ou inexistant",
        )
    return user


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User | None:
    """Auth optionnelle (ex. logout + rappel e-mail)."""
    if not credentials:
        return None
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        return None
    if not session_is_active(db, payload.get("sid")):
        return None
    user = db.query(User).filter(User.id == payload.get("sub")).first()
    if not user or not user.is_active:
        return None
    return user


def require_roles(*roles: UserRole):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas l'autorisation d'accéder à cette ressource.",
            )
        # Admin plateforme : Magic Link / email OTP préférés (TOTP téléphone optionnel)
        return user

    return checker


def require_not_assistant(user: User = Depends(get_current_user)) -> User:
    """Bloque le rôle assistant_juridique (synthèse, suppressions, analyse IA)."""
    if user.role == UserRole.ASSISTANT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas l'autorisation d'accéder à cette ressource.",
        )
    return user


def require_cabinet_billing_admin(user: User = Depends(get_current_user)) -> User:
    """Seul l'admin cabinet (créateur / coordinateur de l'espace) gère l'abonnement."""
    if user.role != UserRole.ADMIN_CABINET:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Seul le responsable du cabinet (qui a créé l'espace) peut payer "
                "ou modifier l'abonnement. Demandez-lui d'ouvrir Paramètres → Abonnement."
            ),
        )
    return user


def user_must_set_password(user: User) -> bool:
    return bool(getattr(user, "must_set_password", False)) or not bool(
        getattr(user, "hashed_password", None)
    )


def require_password_set(user: User = Depends(get_current_user)) -> User:
    """Hard gate : plans, packs, équipe — après onboarding frictionless."""
    if user_must_set_password(user) and not getattr(user, "google_id", None):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="PASSWORD_REQUIRED",
        )
    return user


def log_audit(
    db: Session,
    action: str,
    user: User | None = None,
    request: Request | None = None,
    details: str | None = None,
):
    ip = None
    if request:
        try:
            from app.core.rate_limit import _client_ip

            raw = _client_ip(request)
            ip = None if raw in {"unknown", ""} else raw
        except Exception:
            ip = request.client.host if request.client else None
    db.add(
        AuditLog(
            user_id=user.id if user else None,
            cabinet_id=user.cabinet_id if user else None,
            action=action,
            ip_address=ip,
            details=details,
            created_at=datetime.now(timezone.utc),
        )
    )
