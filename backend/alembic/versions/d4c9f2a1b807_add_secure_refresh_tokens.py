"""Add refresh tokens and remove plaintext-password accounts.

Revision ID: d4c9f2a1b807
Revises: aae9bf741558
Create Date: 2026-07-30
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "d4c9f2a1b807"
down_revision: Union[str, Sequence[str], None] = "aae9bf741558"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Existing passwords cannot be safely distinguished or upgraded without the
    # original password. Remove those accounts and their dependent data.
    plaintext_users = (
        "SELECT id FROM user_details WHERE password NOT LIKE '$argon2%'"
    )
    plaintext_doubts = f"SELECT id FROM doubts WHERE user_id IN ({plaintext_users})"
    plaintext_solutions = (
        f"SELECT id FROM solutions WHERE doubt_id IN ({plaintext_doubts})"
    )
    op.execute(f"DELETE FROM hints WHERE solution_id IN ({plaintext_solutions})")
    op.execute(f"DELETE FROM steps WHERE solution_id IN ({plaintext_solutions})")
    op.execute(f"DELETE FROM solutions WHERE doubt_id IN ({plaintext_doubts})")
    op.execute(f"DELETE FROM questions WHERE doubt_id IN ({plaintext_doubts})")
    op.execute(f"DELETE FROM doubts WHERE user_id IN ({plaintext_users})")
    op.execute(f"DELETE FROM user_details WHERE id IN ({plaintext_users})")

    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("family_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("jti", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("replaced_by_jti", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user_details.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("jti"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(
        op.f("ix_refresh_tokens_family_id"),
        "refresh_tokens",
        ["family_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_refresh_tokens_user_id"),
        "refresh_tokens",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_refresh_tokens_user_id"), table_name="refresh_tokens")
    op.drop_index(op.f("ix_refresh_tokens_family_id"), table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
