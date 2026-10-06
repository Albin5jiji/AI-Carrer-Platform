from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .base import TimestampMixin
from .enums import Difficulty, LearningStatus, Priority

if TYPE_CHECKING:
    from .student import Student


class LearningResource(Base, TimestampMixin):
    """Curated learning material mapped to a single skill (rule based, not AI)."""

    __tablename__ = "learning_resources"
    __table_args__ = (UniqueConstraint("skill_name", "title", name="uq_learning_resource"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    skill_name: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(120))
    url: Mapped[str | None] = mapped_column(String(255))
    resource_type: Mapped[str] = mapped_column(String(40), default="course", nullable=False)
    difficulty: Mapped[Difficulty] = mapped_column(
        Enum(Difficulty), default=Difficulty.beginner, nullable=False
    )
    estimated_hours: Mapped[float] = mapped_column(Float, default=8.0, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)


class LearningPathItem(Base, TimestampMixin):
    """A recommended learning step for one student, generated from their skill gaps."""

    __tablename__ = "learning_path_items"
    __table_args__ = (UniqueConstraint("student_id", "resource_id", name="uq_student_learning_item"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False
    )
    resource_id: Mapped[int] = mapped_column(
        ForeignKey("learning_resources.id", ondelete="CASCADE"), index=True, nullable=False
    )
    skill_name: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    priority: Mapped[Priority] = mapped_column(Enum(Priority), default=Priority.medium, nullable=False)
    status: Mapped[LearningStatus] = mapped_column(
        Enum(LearningStatus), default=LearningStatus.not_started, nullable=False
    )
    progress_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    target_date: Mapped[date | None] = mapped_column(Date)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)

    student: Mapped[Student] = relationship(back_populates="learning_items")
    resource: Mapped[LearningResource] = relationship()
