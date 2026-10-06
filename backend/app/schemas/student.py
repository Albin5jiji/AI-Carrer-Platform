from pydantic import BaseModel, ConfigDict, EmailStr, Field

from ..models import ProficiencyLevel
from .common import ORMModel


class SkillIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    proficiency: ProficiencyLevel = ProficiencyLevel.intermediate
    years_experience: float | None = Field(default=None, ge=0, le=50)


class SkillOut(ORMModel):
    id: int
    name: str
    proficiency: ProficiencyLevel
    years_experience: float | None = None


class ProjectIn(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    description: str | None = None
    tech_stack: list[str] = Field(default_factory=list)
    repo_url: str | None = None
    live_url: str | None = None


class ProjectOut(ORMModel):
    id: int
    title: str
    description: str | None = None
    tech_stack: list[str] = Field(default_factory=list)
    repo_url: str | None = None
    live_url: str | None = None


class CertificationIn(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    issuer: str | None = Field(default=None, max_length=160)
    issued_year: int | None = Field(default=None, ge=1980, le=2100)
    credential_url: str | None = None
    skill_tags: list[str] = Field(default_factory=list)


class CertificationOut(ORMModel):
    id: int
    name: str
    issuer: str | None = None
    issued_year: int | None = None
    credential_url: str | None = None
    skill_tags: list[str] = Field(default_factory=list)


class StudentProfileUpdate(BaseModel):
    """Partial update: only the fields sent by the client are changed."""

    model_config = ConfigDict(extra="forbid")

    phone: str | None = Field(default=None, max_length=20)
    degree: str | None = Field(default=None, max_length=120)
    department: str | None = Field(default=None, max_length=120)
    program: str | None = Field(default=None, max_length=120)
    graduation_year: int | None = Field(default=None, ge=2000, le=2100)
    cgpa: float | None = Field(default=None, ge=0, le=10)
    location: str | None = Field(default=None, max_length=120)
    bio: str | None = None
    target_role: str | None = Field(default=None, max_length=120)
    target_roles: list[str] | None = None
    career_interests: list[str] | None = None
    preferred_locations: list[str] | None = None
    github_url: str | None = Field(default=None, max_length=255)
    linkedin_url: str | None = Field(default=None, max_length=255)
    portfolio_url: str | None = Field(default=None, max_length=255)


class StudentProfileOut(BaseModel):
    id: int
    account_id: int
    full_name: str
    email: EmailStr
    registration_number: str
    program: str
    phone: str | None = None
    degree: str | None = None
    department: str | None = None
    graduation_year: int | None = None
    cgpa: float | None = None
    location: str | None = None
    bio: str | None = None
    target_role: str | None = None
    target_roles: list[str] = Field(default_factory=list)
    career_interests: list[str] = Field(default_factory=list)
    preferred_locations: list[str] = Field(default_factory=list)
    github_url: str | None = None
    linkedin_url: str | None = None
    portfolio_url: str | None = None
    profile_completion: int = 0
    skills: list[SkillOut] = Field(default_factory=list)
    projects: list[ProjectOut] = Field(default_factory=list)
    certifications: list[CertificationOut] = Field(default_factory=list)


class RoleProfileOut(ORMModel):
    id: int
    name: str
    category: str | None = None
    description: str | None = None
