"""Commercial leads (essai Entreprise + Sur mesure).

Revision ID: 038
Revises: 037
"""

from alembic import op
import sqlalchemy as sa

revision = "038"
down_revision = "037"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "commercial_leads",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=40), nullable=True),
        sa.Column("cabinet_name", sa.String(length=255), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("lawyers_count", sa.Integer(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="new"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_commercial_leads_kind", "commercial_leads", ["kind"])
    op.create_index("ix_commercial_leads_email", "commercial_leads", ["email"])


def downgrade() -> None:
    op.drop_index("ix_commercial_leads_email", table_name="commercial_leads")
    op.drop_index("ix_commercial_leads_kind", table_name="commercial_leads")
    op.drop_table("commercial_leads")
