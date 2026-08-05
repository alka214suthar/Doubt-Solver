from uuid import UUID
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ErrorInfo(BaseModel):
    code: str
    message: str
    request_id: str
    details: Any | None = None


class ErrorResponse(BaseModel):
    error: ErrorInfo


class HealthResponse(BaseModel):
    status: str = Field(..., description="Service health status")

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"status": "ok"}]}
    )


class ReadyHealthResponse(BaseModel):
    status: str = Field(..., description="Readiness status")
    checks: dict[str, str] = Field(
        ..., description="Dependency check results (e.g. database)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"status": "ok", "checks": {"database": "ok"}}]
        }
    )


class SolveDoubtResponse(BaseModel):
    doubt_id: UUID = Field(..., description="Created doubt UUID")
    answer: str = Field(..., description="Final answer from the AI solver")
    hints: list[str] = Field(..., description="Helpful hints toward the solution")
    steps: list[str] = Field(..., description="Step-by-step solution")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "doubt_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                    "answer": "x = 5",
                    "hints": ["Isolate the variable term", "Subtract 5 from both sides"],
                    "steps": [
                        "Start with 2x + 5 = 15",
                        "Subtract 5 from both sides: 2x = 10",
                        "Divide both sides by 2: x = 5",
                    ],
                }
            ]
        }
    )


class DoubtSolverResponse(BaseModel):
    answer: str
    hints: list[str]
    steps: list[str]


class AddUserResponse(BaseModel):
    user_id: UUID = Field(..., description="Newly created user UUID")
    name: str
    email: str
    available_free_doubts: int = Field(..., description="Remaining free doubt credits")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "name": "Ada Lovelace",
                    "email": "ada@example.com",
                    "available_free_doubts": 10,
                }
            ]
        }
    )


class LoginUserResponse(BaseModel):
    user_id: UUID
    name: str
    email: str
    available_free_doubts: int
    doubts_asked: int = Field(0, description="Total doubts asked by the user")
    bookmarks: int = Field(0, description="Number of bookmarked doubts")
    first_doubt_asked_at: datetime | None = Field(
        None, description="Timestamp of the user's first doubt, if any"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "name": "Ada Lovelace",
                    "email": "ada@example.com",
                    "available_free_doubts": 8,
                    "doubts_asked": 2,
                    "bookmarks": 1,
                    "first_doubt_asked_at": "2026-07-20T10:30:00",
                }
            ]
        }
    )


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: LoginUserResponse


class LogoutResponse(BaseModel):
    message: str


class SubmitFeedbackResponse(BaseModel):
    isFeedbackSubmitted: bool = Field(..., description="Whether feedback was saved")

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"isFeedbackSubmitted": True}]}
    )


class GetUserDoubtsResponse(BaseModel):
    doubt_id: UUID
    question: str
    img_url: str | None = None
    subject: str
    class_name: int
    answer: str | None = None
    status: str = Field(..., description="created | solved | not_solved")
    hints: list[str] | None = None
    steps: list[str] | None = None
    is_doubt_helpful: bool | None = None
    is_bookmarked: bool | None = None
    created_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "doubt_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                    "question": "Solve for x: 2x + 5 = 15",
                    "img_url": None,
                    "subject": "Mathematics",
                    "class_name": 8,
                    "answer": "x = 5",
                    "status": "solved",
                    "hints": ["Isolate the variable term"],
                    "steps": ["2x + 5 = 15", "2x = 10", "x = 5"],
                    "is_doubt_helpful": True,
                    "is_bookmarked": False,
                    "created_at": "2026-07-20T10:30:00",
                }
            ]
        }
    )


class SubmitBookmarkResponse(BaseModel):
    isBookmarkSubmitted: bool = Field(..., description="Whether bookmark was saved")

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"isBookmarkSubmitted": True}]}
    )


class DeleteDoubtResponse(BaseModel):
    deleted: bool = Field(..., description="Whether the doubt was soft-deleted")

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"deleted": True}]}
    )


class GetBookmarkedDoubtsResponse(BaseModel):
    doubt_id: UUID
    question: str
    img_url: str | None = None
    subject: str
    class_name: int
    answer: str | None = None
    status: str
    hints: list[str] | None = None
    steps: list[str] | None = None
    is_doubt_helpful: bool | None = None
    created_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "doubt_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                    "question": "Solve for x: 2x + 5 = 15",
                    "img_url": None,
                    "subject": "Mathematics",
                    "class_name": 8,
                    "answer": "x = 5",
                    "status": "solved",
                    "hints": ["Isolate the variable term"],
                    "steps": ["2x + 5 = 15", "2x = 10", "x = 5"],
                    "is_doubt_helpful": True,
                    "created_at": "2026-07-20T10:30:00",
                }
            ]
        }
    )


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class UserDoubtsPage(BaseModel):
    items: list[GetUserDoubtsResponse]
    pagination: PaginationMeta


class BookmarkedDoubtsPage(BaseModel):
    items: list[GetBookmarkedDoubtsResponse]
    pagination: PaginationMeta
