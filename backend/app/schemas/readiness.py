from datetime import datetime

from pydantic import BaseModel, Field

from ..models import Difficulty, LearningStatus, Priority, ProficiencyLevel


# --- Skill gap -----------------------------------------------------------------


class SkillGapItem(BaseModel):
    skill_name: str
    priority: Priority
    target_proficiency: ProficiencyLevel
    current_proficiency: ProficiencyLevel | None = None
    status: str  # "covered" | "partial" | "missing"
    score: int  # 0-100 contribution of this skill to the skills component
    action: str


class SkillGapResponse(BaseModel):
    target_role: str
    has_role_data: bool
    required_skill_count: int
    covered_skill_count: int
    missing_skill_count: int
    coverage_percent: int
    skills_component_score: int
    items: list[SkillGapItem]


# --- Readiness -----------------------------------------------------------------


class ReadinessComponent(BaseModel):
    key: str
    label: str
    score: int
    weight: int
    weighted_points: float
    explanation: str


class ReadinessResponse(BaseModel):
    student_id: int
    overall_score: int
    level: str
    target_role: str | None = None
    components: list[ReadinessComponent]
    suggestions: list[str]
    explanation: list[str]
    disclaimer: str
    computed_at: datetime


class ReadinessSnapshotOut(BaseModel):
    id: int
    overall_score: int
    academics: int
    skills: int
    projects: int
    certifications: int
    resume: int
    interview: int
    target_role: str | None = None
    computed_at: datetime


class ReadinessHistoryResponse(BaseModel):
    student_id: int
    target_role: str | None = None
    latest_score: int | None = None
    previous_score: int | None = None
    change: int | None = None
    snapshot_count: int
    snapshots: list[ReadinessSnapshotOut]
    improvement_timeline: list[str]


# --- Learning path -------------------------------------------------------------


class LearningPathItemOut(BaseModel):
    id: int
    skill_name: str
    priority: Priority
    status: LearningStatus
    progress_percent: int
    target_date: str | None = None
    title: str
    provider: str | None = None
    url: str | None = None
    resource_type: str
    difficulty: Difficulty
    estimated_hours: float
    description: str | None = None


class LearningPathResponse(BaseModel):
    student_id: int
    target_role: str | None = None
    total_items: int
    not_started: int
    in_progress: int
    completed: int
    completion_percent: int
    total_estimated_hours: float
    remaining_estimated_hours: float
    next_action: str | None = None
    items: list[LearningPathItemOut]


class LearningProgressUpdate(BaseModel):
    status: LearningStatus | None = None
    progress_percent: int | None = Field(default=None, ge=0, le=100)
    notes: str | None = Field(default=None, max_length=1000)
    target_date: str | None = None


class AISkillGapAnalysisOut(BaseModel):
    strengths: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    explanation: str
    outdated: bool = False
