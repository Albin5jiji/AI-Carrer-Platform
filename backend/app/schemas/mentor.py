from __future__ import annotations

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from ..models import FeedbackStatus, Priority, ProficiencyLevel, ResumeStatus
from .notification import NotificationOut
from .placement import ApplicationOut
from .resume import ResumeOut


class SkillGapSummary(BaseModel):
    skill_name: str
    priority: Priority
    status: str


class MentorStudentSummary(BaseModel):
    student_id: int
    account_id: int
    full_name: str
    email: str
    registration_number: str
    program: str
    department: str | None = None
    graduation_year: int | None = None
    cgpa: float | None = None
    target_role: str | None = None
    profile_completion: int = 0
    overall_score: int | None = None
    resume_status: ResumeStatus | None = None
    pending_resume_reviews: int = 0
    pending_application_reviews: int = 0
    open_applications: int = 0
    needs_attention: bool = False
    attention_reasons: list[str] = Field(default_factory=list)


class MentorStudentDetail(BaseModel):
    student: MentorStudentSummary
    skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    skill_coverage_percent: int = 0
    readiness_components: dict = Field(default_factory=dict)
    readiness_history: list[dict] = Field(default_factory=list)
    resumes: list[ResumeOut] = Field(default_factory=list)
    applications: list[ApplicationOut] = Field(default_factory=list)
    feedback: list[FeedbackOut] = Field(default_factory=list)


class FeedbackCreate(BaseModel):
    student_id: int
    title: str = Field(min_length=2, max_length=160)
    body: str = Field(min_length=2, max_length=4000)
    resume_id: int | None = None
    application_id: int | None = None
    status: FeedbackStatus = FeedbackStatus.open


class FeedbackUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=160)
    body: str | None = Field(default=None, min_length=2, max_length=4000)
    status: FeedbackStatus | None = None


class FeedbackOut(BaseModel):
    id: int
    student_id: int
    student_name: str | None = None
    mentor_id: int
    mentor_name: str | None = None
    resume_id: int | None = None
    application_id: int | None = None
    title: str
    body: str
    status: FeedbackStatus
    created_at: datetime


class AssignmentCreate(BaseModel):
    mentor_id: int
    student_id: int
    notes: str | None = Field(default=None, max_length=500)


class AssignmentOut(BaseModel):
    id: int
    mentor_id: int
    mentor_name: str | None = None
    student_id: int
    student_name: str | None = None
    registration_number: str | None = None
    is_active: bool
    notes: str | None = None
    created_at: datetime


class MentorDashboardOut(BaseModel):
    mentor_name: str
    assigned_student_count: int
    pending_resume_reviews: int
    pending_application_reviews: int
    students_needing_attention: list[MentorStudentSummary] = Field(default_factory=list)
    recent_feedback: list[FeedbackOut] = Field(default_factory=list)
    recent_notifications: list[NotificationOut] = Field(default_factory=list)
    average_readiness: int | None = None
    unassigned_student_count: int = 0


class SkillRequirementIn(BaseModel):
    skill_name: str = Field(min_length=1, max_length=80)
    priority: Priority = Priority.medium
    target_proficiency: ProficiencyLevel = ProficiencyLevel.intermediate
