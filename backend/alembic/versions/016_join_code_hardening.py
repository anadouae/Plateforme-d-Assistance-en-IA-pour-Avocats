"""Join code hardening: longer suffix, expiry, approval quota.

Revision ID: 016
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "016"
down_revision: Union[str, None] = "015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    cols = {c["name"] for c in inspect(bind).get_columns("cabinets")}
    if "join_code_expires_at" not in cols:
        op.add_column(
            "cabinets",
            sa.Column("join_code_expires_at", sa.DateTime(timezone=True), nullable=True),
        )
    if "join_code_approved_count" not in cols:
        op.add_column(
            "cabinets",
            sa.Column(
                "join_code_approved_count",
                sa.Integer(),
                nullable=False,
                server_default="0",
            ),
        )


def downgrade() -> None:
    bind = op.get_bind()
    cols = {c["name"] for c in inspect(bind).get_columns("cabinets")}
    if "join_code_approved_count" in cols:
        op.drop_column("cabinets", "join_code_approved_count")
    if "join_code_expires_at" in cols:
        op.drop_column("cabinets", "join_code_expires_at")
