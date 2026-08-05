"""added password column to userdetails

Revision ID: c01b5e18117f
Revises: c7ead745a556
Create Date: 2026-06-08 11:07:31.675533

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c01b5e18117f'
down_revision: Union[str, Sequence[str], None] = 'cc51e3415b8c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('user_details', sa.Column('password', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('user_details', 'password')
   