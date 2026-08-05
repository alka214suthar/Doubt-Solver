from typing import Optional
from enums.doubt_enums import DoubtStatus, Subjects
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID, uuid4


class Doubt(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    status: DoubtStatus 
    image_url: Optional[str] = None
    is_doubt_helpful: Optional[bool] = None
    question: Optional["Question"] = None
    solution: Optional["Solution"] = None
    created_at: datetime = None
    updated_at: datetime = None
    is_active: bool = True
    is_bookmarked: bool = False

class Hint(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    hint_text: str
    created_at: datetime = None
    updated_at: datetime = None
    is_active: bool = True


class Step(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    step_text: str
    created_at: datetime = None
    updated_at: datetime = None
    is_active: bool = True


class Solution(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    answer: str
    doubt_id: UUID
    hints: list[Hint] = None
    steps: list[Step] = None
    doubt: Optional["Doubt"] = None
    created_at: datetime = None
    updated_at: datetime = None
    is_active: bool = True


class Question(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    question_text: str
    doubt_id: UUID
    subject: Subjects
    class_name: int
    doubt: Optional["Doubt"] = None
    created_at: datetime = None
    updated_at: datetime = None
    is_active: bool = True

class UserDetails(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    email: str
    password: str
    available_free_doubts: int
    created_at: datetime = None
    updated_at: datetime = None
    is_active: bool = True