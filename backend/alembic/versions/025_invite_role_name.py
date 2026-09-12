"""cabinet_invites: role + recipient_name for admin email invites

Revision ID: 025_invite_role_name
Revises: 024_admin_audit_archives
Create Date: 2026-08-31
"""

from alembic import op
import sqlalchemy as sa

revision = "025"
down_revision = "024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "cabinet_invites",
        sa.Column("role", sa.String(32), nullable=False, server_default="avocat"),
    )
    op.add_column(
        "cabinet_invites",
        sa.Column("recipient_name", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("cabinet_invites", "recipient_name")
    op.drop_column("cabinet_invites", "role")
