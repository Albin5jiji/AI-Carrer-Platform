from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field

from ..models import ApplicationStatus, CompanyStatus, DriveStatus, JobPostingStatus
from .common import ORMModel


# --- Companies -----------------------------------------------------------------


class CompanyBase(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    description: str | None = None
    industry: str | None = Field(default=None, max_length=120)
    website: str | None = Field(default=None, max_length=255)
    location: str | None = Field(default=None, max_length=160)
    contact_person: str | None = Field(default=None, max_length=160)
    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(default=None, max_length=30)
    status: CompanyStatus = CompanyStatus.active


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    description: str | None = None
    industry: str | None = Field(default=None, max_length=120)
    website: str | None = Field(default=None, max_length=255)
    location: str | None = Field(default=None, max_length=160)
    contact_person: str | None = Field(default=None, max_length=160)
    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(default=None, max_length=30)
    status: CompanyStatus | None = None


class CompanyOut(ORMModel):
    id: int
    name: str
    description: str | None = None
    industry: str | None = None
    website: str | None = None
    location: str | None = None
    contact_person: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    status: CompanyStatus
    created_at: datetime
    job_count: int = 0
    drive_count: int = 0


# --- Job postings --------------------------------------------------------------


class JobPostingBase(BaseModel):
    company_id: int
    title: str = Field(min_length=2, max_length=160)
    description: str | None = None
    required_skills: list[str] = Field(default_factory=list)
    min_cgpa: float | None = Field(default=None, ge=0, le=10)
    eligible_departments: list[str] = Field(default_factory=list)
    graduation_years: list[int] = Field(default_factory=list)
    job_type: str = Field(default="full_time", max_length=40)
    location: str | None = Field(default=None, max_length=160)
    salary_range: str | None = Field(default=None, max_length=80)
    application_deadline: date | None = None
    status: JobPostingStatus = JobPostingStatus.draft


class JobPostingCreate(JobPostingBase):
    pass


class JobPostingUpdate(BaseModel):
    company_id: int | None = None
    title: str | None = Field(default=None, min_length=2, max_length=160)
    description: str | None = None
    required_skills: list[str] | None = None
    min_cgpa: float | None = Field(default=None, ge=0, le=10)
    eligible_departments: list[str] | None = None
    graduation_years: list[int] | None = None
    job_type: str | None = Field(default=None, max_length=40)
    location: str | None = Field(default=None, max_length=160)
    salary_range: str | None = Field(default=None, max_length=80)
    application_deadline: date | None = None
    status: JobPostingStatus | None = None


class JobPostingOut(ORMModel):
    id: int
    company_id: int
    company_name: str | None = None
    title: str
    description: str | None = None
    required_skills: list[str] = Field(default_factory=list)
    min_cgpa: float | None = None
    eligible_departments: list[str] = Field(default_factory=list)
    graduation_years: list[int] = Field(default_factory=list)
    job_type: str
    location: str | None = None
    salary_range: str | None = None
    application_deadline: date | None = None
    status: JobPostingStatus
    created_at: datetime
    drive_count: int = 0


# --- Placement drives ----------------------------------------------------------


class PlacementDriveBase(BaseModel):
    company_id: int
    job_posting_id: int | None = None
    name: str = Field(min_length=2, max_length=200)
    description: str | None = None
    drive_date: date | None = None
    application_deadline: date | None = None
    min_cgpa: float | None = Field(default=None, ge=0, le=10)
    eligible_departments: list[str] = Field(default_factory=list)
    graduation_years: list[int] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)
    location: str | None = Field(default=None, max_length=160)
    requires_mentor_approval: bool = True
    status: DriveStatus = DriveStatus.draft


class PlacementDriveCreate(PlacementDriveBase):
    pass


class PlacementDriveUpdate(BaseModel):
    company_id: int | None = None
    job_posting_id: int | None = None
    name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = None
    drive_date: date | None = None
    application_deadline: date | None = None
    min_cgpa: float | None = Field(default=None, ge=0, le=10)
    eligible_departments: list[str] | None = None
    graduation_years: list[int] | None = None
    required_skills: list[str] | None = None
    location: str | None = Field(default=None, max_length=160)
    requires_mentor_approval: bool | None = None
    status: DriveStatus | None = None


class DriveStatusUpdate(BaseModel):
    status: DriveStatus
    note: str | None = Field(default=None, max_length=500)


class PlacementDriveOut(ORMModel):
    id: int
    company_id: int
    company_name: str | None = None
    job_posting_id: int | None = None
    job_title: str | None = None
    name: str
    description: str | None = None
    drive_date: date | None = None
    application_deadline: date | None = None
    min_cgpa: float | None = None
    eligible_departments: list[str] = Field(default_factory=list)
    graduation_years: list[int] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)
    location: str | None = None
    requires_mentor_approval: bool
    status: DriveStatus
    created_at: datetime
    application_count: int = 0
    eligible_student_count: int = 0
    days_to_deadline: int | None = None


# --- Eligibility and applications ----------------------------------------------


class EligibilityResponse(BaseModel):
    eligible: bool
    status: str
    reasons: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    matched_skills: list[str] = Field(default_factory=list)
    cgpa_ok: bool = True
    department_ok: bool = True
    graduation_year_ok: bool = True
    deadline_open: bool = True
    already_applied: bool = False
    has_approved_resume: bool = False


class ApplicationCreate(BaseModel):
    drive_id: int
    resume_id: int | None = None
    note_to_mentor: str | None = Field(default=None, max_length=1000)


class ApplicationOut(BaseModel):
    id: int
    code: str
    student_id: int
    student_name: str | None = None
    registration_number: str | None = None
    department: str | None = None
    cgpa: float | None = None
    target_role: str | None = None
    drive_id: int
    drive_name: str | None = None
    company_id: int
    company_name: str | None = None
    job_title: str | None = None
    resume_id: int | None = None
    resume_version_name: str | None = None
    eligibility_status: str
    eligibility_reasons: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    status: ApplicationStatus
    mentor_feedback: str | None = None
    mentor_name: str | None = None
    note_to_mentor: str | None = None
    admin_note: str | None = None
    created_at: datetime
    updated_at: datetime
    decided_at: date | None = None
    next_action: str | None = None


class MentorDecisionRequest(BaseModel):
    """Mentor decision for an application awaiting approval."""

    action: str = Field(pattern="^(approve|request_changes)$")
    feedback: str | None = Field(default=None, max_length=2000)


class AdminApplicationUpdate(BaseModel):
    status: ApplicationStatus
    note: str | None = Field(default=None, max_length=1000)


class DriveEligibilityRow(BaseModel):
    """Per-drive eligibility result for the signed-in student."""

    drive_id: int
    eligibility: EligibilityResponse

