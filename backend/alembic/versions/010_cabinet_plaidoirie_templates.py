"""Cabinet custom plaidoirie templates

Revision ID: 010
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = set(inspect(bind).get_table_names())
    if "cabinet_plaidoirie_templates" in tables:
        return
    op.create_table(
        "cabinet_plaidoirie_templates",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("cabinet_id", sa.String(length=36), sa.ForeignKey("cabinets.id"), nullable=False),
        sa.Column("created_by", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("base_type", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_cabinet_plaidoirie_templates_cabinet_id",
        "cabinet_plaidoirie_templates",
        ["cabinet_id"],
    )


def downgrade() -> None:
    bind = op.get_bind()
    tables = set(inspect(bind).get_table_names())
    if "cabinet_plaidoirie_templates" not in tables:
        return
    op.drop_index(
        "ix_cabinet_plaidoirie_templates_cabinet_id",
        table_name="cabinet_plaidoirie_templates",
    )
    op.drop_table("cabinet_plaidoirie_templates")
