from fastapi import APIRouter, Depends

from service import doubt_service
from dtos.request import SubmitBookmarkRequest
from dtos.response import SubmitBookmarkResponse
from errors import AppError
from security import get_current_user

router = APIRouter(tags=["doubts"])


@router.post(
    "",
    response_model=SubmitBookmarkResponse,
    status_code=200,
    summary="Bookmark or unbookmark a doubt",
    description=(
        "Set `is_bookmarked` to `true` to save a doubt, or `false` to remove it. "
        "Requires an existing `doubt_id`."
    ),
)
def submit_bookmark(
    request: SubmitBookmarkRequest,
    current_user=Depends(get_current_user),
) -> SubmitBookmarkResponse:
    response, error = doubt_service.submit_bookmark(request, current_user.id)
    if error:
        raise AppError("BOOKMARK_ERROR", error.value, 400)
    return response
