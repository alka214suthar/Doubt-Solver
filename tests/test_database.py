"""Database constraint and cascade behavior tests."""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from models.doubt_models import (
    DoubtModel,
    HintModel,
    QuestionModel,
    RefreshTokenModel,
    SolutionModel,
    StepModel,
    UserDetailsModel,
)
from security import hash_password


def test_unique_email_constraint(db_engine):
    Session = sessionmaker(bind=db_engine)
    with Session() as session:
        session.add(
            UserDetailsModel(
                name="First",
                email="unique@example.com",
                password=hash_password("pass1234"),
                available_free_doubts=10,
            )
        )
        session.commit()

        session.add(
            UserDetailsModel(
                name="Second",
                email="unique@example.com",
                password=hash_password("otherpass"),
                available_free_doubts=10,
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()


def test_foreign_key_rejects_orphan_doubt(db_engine):
    Session = sessionmaker(bind=db_engine)
    with Session() as session:
        session.add(
            DoubtModel(
                user_id=uuid.uuid4(),
                status="created",
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()


def test_deleting_user_cascades_to_doubts_and_tokens(db_engine, client, solved_doubt):
    """Deleting a user removes owned doubts, questions, solutions, and refresh tokens."""
    Session = sessionmaker(bind=db_engine)
    user_id = uuid.UUID(solved_doubt["user"]["user_id"])
    doubt_id = uuid.UUID(solved_doubt["doubt_id"])

    with Session() as session:
        assert session.query(DoubtModel).filter_by(id=doubt_id).count() == 1
        assert session.query(QuestionModel).filter_by(doubt_id=doubt_id).count() == 1
        assert session.query(SolutionModel).filter_by(doubt_id=doubt_id).count() == 1
        assert session.query(RefreshTokenModel).filter_by(user_id=user_id).count() >= 1

        solution_id = (
            session.query(SolutionModel.id).filter_by(doubt_id=doubt_id).scalar()
        )
        assert session.query(HintModel).filter_by(solution_id=solution_id).count() >= 1
        assert session.query(StepModel).filter_by(solution_id=solution_id).count() >= 1

        user = session.query(UserDetailsModel).filter_by(id=user_id).one()
        session.delete(user)
        session.commit()

        assert session.query(UserDetailsModel).filter_by(id=user_id).count() == 0
        assert session.query(DoubtModel).filter_by(id=doubt_id).count() == 0
        assert session.query(QuestionModel).filter_by(doubt_id=doubt_id).count() == 0
        assert session.query(SolutionModel).filter_by(doubt_id=doubt_id).count() == 0
        assert session.query(HintModel).filter_by(solution_id=solution_id).count() == 0
        assert session.query(StepModel).filter_by(solution_id=solution_id).count() == 0
        assert session.query(RefreshTokenModel).filter_by(user_id=user_id).count() == 0


def test_deleting_doubt_cascades_to_question_and_solution(db_engine, solved_doubt):
    Session = sessionmaker(bind=db_engine)
    doubt_id = uuid.UUID(solved_doubt["doubt_id"])

    with Session() as session:
        solution_id = (
            session.query(SolutionModel.id).filter_by(doubt_id=doubt_id).scalar()
        )
        doubt = session.query(DoubtModel).filter_by(id=doubt_id).one()
        session.delete(doubt)
        session.commit()

        assert session.query(QuestionModel).filter_by(doubt_id=doubt_id).count() == 0
        assert session.query(SolutionModel).filter_by(doubt_id=doubt_id).count() == 0
        assert session.query(HintModel).filter_by(solution_id=solution_id).count() == 0
        assert session.query(StepModel).filter_by(solution_id=solution_id).count() == 0
