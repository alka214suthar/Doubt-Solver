import datetime
from uuid import uuid4

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    Integer,
    Text,
    JSON,
    CheckConstraint,
    Index,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
from enums.doubt_enums import DoubtStatus, Subjects
from normalization import normalize_email
from entities.doubt_entities import (
    UserDetails,
    Doubt,
    Question,
    Solution,
    Hint,
    Step,
)

SUBJECT_VALUES_SQL = ", ".join(f"'{subject.value}'" for subject in Subjects)
DOUBT_STATUS_VALUES_SQL = ", ".join(f"'{status.value}'" for status in DoubtStatus)


class UserDetailsModel(Base):
    __tablename__ = "user_details"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)
    __table_args__ = (
        Index(
            "uq_user_details_normalized_email",
            func.lower(email),
            unique=True,
        ),
        CheckConstraint(
            "email = lower(trim(email))",
            name="ck_user_details_email_normalized",
        ),
    )

    available_free_doubts = Column(Integer, nullable=False, default=5)

    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    is_active = Column(Boolean, default=True, nullable=False)

    @classmethod
    def from_entity(cls, user_details_entity: "UserDetails") -> "UserDetailsModel":
        return cls(
            id=user_details_entity.id,
            name=user_details_entity.name,
            email=normalize_email(user_details_entity.email),
            password=user_details_entity.password,
            available_free_doubts=user_details_entity.available_free_doubts,
            created_at=user_details_entity.created_at,
            updated_at=user_details_entity.updated_at,
        )

    @classmethod
    def to_entity(cls, user_details_model: "UserDetailsModel") -> "UserDetails":
        return UserDetails(
            id=user_details_model.id,
            name=user_details_model.name,
            email=user_details_model.email,
            available_free_doubts=user_details_model.available_free_doubts,
            password=user_details_model.password,
            created_at=user_details_model.created_at,
            updated_at=user_details_model.updated_at,
        )


class RefreshTokenModel(Base):
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_details.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    family_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    jti = Column(UUID(as_uuid=True), nullable=False, unique=True)
    token_hash = Column(String(64), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    replaced_by_jti = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class DoubtModel(Base):
    __tablename__ = "doubts"
    __table_args__ = (
        CheckConstraint(
            f"status IN ({DOUBT_STATUS_VALUES_SQL})",
            name="ck_doubts_status",
        ),
        CheckConstraint(
            "is_doubt_helpful IS NULL OR is_doubt_helpful IN (true, false)",
            name="ck_doubts_feedback",
        ),
        Index("ix_doubts_user_id", "user_id"),
        Index("ix_doubts_created_at", "created_at"),
        Index("ix_doubts_user_id_created_at", "user_id", "created_at"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_details.id", ondelete="CASCADE"),
        nullable=False,
    )

    status = Column(String(50), nullable=False)

    image_url = Column(String(500), nullable=True)

    is_doubt_helpful = Column(Boolean, nullable=True)

    is_bookmarked = Column(Boolean, default=False, nullable=False)

    question = relationship(
        "QuestionModel",
        back_populates="doubt",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    solution = relationship(
        "SolutionModel",
        back_populates="doubt",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    is_active = Column(Boolean, default=True, nullable=False)

    @classmethod
    def from_entity(cls, doubt_entity: "Doubt") -> "DoubtModel":
        return cls(
            id=doubt_entity.id,
            user_id=doubt_entity.user_id,
            status=doubt_entity.status,
            image_url=doubt_entity.image_url,
            created_at=doubt_entity.created_at,
            updated_at=doubt_entity.updated_at,
            is_doubt_helpful=doubt_entity.is_doubt_helpful,
            is_bookmarked=doubt_entity.is_bookmarked,
        )

    @classmethod
    def to_entity(cls, doubt_model: "DoubtModel") -> "Doubt":
        return Doubt(
            id=doubt_model.id,
            user_id=doubt_model.user_id,
            status=doubt_model.status,
            image_url=doubt_model.image_url,
            created_at=doubt_model.created_at,
            updated_at=doubt_model.updated_at,
            is_doubt_helpful=doubt_model.is_doubt_helpful,
            question=QuestionModel.to_entity(doubt_model.question)
            if doubt_model.question
            else None,
            solution=SolutionModel.to_entity(doubt_model.solution)
            if doubt_model.solution
            else None,
            is_bookmarked=doubt_model.is_bookmarked,
        )


class QuestionModel(Base):
    __tablename__ = "questions"
    __table_args__ = (
        CheckConstraint(
            f"subject IN ({SUBJECT_VALUES_SQL})",
            name="ck_questions_subject",
        ),
        CheckConstraint(
            "class_name BETWEEN 1 AND 12",
            name="ck_questions_class_name",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    doubt_id = Column(
        UUID(as_uuid=True),
        ForeignKey("doubts.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  
    )

    question_text = Column(Text, nullable=False)

    subject = Column(String(100), nullable=False)

    class_name = Column(Integer, nullable=False)

    doubt = relationship("DoubtModel", back_populates="question", uselist=False)

    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    is_active = Column(Boolean, default=True, nullable=False)

    @classmethod
    def from_entity(cls, question_entity: "Question") -> "QuestionModel":
        return cls(
            id=question_entity.id,
            doubt_id=question_entity.doubt_id,
            question_text=question_entity.question_text,
            subject=question_entity.subject,
            class_name=question_entity.class_name,
            created_at=question_entity.created_at,
            updated_at=question_entity.updated_at,
        )

    @classmethod
    def to_entity(cls, question_model: "QuestionModel") -> "Question":
        return Question(
            id=question_model.id,
            doubt_id=question_model.doubt_id,
            question_text=question_model.question_text,
            subject=question_model.subject,
            class_name=question_model.class_name,
            created_at=question_model.created_at,
            updated_at=question_model.updated_at,
        )


class SolutionModel(Base):
    __tablename__ = "solutions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    doubt_id = Column(
        UUID(as_uuid=True),
        ForeignKey("doubts.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    answer = Column(Text, nullable=False)
    hints = relationship(
        "HintModel",
        back_populates="solution",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    steps = relationship(
        "StepModel",
        back_populates="solution",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    doubt = relationship("DoubtModel", back_populates="solution", uselist=False)

    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    is_active = Column(Boolean, default=True, nullable=False)

    @classmethod
    def from_entity(cls, solution_entity: "Solution") -> "SolutionModel":
        return cls(
            id=solution_entity.id,
            doubt_id=solution_entity.doubt_id,
            answer=solution_entity.answer,
            created_at=solution_entity.created_at,
            updated_at=solution_entity.updated_at,
            hints=[HintModel.from_entity(hint, solution_entity.id) for hint in solution_entity.hints or []],
            steps=[StepModel.from_entity(step, solution_entity.id) for step in solution_entity.steps or []],
        )

    @classmethod
    def to_entity(cls, solution_model: "SolutionModel") -> "Solution":
        return Solution(
            id=solution_model.id,
            doubt_id=solution_model.doubt_id,
            answer=solution_model.answer,
            hints=[HintModel.to_entity(hint) for hint in solution_model.hints or []],
            steps=[StepModel.to_entity(step) for step in solution_model.steps or []],
            created_at=solution_model.created_at,
            updated_at=solution_model.updated_at,
        )


class HintModel(Base):
    __tablename__ = "hints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    solution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("solutions.id", ondelete="CASCADE"),
        nullable=False,
    )

    hint_text = Column(Text, nullable=False)

    solution = relationship("SolutionModel", back_populates="hints", uselist=False)

    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    is_active = Column(Boolean, default=True, nullable=False)

    @classmethod
    def from_entity(cls, hint_entity: "Hint", solution_id: UUID) -> "HintModel":
        return cls(
            id=hint_entity.id,
            solution_id=solution_id,
            hint_text=hint_entity.hint_text,
            created_at=hint_entity.created_at,
            updated_at=hint_entity.updated_at,
        )

    @classmethod
    def to_entity(cls, hint_model: "HintModel") -> "Hint":
        return Hint(
            id=hint_model.id,
            hint_text=hint_model.hint_text,
            created_at=hint_model.created_at,
            updated_at=hint_model.updated_at,
        )


class StepModel(Base):
    __tablename__ = "steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    solution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("solutions.id", ondelete="CASCADE"),
        nullable=False,
    )

    step_text = Column(Text, nullable=False)

    solution = relationship("SolutionModel", back_populates="steps", uselist=False)

    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    is_active = Column(Boolean, default=True, nullable=False)

    @classmethod
    def from_entity(cls, step_entity: "Step", solution_id: UUID) -> "StepModel":
        return cls(
            id=step_entity.id,
            solution_id=solution_id,
            step_text=step_entity.step_text,
            created_at=step_entity.created_at,
            updated_at=step_entity.updated_at,
        )

    @classmethod
    def to_entity(cls, step_model: "StepModel") -> "Step":
        return Step(
            id=step_model.id,
            step_text=step_model.step_text,
            created_at=step_model.created_at,
            updated_at=step_model.updated_at,
        )


class SolutionCacheModel(Base):
    """Cached AI answers keyed by normalized question hash."""

    __tablename__ = "solution_cache"

    question_hash = Column(String(64), primary_key=True)
    answer = Column(Text, nullable=False)
    hints = Column(JSON, nullable=False, default=list)
    steps = Column(JSON, nullable=False, default=list)
    hit_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )
