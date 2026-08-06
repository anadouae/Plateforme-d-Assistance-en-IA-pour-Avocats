"""Chat sessions, summary persistence, cabinet AI prompt

Revision ID: 003
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("cabinets", sa.Column("ai_custom_prompt", sa.Text(), nullable=True))

    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("cabinet_id", sa.String(36), sa.ForeignKey("cabinets.id"), nullable=False),
        sa.Column("case_id", sa.String(36), sa.ForeignKey("cases.id"), nullable=True),
        sa.Column("title", sa.String(255), nullable=False, server_default="Nouvelle conversation"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_chat_sessions_user_id", "chat_sessions", ["user_id"])

    op.add_column("chat_messages", sa.Column("session_id", sa.String(36), nullable=True))
    op.add_column("chat_messages", sa.Column("summary", sa.Text(), nullable=True))
    op.create_foreign_key(
        "fk_chat_messages_session_id",
        "chat_messages",
        "chat_sessions",
        ["session_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_chat_messages_session_id", "chat_messages", type_="foreignkey")
    op.drop_column("chat_messages", "summary")
    op.drop_column("chat_messages", "session_id")
    op.drop_index("ix_chat_sessions_user_id", table_name="chat_sessions")
    op.drop_table("chat_sessions")
    op.drop_column("cabinets", "ai_custom_prompt")
