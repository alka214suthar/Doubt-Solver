from uuid import UUID
import datetime
import math
from entities.doubt_entities import Doubt, Question, Solution, Hint, Step, UserDetails
from dtos.request import (
    SolveDoubtRequest,
    AddUserRequest,
    LoginUserRequest,
    SubmitFeedbackRequest,
    DoubtSolverRequest,
    SubmitBookmarkRequest,
)
from dtos.response import (
    SolveDoubtResponse,
    AddUserResponse,
    LoginUserResponse,
    SubmitFeedbackResponse,
    GetUserDoubtsResponse,
    SubmitBookmarkResponse,
    DeleteDoubtResponse,
    GetBookmarkedDoubtsResponse,
    UserDoubtsPage,
    BookmarkedDoubtsPage,
    PaginationMeta,
)
from enums.doubt_enums import DoubtStatus, ErrorResponse
from LLM import doubt_solver
from repo import doubt_repo
from decorators.decorators import db_transaction, log_calls
from database import SessionLocal
from security import hash_password, verify_password
from typing import Tuple
from image_uploads import delete_expired_uploads
from normalization import normalize_email
from question_cache import (
    compute_question_hash,
    get_cached_solution,
    store_cached_solution,
)
from logging_config import get_logger
from config import GEMINI_MODEL

logger = get_logger(__name__)

DEFAULT_AVAILABLE_FREE_DOUBTS = 10


@log_calls
def _create_doubt(
    request: SolveDoubtRequest, session: SessionLocal
) -> Tuple[Doubt, ErrorResponse]:

    doubt_entity = Doubt(
        user_id=request.user_id, status=DoubtStatus.CREATED, image_url=request.image_url
    )

    created_doubt = doubt_repo.create_doubt(doubt_entity, session)
    if not created_doubt:
        return None, ErrorResponse.FAILED_TO_CREATE_DOUBT

    return created_doubt, None


@log_calls
def _solve_doubt(
    request: SolveDoubtRequest, doubt_id: UUID, session: SessionLocal
) -> Tuple[SolveDoubtResponse, ErrorResponse]:
    question_hash = compute_question_hash(
        question=request.question,
        subject=request.subject,
        class_name=request.class_name,
        image_url=request.image_url,
    )
    cached = get_cached_solution(session, question_hash)
    if cached:
        logger.info(
            "solve_doubt used cache",
            extra={
                "event": "solve_doubt_cache_hit",
                "user_id": str(request.user_id),
                "ai_model": GEMINI_MODEL,
                "ai_success": True,
                "question_hash": question_hash,
            },
        )
        doubt_solution = cached
    else:
        doubt_solver_request = DoubtSolverRequest(
            user_id=request.user_id,
            question=request.question,
            subject=request.subject,
            class_name=request.class_name,
            image_url=request.image_url,
        )
        doubt_solution = doubt_solver.solve_doubt(doubt_solver_request)
        store_cached_solution(session, question_hash, doubt_solution)

    doubt_repo.update_doubt_status(doubt_id, DoubtStatus.SOLVED, session)
    response = SolveDoubtResponse(
        answer=doubt_solution.answer,
        hints=doubt_solution.hints,
        steps=doubt_solution.steps,
        doubt_id=doubt_id,
    )
    return response, None

    

@log_calls
def _check_user_eligibility(user_id: UUID, session: SessionLocal) -> bool:

    available_free_doubt = doubt_repo.get_available_free_doubt_for_user(
        user_id, session
    )
    return available_free_doubt is not None and available_free_doubt > 0


@log_calls
def _add_question_to_doubt(
    doubt: Doubt, request: SolveDoubtRequest, session: SessionLocal
) -> Question:

    question_entity = doubt_repo.add_doubt_question(
        Question(
            question_text=request.question,
            subject=request.subject,
            class_name=request.class_name,
            doubt_id=doubt.id,
        ),
        session,
    )
    return question_entity


@log_calls
def _add_solution_to_doubt(
    solution: SolveDoubtResponse, doubt_id: UUID, session: SessionLocal
) -> None:

    doubt_repo.add_doubt_solution(
        Solution(
            answer=solution.answer,
            doubt_id=doubt_id,
            hints=[Hint(hint_text=hint) for hint in solution.hints],
            steps=[Step(step_text=step) for step in solution.steps],
        ),
        session,
    )


@log_calls
@db_transaction
def solve_doubt(
    request: SolveDoubtRequest, session: SessionLocal = None
) -> Tuple[SolveDoubtResponse, ErrorResponse]:
    user_able_to_ask_doubt = _check_user_eligibility(request.user_id, session)
    if not user_able_to_ask_doubt:
        return None, ErrorResponse.NOT_AVAILABLE_FREE_DOUBT
    doubt_entity, error = _create_doubt(request, session)
    if error:
        return None, error
    _add_question_to_doubt(doubt_entity, request, session)
    solution, error = _solve_doubt(request, doubt_entity.id, session)
    if error:
        doubt_repo.update_doubt_status(doubt_entity.id, DoubtStatus.NOT_SOLVED, session)
        return None, error
    doubt_repo.update_doubt_status(doubt_entity.id, DoubtStatus.SOLVED, session)
    _add_solution_to_doubt(solution, doubt_entity.id, session)
    return solution, None


@log_calls
@db_transaction
def add_user(
    request: AddUserRequest, session: SessionLocal = None
) -> Tuple[AddUserResponse, ErrorResponse]:
    response = doubt_repo.get_user_by_email(request.email, session)
    if response:
        return None, ErrorResponse.USER_ALREADY_EXISTS
    user_entity = doubt_repo.add_user(
        UserDetails(
            name=request.name,
            password=hash_password(request.password),
            email=normalize_email(request.email),
            available_free_doubts=DEFAULT_AVAILABLE_FREE_DOUBTS,
        ),
        session,
    )
    if not user_entity:
        return None, ErrorResponse.FAILED_TO_ADD_USER
    return AddUserResponse(
        user_id=user_entity.id,
        name=user_entity.name,
        email=user_entity.email,
        available_free_doubts=user_entity.available_free_doubts,
    ), None


@log_calls
@db_transaction
def login_user(
    request: LoginUserRequest, session: SessionLocal = None
) -> Tuple[LoginUserResponse, ErrorResponse]:
    user_entity = doubt_repo.get_user_by_email(request.email, session)
    if not user_entity:
        return None, ErrorResponse.USER_NOT_FOUND
    if not verify_password(request.password, user_entity.password):
        return None, ErrorResponse.PASSWORD_INCORRECT
    return LoginUserResponse(
        user_id=user_entity.id,
        name=user_entity.name,
        email=user_entity.email,
        available_free_doubts=user_entity.available_free_doubts,
    ), None


@log_calls
@db_transaction
def get_user_details(
    user_id: UUID, session: SessionLocal = None
) -> Tuple[LoginUserResponse, ErrorResponse]:
    user_entity = doubt_repo.get_user_by_id(user_id, session)
    if not user_entity:
        return None, ErrorResponse.USER_NOT_FOUND

    doubts_asked = doubt_repo.count_user_doubts(user_entity.id, session)
    bookmarks = doubt_repo.count_bookmarked_doubts(user_entity.id, session)
    first_doubt_asked_at = doubt_repo.get_first_doubt_created_at(
        user_entity.id, session
    )

    return LoginUserResponse(
        user_id=user_entity.id,
        name=user_entity.name,
        email=user_entity.email,
        available_free_doubts=user_entity.available_free_doubts,
        doubts_asked=doubts_asked,
        bookmarks=bookmarks,
        first_doubt_asked_at=first_doubt_asked_at,
    ), None


@log_calls
@db_transaction
def submit_feedback(
    request: SubmitFeedbackRequest,
    user_id: UUID,
    session: SessionLocal = None,
) -> Tuple[SubmitFeedbackResponse, ErrorResponse]:
    doubt_entity = doubt_repo.get_owned_doubt(request.doubt_id, user_id, session)
    if not doubt_entity:
        return None, ErrorResponse.DOUBT_NOT_FOUND
    doubt_repo.add_feedback_to_doubt(request.is_doubt_helpful, doubt_entity.id, session)
    return SubmitFeedbackResponse(isFeedbackSubmitted=True), None


@log_calls
@db_transaction
def get_user_doubts(
    user_id: UUID,
    page: int = 1,
    page_size: int = 20,
    subject: str | None = None,
    class_name: int | None = None,
    status: str | None = None,
    created_from: datetime.datetime | None = None,
    created_to: datetime.datetime | None = None,
    session: SessionLocal = None,
) -> Tuple[UserDoubtsPage, ErrorResponse]:
    delete_expired_uploads()
    doubts, total = doubt_repo.get_user_doubts(
        user_id,
        page=page,
        page_size=page_size,
        subject=subject,
        class_name=class_name,
        status=status,
        created_from=created_from,
        created_to=created_to,
        session=session,
    )
    items = [
        GetUserDoubtsResponse(
            doubt_id=doubt.id,
            img_url=doubt.image_url if doubt.image_url else None,
            question=doubt.question.question_text if doubt.question else None,
            answer=doubt.solution.answer if doubt.solution else None,
            subject=doubt.question.subject if doubt.question else None,
            class_name=doubt.question.class_name if doubt.question else None,
            hints=[hint.hint_text for hint in doubt.solution.hints]
            if doubt.solution and doubt.solution.hints
            else [],
            steps=[step.step_text for step in doubt.solution.steps]
            if doubt.solution and doubt.solution.steps
            else [],
            is_doubt_helpful=doubt.is_doubt_helpful,
            is_bookmarked=bool(doubt.is_bookmarked),
            created_at=doubt.created_at,
            status=doubt.status.value if hasattr(doubt.status, "value") else doubt.status,
        )
        for doubt in doubts
    ]
    return UserDoubtsPage(
        items=items,
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=math.ceil(total / page_size),
        ),
    ), None

@log_calls
@db_transaction
def submit_bookmark(
    request: SubmitBookmarkRequest,
    user_id: UUID,
    session: SessionLocal = None,
) -> Tuple[SubmitBookmarkResponse, ErrorResponse]:
    doubt_entity = doubt_repo.get_owned_doubt(request.doubt_id, user_id, session)
    if not doubt_entity:
        return None, ErrorResponse.DOUBT_NOT_FOUND
    doubt_repo.add_bookmark_to_doubt(request.doubt_id, request.is_bookmarked, session)
    return SubmitBookmarkResponse(isBookmarkSubmitted=True), None


@log_calls
@db_transaction
def delete_doubt(
    doubt_id: UUID,
    user_id: UUID,
    session: SessionLocal = None,
) -> Tuple[DeleteDoubtResponse, ErrorResponse]:
    doubt_entity = doubt_repo.get_owned_doubt(doubt_id, user_id, session)
    if not doubt_entity:
        return None, ErrorResponse.DOUBT_NOT_FOUND
    doubt_repo.soft_delete_doubt(doubt_id, session)
    return DeleteDoubtResponse(deleted=True), None

@log_calls
@db_transaction
def get_bookmarked_doubts(
    user_id: UUID,
    page: int = 1,
    page_size: int = 20,
    subject: str | None = None,
    class_name: int | None = None,
    status: str | None = None,
    created_from: datetime.datetime | None = None,
    created_to: datetime.datetime | None = None,
    session: SessionLocal = None,
) -> Tuple[BookmarkedDoubtsPage, ErrorResponse]:
    delete_expired_uploads()
    doubts, total = doubt_repo.get_bookmarked_doubts(
        user_id,
        page=page,
        page_size=page_size,
        subject=subject,
        class_name=class_name,
        status=status,
        created_from=created_from,
        created_to=created_to,
        session=session,
    )
    items = [
        GetBookmarkedDoubtsResponse(
            doubt_id=doubt.id,
            img_url=doubt.image_url if doubt.image_url else None,
            question=doubt.question.question_text if doubt.question else None,
            answer=doubt.solution.answer if doubt.solution else None,
            subject=doubt.question.subject if doubt.question else None,
            class_name=doubt.question.class_name if doubt.question else None,
            hints=[hint.hint_text for hint in doubt.solution.hints]
            if doubt.solution and doubt.solution.hints
            else [],
            steps=[step.step_text for step in doubt.solution.steps]
            if doubt.solution and doubt.solution.steps
            else [],
            is_doubt_helpful=doubt.is_doubt_helpful,
            created_at=doubt.created_at,
            status=doubt.status.value if hasattr(doubt.status, "value") else doubt.status,
        )
        for doubt in doubts
    ]
    return BookmarkedDoubtsPage(
        items=items,
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=math.ceil(total / page_size),
        ),
    ), None