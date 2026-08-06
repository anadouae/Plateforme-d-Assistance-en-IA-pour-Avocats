"""Add case notes, tasks and agenda events

Revision ID: 005
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "case_notes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("cabinet_id", sa.String(36), sa.ForeignKey("cabinets.id"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("case_id", sa.String(36), sa.ForeignKey("cases.id"), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_case_notes_cabinet_id", "case_notes", ["cabinet_id"])
    op.create_index("ix_case_notes_case_id", "case_notes", ["case_id"])

    op.create_table(
        "case_tasks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("cabinet_id", sa.String(36), sa.ForeignKey("cabinets.id"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("case_id", sa.String(36), sa.ForeignKey("cases.id"), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="todo"),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_case_tasks_cabinet_id", "case_tasks", ["cabinet_id"])
    op.create_index("ix_case_tasks_case_id", "case_tasks", ["case_id"])
    op.create_index("ix_case_tasks_due_at", "case_tasks", ["due_at"])

    op.create_table(
        "agenda_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("cabinet_id", sa.String(36), sa.ForeignKey("cabinets.id"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("case_id", sa.String(36), sa.ForeignKey("cases.id"), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("event_type", sa.String(30), nullable=False, server_default="other"),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_agenda_events_cabinet_id", "agenda_events", ["cabinet_id"])
    op.create_index("ix_agenda_events_case_id", "agenda_events", ["case_id"])
    op.create_index("ix_agenda_events_starts_at", "agenda_events", ["starts_at"])


def downgrade() -> None:
    op.drop_table("agenda_events")
    op.drop_table("case_tasks")
    op.drop_table("case_notes")
