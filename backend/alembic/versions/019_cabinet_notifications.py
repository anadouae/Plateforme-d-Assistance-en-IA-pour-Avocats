"""cabinet notifications for assistants

Revision ID: 019
Revises: 018
Create Date: 2026-08-29
"""

from alembic import op
import sqlalchemy as sa

revision = "019"
down_revision = "018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cabinet_notifications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("cabinet_id", sa.String(36), sa.ForeignKey("cabinets.id"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("role_target", sa.String(40), nullable=True),
        sa.Column("type", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("href", sa.String(255), nullable=True),
        sa.Column("payload_json", sa.Text(), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_cabinet_notifications_cabinet", "cabinet_notifications", ["cabinet_id"])
    op.create_index("ix_cabinet_notifications_user", "cabinet_notifications", ["user_id"])
    op.create_index("ix_cabinet_notifications_created", "cabinet_notifications", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_cabinet_notifications_created", table_name="cabinet_notifications")
    op.drop_index("ix_cabinet_notifications_user", table_name="cabinet_notifications")
    op.drop_index("ix_cabinet_notifications_cabinet", table_name="cabinet_notifications")
    op.drop_table("cabinet_notifications")
