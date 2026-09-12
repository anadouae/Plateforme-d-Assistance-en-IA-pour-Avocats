"""Prepaid AI credit packs + extra avocat seats on Cabinet.

Revision ID: 036
Revises: 035
"""

from alembic import op
import sqlalchemy as sa

revision = "036"
down_revision = "035"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "cabinet_subscriptions",
        sa.Column("extra_avocat_seats", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "cabinet_subscriptions",
        sa.Column("prepaid_ai_credits", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_table(
        "billing_credit_pack_purchases",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("cabinet_id", sa.String(36), sa.ForeignKey("cabinets.id"), nullable=False, index=True),
        sa.Column("pack_id", sa.String(64), nullable=False),
        sa.Column("credits", sa.Integer(), nullable=False),
        sa.Column("amount_mad", sa.Integer(), nullable=False),
        sa.Column("unit_price_mad", sa.Float(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="paid_mock"),
        sa.Column("invoice_id", sa.String(36), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("created_by", sa.String(36), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("billing_credit_pack_purchases")
    op.drop_column("cabinet_subscriptions", "prepaid_ai_credits")
    op.drop_column("cabinet_subscriptions", "extra_avocat_seats")
