"""Patch models __init__.py for dossier judiciaire vivant."""
from pathlib import Path

p = Path(r"C:\Users\daurinia\Desktop\Avocat-AI-Assistance\backend\app\models\__init__.py")
t = p.read_text(encoding="utf-8")

# Case fields after opposing_domicile
needle = """    opposing_domicile: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cabinet_id: Mapped[str] = mapped_column(String(36), ForeignKey("cabinets.id"), nullable=False)
    responsible_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)"""
insert = """    opposing_domicile: Mapped[str | None] = mapped_column(String(255), nullable=True)
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
    responsible_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)"""
if "court_file_number" not in t:
    if "Integer" not in t.split("from sqlalchemy")[1][:400]:
        t = t.replace(
            "from sqlalchemy import (",
            "from sqlalchemy import (\n    Integer,",
            1,
        ) if "from sqlalchemy import (" in t else t
    # Check Integer import
    if "Integer" not in t[:500]:
        for imp in ("Boolean,", "DateTime,", "Enum,", "ForeignKey,", "String,", "Text,"):
            if imp in t:
                t = t.replace(imp, f"Integer, {imp}", 1)
                break
    t = t.replace(needle, insert, 1)

# AgendaEventType expand
old_types = '''class AgendaEventType(str, enum.Enum):
    AUDIENCE = "audience"
    DEADLINE = "deadline"
    RDV = "rdv"
    OTHER = "other"'''
new_types = '''class AgendaEventType(str, enum.Enum):
    AUDIENCE = "audience"
    DEADLINE = "deadline"
    RDV = "rdv"
    NOTIFICATION = "notification"
    RECOURS = "recours"
    EXPERTISE = "expertise"
    MEDIATION = "mediation"
    OTHER = "other"'''
if "NOTIFICATION" not in t:
    t = t.replace(old_types, new_types, 1)

# Agenda reminders multi
if "reminder_7d_sent_at" not in t:
    t = t.replace(
        "    reminder_48h_sent_at: Mapped[datetime | None] = mapped_column(",
        """    reminder_7d_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reminder_2d_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reminder_1d_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reminder_48h_sent_at: Mapped[datetime | None] = mapped_column(""",
        1,
    )

# Document bordereau — find Document class uploaded_by or created_at
if "inventory_number" not in t:
    t = t.replace(
        "    uploaded_by: Mapped[str | None] = mapped_column(String(36), ForeignKey(\"users.id\"), nullable=True)",
        """    uploaded_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    inventory_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    exhibit_type: Mapped[str | None] = mapped_column(String(60), nullable=True)
    produced_by: Mapped[str | None] = mapped_column(String(40), nullable=True)
    exhibit_version: Mapped[str | None] = mapped_column(String(40), nullable=True)
    cited_in_plea: Mapped[str | None] = mapped_column(String(255), nullable=True)""",
        1,
    )

# CaseTask assignee
if "assignee_id" not in t or "case_tasks" in t and "assignee_id" not in t[t.find("class CaseTask"):t.find("class CaseTask")+800]:
    chunk_start = t.find("class CaseTask")
    if chunk_start > 0 and "assignee_id" not in t[chunk_start:chunk_start+600]:
        t = t.replace(
            "    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)\n    created_at: Mapped[datetime] = mapped_column(\n        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)\n    )\n    updated_at: Mapped[datetime] = mapped_column(\n        DateTime(timezone=True),\n        default=lambda: datetime.now(timezone.utc),\n        onupdate=lambda: datetime.now(timezone.utc),\n    )\n\n    case: Mapped[\"Case | None\"] = relationship(back_populates=\"tasks\")",
            """    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    assignee_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    case: Mapped["Case | None"] = relationship(back_populates="tasks")""",
            1,
        )

# PlaidoirieDraft fields
if "citations_json" not in t:
    # find PlaidoirieDraft status or checks_json
    t = t.replace(
        "    checks_json: Mapped[str | None] = mapped_column(Text, nullable=True)",
        """    checks_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_mode: Mapped[str | None] = mapped_column(String(20), nullable=True)  # orale | ecrite
    citations_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    sources_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    validated_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    read_by_json: Mapped[str | None] = mapped_column(Text, nullable=True)""",
        1,
    )

# New models at end before last line
if "class CaseComment" not in t:
    t += '''


class PlaidoirieRevision(Base):
    """Historique des révisions d'une plaidoirie."""

    __tablename__ = "plaidoirie_revisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    draft_id: Mapped[str] = mapped_column(String(36), ForeignKey("plaidoirie_drafts.id"), nullable=False, index=True)
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
'''

tmp = p.with_suffix(".py.tmp")
tmp.write_text(t, encoding="utf-8")
tmp.replace(p)
print("models patched", "court_file_number" in t, "CaseComment" in t)
