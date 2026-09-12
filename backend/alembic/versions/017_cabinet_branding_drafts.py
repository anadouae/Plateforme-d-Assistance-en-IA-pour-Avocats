"""Cabinet branding (logo, name_ar) + plaidoirie drafts history."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "017"
down_revision = "016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("cabinets", sa.Column("logo_path", sa.String(512), nullable=True))
    op.add_column("cabinets", sa.Column("name_ar", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("full_name_ar", sa.String(255), nullable=True))

    op.create_table(
        "plaidoirie_drafts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("cabinet_id", sa.String(36), sa.ForeignKey("cabinets.id"), nullable=False, index=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("case_id", sa.String(36), sa.ForeignKey("cases.id"), nullable=True, index=True),
        sa.Column("title", sa.String(512), nullable=False, server_default=""),
        sa.Column("body", sa.Text(), nullable=False, server_default=""),
        sa.Column("template_id", sa.String(64), nullable=True),
        sa.Column("checks_json", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("plaidoirie_drafts")
    op.drop_column("users", "full_name_ar")
    op.drop_column("cabinets", "name_ar")
    op.drop_column("cabinets", "logo_path")
