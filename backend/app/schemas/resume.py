from datetime import datetime

from pydantic import BaseModel, Field

from ..models import ResumeStatus


class ResumeContent(BaseModel):
    """Structured resume body. Kept as JSON so completeness can be scored."""

    education: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)


class ResumeCreate(BaseModel):
    version_name: str | None = Field(default=None, min_length=2, max_length=80)
    title: str | None = Field(default=None, min_length=2, max_length=160)
    target_role: str | None = Field(default=None, min_length=2, max_length=120)
    summary: str | None = Field(default=None, max_length=2000)
    content: ResumeContent = Field(default_factory=ResumeContent)
    file_url: str | None = Field(default=None, max_length=255)


class ResumeUpdate(BaseModel):
    version_name: str | None = Field(default=None, min_length=2, max_length=80)
    title: str | None = Field(default=None, min_length=2, max_length=160)
    target_role: str | None = Field(default=None, min_length=2, max_length=120)
    summary: str | None = Field(default=None, max_length=2000)
    content: ResumeContent | None = None
    file_url: str | None = Field(default=None, max_length=255)


class ResumeOut(BaseModel):
    id: int
    student_id: int
    version_number: int
    version_name: str
    title: str
    target_role: str
    summary: str | None = None
    content: dict = Field(default_factory=dict)
    file_url: str | None = None
    status: ResumeStatus
    mentor_feedback: str | None = None
    reviewer_name: str | None = None
    submitted_at: datetime | None = None
    reviewed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    completeness: int = 0


class ResumeReviewRequest(BaseModel):
    """Mentor decision on a submitted resume version."""

    action: str = Field(pattern="^(approve|request_changes)$")
    feedback: str | None = Field(default=None, max_length=2000)


class ResumeUploadRequest(BaseModel):
    filename: str = Field(min_length=5, max_length=255)
    content_type: str = Field(min_length=1, max_length=120)
    size: int = Field(gt=0)


class ResumeUploadUrl(BaseModel):
    storage_key: str
    upload_url: str
    expires_in: int


class ResumeDownloadUrl(BaseModel):
    download_url: str
    expires_in: int
