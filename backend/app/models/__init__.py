"""SQLAlchemy models for the AI Career Platform.

Importing this package registers every table on `Base.metadata`, which is what makes
`create_all` (development) and Alembic autogenerate (migrations) see the full schema.
"""

from .account import Account, Administrator
from .ai import AISkillGapResult
from .audit import AuditLog
from .enums import (
    ApplicationStatus,
    CompanyStatus,
    Difficulty,
    DriveStatus,
    EligibilityStatus,
    FeedbackStatus,
    InterviewCategory,
    JobPostingStatus,
    LearningStatus,
    NotificationType,
    PracticeStatus,
    Priority,
    ProficiencyLevel,
    ResumeStatus,
    UserRole,
)
from .interview import InterviewPractice, InterviewQuestion, MockInterview
from .learning import LearningPathItem, LearningResource
from .mentor import Feedback, Mentor, MentorAssignment
from .notification import Notification
from .placement import Application, Company, JobPosting, PlacementDrive
from .readiness import ReadinessSnapshot, RoleProfile, RoleSkill
from .resume import Resume
from .student import Certification, Project, Skill, Student

__all__ = [
    "Account",
    "AISkillGapResult",
    "Administrator",
    "Application",
    "ApplicationStatus",
    "AuditLog",
    "Certification",
    "Company",
    "CompanyStatus",
    "Difficulty",
    "DriveStatus",
    "EligibilityStatus",
    "Feedback",
    "FeedbackStatus",
    "InterviewCategory",
    "InterviewPractice",
    "InterviewQuestion",
    "JobPosting",
    "JobPostingStatus",
    "LearningPathItem",
    "LearningResource",
    "LearningStatus",
    "Mentor",
    "MentorAssignment",
    "MockInterview",
    "Notification",
    "NotificationType",
    "PlacementDrive",
    "PracticeStatus",
    "Priority",
    "ProficiencyLevel",
    "Project",
    "ReadinessSnapshot",
    "Resume",
    "ResumeStatus",
    "RoleProfile",
    "RoleSkill",
    "Skill",
    "Student",
    "UserRole",
]
