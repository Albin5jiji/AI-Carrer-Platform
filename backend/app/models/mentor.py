from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .base import TimestampMixin
from .enums import FeedbackStatus

if TYPE_CHECKING:
    from .account import Account
    from .placement import Application
    from .resume import Resume
    from .student import Student


class Mentor(Base, TimestampMixin):
    """Mentor profile linked to an `Account` with the mentor role."""

    __tablename__ = "mentors"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), index=True, unique=True, nullable=False
    )
    employee_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    department: Mapped[str] = mapped_column(String(120), nullable=False, default="Placement Cell")

    account: Mapped[Account] = relationship(back_populates="mentor")
    assignments: Mapped[list[MentorAssignment]] = relationship(
        back_populates="mentor", cascade="all, delete-orphan"
    )
    feedback_entries: Mapped[list[Feedback]] = relationship(
        back_populates="mentor", cascade="all, delete-orphan"
    )


class MentorAssignment(Base, TimestampMixin):
    """Links a mentor to the students they monitor and review."""

    __tablename__ = "mentor_assignments"
    __table_args__ = (UniqueConstraint("mentor_id", "student_id", name="uq_mentor_student"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    mentor_id: Mapped[int] = mapped_column(
        ForeignKey("mentors.id", ondelete="CASCADE"), index=True, nullable=False
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    mentor: Mapped[Mentor] = relationship(back_populates="assignments")
    student: Mapped[Student] = relationship(back_populates="mentor_assignments")


class Feedback(Base, TimestampMixin):
    """Mentor feedback, optionally attached to a resume version or an application."""

    __tablename__ = "feedback_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False
    )
    mentor_id: Mapped[int] = mapped_column(
        ForeignKey("mentors.id", ondelete="CASCADE"), index=True, nullable=False
    )
    resume_id: Mapped[int | None] = mapped_column(ForeignKey("resumes.id", ondelete="SET NULL"), index=True)
    application_id: Mapped[int | None] = mapped_column(
        ForeignKey("applications.id", ondelete="SET NULL"), index=True
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[FeedbackStatus] = mapped_column(
        Enum(FeedbackStatus), default=FeedbackStatus.open, nullable=False
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    student: Mapped[Student] = relationship(back_populates="feedback_entries")
    mentor: Mapped[Mentor] = relationship(back_populates="feedback_entries")
    resume: Mapped[Resume | None] = relationship()
    application: Mapped[Application | None] = relationship()
