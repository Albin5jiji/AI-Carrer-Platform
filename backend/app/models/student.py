from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .base import TimestampMixin
from .enums import ProficiencyLevel

if TYPE_CHECKING:
    from .account import Account
    from .interview import InterviewPractice, MockInterview
    from .learning import LearningPathItem
    from .mentor import Feedback, MentorAssignment
    from .placement import Application
    from .readiness import ReadinessSnapshot
    from .resume import Resume


class Student(Base, TimestampMixin):
    """Full student career profile. Exactly one row per student account."""

    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), index=True, unique=True, nullable=False
    )
    registration_number: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    program: Mapped[str] = mapped_column(String(120), nullable=False, default="")

    phone: Mapped[str | None] = mapped_column(String(20))
    degree: Mapped[str | None] = mapped_column(String(120))
    department: Mapped[str | None] = mapped_column(String(120), index=True)
    graduation_year: Mapped[int | None] = mapped_column(Integer, index=True)
    cgpa: Mapped[float | None] = mapped_column(Float)
    location: Mapped[str | None] = mapped_column(String(120))
    bio: Mapped[str | None] = mapped_column(Text)

    target_role: Mapped[str | None] = mapped_column(String(120), index=True)
    career_interests: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    target_roles: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    preferred_locations: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    github_url: Mapped[str | None] = mapped_column(String(255))
    linkedin_url: Mapped[str | None] = mapped_column(String(255))
    portfolio_url: Mapped[str | None] = mapped_column(String(255))

    profile_completion: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    account: Mapped[Account] = relationship(back_populates="student")
    skills: Mapped[list[Skill]] = relationship(
        back_populates="student", cascade="all, delete-orphan", order_by="Skill.name"
    )
    projects: Mapped[list[Project]] = relationship(
        back_populates="student", cascade="all, delete-orphan", order_by="Project.id.desc()"
    )
    certifications: Mapped[list[Certification]] = relationship(
        back_populates="student", cascade="all, delete-orphan", order_by="Certification.id.desc()"
    )
    resumes: Mapped[list[Resume]] = relationship(
        back_populates="student", cascade="all, delete-orphan", order_by="Resume.version_number.desc()"
    )
    snapshots: Mapped[list[ReadinessSnapshot]] = relationship(
        back_populates="student", cascade="all, delete-orphan", order_by="ReadinessSnapshot.computed_at.desc()"
    )
    applications: Mapped[list[Application]] = relationship(back_populates="student", cascade="all, delete-orphan")
    learning_items: Mapped[list[LearningPathItem]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    practices: Mapped[list[InterviewPractice]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    mock_interviews: Mapped[list[MockInterview]] = relationship(
        back_populates="student", cascade="all, delete-orphan", order_by="MockInterview.id.desc()"
    )
    mentor_assignments: Mapped[list[MentorAssignment]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    feedback_entries: Mapped[list[Feedback]] = relationship(
        back_populates="student", cascade="all, delete-orphan", order_by="Feedback.id.desc()"
    )



class Skill(Base, TimestampMixin):
    """A skill claimed by the student, with the proficiency used by skill-gap analysis."""

    __tablename__ = "student_skills"
    __table_args__ = (UniqueConstraint("student_id", "name", name="uq_student_skill_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    proficiency: Mapped[ProficiencyLevel] = mapped_column(
        Enum(ProficiencyLevel), default=ProficiencyLevel.intermediate, nullable=False
    )
    years_experience: Mapped[float | None] = mapped_column(Float)

    student: Mapped[Student] = relationship(back_populates="skills")


class Project(Base, TimestampMixin):
    """Project evidence for the project-relevance readiness component."""

    __tablename__ = "student_projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    tech_stack: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    repo_url: Mapped[str | None] = mapped_column(String(255))
    live_url: Mapped[str | None] = mapped_column(String(255))

    student: Mapped[Student] = relationship(back_populates="projects")


class Certification(Base, TimestampMixin):
    """A completed certification, optionally tagged with the skills it proves."""

    __tablename__ = "student_certifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    issuer: Mapped[str | None] = mapped_column(String(160))
    issued_year: Mapped[int | None] = mapped_column(Integer)
    credential_url: Mapped[str | None] = mapped_column(String(255))
    skill_tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    student: Mapped[Student] = relationship(back_populates="certifications")
