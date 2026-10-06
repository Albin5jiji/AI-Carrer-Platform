from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .base import TimestampMixin

if TYPE_CHECKING:
    from .student import Student


class AISkillGapResult(Base, TimestampMixin):
    """Most recent validated advisory result generated for a student and role."""

    __tablename__ = "ai_skill_gap_results"
    __table_args__ = (
        Index("ix_ai_skill_gap_results_student_role_created", "student_id", "target_role", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False
    )
    target_role: Mapped[str | None] = mapped_column(String(120), index=True)
    strengths: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    missing_skills: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    recommendations: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    validation_status: Mapped[str] = mapped_column(String(20), default="approved", nullable=False, index=True)
    is_outdated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    student: Mapped[Student] = relationship()
