# -*- coding: utf-8 -*-
"""Drop unused legacy tables (dead product features).

Revision ID: 043
Revises: 042

Tables removed (0–1 rows in prod, no UI callers):
- case_notes
- membership_requests
- payment_transfer_requests
- commercial_leads
"""

from alembic import op


revision = "043"
down_revision = "042"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP TABLE IF EXISTS case_notes CASCADE")
    op.execute("DROP TABLE IF EXISTS membership_requests CASCADE")
    op.execute("DROP TABLE IF EXISTS payment_transfer_requests CASCADE")
    op.execute("DROP TABLE IF EXISTS commercial_leads CASCADE")
    # enum type for membership status if orphaned
    op.execute("DROP TYPE IF EXISTS membershiprequeststatus CASCADE")


def downgrade() -> None:
    # Intentionally empty: feature removed from product.
    pass
