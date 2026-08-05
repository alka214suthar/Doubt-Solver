from uuid import UUID

from fastapi import APIRouter, Depends

from dtos.response import DeleteDoubtResponse
from errors import AppError
from security import get_current_user
from service import doubt_service

router = APIRouter(tags=["doubts"])


@router.delete(
    "/{doubt_id}",
    response_model=DeleteDoubtResponse,
    status_code=200,
    summary="Delete a doubt",
    description=(
        "Soft-delete one of your doubts. "
        "Other users' doubts cannot be deleted."
    ),
)
def delete_doubt(
    doubt_id: UUID,
    current_user=Depends(get_current_user),
) -> DeleteDoubtResponse:
    response, error = doubt_service.delete_doubt(doubt_id, current_user.id)
    if error:
        raise AppError("DELETE_DOUBT_ERROR", error.value, 400)
    return response
