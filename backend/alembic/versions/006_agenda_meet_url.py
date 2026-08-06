"""Add meet_url to agenda events

Revision ID: 006
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "agenda_events",
        sa.Column("meet_url", sa.String(500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("agenda_events", "meet_url")
