from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .base import TimestampMixin
from .enums import Difficulty, InterviewCategory, PracticeStatus

if TYPE_CHECKING:
    from .mentor import Mentor
    from .student import Student


class InterviewQuestion(Base, TimestampMixin):
    """Pool of interview questions grouped by category and target role."""

    __tablename__ = "interview_questions"
    __table_args__ = (UniqueConstraint("question", name="uq_interview_question_text"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[InterviewCategory] = mapped_column(Enum(InterviewCategory), nullable=False, index=True)
    target_role: Mapped[str | None] = mapped_column(String(120), index=True)
    difficulty: Mapped[Difficulty] = mapped_column(Enum(Difficulty), default=Difficulty.intermediate, nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    guidance: Mapped[str | None] = mapped_column(Text)
    skill_tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)


class InterviewPractice(Base, TimestampMixin):
    """A student's practice record for one question."""

    __tablename__ = "interview_practice"
    __table_args__ = (UniqueConstraint("student_id", "question_id", name="uq_student_practice"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("interview_questions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    status: Mapped[PracticeStatus] = mapped_column(
        Enum(PracticeStatus), default=PracticeStatus.not_started, nullable=False
    )
    self_rating: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)
    practiced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    student: Mapped[Student] = relationship(back_populates="practices")
    question: Mapped[InterviewQuestion] = relationship()


class MockInterview(Base, TimestampMixin):
    """A recorded mock interview round with its outcome and feedback."""

    __tablename__ = "mock_interviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False
    )
    target_role: Mapped[str | None] = mapped_column(String(120))
    mode: Mapped[str] = mapped_column(String(40), default="technical", nullable=False)
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    score: Mapped[int | None] = mapped_column(Integer)
    strengths: Mapped[str | None] = mapped_column(Text)
    improvements: Mapped[str | None] = mapped_column(Text)
    feedback: Mapped[str | None] = mapped_column(Text)
    mentor_id: Mapped[int | None] = mapped_column(ForeignKey("mentors.id", ondelete="SET NULL"), index=True)

    student: Mapped[Student] = relationship(back_populates="mock_interviews")
    mentor: Mapped[Mentor | None] = relationship()
