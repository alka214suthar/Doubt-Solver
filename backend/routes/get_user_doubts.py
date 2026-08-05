from datetime import datetime

from fastapi import APIRouter, Depends, Query

from service import doubt_service
from dtos.response import UserDoubtsPage
from enums.doubt_enums import DoubtStatus, Subjects
from errors import AppError
from security import get_current_user

router = APIRouter(tags=["doubts"])


@router.get(
    "",
    response_model=UserDoubtsPage,
    status_code=200,
    summary="Get user doubt history",
    description=(
        "Return all doubts for a user, including question, solution, status, "
        "feedback, and bookmark flags. Ordered by creation time from the database."
    ),
)
async def get_user_doubts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    subject: Subjects | None = Query(None),
    class_name: int | None = Query(None, ge=1, le=12),
    status: DoubtStatus | None = Query(None),
    created_from: datetime | None = Query(None),
    created_to: datetime | None = Query(None),
    current_user=Depends(get_current_user),
) -> UserDoubtsPage:
    if created_from and created_to and created_from > created_to:
        raise AppError(
            "VALIDATION_ERROR",
            "Please check the date range and try again.",
            422,
        )
    response, error = doubt_service.get_user_doubts(
        current_user.id,
        page=page,
        page_size=page_size,
        subject=subject.value if subject else None,
        class_name=class_name,
        status=status.value if status else None,
        created_from=created_from,
        created_to=created_to,
    )
    if error:
        raise AppError("DOUBT_HISTORY_ERROR", error.value, 400)
    return response
