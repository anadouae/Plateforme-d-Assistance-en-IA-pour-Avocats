"""agenda events 48h reminder flag

Revision ID: 023
Revises: 022
Create Date: 2026-08-30
"""

from alembic import op
import sqlalchemy as sa

revision = "023"
down_revision = "022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "agenda_events",
        sa.Column("reminder_48h_sent_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("agenda_events", "reminder_48h_sent_at")
