"""create tables

Revision ID: c7ead745a556
Revises:
Create Date: 2026-06-06 16:44:29.003536
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers
revision: str = "c7ead745a556"
down_revision: Union[str, Sequence[str], None]  = 'c01b5e18117f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.alter_column("user_details", "password", existing_type=sa.String(length=255), nullable=False)

  


def downgrade() -> None:
    op.alter_column("user_details", "password", existing_type=sa.String(length=255), nullable=True)
   