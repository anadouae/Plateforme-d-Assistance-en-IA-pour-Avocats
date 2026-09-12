"""Cabinet referral / parrainage

Revision ID: 034
Revises: 033
Create Date: 2026-09-05
"""

from alembic import op
import sqlalchemy as sa

revision = "034"
down_revision = "033"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "cabinets",
        sa.Column("referral_code", sa.String(24), nullable=True),
    )
    op.create_index("ix_cabinets_referral_code", "cabinets", ["referral_code"], unique=True)
    op.add_column(
        "cabinets",
        sa.Column("referred_by_cabinet_id", sa.String(36), nullable=True),
    )

    op.create_table(
        "cabinet_referrals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("referrer_cabinet_id", sa.String(36), nullable=False, index=True),
        sa.Column("referee_cabinet_id", sa.String(36), nullable=False, index=True),
        sa.Column("code_used", sa.String(24), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="pending"),
        sa.Column("referee_bonus_days", sa.Integer(), nullable=False, server_default="14"),
        sa.Column("referee_bonus_applied", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("referrer_reward_applied", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("qualified_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("referee_cabinet_id", name="uq_referral_referee"),
    )


def downgrade() -> None:
    op.drop_table("cabinet_referrals")
    op.drop_index("ix_cabinets_referral_code", table_name="cabinets")
    op.drop_column("cabinets", "referred_by_cabinet_id")
    op.drop_column("cabinets", "referral_code")
