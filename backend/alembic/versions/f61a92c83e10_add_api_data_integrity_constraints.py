"""Add normalized email, indexes, constraints, and cascade foreign keys.

Revision ID: f61a92c83e10
Revises: d4c9f2a1b807
Create Date: 2026-07-30
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f61a92c83e10"
down_revision: Union[str, Sequence[str], None] = "d4c9f2a1b807"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CASCADE_FOREIGN_KEYS = (
    ("doubts", "doubts_user_id_fkey", "user_id", "user_details", "id"),
    ("questions", "questions_doubt_id_fkey", "doubt_id", "doubts", "id"),
    ("solutions", "solutions_doubt_id_fkey", "doubt_id", "doubts", "id"),
    ("hints", "hints_solution_id_fkey", "solution_id", "solutions", "id"),
    ("steps", "steps_solution_id_fkey", "solution_id", "solutions", "id"),
)


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM user_details
                GROUP BY lower(btrim(email))
                HAVING count(*) > 1
            ) THEN
                RAISE EXCEPTION
                    'Cannot normalize emails: case-insensitive duplicates exist';
            END IF;
        END $$;
        """
    )
    op.execute("UPDATE user_details SET email = lower(btrim(email))")
    op.drop_constraint("user_details_email_key", "user_details", type_="unique")
    op.create_index(
        "uq_user_details_normalized_email",
        "user_details",
        [sa.text("lower(email)")],
        unique=True,
    )
    op.create_check_constraint(
        "ck_user_details_email_normalized",
        "user_details",
        "email = lower(btrim(email))",
    )

    op.execute(
        "UPDATE doubts SET is_bookmarked = false WHERE is_bookmarked IS NULL"
    )
    op.alter_column(
        "doubts",
        "is_bookmarked",
        existing_type=sa.Boolean(),
        nullable=False,
        server_default=sa.text("false"),
    )

    op.create_index("ix_doubts_user_id", "doubts", ["user_id"])
    op.create_index("ix_doubts_created_at", "doubts", ["created_at"])
    op.create_index(
        "ix_doubts_user_id_created_at",
        "doubts",
        ["user_id", "created_at"],
    )

    op.create_check_constraint(
        "ck_doubts_status",
        "doubts",
        "status IN ('created', 'solved', 'not_solved')",
    )
    op.create_check_constraint(
        "ck_doubts_feedback",
        "doubts",
        "is_doubt_helpful IS NULL OR is_doubt_helpful IN (true, false)",
    )
    op.create_check_constraint(
        "ck_questions_subject",
        "questions",
        """
        subject IN (
            'Mathematics', 'Physics', 'Chemistry', 'Biology', 'History',
            'Geography', 'English', 'Computer Science', 'Logical Reasoning'
        )
        """,
    )
    op.create_check_constraint(
        "ck_questions_class_name",
        "questions",
        "class_name BETWEEN 1 AND 12",
    )

    for table, name, local_column, remote_table, remote_column in CASCADE_FOREIGN_KEYS:
        op.drop_constraint(name, table, type_="foreignkey")
        op.create_foreign_key(
            name,
            table,
            remote_table,
            [local_column],
            [remote_column],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    for table, name, local_column, remote_table, remote_column in reversed(
        CASCADE_FOREIGN_KEYS
    ):
        op.drop_constraint(name, table, type_="foreignkey")
        op.create_foreign_key(
            name,
            table,
            remote_table,
            [local_column],
            [remote_column],
        )

    op.drop_constraint("ck_questions_class_name", "questions", type_="check")
    op.drop_constraint("ck_questions_subject", "questions", type_="check")
    op.drop_constraint("ck_doubts_feedback", "doubts", type_="check")
    op.drop_constraint("ck_doubts_status", "doubts", type_="check")

    op.drop_index("ix_doubts_user_id_created_at", table_name="doubts")
    op.drop_index("ix_doubts_created_at", table_name="doubts")
    op.drop_index("ix_doubts_user_id", table_name="doubts")
    op.alter_column(
        "doubts",
        "is_bookmarked",
        existing_type=sa.Boolean(),
        nullable=True,
        server_default=sa.text("false"),
    )

    op.drop_constraint(
        "ck_user_details_email_normalized",
        "user_details",
        type_="check",
    )
    op.drop_index(
        "uq_user_details_normalized_email",
        table_name="user_details",
    )
    op.create_unique_constraint(
        "user_details_email_key",
        "user_details",
        ["email"],
    )
