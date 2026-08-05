from fastapi import APIRouter, Depends

from service import doubt_service
from dtos.request import SubmitFeedbackRequest
from dtos.response import SubmitFeedbackResponse
from errors import AppError
from security import get_current_user

router = APIRouter(tags=["doubts"])


@router.post(
    "",
    response_model=SubmitFeedbackResponse,
    status_code=200,
    summary="Submit feedback on a doubt",
    description=(
        "Mark whether a solved doubt was helpful. "
        "Requires an existing `doubt_id`."
    ),
)
async def submit_feedback(
    request: SubmitFeedbackRequest,
    current_user=Depends(get_current_user),
) -> SubmitFeedbackResponse:
    response, error = doubt_service.submit_feedback(request, current_user.id)
    if error:
        raise AppError("FEEDBACK_ERROR", error.value, 400)
    return response
