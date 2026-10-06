from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from ..models import NotificationType, UserRole
from .mentor import AssignmentOut, MentorStudentSummary
from .placement import ApplicationOut


class NotificationOut(BaseModel):
    id: int
    title: str
    message: str
    type: NotificationType
    entity_type: str | None = None
    entity_id: int | None = None
    is_read: bool
    created_at: datetime


class NotificationListOut(BaseModel):
    unread_count: int
    items: list[NotificationOut]


class AdminUserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: UserRole
    identifier: str
    department_or_program: str
    is_active: bool
    created_at: datetime


class AdminUserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    role: UserRole
    identifier: str = Field(min_length=2, max_length=30)
    department_or_program: str = Field(min_length=2, max_length=120)


class AdminUserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    is_active: bool | None = None
    role: UserRole | None = None
    department_or_program: str | None = Field(default=None, min_length=2, max_length=120)


class AuditLogOut(BaseModel):
    id: int
    actor_account_id: int | None = None
    actor_email: str | None = None
    actor_role: str | None = None
    action: str
    entity_type: str
    entity_id: int | None = None
    summary: str | None = None
    meta: dict = Field(default_factory=dict)
    created_at: datetime


class AuditLogPage(BaseModel):
    items: list[AuditLogOut]
    total: int
    page: int
    page_size: int


class DashboardCounts(BaseModel):
    students: int
    mentors: int
    administrators: int
    companies: int
    active_companies: int
    job_postings: int
    published_job_postings: int
    placement_drives: int
    open_drives: int
    applications: int
    applications_by_status: dict[str, int] = Field(default_factory=dict)
    pending_mentor_reviews: int
    pending_resume_reviews: int
    students_without_mentor: int
    notifications_unread: int


class AdminDashboardOut(BaseModel):
    counts: DashboardCounts
    upcoming_deadlines: list[dict] = Field(default_factory=list)
    recent_applications: list[ApplicationOut] = Field(default_factory=list)
    recent_audit_logs: list[AuditLogOut] = Field(default_factory=list)
    top_companies_by_drives: list[dict] = Field(default_factory=list)


class AdminStudentRow(MentorStudentSummary):
    mentor_names: list[str] = Field(default_factory=list)
    applications_count: int = 0


class AssignmentListOut(BaseModel):
    items: list[AssignmentOut]
    total: int
