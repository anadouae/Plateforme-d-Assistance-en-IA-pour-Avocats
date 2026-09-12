"""Dossier judiciaire vivant: RG, greffe, décisions, bordereau, collab, rappels multi-J."""

from alembic import op
import sqlalchemy as sa

revision = "031"
down_revision = "030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # —— Cases: cerveau du dossier ——
    op.add_column("cases", sa.Column("court_file_number", sa.String(80), nullable=True))
    op.add_column("cases", sa.Column("judge_name", sa.String(120), nullable=True))
    op.add_column("cases", sa.Column("chamber", sa.String(120), nullable=True))
    op.add_column("cases", sa.Column("greffe", sa.String(120), nullable=True))
    op.add_column("cases", sa.Column("procedure_status", sa.String(40), nullable=True))
    op.add_column("cases", sa.Column("assistant_id", sa.String(36), nullable=True))
    op.add_column("cases", sa.Column("last_decision_type", sa.String(80), nullable=True))
    op.add_column("cases", sa.Column("last_decision_date", sa.DateTime(timezone=True), nullable=True))
    op.add_column("cases", sa.Column("notification_date", sa.DateTime(timezone=True), nullable=True))
    op.add_column("cases", sa.Column("appeal_deadline_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("cases", sa.Column("appeal_deadline_days", sa.Integer(), nullable=True))

    # —— Documents: bordereau ——
    op.add_column("documents", sa.Column("inventory_number", sa.Integer(), nullable=True))
    op.add_column("documents", sa.Column("exhibit_type", sa.String(60), nullable=True))
    op.add_column("documents", sa.Column("produced_by", sa.String(40), nullable=True))
    op.add_column("documents", sa.Column("exhibit_version", sa.String(40), nullable=True))
    op.add_column("documents", sa.Column("cited_in_plea", sa.String(255), nullable=True))

    # —— Plaidoirie drafts: confiance + versions ——
    op.add_column("plaidoirie_drafts", sa.Column("output_mode", sa.String(20), nullable=True))
    op.add_column("plaidoirie_drafts", sa.Column("citations_json", sa.Text(), nullable=True))
    op.add_column("plaidoirie_drafts", sa.Column("sources_json", sa.Text(), nullable=True))
    op.add_column("plaidoirie_drafts", sa.Column("validated_by", sa.String(36), nullable=True))
    op.add_column("plaidoirie_drafts", sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("plaidoirie_drafts", sa.Column("read_by_json", sa.Text(), nullable=True))

    # —— Agenda: rappels multi-jours ——
    op.add_column("agenda_events", sa.Column("reminder_7d_sent_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("agenda_events", sa.Column("reminder_2d_sent_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("agenda_events", sa.Column("reminder_1d_sent_at", sa.DateTime(timezone=True), nullable=True))

    # —— Case tasks: assignee ——
    op.add_column("case_tasks", sa.Column("assignee_id", sa.String(36), nullable=True))

    # —— Révisions plaidoirie ——
    op.create_table(
        "plaidoirie_revisions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("draft_id", sa.String(36), sa.ForeignKey("plaidoirie_drafts.id"), nullable=False, index=True),
        sa.Column("cabinet_id", sa.String(36), nullable=False, index=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("body_snapshot", sa.Text(), nullable=False),
        sa.Column("note", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # —— Commentaires dossier ——
    op.create_table(
        "case_comments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("cabinet_id", sa.String(36), nullable=False, index=True),
        sa.Column("case_id", sa.String(36), sa.ForeignKey("cases.id"), nullable=False, index=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # —— Demandes de paiement virement (préparation CMI) ——
    op.create_table(
        "payment_transfer_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("cabinet_id", sa.String(36), nullable=False, index=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("plan_slug", sa.String(64), nullable=False),
        sa.Column("billing_cycle", sa.String(20), nullable=False),
        sa.Column("amount_mad", sa.Integer(), nullable=False),
        sa.Column("reference", sa.String(64), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("ice", sa.String(40), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("payment_transfer_requests")
    op.drop_table("case_comments")
    op.drop_table("plaidoirie_revisions")
    op.drop_column("case_tasks", "assignee_id")
    for col in ("reminder_7d_sent_at", "reminder_2d_sent_at", "reminder_1d_sent_at"):
        op.drop_column("agenda_events", col)
    for col in (
        "output_mode",
        "citations_json",
        "sources_json",
        "validated_by",
        "validated_at",
        "read_by_json",
    ):
        op.drop_column("plaidoirie_drafts", col)
    for col in (
        "inventory_number",
        "exhibit_type",
        "produced_by",
        "exhibit_version",
        "cited_in_plea",
    ):
        op.drop_column("documents", col)
    for col in (
        "court_file_number",
        "judge_name",
        "chamber",
        "greffe",
        "procedure_status",
        "assistant_id",
        "last_decision_type",
        "last_decision_date",
        "notification_date",
        "appeal_deadline_at",
        "appeal_deadline_days",
    ):
        op.drop_column("cases", col)
