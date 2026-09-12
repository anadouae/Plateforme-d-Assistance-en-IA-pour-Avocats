"""plea assign + pinned

Revision ID: 020
Revises: 019
Create Date: 2026-08-29
"""

from alembic import op
import sqlalchemy as sa

revision = "020"
down_revision = "019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "plaidoirie_drafts",
        sa.Column("assigned_to_user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
    )
    op.add_column(
        "plaidoirie_drafts",
        sa.Column("pinned", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_index(
        "ix_plaidoirie_drafts_assigned",
        "plaidoirie_drafts",
        ["assigned_to_user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_plaidoirie_drafts_assigned", table_name="plaidoirie_drafts")
    op.drop_column("plaidoirie_drafts", "pinned")
    op.drop_column("plaidoirie_drafts", "assigned_to_user_id")
