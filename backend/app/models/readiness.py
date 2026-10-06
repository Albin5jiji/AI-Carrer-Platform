from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .base import TimestampMixin
from .enums import Priority, ProficiencyLevel

if TYPE_CHECKING:
    from .student import Student


class RoleProfile(Base, TimestampMixin):
    """A career target role a student can choose (drives PRS and skill-gap analysis)."""

    __tablename__ = "role_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    category: Mapped[str | None] = mapped_column(String(80))
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    skills: Mapped[list[RoleSkill]] = relationship(
        back_populates="role", cascade="all, delete-orphan", order_by="RoleSkill.display_order"
    )


class RoleSkill(Base, TimestampMixin):
    """Database backed skill requirement of a target role.

    `priority` and `target_proficiency` decide how much a missing skill costs the
    skills component of the readiness score, so two students never get the same result.
    """

    __tablename__ = "role_skills"
    __table_args__ = (UniqueConstraint("role_profile_id", "skill_name", name="uq_role_skill"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    role_profile_id: Mapped[int] = mapped_column(
        ForeignKey("role_profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    role_name: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    skill_name: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    priority: Mapped[Priority] = mapped_column(Enum(Priority), default=Priority.medium, nullable=False)
    target_proficiency: Mapped[ProficiencyLevel] = mapped_column(
        Enum(ProficiencyLevel), default=ProficiencyLevel.intermediate, nullable=False
    )
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    role: Mapped[RoleProfile] = relationship(back_populates="skills")


class ReadinessSnapshot(Base, TimestampMixin):
    """Immutable history row produced every time the readiness score is calculated."""

    __tablename__ = "readiness_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False
    )
    overall_score: Mapped[int] = mapped_column(Integer, nullable=False)
    academics: Mapped[int] = mapped_column(Integer, nullable=False)
    skills: Mapped[int] = mapped_column(Integer, nullable=False)
    projects: Mapped[int] = mapped_column(Integer, nullable=False)
    certifications: Mapped[int] = mapped_column(Integer, nullable=False)
    resume: Mapped[int] = mapped_column(Integer, nullable=False)
    interview: Mapped[int] = mapped_column(Integer, nullable=False)
    weights: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    target_role: Mapped[str | None] = mapped_column(String(120))
    explanation: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    student: Mapped[Student] = relationship(back_populates="snapshots")
