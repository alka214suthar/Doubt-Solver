from fastapi import APIRouter, Depends, File, Form, UploadFile

from service import doubt_service
from dtos.request import SolveDoubtRequest
from dtos.response import SolveDoubtResponse
from enums.doubt_enums import Subjects
from errors import AppError
from image_uploads import delete_expired_uploads, save_validated_image
from rate_limit import enforce_solve_rate_limit

router = APIRouter(tags=["doubts"])


@router.post(
    "/solve-doubt",
    response_model=SolveDoubtResponse,
    status_code=200,
    summary="Solve a doubt",
    description=(
        "Submit an academic question (multipart form). Optionally attach an image. "
        "Consumes one free doubt credit. Returns the AI answer, hints, and steps.\n\n"
        "**Request body (multipart/form-data):**\n"
        "- `question` (string, required)\n"
        "- `subject` (string, required)\n"
        "- `class_name` (integer, required)\n"
        "- `image` (file, optional)"
    ),
)
async def solve_doubt(
    question: str = Form(
        ...,
        description="The academic question to solve",
        examples=["Solve for x: 2x + 5 = 15"],
    ),
    subject: Subjects = Form(
        ...,
        description="Subject name",
        examples=["Mathematics"],
    ),
    class_name: int = Form(
        ...,
        description="Class/grade level (1–12)",
        ge=1,
        le=12,
        examples=[8],
    ),
    image: UploadFile | None = File(
        None,
        description="Optional image of the question or diagram",
    ),
    current_user=Depends(enforce_solve_rate_limit),
) -> SolveDoubtResponse:
    delete_expired_uploads()
    image_path = None
    if image and image.filename:
        image_path = await save_validated_image(image)

    solve_request = SolveDoubtRequest(
        user_id=current_user.id,
        question=question,
        subject=subject,
        class_name=class_name,
        image_url=f"uploads/{image_path.name}" if image_path else None,
    )

    try:
        response, error = doubt_service.solve_doubt(solve_request)
    except Exception:
        if image_path:
            image_path.unlink(missing_ok=True)
        raise
    if error:
        if image_path:
            image_path.unlink(missing_ok=True)
        raise AppError("SOLVE_DOUBT_ERROR", error.value, 400)
    return response
