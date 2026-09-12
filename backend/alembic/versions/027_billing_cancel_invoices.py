"""Billing UX: cancel reason, subscription events, invoices

Revision ID: 027
Revises: 026
Create Date: 2026-08-31
"""

from alembic import op
import sqlalchemy as sa

revision = "027"
down_revision = "026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "cabinet_subscriptions",
        sa.Column("cancel_reason_code", sa.String(64), nullable=True),
    )
    op.add_column(
        "cabinet_subscriptions",
        sa.Column("cancel_reason_text", sa.Text(), nullable=True),
    )
    op.add_column(
        "cabinet_subscriptions",
        sa.Column("cancel_requested_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "subscription_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("cabinet_id", sa.String(36), sa.ForeignKey("cabinets.id"), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("plan_slug", sa.String(64), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(36), nullable=True),
    )
    op.create_index("ix_subscription_events_cabinet_id", "subscription_events", ["cabinet_id"])

    op.create_table(
        "billing_invoices",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("cabinet_id", sa.String(36), sa.ForeignKey("cabinets.id"), nullable=False),
        sa.Column("number", sa.String(32), nullable=False),
        sa.Column("plan_slug", sa.String(64), nullable=False),
        sa.Column("plan_name", sa.String(120), nullable=False),
        sa.Column("amount_mad", sa.Integer(), server_default="0", nullable=False),
        sa.Column("currency", sa.String(8), server_default="MAD", nullable=False),
        sa.Column("billing_cycle", sa.String(16), server_default="monthly", nullable=False),
        sa.Column("status", sa.String(32), server_default="draft", nullable=False),
        sa.Column("period_label", sa.String(64), nullable=True),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("pdf_html", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_billing_invoices_cabinet_id", "billing_invoices", ["cabinet_id"])
    op.create_index("ix_billing_invoices_number", "billing_invoices", ["number"], unique=True)


def downgrade() -> None:
    op.drop_table("billing_invoices")
    op.drop_table("subscription_events")
    op.drop_column("cabinet_subscriptions", "cancel_requested_at")
    op.drop_column("cabinet_subscriptions", "cancel_reason_text")
    op.drop_column("cabinet_subscriptions", "cancel_reason_code")
