"""added is_bookmarked to DoubtModel

Revision ID: aae9bf741558
Revises: 0782744c9086
Create Date: 2026-07-08 08:17:33.423727

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'aae9bf741558'
down_revision: Union[str, Sequence[str], None] = '0782744c9086'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('doubts', sa.Column('is_bookmarked', sa.Boolean(), nullable=True, server_default=sa.text('false')))


def downgrade() -> None:
    op.drop_column('doubts', 'is_bookmarked')