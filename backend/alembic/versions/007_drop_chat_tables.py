"""Drop chat tables (hors cahier des charges plaidoirie)

Revision ID: 007
"""
from typing import Sequence, Union

from alembic import op

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")


def downgrade() -> None:
    # Non restauré : le chat libre n'est plus dans le périmètre produit.
    raise NotImplementedError("chat_sessions / chat_messages retirés du CDC")
