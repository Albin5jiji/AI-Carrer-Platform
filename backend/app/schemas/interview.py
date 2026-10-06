from datetime import datetime

from pydantic import BaseModel, Field

from ..models import Difficulty, InterviewCategory, PracticeStatus


class InterviewQuestionOut(BaseModel):
    id: int
    category: InterviewCategory
    target_role: str | None = None
    difficulty: Difficulty
    question: str
    guidance: str | None = None
    skill_tags: list[str] = Field(default_factory=list)
    practice_status: PracticeStatus = PracticeStatus.not_started
    self_rating: int | None = None
    practiced_at: datetime | None = None


class InterviewCategoryProgress(BaseModel):
    category: InterviewCategory
    total: int
    practiced: int
    needs_revision: int
    progress_percent: int


class MockInterviewOut(BaseModel):
    id: int
    target_role: str | None = None
    mode: str
    scheduled_for: datetime | None = None
    completed: bool
    score: int | None = None
    strengths: str | None = None
    improvements: str | None = None
    feedback: str | None = None
    created_at: datetime


class MockInterviewCreate(BaseModel):
    target_role: str | None = Field(default=None, max_length=120)
    mode: str = Field(default="technical", pattern="^(technical|behavioral|mixed)$")
    scheduled_for: datetime | None = None
    score: int | None = Field(default=None, ge=0, le=100)
    completed: bool = False
    strengths: str | None = None
    improvements: str | None = None


class InterviewOverview(BaseModel):
    student_id: int
    target_role: str | None = None
    total_questions: int
    practiced_count: int
    needs_revision_count: int
    progress_percent: int
    interview_component_score: int
    categories: list[InterviewCategoryProgress]
    mock_interviews: list[MockInterviewOut]
    completed_mock_interviews: int
    average_mock_score: int | None = None
    suggestions: list[str]


class PracticeUpdate(BaseModel):
    status: PracticeStatus
    self_rating: int | None = Field(default=None, ge=1, le=5)
    notes: str | None = Field(default=None, max_length=1000)
