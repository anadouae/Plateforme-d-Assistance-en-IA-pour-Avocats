"""Ensure workspace tables exist (case_tasks, agenda_events)

Revision ID: 008
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())

    if "case_tasks" not in tables:
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

    if "agenda_events" not in tables:
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
            sa.Column("meet_url", sa.String(500), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_agenda_events_cabinet_id", "agenda_events", ["cabinet_id"])
        op.create_index("ix_agenda_events_case_id", "agenda_events", ["case_id"])
        op.create_index("ix_agenda_events_starts_at", "agenda_events", ["starts_at"])
    else:
        cols = {c["name"] for c in inspector.get_columns("agenda_events")}
        if "meet_url" not in cols:
            op.add_column(
                "agenda_events",
                sa.Column("meet_url", sa.String(500), nullable=True),
            )


def downgrade() -> None:
    pass
