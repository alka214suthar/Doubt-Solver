from uuid import UUID
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from enums.doubt_enums import Subjects
from normalization import normalize_email


class SolveDoubtRequest(BaseModel):
    user_id: UUID = Field(..., description="Authenticated user's UUID")
    question: str = Field(..., description="The academic question to solve", min_length=1)
    subject: Subjects = Field(..., description="Subject name, e.g. Mathematics")
    class_name: int = Field(..., description="Class/grade level", ge=1, le=12)
    image_url: Optional[str] = Field(
        None, description="Optional relative path to an uploaded image"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "question": "Solve for x: 2x + 5 = 15",
                    "subject": "Mathematics",
                    "class_name": 8,
                    "image_url": "uploads/uuid_diagram.png",
                }
            ]
        }
    )


class DoubtSolverRequest(BaseModel):
    user_id: UUID
    question: str
    subject: str
    class_name: int
    image_url: str | None = None


class AddUserRequest(BaseModel):
    name: str = Field(..., description="Full name", min_length=1, examples=["Ada Lovelace"])
    email: str = Field(..., description="Unique email address", examples=["ada@example.com"])
    password: str = Field(..., description="Account password", min_length=8, examples=["securePass123"])

    @field_validator("email")
    @classmethod
    def normalize_email_value(cls, value: str) -> str:
        return normalize_email(value)

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Ada Lovelace",
                    "email": "ada@example.com",
                    "password": "securePass123",
                }
            ]
        }
    )


class LoginUserRequest(BaseModel):
    email: str = Field(..., description="Registered email", examples=["ada@example.com"])
    password: str = Field(..., description="Account password", examples=["securePass123"])

    @field_validator("email")
    @classmethod
    def normalize_email_value(cls, value: str) -> str:
        return normalize_email(value)

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"email": "ada@example.com", "password": "securePass123"}
            ]
        }
    )


class SubmitFeedbackRequest(BaseModel):
    is_doubt_helpful: bool = Field(..., description="Whether the solution was helpful")
    doubt_id: UUID = Field(..., description="Doubt being rated")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "is_doubt_helpful": True,
                    "doubt_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                }
            ]
        }
    )


class SubmitBookmarkRequest(BaseModel):
    doubt_id: UUID = Field(..., description="Doubt to bookmark or unbookmark")
    is_bookmarked: bool = Field(True, description="True to bookmark, false to remove")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "doubt_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                    "is_bookmarked": True,
                }
            ]
        }
    )
