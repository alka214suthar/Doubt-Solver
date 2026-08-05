"""added is_doubt_helpful field

Revision ID: 0782744c9086
Revises: c7ead745a556
Create Date: 2026-07-03 05:57:38.188833

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0782744c9086'
down_revision: Union[str, Sequence[str], None] = 'c7ead745a556'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('doubts', sa.Column('is_doubt_helpful', sa.Boolean(), nullable=True))
   


def downgrade() -> None:
    op.drop_column('doubts', 'is_doubt_helpful')