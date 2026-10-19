"""Add cases.title (intitulé métier du dossier).

Revision ID: 039
Revises: 038
"""

from alembic import op
import sqlalchemy as sa

revision = "039"
down_revision = "038"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "cases",
        sa.Column("title", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("cases", "title")
