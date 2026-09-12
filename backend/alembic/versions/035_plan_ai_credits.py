"""Add max_ai_credits_month on subscription_plans.

Revision ID: 035
Revises: 034
"""

from alembic import op
import sqlalchemy as sa

revision = "035"
down_revision = "034"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "subscription_plans",
        sa.Column("max_ai_credits_month", sa.Integer(), nullable=False, server_default="50"),
    )
    conn = op.get_bind()
    defaults = {"free": 50, "solo": 600, "pro": 2000, "enterprise": 5000}
    for slug, credits in defaults.items():
        conn.execute(
            sa.text("UPDATE subscription_plans SET max_ai_credits_month = :c WHERE slug = :s"),
            {"c": credits, "s": slug},
        )


def downgrade() -> None:
    op.drop_column("subscription_plans", "max_ai_credits_month")
