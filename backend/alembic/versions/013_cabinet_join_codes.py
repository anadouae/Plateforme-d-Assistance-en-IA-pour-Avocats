"""Cabinet join codes + membership requests

Revision ID: 013
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect, text

revision: str = "013"
down_revision: Union[str, None] = "012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _gen_code(prefix: str) -> str:
    import secrets

    clean = "".join(c for c in (prefix or "SANAD").upper() if c in _ALPHABET) or "SANAD"
    head = clean[:5]
    tail = "".join(secrets.choice(_ALPHABET) for _ in range(4))
    return f"{head}-{tail}"


def upgrade() -> None:
    bind = op.get_bind()
    cols = {c["name"] for c in inspect(bind).get_columns("cabinets")}
    if "join_code" not in cols:
        op.add_column("cabinets", sa.Column("join_code", sa.String(length=32), nullable=True))
        op.add_column(
            "cabinets",
            sa.Column("join_code_regenerated_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_cabinets_join_code", "cabinets", ["join_code"], unique=True)

    tables = set(inspect(bind).get_table_names())
    if "membership_requests" not in tables:
        op.create_table(
            "membership_requests",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("cabinet_id", sa.String(length=36), sa.ForeignKey("cabinets.id"), nullable=False),
            sa.Column("full_name", sa.String(length=255), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("hashed_password", sa.String(length=255), nullable=False),
            sa.Column(
                "status",
                sa.Enum("pending", "approved", "rejected", name="membershiprequeststatus"),
                nullable=False,
            ),
            sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("resolved_by", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        )
        op.create_index("ix_membership_requests_email", "membership_requests", ["email"])

    # Backfill codes for existing cabinets
    rows = bind.execute(text("SELECT id, name FROM cabinets WHERE join_code IS NULL")).fetchall()
    used: set[str] = set()
    existing = bind.execute(
        text("SELECT join_code FROM cabinets WHERE join_code IS NOT NULL")
    ).fetchall()
    used.update(r[0] for r in existing if r[0])
    for cab_id, name in rows:
        for _ in range(30):
            code = _gen_code(name or "SANAD")
            if code not in used:
                used.add(code)
                bind.execute(
                    text(
                        "UPDATE cabinets SET join_code = :c, "
                        "join_code_regenerated_at = NOW() WHERE id = :id"
                    ),
                    {"c": code, "id": cab_id},
                )
                break


def downgrade() -> None:
    bind = op.get_bind()
    tables = set(inspect(bind).get_table_names())
    if "membership_requests" in tables:
        op.drop_table("membership_requests")
        sa.Enum(name="membershiprequeststatus").drop(bind, checkfirst=True)
    cols = {c["name"] for c in inspect(bind).get_columns("cabinets")}
    if "join_code" in cols:
        op.drop_index("ix_cabinets_join_code", table_name="cabinets")
        op.drop_column("cabinets", "join_code_regenerated_at")
        op.drop_column("cabinets", "join_code")
