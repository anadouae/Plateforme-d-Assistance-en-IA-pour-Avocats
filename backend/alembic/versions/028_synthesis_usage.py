"""Usage counters: synthesis IA mensuelle

Revision ID: 028
Revises: 027
Create Date: 2026-09-01
"""

from alembic import op
import sqlalchemy as sa

revision = "028"
down_revision = "027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "usage_counters",
        sa.Column("synthesis_count", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("usage_counters", "synthesis_count")
