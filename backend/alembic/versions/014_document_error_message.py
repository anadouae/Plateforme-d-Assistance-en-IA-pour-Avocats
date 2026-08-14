"""Document error_message for failed processing (e.g. Whisper disabled)

Revision ID: 014
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "014"
down_revision: Union[str, None] = "013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    cols = {c["name"] for c in inspect(bind).get_columns("documents")}
    if "error_message" not in cols:
        op.add_column(
            "documents",
            sa.Column("error_message", sa.Text(), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    cols = {c["name"] for c in inspect(bind).get_columns("documents")}
    if "error_message" in cols:
        op.drop_column("documents", "error_message")
