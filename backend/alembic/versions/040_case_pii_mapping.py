"""Add cases.pii_mapping_json (persisted PII token mapping).

Revision ID: 040
Revises: 039
"""

from alembic import op
import sqlalchemy as sa


revision = "040"
down_revision = "039"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "cases",
        sa.Column("pii_mapping_json", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("cases", "pii_mapping_json")
