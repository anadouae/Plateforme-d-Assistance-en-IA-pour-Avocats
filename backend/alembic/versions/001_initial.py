"""Initial schema — all Sanad tables

Revision ID: 001
"""
from typing import Sequence, Union

from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from app.core.database import Base
    from app.models import (  # noqa: F401
        AuditLog,
        Cabinet,
        Case,
        ChatMessage,
        Document,
        EmailToken,
        User,
    )

    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    from app.core.database import Base
    from app.models import (  # noqa: F401
        AuditLog,
        Cabinet,
        Case,
        ChatMessage,
        Document,
        EmailToken,
        User,
    )

    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
