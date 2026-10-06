from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, Float, ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .base import TimestampMixin
from .enums import ApplicationStatus, CompanyStatus, DriveStatus, JobPostingStatus

if TYPE_CHECKING:
    from .account import Account
    from .mentor import Mentor
    from .resume import Resume
    from .student import Student


class Company(Base, TimestampMixin):
    """A recruiting company managed by the placement cell."""

    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    industry: Mapped[str | None] = mapped_column(String(120), index=True)
    website: Mapped[str | None] = mapped_column(String(255))
    location: Mapped[str | None] = mapped_column(String(160))
    contact_person: Mapped[str | None] = mapped_column(String(160))
    contact_email: Mapped[str | None] = mapped_column(String(255))
    contact_phone: Mapped[str | None] = mapped_column(String(30))
    status: Mapped[CompanyStatus] = mapped_column(
        Enum(CompanyStatus), default=CompanyStatus.active, nullable=False
    )

    jobs: Mapped[list[JobPosting]] = relationship(back_populates="company", cascade="all, delete-orphan")
    drives: Mapped[list[PlacementDrive]] = relationship(back_populates="company", cascade="all, delete-orphan")


class JobPosting(Base, TimestampMixin):
    """A single opening published for a company."""

    __tablename__ = "job_postings"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(160), index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    required_skills: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    min_cgpa: Mapped[float | None] = mapped_column(Float)
    eligible_departments: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    graduation_years: Mapped[list[int]] = mapped_column(JSON, default=list, nullable=False)
    job_type: Mapped[str] = mapped_column(String(40), default="full_time", nullable=False)
    location: Mapped[str | None] = mapped_column(String(160))
    salary_range: Mapped[str | None] = mapped_column(String(80))
    application_deadline: Mapped[date | None] = mapped_column(Date)
    status: Mapped[JobPostingStatus] = mapped_column(
        Enum(JobPostingStatus), default=JobPostingStatus.draft, nullable=False, index=True
    )
    created_by_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id", ondelete="SET NULL"))

    company: Mapped[Company] = relationship(back_populates="jobs")
    drives: Mapped[list[PlacementDrive]] = relationship(back_populates="job_posting")


class PlacementDrive(Base, TimestampMixin):
    """A hiring event that bundles a company, a job posting and eligibility criteria."""

    __tablename__ = "placement_drives"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    job_posting_id: Mapped[int | None] = mapped_column(
        ForeignKey("job_postings.id", ondelete="SET NULL"), index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    drive_date: Mapped[date | None] = mapped_column(Date)
    application_deadline: Mapped[date | None] = mapped_column(Date, index=True)
    min_cgpa: Mapped[float | None] = mapped_column(Float)
    eligible_departments: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    graduation_years: Mapped[list[int]] = mapped_column(JSON, default=list, nullable=False)
    required_skills: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    location: Mapped[str | None] = mapped_column(String(160))
    requires_mentor_approval: Mapped[bool] = mapped_column(default=True, nullable=False)
    status: Mapped[DriveStatus] = mapped_column(
        Enum(DriveStatus), default=DriveStatus.draft, nullable=False, index=True
    )
    created_by_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id", ondelete="SET NULL"))

    company: Mapped[Company] = relationship(back_populates="drives")
    job_posting: Mapped[JobPosting | None] = relationship(back_populates="drives")
    applications: Mapped[list[Application]] = relationship(
        back_populates="drive", cascade="all, delete-orphan"
    )


class Application(Base, TimestampMixin):
    """A student's application to a placement drive, including mentor review state."""

    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("student_id", "drive_id", name="uq_student_drive_application"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False
    )
    drive_id: Mapped[int] = mapped_column(
        ForeignKey("placement_drives.id", ondelete="CASCADE"), index=True, nullable=False
    )
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    job_posting_id: Mapped[int | None] = mapped_column(ForeignKey("job_postings.id", ondelete="SET NULL"))
    resume_id: Mapped[int | None] = mapped_column(ForeignKey("resumes.id", ondelete="SET NULL"), index=True)

    eligibility_status: Mapped[str] = mapped_column(String(30), default="eligible", nullable=False)
    eligibility_reasons: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    missing_skills: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus), default=ApplicationStatus.pending_mentor_approval, nullable=False, index=True
    )
    mentor_feedback: Mapped[str | None] = mapped_column(Text)
    mentor_id: Mapped[int | None] = mapped_column(ForeignKey("mentors.id", ondelete="SET NULL"), index=True)
    decided_at: Mapped[date | None] = mapped_column(Date)
    note_to_mentor: Mapped[str | None] = mapped_column(Text)
    admin_note: Mapped[str | None] = mapped_column(Text)

    student: Mapped[Student] = relationship(back_populates="applications")
    drive: Mapped[PlacementDrive] = relationship(back_populates="applications")
    company: Mapped[Company] = relationship()
    job_posting: Mapped[JobPosting | None] = relationship()
    resume: Mapped[Resume | None] = relationship()
    mentor: Mapped[Mentor | None] = relationship()
