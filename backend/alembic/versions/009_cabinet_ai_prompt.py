"""Ensure cabinets.ai_custom_prompt exists

Revision ID: 009
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    cols = {c["name"] for c in inspect(bind).get_columns("cabinets")}
    if "ai_custom_prompt" not in cols:
        op.add_column("cabinets", sa.Column("ai_custom_prompt", sa.Text(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    cols = {c["name"] for c in inspect(bind).get_columns("cabinets")}
    if "ai_custom_prompt" in cols:
        op.drop_column("cabinets", "ai_custom_prompt")
