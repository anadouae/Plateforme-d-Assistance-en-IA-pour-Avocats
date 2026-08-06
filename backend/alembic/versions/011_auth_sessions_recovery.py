"""Auth sessions + MFA recovery codes

Revision ID: 011
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = set(inspect(bind).get_table_names())

    if "auth_sessions" not in tables:
        op.create_table(
            "auth_sessions",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("refresh_token_hash", sa.String(length=64), nullable=False),
            sa.Column("user_agent", sa.String(length=255), nullable=True),
            sa.Column("ip_address", sa.String(length=45), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"])
        op.create_index(
            "ix_auth_sessions_refresh_token_hash",
            "auth_sessions",
            ["refresh_token_hash"],
            unique=True,
        )

    if "mfa_recovery_codes" not in tables:
        op.create_table(
            "mfa_recovery_codes",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("code_hash", sa.String(length=64), nullable=False),
            sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_mfa_recovery_codes_user_id", "mfa_recovery_codes", ["user_id"])
        op.create_index(
            "ix_mfa_recovery_codes_code_hash",
            "mfa_recovery_codes",
            ["code_hash"],
            unique=True,
        )


def downgrade() -> None:
    bind = op.get_bind()
    tables = set(inspect(bind).get_table_names())
    if "mfa_recovery_codes" in tables:
        op.drop_table("mfa_recovery_codes")
    if "auth_sessions" in tables:
        op.drop_table("auth_sessions")
