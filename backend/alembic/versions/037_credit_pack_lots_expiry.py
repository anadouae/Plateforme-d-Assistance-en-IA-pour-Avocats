"""Credit pack lots: remaining, expiry, pending payment.

Revision ID: 037
Revises: 036
"""

from alembic import op
import sqlalchemy as sa

revision = "037"
down_revision = "036"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "billing_credit_pack_purchases",
        sa.Column("credits_remaining", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "billing_credit_pack_purchases",
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "billing_credit_pack_purchases",
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "billing_credit_pack_purchases",
        sa.Column("payment_provider", sa.String(64), nullable=True),
    )
    op.add_column(
        "billing_credit_pack_purchases",
        sa.Column("card_last4", sa.String(4), nullable=True),
    )
    # Migrate existing paid rows → remaining = credits, expire +12m from created_at
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            UPDATE billing_credit_pack_purchases
            SET credits_remaining = credits,
                paid_at = COALESCE(paid_at, created_at),
                expires_at = COALESCE(expires_at, created_at + INTERVAL '12 months'),
                status = CASE
                    WHEN status IN ('paid_mock', 'paid') THEN 'paid'
                    ELSE status
                END
            WHERE status IN ('paid_mock', 'paid')
            """
        )
    )


def downgrade() -> None:
    op.drop_column("billing_credit_pack_purchases", "card_last4")
    op.drop_column("billing_credit_pack_purchases", "payment_provider")
    op.drop_column("billing_credit_pack_purchases", "paid_at")
    op.drop_column("billing_credit_pack_purchases", "expires_at")
    op.drop_column("billing_credit_pack_purchases", "credits_remaining")
