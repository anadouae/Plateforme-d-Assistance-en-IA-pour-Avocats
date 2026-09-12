"""Add hearing city/location on agenda + court_city on cases."""

from alembic import op
import sqlalchemy as sa

revision = "030"
down_revision = "029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("cases", sa.Column("court_city", sa.String(80), nullable=True))
    op.add_column("agenda_events", sa.Column("city", sa.String(80), nullable=True))
    op.add_column("agenda_events", sa.Column("location", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("agenda_events", "location")
    op.drop_column("agenda_events", "city")
    op.drop_column("cases", "court_city")
