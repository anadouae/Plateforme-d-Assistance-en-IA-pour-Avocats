"""case legal identity fields (jurisdiction, tribunal, parties)

Revision ID: 029
Revises: 028
"""

from alembic import op
import sqlalchemy as sa

revision = "029"
down_revision = "028"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("cases", sa.Column("jurisdiction_degree", sa.String(32), nullable=True))
    op.add_column("cases", sa.Column("tribunal", sa.String(120), nullable=True))
    op.add_column("cases", sa.Column("client_role", sa.String(40), nullable=True))
    op.add_column("cases", sa.Column("client_quality", sa.String(120), nullable=True))
    op.add_column("cases", sa.Column("client_domicile", sa.String(255), nullable=True))
    op.add_column("cases", sa.Column("opposing_name", sa.String(255), nullable=True))
    op.add_column("cases", sa.Column("opposing_role", sa.String(40), nullable=True))
    op.add_column("cases", sa.Column("opposing_quality", sa.String(120), nullable=True))
    op.add_column("cases", sa.Column("opposing_domicile", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("cases", "opposing_domicile")
    op.drop_column("cases", "opposing_quality")
    op.drop_column("cases", "opposing_role")
    op.drop_column("cases", "opposing_name")
    op.drop_column("cases", "client_domicile")
    op.drop_column("cases", "client_quality")
    op.drop_column("cases", "client_role")
    op.drop_column("cases", "tribunal")
    op.drop_column("cases", "jurisdiction_degree")
