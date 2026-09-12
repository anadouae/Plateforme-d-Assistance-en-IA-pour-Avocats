"""Usage counters: AI credits + analyse/ask/revise

Revision ID: 032
Revises: 031
Create Date: 2026-09-05
"""

from alembic import op
import sqlalchemy as sa

revision = "032"
down_revision = "031"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "usage_counters",
        sa.Column("ai_credits_used", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "usage_counters",
        sa.Column("analyse_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "usage_counters",
        sa.Column("ask_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "usage_counters",
        sa.Column("revise_count", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("usage_counters", "revise_count")
    op.drop_column("usage_counters", "ask_count")
    op.drop_column("usage_counters", "analyse_count")
    op.drop_column("usage_counters", "ai_credits_used")
