"""Billing: subscription plans, cabinet subscriptions, usage counters

Revision ID: 026
Revises: 025
Create Date: 2026-08-31
"""

from alembic import op
import sqlalchemy as sa

revision = "026"
down_revision = "025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "subscription_plans",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("slug", sa.String(64), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("name_ar", sa.String(120), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price_mad_monthly", sa.Integer(), server_default="0", nullable=False),
        sa.Column("price_mad_yearly", sa.Integer(), server_default="0", nullable=False),
        sa.Column("max_avocats", sa.Integer(), server_default="1", nullable=False),
        sa.Column("max_assistants", sa.Integer(), server_default="0", nullable=False),
        sa.Column("max_cases", sa.Integer(), server_default="3", nullable=False),
        sa.Column("max_plaidoiries_month", sa.Integer(), server_default="5", nullable=False),
        sa.Column("features_json", sa.Text(), nullable=True),
        sa.Column("is_public", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("is_recommended", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="100", nullable=False),
        sa.Column("trial_days", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_subscription_plans_slug", "subscription_plans", ["slug"], unique=True)

    op.create_table(
        "cabinet_subscriptions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("cabinet_id", sa.String(36), sa.ForeignKey("cabinets.id"), nullable=False),
        sa.Column("plan_id", sa.String(36), sa.ForeignKey("subscription_plans.id"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="trial"),
        sa.Column("billing_cycle", sa.String(16), nullable=False, server_default="monthly"),
        sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_at_period_end", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("payment_provider", sa.String(32), server_default="manual", nullable=False),
        sa.Column("external_customer_id", sa.String(128), nullable=True),
        sa.Column("external_subscription_id", sa.String(128), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_cabinet_subscriptions_cabinet_id", "cabinet_subscriptions", ["cabinet_id"], unique=True)
    op.create_index("ix_cabinet_subscriptions_plan_id", "cabinet_subscriptions", ["plan_id"])

    op.create_table(
        "usage_counters",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("cabinet_id", sa.String(36), sa.ForeignKey("cabinets.id"), nullable=False),
        sa.Column("period_ym", sa.String(7), nullable=False),
        sa.Column("plaidoiries_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("cle_de_barre_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_usage_counters_cabinet_id", "usage_counters", ["cabinet_id"])
    op.create_index("ix_usage_counters_period_ym", "usage_counters", ["period_ym"])
    op.create_index(
        "ix_usage_counters_cabinet_period",
        "usage_counters",
        ["cabinet_id", "period_ym"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("usage_counters")
    op.drop_table("cabinet_subscriptions")
    op.drop_table("subscription_plans")
