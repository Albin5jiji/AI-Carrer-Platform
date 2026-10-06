from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .base import TimestampMixin
from .enums import ResumeStatus

if TYPE_CHECKING:
    from .mentor import Mentor
    from .student import Student


class Resume(Base, TimestampMixin):
    """One resume version of a student.

    Resume content is stored as structured JSON (`content`) so the platform can score
    completeness and render it without storing sensitive file paths. `file_url` keeps a
    reference to an externally hosted copy when the student has one.
    """

    __tablename__ = "resumes"
    __table_args__ = (UniqueConstraint("student_id", "version_number", name="uq_resume_version"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    version_name: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    target_role: Mapped[str] = mapped_column(String(120), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    content: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    file_url: Mapped[str | None] = mapped_column(String(255))

    status: Mapped[ResumeStatus] = mapped_column(Enum(ResumeStatus), default=ResumeStatus.draft, nullable=False)
    mentor_feedback: Mapped[str | None] = mapped_column(Text)
    reviewed_by_mentor_id: Mapped[int | None] = mapped_column(
        ForeignKey("mentors.id", ondelete="SET NULL"), index=True
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    student: Mapped[Student] = relationship(back_populates="resumes")
    reviewer: Mapped[Mentor | None] = relationship()
