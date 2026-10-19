"""Add users.must_set_password + nullable hashed_password (frictionless signup).

Revision ID: 041
Revises: 040
"""

from alembic import op
import sqlalchemy as sa


revision = "041"
down_revision = "040"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("must_set_password", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column(
        "users",
        "hashed_password",
        existing_type=sa.String(255),
        nullable=True,
    )


def downgrade() -> None:
    op.execute(
        "UPDATE users SET hashed_password = '!' WHERE hashed_password IS NULL"
    )
    op.alter_column(
        "users",
        "hashed_password",
        existing_type=sa.String(255),
        nullable=False,
    )
    op.drop_column("users", "must_set_password")
