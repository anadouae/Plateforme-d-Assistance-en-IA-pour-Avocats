"""Add users.has_seen_onboarding_tour for first-login product tour.

Revision ID: 015
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "015"
down_revision: Union[str, None] = "014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    cols = {c["name"] for c in inspect(bind).get_columns("users")}
    if "has_seen_onboarding_tour" not in cols:
        op.add_column(
            "users",
            sa.Column(
                "has_seen_onboarding_tour",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
        )
        # Comptes déjà actifs : ne pas forcer le tour après déploiement.
        op.execute("UPDATE users SET has_seen_onboarding_tour = true")


def downgrade() -> None:
    bind = op.get_bind()
    cols = {c["name"] for c in inspect(bind).get_columns("users")}
    if "has_seen_onboarding_tour" in cols:
        op.drop_column("users", "has_seen_onboarding_tour")
