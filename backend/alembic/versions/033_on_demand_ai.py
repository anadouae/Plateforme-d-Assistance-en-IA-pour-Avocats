"""On-demand IA spending + overage credits

Revision ID: 033
Revises: 032
Create Date: 2026-09-05
"""

from alembic import op
import sqlalchemy as sa

revision = "033"
down_revision = "032"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "cabinet_subscriptions",
        sa.Column("on_demand_enabled", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "cabinet_subscriptions",
        sa.Column("on_demand_mad_limit", sa.Integer(), nullable=True),
    )
    op.add_column(
        "usage_counters",
        sa.Column("ai_overage_credits", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("usage_counters", "ai_overage_credits")
    op.drop_column("cabinet_subscriptions", "on_demand_mad_limit")
    op.drop_column("cabinet_subscriptions", "on_demand_enabled")
