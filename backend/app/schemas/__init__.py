from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.password_policy import validate_password_strength


class RegisterRequest(BaseModel):
    """Inscription minimale : e-mail + mot de passe (+ OTP).

    Les infos cabinet (ville, barreau, adresse, ICE…) sont optionnelles
    et se complètent ensuite dans Paramètres → Cabinet.
    """

    email: EmailStr
    password: str = Field(..., min_length=12, max_length=72)
    email_otp: str = Field(..., min_length=6, max_length=6)
    # Optionnels — complétés après accès à l'espace
    cabinet_name: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=500)
    barreau: Optional[str] = Field(None, max_length=100)
    ice: Optional[str] = Field(None, max_length=50)
    manager_name: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=30)
    referral_code: Optional[str] = Field(None, max_length=24)

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
    def normalize_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not str(v).strip():
            return None
        cleaned = "".join(c for c in str(v).strip() if c.isdigit() or c in "+ ")
        digits = cleaned.replace(" ", "").replace("+", "")
        if digits and len(digits) < 8:
            raise ValueError("Numéro de téléphone invalide.")
        return cleaned.strip() or None


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
    full_name_ar: Optional[str] = None
    phone: Optional[str] = None
    role: str
    cabinet_id: str
    cabinet_name: str
    cabinet_name_ar: Optional[str] = None
    cabinet_city: Optional[str] = None
    cabinet_barreau: Optional[str] = None
    cabinet_address: Optional[str] = None
    cabinet_has_logo: bool = False
    cabinet_profile_complete: bool = True
    totp_enabled: bool = False
    mfa_required: bool = False
    has_seen_onboarding_tour: bool = False

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
    jurisdiction_degree: Optional[str] = Field(None, max_length=32)
    tribunal: Optional[str] = Field(None, max_length=120)
    court_city: Optional[str] = Field(None, max_length=120)

    court_file_number: Optional[str] = Field(None, max_length=120)
    judge_name: Optional[str] = Field(None, max_length=120)
    chamber: Optional[str] = Field(None, max_length=120)
    greffe: Optional[str] = Field(None, max_length=120)
    procedure_status: Optional[str] = Field(None, max_length=40)
    assistant_id: Optional[str] = Field(None, max_length=36)
    last_decision_type: Optional[str] = Field(None, max_length=120)
    last_decision_date: Optional[datetime] = None
    notification_date: Optional[datetime] = None
    appeal_deadline_at: Optional[datetime] = None
    appeal_deadline_days: Optional[int] = None
    client_role: Optional[str] = Field(None, max_length=40)
    client_quality: Optional[str] = Field(None, max_length=120)
    client_domicile: Optional[str] = Field(None, max_length=255)
    opposing_name: Optional[str] = Field(None, max_length=255)
    opposing_role: Optional[str] = Field(None, max_length=40)
    opposing_quality: Optional[str] = Field(None, max_length=120)
    opposing_domicile: Optional[str] = Field(None, max_length=255)


class CaseUpdate(BaseModel):
    client_name: Optional[str] = None
    case_type: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[list[str]] = None
    jurisdiction_degree: Optional[str] = None
    tribunal: Optional[str] = None
    court_city: Optional[str] = Field(None, max_length=120)
    court_file_number: Optional[str] = Field(None, max_length=120)
    judge_name: Optional[str] = None
    chamber: Optional[str] = None
    greffe: Optional[str] = None
    procedure_status: Optional[str] = None
    assistant_id: Optional[str] = None
    last_decision_type: Optional[str] = Field(None, max_length=120)
    last_decision_date: Optional[datetime] = None
    notification_date: Optional[datetime] = None
    appeal_deadline_at: Optional[datetime] = None
    appeal_deadline_days: Optional[int] = None
    client_role: Optional[str] = None
    client_quality: Optional[str] = None
    client_domicile: Optional[str] = None
    opposing_name: Optional[str] = None
    opposing_role: Optional[str] = None
    opposing_quality: Optional[str] = None
    opposing_domicile: Optional[str] = None


class CaseResponse(BaseModel):
    id: str
    reference: str
    client_name: str
    case_type: str
    status: str
    responsible_name: str
    responsible_id: Optional[str] = None
    description: Optional[str] = None
    tags: list[str] = []
    opened_at: datetime
    updated_at: datetime
    jurisdiction_degree: Optional[str] = None
    tribunal: Optional[str] = None
    court_city: Optional[str] = None
    court_file_number: Optional[str] = None
    judge_name: Optional[str] = None
    chamber: Optional[str] = None
    greffe: Optional[str] = None
    procedure_status: Optional[str] = None
    assistant_id: Optional[str] = None
    last_decision_type: Optional[str] = None
    last_decision_date: Optional[datetime] = None
    notification_date: Optional[datetime] = None
    appeal_deadline_at: Optional[datetime] = None
    appeal_deadline_days: Optional[int] = None
    client_role: Optional[str] = None
    client_quality: Optional[str] = None
    client_domicile: Optional[str] = None
    opposing_name: Optional[str] = None
    opposing_role: Optional[str] = None
    opposing_quality: Optional[str] = None
    opposing_domicile: Optional[str] = None

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
    inventory_number: Optional[int] = None
    exhibit_type: Optional[str] = None
    produced_by: Optional[str] = None
    exhibit_version: Optional[str] = None
    cited_in_plea: Optional[str] = None
    uploaded_by: Optional[str] = None

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
    assignee_id: Optional[str] = Field(None, max_length=36)


class CaseTaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    case_id: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(todo|doing|done)$")
    due_at: Optional[datetime] = None
    assignee_id: Optional[str] = Field(None, max_length=36)


class CaseTaskResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    case_id: Optional[str] = None
    case_reference: Optional[str] = None
    status: str
    due_at: Optional[datetime] = None
    assignee_id: Optional[str] = None
    assignee_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgendaEventCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    case_id: Optional[str] = None
    event_type: str = Field("other", pattern="^(audience|deadline|rdv|notification|recours|expertise|mediation|other)$")
    starts_at: datetime
    ends_at: Optional[datetime] = None
    meet_url: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=80)
    location: Optional[str] = Field(None, max_length=255)


class AgendaEventUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    case_id: Optional[str] = None
    event_type: Optional[str] = Field(None, pattern="^(audience|deadline|rdv|notification|recours|expertise|mediation|other)$")
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    meet_url: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=80)
    location: Optional[str] = Field(None, max_length=255)


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
    city: Optional[str] = None
    location: Optional[str] = None
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
    expires_at: Optional[datetime] = None
    approved_count: int = 0
    max_approvals: int = 1
    remaining_approvals: int = 1
    is_expired: bool = False
    is_exhausted: bool = False
    is_active: bool = True


class CabinetInviteItem(BaseModel):
    id: str
    email: str
    code: str
    role: str = "avocat"
    expires_at: datetime
    created_at: datetime
    # new | already_member_same | already_on_lexhub
    email_status: str = "new"

    class Config:
        from_attributes = True


class JoinCodeValidateRequest(BaseModel):
    code: str = Field(..., min_length=4, max_length=40)


class JoinCodeValidateResponse(BaseModel):
    valid: bool


class JoinRequestCreate(BaseModel):
    code: str = Field(..., min_length=4, max_length=40)
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
    name_ar: Optional[str] = None
    city: str
    address: str
    barreau: str
    ice: Optional[str] = None
    ai_custom_prompt: Optional[str] = None
    has_logo: bool = False
    status: str

    class Config:
        from_attributes = True


class CabinetSettingsUpdate(BaseModel):
    name: Optional[str] = None
    name_ar: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    barreau: Optional[str] = None
    ice: Optional[str] = None
    ai_custom_prompt: Optional[str] = Field(None, max_length=4000)


class ProfileNameUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    full_name_ar: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = Field(None, max_length=30)


class EmailChangeRequestOtp(BaseModel):
    new_email: EmailStr


class EmailChangeConfirm(BaseModel):
    new_email: EmailStr
    email_otp: str = Field(..., min_length=6, max_length=6)
    current_password: str = Field(..., min_length=1, max_length=128)


class PlaidoirieDraftCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=512)
    body: str = Field(..., min_length=1)
    template_id: Optional[str] = None
    case_id: Optional[str] = None
    checks: list[str] = Field(default_factory=list)
    status: str = Field("draft", pattern="^(draft|validated|finalized)$")
    output_mode: Optional[str] = Field(None, pattern="^(orale|ecrite)$")
    sources: list[dict] = Field(default_factory=list)


class PlaidoirieDraftUpdate(BaseModel):
    """Mise à jour partielle — ex. rattacher à un dossier après création."""
    case_id: Optional[str] = None  # "" ou null = sans dossier
    title: Optional[str] = Field(None, min_length=1, max_length=512)
    body: Optional[str] = None
    output_mode: Optional[str] = Field(None, pattern="^(orale|ecrite)$")
    sources: Optional[list[dict]] = None
    status: Optional[str] = Field(None, pattern="^(draft|validated|finalized)$")
    checks: Optional[list[str]] = None


class PlaidoirieDraftResponse(BaseModel):
    id: str
    title: str
    body: str
    template_id: Optional[str] = None
    case_id: Optional[str] = None
    case_reference: Optional[str] = None
    checks: list[str] = Field(default_factory=list)
    status: str = "draft"
    assigned_to_user_id: Optional[str] = None
    assigned_to_name: Optional[str] = None
    pinned: bool = False
    output_mode: Optional[str] = None
    citations: list[dict] = Field(default_factory=list)
    sources: list[dict] = Field(default_factory=list)
    validated_by: Optional[str] = None
    validated_at: Optional[datetime] = None
    trust_badge: str = "a_relire"
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PlaidoirieAssignRequest(BaseModel):
    user_id: Optional[str] = None  # None = désassigner


class WorkspaceSearchHit(BaseModel):
    kind: str  # case | document | plaidoirie
    id: str
    title: str
    subtitle: Optional[str] = None
    href: str


class WorkspaceActivityItem(BaseModel):
    id: str
    action: str
    label: str
    details: Optional[str] = None
    actor_name: Optional[str] = None
    created_at: datetime
    href: Optional[str] = None


class ActivityArchiveItem(BaseModel):
    id: str
    filename: str
    period_start: datetime
    period_end: datetime
    row_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class TeamInviteEmailRequest(BaseModel):
    email: EmailStr
    recipient_name: Optional[str] = Field(None, max_length=120)
    role: str = Field(default="avocat", pattern="^(avocat|assistant_juridique|admin_cabinet)$")


class InvitePreviewResponse(BaseModel):
    valid: bool
    email: str
    cabinet_name: str
    recipient_name: Optional[str] = None
    role: str = "avocat"
    email_already_registered: bool = False
    email_same_cabinet: bool = False


class AcceptInviteRequest(BaseModel):
    code: str = Field(..., min_length=8, max_length=64)
    full_name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=12, max_length=72)

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        return validate_password_strength(v)


class PasswordChangeRequest(BaseModel):
    new_password: str = Field(..., min_length=12, max_length=72)
    email_otp: str = Field(..., min_length=6, max_length=6)
    current_password: Optional[str] = Field(None, min_length=1, max_length=128)

    @field_validator("new_password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        return validate_password_strength(v)


class AccountDeleteRequest(BaseModel):
    """Suppression de compte — confirmation forte (grandes apps)."""

    password: str = Field(..., min_length=1, max_length=128)
    email_otp: str = Field(..., min_length=6, max_length=6)
    confirmation: str = Field(..., min_length=8, max_length=32)


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
    address: str
    barreau: str
    ice: Optional[str] = None
    status: str
    user_count: int
    document_count: int
    case_count: int
    created_at: datetime


class AdminCabinetUserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    phone: Optional[str] = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    is_deleted_account: bool = False


class AdminSubscriptionSnapshot(BaseModel):
    plan_slug: Optional[str] = None
    plan_name: Optional[str] = None
    status: Optional[str] = None
    billing_cycle: Optional[str] = None
    trial_ends_at: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False
    cancel_reason_code: Optional[str] = None
    cancel_reason_text: Optional[str] = None
    cancel_requested_at: Optional[datetime] = None
    payment_provider: Optional[str] = None


class AdminBillingEventOut(BaseModel):
    event_type: str
    plan_slug: Optional[str] = None
    detail: Optional[str] = None
    created_at: Optional[datetime] = None


class AdminInvoiceOut(BaseModel):
    id: str
    number: str
    plan_name: str
    amount_mad: int
    status: str
    billing_cycle: Optional[str] = None
    issued_at: Optional[datetime] = None
    kind: str = "invoice"  # invoice | trial_receipt


class AdminCabinetDetailResponse(AdminCabinetResponse):
    users: list[AdminCabinetUserResponse]
    deleted_accounts_count: int = 0
    deleted_accounts: list[AdminCabinetUserResponse] = []
    subscription: Optional[AdminSubscriptionSnapshot] = None
    billing_history: list[AdminBillingEventOut] = []
    invoices: list[AdminInvoiceOut] = []


class AdminUserStatusUpdate(BaseModel):
    is_active: bool


class AdminMetricsResponse(BaseModel):
    active_cabinets: int
    suspended_cabinets: int
    total_users: int
    total_documents: int
    deleted_accounts: int = 0
    cancel_requests: int = 0


class AuditLogResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    cabinet_id: Optional[str] = None
    action: str
    ip_address: Optional[str] = None
    details: Optional[str] = None
    created_at: datetime
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    cabinet_name: Optional[str] = None

    class Config:
        from_attributes = True


class CabinetStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(active|suspended)$")


class CabinetDeleteRequest(BaseModel):
    """Confirmation obligatoire pour suppression définitive (admin plateforme)."""

    confirmation: str = Field(..., min_length=5, max_length=32)


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
    case_reference: Optional[str] = Field(None, max_length=64)
    client_name: Optional[str] = Field(None, max_length=255)
    include_esignature: bool = False



class DocumentMetaUpdate(BaseModel):
    inventory_number: Optional[int] = None
    exhibit_type: Optional[str] = Field(None, max_length=60)
    produced_by: Optional[str] = Field(None, max_length=40)
    exhibit_version: Optional[str] = Field(None, max_length=40)
    cited_in_plea: Optional[str] = Field(None, max_length=255)


class CaseCommentCreate(BaseModel):
    body: str = Field(..., min_length=1, max_length=4000)


class CaseCommentResponse(BaseModel):
    id: str
    case_id: str
    body: str
    author_name: str
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentTransferCreate(BaseModel):
    plan_slug: str = Field(..., min_length=2, max_length=64)
    billing_cycle: str = Field("monthly", pattern="^(monthly|yearly)$")
    notes: Optional[str] = Field(None, max_length=1000)


class PaymentTransferResponse(BaseModel):
    id: str
    reference: str
    amount_mad: int
    plan_slug: str
    billing_cycle: str
    status: str
    ice: Optional[str] = None
    bank_rib: Optional[str] = None
    bank_name: Optional[str] = None
    beneficiary: Optional[str] = None
    instructions: str
    created_at: datetime
