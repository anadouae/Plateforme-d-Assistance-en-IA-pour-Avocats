"""plaidoirie drafts: status draft|validated

Revision ID: 018
Revises: 017
Create Date: 2026-08-29
"""

from alembic import op
import sqlalchemy as sa

revision = "018"
down_revision = "017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "plaidoirie_drafts",
        sa.Column(
            "status",
            sa.String(16),
            nullable=False,
            server_default="draft",
        ),
    )
    op.create_index("ix_plaidoirie_drafts_status", "plaidoirie_drafts", ["status"])


def downgrade() -> None:
    op.drop_index("ix_plaidoirie_drafts_status", table_name="plaidoirie_drafts")
    op.drop_column("plaidoirie_drafts", "status")
