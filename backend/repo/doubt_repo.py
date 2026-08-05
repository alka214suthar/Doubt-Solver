import datetime
from entities.doubt_entities import Doubt, Question, Solution, UserDetails
from uuid import UUID
from database import SessionLocal
from config import DOUBT_RETENTION_DAYS
from models.doubt_models import (
    DoubtModel,
    QuestionModel,
    SolutionModel,
    UserDetailsModel,
    HintModel,
    StepModel,
)
from decorators.decorators import log_calls
from sqlalchemy.orm import joinedload, with_loader_criteria
from normalization import normalize_email


@log_calls
def _reduce_one_available_free_doubt_for_user(
    user_id: UUID, session: SessionLocal = None
) -> None:
    session.query(UserDetailsModel).filter(
        UserDetailsModel.id == user_id,
        UserDetailsModel.is_active.is_(True),
        UserDetailsModel.available_free_doubts > 0,
    ).update({"available_free_doubts": UserDetailsModel.available_free_doubts - 1})
    session.flush()


@log_calls
def create_doubt(doubt: Doubt, session: SessionLocal = None) -> Doubt:
    _reduce_one_available_free_doubt_for_user(doubt.user_id, session)
    doubt_model = DoubtModel.from_entity(doubt)
    session.add(doubt_model)
    session.flush()
    doubt_entity = DoubtModel.to_entity(doubt_model)
    return doubt_entity


@log_calls
def add_doubt_question(
    question: Question, session: SessionLocal = None
) -> QuestionModel:
    question_model = QuestionModel.from_entity(question)
    session.add(question_model)
    session.flush()
    return QuestionModel.to_entity(question_model)


@log_calls
def update_doubt_status(
    doubt_id: UUID, status: str, session: SessionLocal = None
) -> None:
    session.query(DoubtModel).filter(
        DoubtModel.id == doubt_id, DoubtModel.is_active.is_(True)
    ).update({"status": status})
    session.flush()


@log_calls
def get_available_free_doubt_for_user(
    user_id: UUID, session: SessionLocal = None
) -> int | None:
    user_details = (
        session.query(UserDetailsModel)
        .filter(UserDetailsModel.id == user_id, UserDetailsModel.is_active.is_(True))
        .first()
    )
    if user_details:
        return user_details.available_free_doubts
    return None


@log_calls
def add_doubt_solution(solution: Solution, session: SessionLocal = None) -> Solution:
    solution_model = SolutionModel.from_entity(solution)
    session.add(solution_model)
    session.flush()
    return SolutionModel.to_entity(solution_model)


@log_calls
def add_user(user_details: UserDetails, session: SessionLocal = None) -> UserDetails:
    user_details_model = UserDetailsModel.from_entity(user_details)
    session.add(user_details_model)
    session.flush()
    return UserDetailsModel.to_entity(user_details_model)


@log_calls
def get_user_by_email(email: str, session: SessionLocal = None) -> UserDetails:
    user_details_model = (
        session.query(UserDetailsModel)
        .filter(
            UserDetailsModel.email == normalize_email(email),
            UserDetailsModel.is_active.is_(True),
        )
        .first()
    )
    if not user_details_model:
        return None
    return UserDetailsModel.to_entity(user_details_model)


@log_calls
def get_user_by_id(user_id: UUID, session: SessionLocal = None) -> UserDetails:
    user_details_model = (
        session.query(UserDetailsModel)
        .filter(
            UserDetailsModel.id == user_id,
            UserDetailsModel.is_active.is_(True),
        )
        .first()
    )
    if not user_details_model:
        return None
    return UserDetailsModel.to_entity(user_details_model)


@log_calls
def count_user_doubts(user_id: UUID, session: SessionLocal = None) -> int:
    return (
        session.query(DoubtModel)
        .filter(DoubtModel.user_id == user_id, DoubtModel.is_active.is_(True))
        .count()
    )


@log_calls
def count_bookmarked_doubts(user_id: UUID, session: SessionLocal = None) -> int:
    return (
        session.query(DoubtModel)
        .filter(
            DoubtModel.user_id == user_id,
            DoubtModel.is_active.is_(True),
            DoubtModel.is_bookmarked.is_(True),
        )
        .count()
    )


@log_calls
def get_first_doubt_created_at(user_id: UUID, session: SessionLocal = None):
    return (
        session.query(DoubtModel.created_at)
        .filter(DoubtModel.user_id == user_id, DoubtModel.is_active.is_(True))
        .order_by(DoubtModel.created_at.asc())
        .limit(1)
        .scalar()
    )


@log_calls
def get_doubt_by_id(doubt_id: UUID, session: SessionLocal = None) -> Doubt:
    doubt_model = (
        session.query(DoubtModel)
        .options(
            joinedload(DoubtModel.question),
            joinedload(DoubtModel.solution).joinedload(SolutionModel.hints),
            joinedload(DoubtModel.solution).joinedload(SolutionModel.steps),
        )
        .filter(DoubtModel.id == doubt_id, DoubtModel.is_active.is_(True))
        .first()
    )
    if doubt_model:
        return DoubtModel.to_entity(doubt_model)
    return None


@log_calls
def get_owned_doubt(
    doubt_id: UUID, user_id: UUID, session: SessionLocal = None
) -> Doubt:
    doubt_model = (
        session.query(DoubtModel)
        .options(
            joinedload(DoubtModel.question),
            joinedload(DoubtModel.solution).joinedload(SolutionModel.hints),
            joinedload(DoubtModel.solution).joinedload(SolutionModel.steps),
        )
        .filter(
            DoubtModel.id == doubt_id,
            DoubtModel.user_id == user_id,
            DoubtModel.is_active.is_(True),
        )
        .first()
    )
    return DoubtModel.to_entity(doubt_model) if doubt_model else None


@log_calls
def add_feedback_to_doubt(
    is_doubt_helpful: bool, doubt_id: UUID, session: SessionLocal = None
) -> None:
    session.query(DoubtModel).filter(
        DoubtModel.id == doubt_id, DoubtModel.is_active.is_(True)
    ).update({DoubtModel.is_doubt_helpful: is_doubt_helpful})
    session.flush()


def _get_doubts_page(
    user_id: UUID,
    *,
    page: int,
    page_size: int,
    subject: str | None,
    class_name: int | None,
    status: str | None,
    created_from: datetime.datetime | None,
    created_to: datetime.datetime | None,
    bookmarked_only: bool,
    session: SessionLocal,
) -> tuple[list[Doubt], int]:
    cutoff = datetime.datetime.now(datetime.UTC).replace(
        tzinfo=None
    ) - datetime.timedelta(days=DOUBT_RETENTION_DAYS)
    query = (
        session.query(DoubtModel)
        .options(
            joinedload(DoubtModel.question),
            joinedload(DoubtModel.solution).joinedload(SolutionModel.hints),
            joinedload(DoubtModel.solution).joinedload(SolutionModel.steps),
            with_loader_criteria(QuestionModel, QuestionModel.is_active.is_(True)),
            with_loader_criteria(SolutionModel, SolutionModel.is_active.is_(True)),
            with_loader_criteria(HintModel, HintModel.is_active.is_(True)),
            with_loader_criteria(StepModel, StepModel.is_active.is_(True)),
        )
        .filter(
            DoubtModel.user_id == user_id,
            DoubtModel.is_active.is_(True),
            DoubtModel.created_at >= cutoff,
        )
    )
    if bookmarked_only:
        query = query.filter(DoubtModel.is_bookmarked.is_(True))
    if subject is not None or class_name is not None:
        query = query.join(DoubtModel.question)
        if subject is not None:
            query = query.filter(QuestionModel.subject == subject)
        if class_name is not None:
            query = query.filter(QuestionModel.class_name == class_name)
    if status is not None:
        query = query.filter(DoubtModel.status == status)
    if created_from is not None:
        query = query.filter(DoubtModel.created_at >= created_from)
    if created_to is not None:
        query = query.filter(DoubtModel.created_at <= created_to)

    total = query.order_by(None).count()
    doubt_models = (
        query.order_by(DoubtModel.created_at.desc(), DoubtModel.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return [DoubtModel.to_entity(model) for model in doubt_models], total


@log_calls
def get_user_doubts(
    user_id: UUID,
    *,
    page: int = 1,
    page_size: int = 20,
    subject: str | None = None,
    class_name: int | None = None,
    status: str | None = None,
    created_from: datetime.datetime | None = None,
    created_to: datetime.datetime | None = None,
    session: SessionLocal = None,
) -> tuple[list[Doubt], int]:
    return _get_doubts_page(
        user_id,
        page=page,
        page_size=page_size,
        subject=subject,
        class_name=class_name,
        status=status,
        created_from=created_from,
        created_to=created_to,
        bookmarked_only=False,
        session=session,
    )

@log_calls
def add_bookmark_to_doubt(
    doubt_id: UUID, is_bookmarked: bool = True, session: SessionLocal = None
) -> None:
    session.query(DoubtModel).filter(
        DoubtModel.id == doubt_id, DoubtModel.is_active.is_(True)
    ).update({DoubtModel.is_bookmarked: is_bookmarked})
    session.flush()


@log_calls
def soft_delete_doubt(doubt_id: UUID, session: SessionLocal = None) -> bool:
    updated = (
        session.query(DoubtModel)
        .filter(DoubtModel.id == doubt_id, DoubtModel.is_active.is_(True))
        .update({"is_active": False})
    )
    session.flush()
    return updated > 0

@log_calls
def get_bookmarked_doubts(
    user_id: UUID,
    *,
    page: int = 1,
    page_size: int = 20,
    subject: str | None = None,
    class_name: int | None = None,
    status: str | None = None,
    created_from: datetime.datetime | None = None,
    created_to: datetime.datetime | None = None,
    session: SessionLocal = None,
) -> tuple[list[Doubt], int]:
    return _get_doubts_page(
        user_id,
        page=page,
        page_size=page_size,
        subject=subject,
        class_name=class_name,
        status=status,
        created_from=created_from,
        created_to=created_to,
        bookmarked_only=True,
        session=session,
    )