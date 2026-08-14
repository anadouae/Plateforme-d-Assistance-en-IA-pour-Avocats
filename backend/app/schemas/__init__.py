from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.password_policy import validate_password_strength


class RegisterRequest(BaseModel):
    cabinet_name: str = Field(..., min_length=2, max_length=255)
    city: str = Field(..., min_length=2, max_length=100)
    address: str = Field(..., min_length=5, max_length=500)
    barreau: str = Field(..., min_length=2, max_length=100)
    ice: Optional[str] = Field(None, max_length=50)
    manager_name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    phone: str = Field(..., min_length=8, max_length=30)
    password: str = Field(..., min_length=12, max_length=72)
    email_otp: str = Field(..., min_length=6, max_length=6)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        return validate_password_strength(v)

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, v: str) -> str:
        cleaned = "".join(c for c in v.strip() if c.isdigit() or c in "+ ")
        if len(cleaned.replace(" ", "").replace("+", "")) < 8:
            raise ValueError("Numéro de téléphone invalide.")
        return cleaned.strip()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)
    totp_code: Optional[str] = Field(None, min_length=6, max_length=6)
    recovery_code: Optional[str] = Field(None, min_length=8, max_length=32)
    captcha_token: Optional[str] = Field(None, max_length=2048)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("totp_code")
    @classmethod
    def digits_only(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not v.isdigit():
            raise ValueError("Code 2FA invalide.")
        return v


class GoogleAuthRequest(BaseModel):
    id_token: str = Field(..., min_length=20, max_length=4096)
    totp_code: Optional[str] = Field(None, min_length=6, max_length=6)
    recovery_code: Optional[str] = Field(None, min_length=8, max_length=32)
    captcha_token: Optional[str] = Field(None, max_length=2048)


class TwoFactorSetupResponse(BaseModel):
    secret: str
    qr_code_base64: str
    provisioning_uri: str


class TwoFactorEnableRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)


class TwoFactorLoginResponse(BaseModel):
    requires_2fa: bool = True
    message: str = "Code 2FA requis."


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    cabinet_id: str
    cabinet_name: str
    totp_enabled: bool = False
    mfa_required: bool = False

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
    mfa_setup_required: bool = False
    captcha_required: bool = False


class TwoFactorEnableResponse(BaseModel):
    message: str
    recovery_codes: list[str] = []


class MessageResponse(BaseModel):
    message: str


class CaseCreate(BaseModel):
    client_name: str = Field(..., min_length=2, max_length=255)
    case_type: str = Field(..., min_length=2, max_length=100)
    status: str = "En cours"
    description: Optional[str] = None
    tags: Optional[list[str]] = None
    responsible_id: Optional[str] = Field(None, max_length=36)
    first_hearing_at: Optional[str] = Field(
        None,
        description="Date première audience (YYYY-MM-DD), stockée dans tags/description si besoin",
    )


class CaseUpdate(BaseModel):
    client_name: Optional[str] = None
    case_type: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[list[str]] = None


class CaseResponse(BaseModel):
    id: str
    reference: str
    client_name: str
    case_type: str
    status: str
    responsible_name: str
    description: Optional[str] = None
    tags: list[str] = []
    opened_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    id: str
    original_name: str
    mime_type: str
    file_size: int
    ocr_score: Optional[int] = None
    ocr_alert: bool = False
    status: str
    case_id: str
    case_reference: Optional[str] = None
    created_at: datetime
    # "audio" | "file" — déduit de l'extension / MIME (pas de colonne dédiée)
    kind: str = "file"
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class DocumentDetailResponse(DocumentResponse):
    extracted_text_preview: Optional[str] = None


class DocumentAskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)
    language: Optional[str] = Field(None, pattern="^(fr|ar|en)$")


class Citation(BaseModel):
    label: str
    excerpt: str
    url: Optional[str] = None


class AIResponse(BaseModel):
    answer: str
    source_type: str
    sources: list[Citation]
    confidence_score: int
    summary: str = ""
    disclaimer: str = "Ceci ne constitue pas un avis juridique."
    session_id: Optional[str] = None


class SynthesisResponse(BaseModel):
    document_id: str
    document_name: str
    parties: list[str]
    key_dates: list[str]
    amounts: list[str]
    risk_clauses: list[str]
    attention_points: list[str]
    summary: str
    sources: list[Citation]
    disclaimer: str = "Ceci ne constitue pas un avis juridique."


class CaseAnalysisResponse(BaseModel):
    case_id: str
    case_reference: str
    facts: str
    key_documents: list[str]
    legal_issues: list[str]
    risks_and_deadlines: list[str]
    checklist: list[str]
    summary: str
    parties: list[str] = []
    key_dates: list[str] = []
    amounts: list[str] = []
    sources: list[Citation] = []
    confidence_score: int = 0
    disclaimer: str = "Ceci ne constitue pas un avis juridique."


class CaseNoteCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    body: str = ""
    case_id: Optional[str] = None


class CaseNoteUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    body: Optional[str] = None
    case_id: Optional[str] = None


class CaseNoteResponse(BaseModel):
    id: str
    title: str
    body: str
    case_id: Optional[str] = None
    case_reference: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CaseTaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    case_id: Optional[str] = None
    status: str = Field("todo", pattern="^(todo|doing|done)$")
    due_at: Optional[datetime] = None


class CaseTaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    case_id: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(todo|doing|done)$")
    due_at: Optional[datetime] = None


class CaseTaskResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    case_id: Optional[str] = None
    case_reference: Optional[str] = None
    status: str
    due_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgendaEventCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    case_id: Optional[str] = None
    event_type: str = Field("other", pattern="^(audience|deadline|rdv|other)$")
    starts_at: datetime
    ends_at: Optional[datetime] = None
    meet_url: Optional[str] = Field(None, max_length=500)


class AgendaEventUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    case_id: Optional[str] = None
    event_type: Optional[str] = Field(None, pattern="^(audience|deadline|rdv|other)$")
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    meet_url: Optional[str] = Field(None, max_length=500)


class AgendaEventResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    case_id: Optional[str] = None
    case_reference: Optional[str] = None
    event_type: str
    starts_at: datetime
    ends_at: Optional[datetime] = None
    meet_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class WorkspaceSummaryResponse(BaseModel):
    upcoming_events: list[AgendaEventResponse]
    open_tasks: list[CaseTaskResponse]
    recent_notes: list[CaseNoteResponse]


class TeamMemberResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TeamInviteRequest(BaseModel):
    """Deprecated — conservé pour compat, préférer join-code."""

    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    role: str = Field(..., pattern="^(avocat|assistant_juridique|admin_cabinet)$")


class TeamInviteResponse(BaseModel):
    message: str
    invite_url: str
    email: str
    email_sent: bool = False
    dev_mail_url: Optional[str] = None


class TeamUpdateRequest(BaseModel):
    role: Optional[str] = Field(None, pattern="^(avocat|assistant_juridique|admin_cabinet)$")
    is_active: Optional[bool] = None


class JoinCodeResponse(BaseModel):
    join_code: str
    regenerated_at: Optional[datetime] = None


class JoinCodeValidateRequest(BaseModel):
    code: str = Field(..., min_length=4, max_length=32)


class JoinCodeValidateResponse(BaseModel):
    valid: bool


class JoinRequestCreate(BaseModel):
    code: str = Field(..., min_length=4, max_length=32)
    full_name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=12, max_length=72)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class MembershipRequestResponse(BaseModel):
    id: str
    full_name: str
    email: str
    status: str
    requested_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MembershipApproveRequest(BaseModel):
    role: str = Field(..., pattern="^(avocat|assistant_juridique|admin_cabinet)$")


class CabinetSettingsResponse(BaseModel):
    id: str
    name: str
    city: str
    address: str
    barreau: str
    ice: Optional[str] = None
    ai_custom_prompt: Optional[str] = None
    status: str

    class Config:
        from_attributes = True


class CabinetSettingsUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    barreau: Optional[str] = None
    ice: Optional[str] = None
    ai_custom_prompt: Optional[str] = Field(None, max_length=4000)


class PasswordChangeRequest(BaseModel):
    new_password: str = Field(..., min_length=12, max_length=72)
    email_otp: str = Field(..., min_length=6, max_length=6)
    current_password: Optional[str] = Field(None, min_length=1, max_length=128)

    @field_validator("new_password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        return validate_password_strength(v)


class EmailOnlyRequest(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class EmailOtpVerifyRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class MagicLoginRequest(BaseModel):
    token: str = Field(..., min_length=16, max_length=512)


class AdminCabinetResponse(BaseModel):
    id: str
    name: str
    city: str
    barreau: str
    status: str
    user_count: int
    document_count: int
    case_count: int
    summarize_count: int
    created_at: datetime


class AdminMetricsResponse(BaseModel):
    active_cabinets: int
    suspended_cabinets: int
    total_users: int
    total_documents: int
    ai_actions_today: int
    avg_ocr_score: float


class AuditLogResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    cabinet_id: Optional[str] = None
    action: str
    ip_address: Optional[str] = None
    details: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CabinetStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(active|suspended)$")


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=16, max_length=512)
    new_password: str = Field(..., min_length=12, max_length=72)

    @field_validator("new_password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        return validate_password_strength(v)


class RefreshTokenRequest(BaseModel):
    refresh_token: Optional[str] = None


class CabinetPlaidoirieTemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    body: str = Field(..., min_length=1, max_length=100_000)
    base_type: Optional[str] = Field(None, max_length=64)


class CabinetPlaidoirieTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    body: Optional[str] = Field(None, min_length=1, max_length=100_000)
    base_type: Optional[str] = Field(None, max_length=64)


class CabinetPlaidoirieTemplateResponse(BaseModel):
    id: str
    name: str
    body: str
    base_type: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PlaidoirieDocxRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    body: str = Field(..., min_length=1, max_length=200_000)
    cabinet_name: Optional[str] = Field(None, max_length=255)
    lawyer_name: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
