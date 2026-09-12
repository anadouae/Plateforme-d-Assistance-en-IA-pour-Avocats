"""cabinet personal invites (one-person-one-code)

Revision ID: 022
Revises: 021
Create Date: 2026-08-29
"""

from alembic import op
import sqlalchemy as sa

revision = "022"
down_revision = "021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cabinet_invites",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("cabinet_id", sa.String(36), sa.ForeignKey("cabinets.id"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_cabinet_invites_code", "cabinet_invites", ["code"], unique=True)
    op.create_index("ix_cabinet_invites_cabinet_id", "cabinet_invites", ["cabinet_id"])


def downgrade() -> None:
    op.drop_index("ix_cabinet_invites_cabinet_id", table_name="cabinet_invites")
    op.drop_index("ix_cabinet_invites_code", table_name="cabinet_invites")
    op.drop_table("cabinet_invites")
