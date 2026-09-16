import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserRole(str, enum.Enum):
    AVOCAT = "avocat"
    ASSISTANT = "assistant_juridique"
    ADMIN_CABINET = "admin_cabinet"
    ADMIN_WEBVOICE = "admin_webvoice"


class CabinetStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"


class Cabinet(Base):
    __tablename__ = "cabinets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    barreau: Mapped[str] = mapped_column(String(100), nullable=False)
    ice: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ai_custom_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    logo_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    name_ar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    join_code: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True, index=True)
    join_code_regenerated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    join_code_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    join_code_approved_count: Mapped[int] = mapped_column(Integer, default=0)
    referral_code: Mapped[str | None] = mapped_column(String(24), unique=True, nullable=True, index=True)
    referred_by_cabinet_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    status: Mapped[CabinetStatus] = mapped_column(
        Enum(CabinetStatus), default=CabinetStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    users: Mapped[list["User"]] = relationship(back_populates="cabinet")
    cases: Mapped[list["Case"]] = relationship(back_populates="cabinet")
    membership_requests: Mapped[list["MembershipRequest"]] = relationship(
        back_populates="cabinet"
    )


class MembershipRequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class MembershipRequest(Base):
    """Demande d'adhésion via code cabinet — aucun accès avant approbation."""

    __tablename__ = "membership_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cabinet_id: Mapped[str] = mapped_column(String(36), ForeignKey("cabinets.id"), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[MembershipRequestStatus] = mapped_column(
        Enum(
            MembershipRequestStatus,
            name="membershiprequeststatus",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        default=MembershipRequestStatus.PENDING,
    )
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    cabinet: Mapped["Cabinet"] = relationship(back_populates="membership_requests")


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name_ar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.AVOCAT)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    google_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    totp_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)
    totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    has_seen_onboarding_tour: Mapped[bool] = mapped_column(Boolean, default=False)
    cabinet_id: Mapped[str] = mapped_column(String(36), ForeignKey("cabinets.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    cabinet: Mapped["Cabinet"] = relationship(back_populates="users")
    cases: Mapped[list["Case"]] = relationship(back_populates="responsible")


class CaseStatus(str, enum.Enum):
    EN_COURS = "En cours"
    URGENT = "Urgent"
    CLOTURE = "Clôturé"


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reference: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    case_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=CaseStatus.EN_COURS.value)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Identité juridique (art. 32 CPC) — fiche dossier, pas l’écran « matière & type »
    jurisdiction_degree: Mapped[str | None] = mapped_column(String(32), nullable=True)
    tribunal: Mapped[str | None] = mapped_column(String(120), nullable=True)
    court_city: Mapped[str | None] = mapped_column(String(80), nullable=True)
    client_role: Mapped[str | None] = mapped_column(String(40), nullable=True)
    client_quality: Mapped[str | None] = mapped_column(String(120), nullable=True)
    client_domicile: Mapped[str | None] = mapped_column(String(255), nullable=True)
    opposing_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    opposing_role: Mapped[str | None] = mapped_column(String(40), nullable=True)
    opposing_quality: Mapped[str | None] = mapped_column(String(120), nullable=True)
    opposing_domicile: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Dossier judiciaire vivant
    court_file_number: Mapped[str | None] = mapped_column(String(80), nullable=True)  # N° RG
    judge_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    chamber: Mapped[str | None] = mapped_column(String(120), nullable=True)
    greffe: Mapped[str | None] = mapped_column(String(120), nullable=True)
    procedure_status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    assistant_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    last_decision_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    last_decision_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notification_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    appeal_deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    appeal_deadline_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cabinet_id: Mapped[str] = mapped_column(String(36), ForeignKey("cabinets.id"), nullable=False)
    responsible_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    cabinet: Mapped["Cabinet"] = relationship(back_populates="cases")
    responsible: Mapped["User"] = relationship(back_populates="cases")
    documents: Mapped[list["Document"]] = relationship(back_populates="case")
    notes: Mapped[list["CaseNote"]] = relationship(back_populates="case")
    tasks: Mapped[list["CaseTask"]] = relationship(back_populates="case")
    agenda_events: Mapped[list["AgendaEvent"]] = relationship(back_populates="case")


class TaskStatus(str, enum.Enum):
    TODO = "todo"
    DOING = "doing"
    DONE = "done"


class AgendaEventType(str, enum.Enum):
    AUDIENCE = "audience"
    DEADLINE = "deadline"
    RDV = "rdv"
    NOTIFICATION = "notification"
    RECOURS = "recours"
    EXPERTISE = "expertise"
    MEDIATION = "mediation"
    OTHER = "other"


class CaseNote(Base):
    """Notes internes de dossier."""

    __tablename__ = "case_notes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cabinet_id: Mapped[str] = mapped_column(String(36), ForeignKey("cabinets.id"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    case_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("cases.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="Note")
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    case: Mapped["Case | None"] = relationship(back_populates="notes")


class CaseTask(Base):
    """Tâches / planning léger liés au cabinet ou à un dossier."""

    __tablename__ = "case_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cabinet_id: Mapped[str] = mapped_column(String(36), ForeignKey("cabinets.id"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    case_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("cases.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=TaskStatus.TODO.value, nullable=False)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    assignee_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    case: Mapped["Case | None"] = relationship(back_populates="tasks")


class AgendaEvent(Base):
    """Événements agenda : audiences, délais, RDV."""

    __tablename__ = "agenda_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cabinet_id: Mapped[str] = mapped_column(String(36), ForeignKey("cabinets.id"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    case_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("cases.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_type: Mapped[str] = mapped_column(String(30), default=AgendaEventType.OTHER.value, nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    meet_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city: Mapped[str | None] = mapped_column(String(80), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reminder_7d_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reminder_2d_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reminder_1d_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reminder_48h_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    case: Mapped["Case | None"] = relationship(back_populates="agenda_events")


class DocumentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocr_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus), default=DocumentStatus.PENDING
    )
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id"), nullable=False)
    cabinet_id: Mapped[str] = mapped_column(String(36), ForeignKey("cabinets.id"), nullable=False)
    uploaded_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    inventory_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    exhibit_type: Mapped[str | None] = mapped_column(String(60), nullable=True)
    produced_by: Mapped[str | None] = mapped_column(String(40), nullable=True)
    exhibit_version: Mapped[str | None] = mapped_column(String(40), nullable=True)
    cited_in_plea: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    case: Mapped["Case"] = relationship(back_populates="documents")


class CabinetPlaidoirieTemplate(Base):
    """Modèles de plaidoirie personnalisés, réutilisables par cabinet."""

    __tablename__ = "cabinet_plaidoirie_templates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cabinet_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cabinets.id"), nullable=False, index=True
    )
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    base_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class PlaidoirieDraft(Base):
    """Trace des plaidoiries : brouillon (avocat) ou validée (visible assistant)."""

    __tablename__ = "plaidoirie_drafts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cabinet_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cabinets.id"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    case_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("cases.id"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    template_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    checks_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_mode: Mapped[str | None] = mapped_column(String(20), nullable=True)  # orale | ecrite
    citations_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    sources_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    validated_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    read_by_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    # draft = brouillon | validated = partagée assistant | finalized = exportée / fin rédigée
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="draft", index=True)
    assigned_to_user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True, index=True
    )
    pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    cabinet_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class CabinetNotification(Base):
    """Notifications collab cabinet (ex. plaidoirie validée → assistant)."""

    __tablename__ = "cabinet_notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cabinet_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cabinets.id"), nullable=False, index=True
    )
    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True, index=True
    )
    role_target: Mapped[str | None] = mapped_column(String(40), nullable=True)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    href: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )


class ActivityArchive(Base):
    """Exports Excel de l'activité cabinet (rétention 90 j live → archive)."""

    __tablename__ = "activity_archives"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cabinet_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cabinets.id"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class AdminAuditArchive(Base):
    """Exports Excel du journal d'audit plateforme (WebVoice admin)."""

    __tablename__ = "admin_audit_archives"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class CabinetInvite(Base):
    """Invitation personnelle one-time (un code = une personne)."""

    __tablename__ = "cabinet_invites"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cabinet_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cabinets.id"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="avocat")
    recipient_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class TokenType(str, enum.Enum):
    VERIFY_EMAIL = "verify_email"
    RESET_PASSWORD = "reset_password"
    TEAM_INVITE = "team_invite"


class EmailToken(Base):
    __tablename__ = "email_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    token_type: Mapped[TokenType] = mapped_column(Enum(TokenType), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class EmailOtp(Base):
    """OTP / magic-link email (hashés) — register, login, changement MDP."""

    __tablename__ = "email_otps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    purpose: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    code_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class AuthSession(Base):
    """Session serveur liée au refresh token (rotation / révocation)."""

    __tablename__ = "auth_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    refresh_token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MfaRecoveryCode(Base):
    """Codes de récupération MFA à usage unique (stockés hashés)."""

    __tablename__ = "mfa_recovery_codes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    code_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class SubscriptionStatus(str, enum.Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    EXPIRED = "expired"


class BillingCycle(str, enum.Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"


class SubscriptionPlan(Base):
    """Offre tarifaire LexHub (éditable par admin WebVoice)."""

    __tablename__ = "subscription_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    name_ar: Mapped[str | None] = mapped_column(String(120), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price_mad_monthly: Mapped[int] = mapped_column(Integer, default=0)
    price_mad_yearly: Mapped[int] = mapped_column(Integer, default=0)
    max_avocats: Mapped[int] = mapped_column(Integer, default=1)
    max_assistants: Mapped[int] = mapped_column(Integer, default=0)
    max_cases: Mapped[int] = mapped_column(Integer, default=3)  # -1 = illimité
    max_plaidoiries_month: Mapped[int] = mapped_column(Integer, default=5)  # -1 = illimité
    max_ai_credits_month: Mapped[int] = mapped_column(Integer, default=50)  # crédits IA / mois
    features_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list[str]
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    is_recommended: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=100)
    trial_days: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class CabinetSubscription(Base):
    """Abonnement / essai d'un cabinet (paiement réel phase 2)."""

    __tablename__ = "cabinet_subscriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cabinet_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cabinets.id"), nullable=False, unique=True, index=True
    )
    plan_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("subscription_plans.id"), nullable=False, index=True
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(
            SubscriptionStatus,
            name="subscriptionstatus",
            values_callable=lambda e: [m.value for m in e],
            native_enum=False,
        ),
        default=SubscriptionStatus.TRIAL,
    )
    billing_cycle: Mapped[BillingCycle] = mapped_column(
        Enum(
            BillingCycle,
            name="billingcycle",
            values_callable=lambda e: [m.value for m in e],
            native_enum=False,
        ),
        default=BillingCycle.MONTHLY,
    )
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False)
    # Préparation PSP (Stripe / CMI) — non branché
    payment_provider: Mapped[str] = mapped_column(String(32), default="manual")
    external_customer_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    external_subscription_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    cancel_reason_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    cancel_reason_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancel_requested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Usage à la demande (dépassement facturé) — style Cursor On-Demand
    on_demand_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    on_demand_mad_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)  # None/-1 = pas de plafond MAD
    # Add-ons : packs prépayés (solde) + sièges avocat extra (Cabinet)
    extra_avocat_seats: Mapped[int] = mapped_column(Integer, default=0)
    prepaid_ai_credits: Mapped[int] = mapped_column(Integer, default=0)


class BillingCreditPackPurchase(Base):
    """Lot de crédits IA prépayés — paiement séparé de l'abonnement / PAYG."""

    __tablename__ = "billing_credit_pack_purchases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cabinet_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cabinets.id"), nullable=False, index=True
    )
    pack_id: Mapped[str] = mapped_column(String(64), nullable=False)
    credits: Mapped[int] = mapped_column(Integer, nullable=False)
    credits_remaining: Mapped[int] = mapped_column(Integer, default=0)
    amount_mad: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price_mad: Mapped[float] = mapped_column(Float, nullable=False)
    # pending_payment | paid | expired | cancelled
    status: Mapped[str] = mapped_column(String(32), default="pending_payment")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payment_provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    card_last4: Mapped[str | None] = mapped_column(String(4), nullable=True)
    invoice_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True)


class SubscriptionEvent(Base):
    """Historique d'abonnement (essai, changement, résiliation…)."""

    __tablename__ = "subscription_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cabinet_id: Mapped[str] = mapped_column(String(36), ForeignKey("cabinets.id"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    plan_slug: Mapped[str | None] = mapped_column(String(64), nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True)


class BillingInvoice(Base):
    """Facture LexHub (génération locale — paiement réel phase 2)."""

    __tablename__ = "billing_invoices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cabinet_id: Mapped[str] = mapped_column(String(36), ForeignKey("cabinets.id"), nullable=False, index=True)
    number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    plan_slug: Mapped[str] = mapped_column(String(64), nullable=False)
    plan_name: Mapped[str] = mapped_column(String(120), nullable=False)
    amount_mad: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(8), default="MAD")
    billing_cycle: Mapped[str] = mapped_column(String(16), default="monthly")
    status: Mapped[str] = mapped_column(String(32), default="draft")
    period_label: Mapped[str | None] = mapped_column(String(64), nullable=True)
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    pdf_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class UsageCounter(Base):
    """Compteurs d'usage mensuels par cabinet (quotas)."""

    __tablename__ = "usage_counters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cabinet_id: Mapped[str] = mapped_column(String(36), ForeignKey("cabinets.id"), nullable=False, index=True)
    period_ym: Mapped[str] = mapped_column(String(7), nullable=False, index=True)  # YYYY-MM
    plaidoiries_count: Mapped[int] = mapped_column(Integer, default=0)
    cle_de_barre_count: Mapped[int] = mapped_column(Integer, default=0)
    synthesis_count: Mapped[int] = mapped_column(Integer, default=0)
    ai_credits_used: Mapped[int] = mapped_column(Integer, default=0)
    analyse_count: Mapped[int] = mapped_column(Integer, default=0)
    ask_count: Mapped[int] = mapped_column(Integer, default=0)
    revise_count: Mapped[int] = mapped_column(Integer, default=0)
    ai_overage_credits: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )



class PlaidoirieRevision(Base):
    """Historique des révisions d'une plaidoirie."""

    __tablename__ = "plaidoirie_revisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    draft_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("plaidoirie_drafts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cabinet_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    body_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class CaseComment(Base):
    """Fil de discussion interne sur un dossier."""

    __tablename__ = "case_comments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cabinet_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class PaymentTransferRequest(Base):
    """Demande de paiement par virement (ICE) — préparation CMI/PayZone."""

    __tablename__ = "payment_transfer_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cabinet_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    plan_slug: Mapped[str] = mapped_column(String(64), nullable=False)
    billing_cycle: Mapped[str] = mapped_column(String(20), nullable=False)
    amount_mad: Mapped[int] = mapped_column(Integer, nullable=False)
    reference: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)
    ice: Mapped[str | None] = mapped_column(String(40), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CabinetReferral(Base):
    """Parrainage cabinet → cabinet (récompense au 1er abonnement payant)."""

    __tablename__ = "cabinet_referrals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    referrer_cabinet_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    referee_cabinet_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)
    code_used: Mapped[str] = mapped_column(String(24), nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="pending")  # pending|bonus_applied|rewarded
    referee_bonus_days: Mapped[int] = mapped_column(Integer, default=14)
    referee_bonus_applied: Mapped[bool] = mapped_column(Boolean, default=False)
    referrer_reward_applied: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    qualified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CommercialLead(Base):
    """Demandes Entreprise / Sur mesure — qualification humaine avant essai large."""

    __tablename__ = "commercial_leads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    kind: Mapped[str] = mapped_column(String(32), nullable=False, index=True)  # enterprise_trial | custom
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    cabinet_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    lawyers_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(24), default="new", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
