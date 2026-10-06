import enum


class UserRole(str, enum.Enum):
    student = "student"
    mentor = "mentor"
    administrator = "administrator"


class ProficiencyLevel(str, enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class Priority(str, enum.Enum):
    high = "high"
    medium = "medium"
    low = "low"


class Difficulty(str, enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class ResumeStatus(str, enum.Enum):
    """Resume review workflow: draft -> pending_review -> approved | changes_requested."""

    draft = "draft"
    pending_review = "pending_review"
    approved = "approved"
    changes_requested = "changes_requested"


class LearningStatus(str, enum.Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    completed = "completed"


class InterviewCategory(str, enum.Enum):
    technical = "technical"
    behavioral = "behavioral"
    role_specific = "role_specific"


class PracticeStatus(str, enum.Enum):
    not_started = "not_started"
    practiced = "practiced"
    needs_revision = "needs_revision"


class CompanyStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"


class JobPostingStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    closed = "closed"


class DriveStatus(str, enum.Enum):
    draft = "draft"
    open = "open"
    closed = "closed"
    completed = "completed"


class ApplicationStatus(str, enum.Enum):
    """Single documented lifecycle for a placement application.

    pending_mentor_approval -> approved | changes_requested
    changes_requested       -> pending_mentor_approval
    approved                -> submitted
    submitted               -> shortlisted | rejected
    shortlisted             -> interview_scheduled | rejected
    interview_scheduled     -> selected | rejected
    any open state          -> withdrawn (student) / rejected (admin)
    """

    pending_mentor_approval = "pending_mentor_approval"
    changes_requested = "changes_requested"
    approved = "approved"
    submitted = "submitted"
    shortlisted = "shortlisted"
    interview_scheduled = "interview_scheduled"
    selected = "selected"
    rejected = "rejected"
    withdrawn = "withdrawn"


class EligibilityStatus(str, enum.Enum):
    eligible = "eligible"
    not_eligible = "not_eligible"


class FeedbackStatus(str, enum.Enum):
    open = "open"
    action_needed = "action_needed"
    resolved = "resolved"


class NotificationType(str, enum.Enum):
    application_status = "application_status"
    mentor_feedback = "mentor_feedback"
    resume_review = "resume_review"
    deadline_reminder = "deadline_reminder"
    drive_announcement = "drive_announcement"
    eligibility_update = "eligibility_update"
    readiness_update = "readiness_update"
    general = "general"
