"""Application lifecycle: the single documented set of allowed status transitions."""

from sqlalchemy.orm import Session

from ..models import ApplicationStatus, Resume, ResumeStatus

# pending_mentor_approval -> approved | changes_requested | withdrawn
# changes_requested      -> pending_mentor_approval | withdrawn
# approved               -> submitted | withdrawn | rejected
# submitted              -> shortlisted | rejected | withdrawn
# shortlisted            -> interview_scheduled | selected | rejected
# interview_scheduled    -> selected | rejected
# selected / rejected / withdrawn are terminal states.
ALLOWED_TRANSITIONS: dict[ApplicationStatus, set[ApplicationStatus]] = {
    ApplicationStatus.pending_mentor_approval: {
        ApplicationStatus.approved,
        ApplicationStatus.changes_requested,
        ApplicationStatus.withdrawn,
    },
    ApplicationStatus.changes_requested: {
        ApplicationStatus.pending_mentor_approval,
        ApplicationStatus.withdrawn,
    },
    ApplicationStatus.approved: {
        ApplicationStatus.submitted,
        ApplicationStatus.withdrawn,
        ApplicationStatus.rejected,
    },
    ApplicationStatus.submitted: {
        ApplicationStatus.shortlisted,
        ApplicationStatus.rejected,
        ApplicationStatus.withdrawn,
    },
    ApplicationStatus.shortlisted: {
        ApplicationStatus.interview_scheduled,
        ApplicationStatus.selected,
        ApplicationStatus.rejected,
    },
    ApplicationStatus.interview_scheduled: {
        ApplicationStatus.selected,
        ApplicationStatus.rejected,
    },
    ApplicationStatus.selected: set(),
    ApplicationStatus.rejected: set(),
    ApplicationStatus.withdrawn: set(),
}

ACTIVE_APPLICATION_STATUSES = {
    ApplicationStatus.pending_mentor_approval,
    ApplicationStatus.changes_requested,
    ApplicationStatus.approved,
    ApplicationStatus.submitted,
    ApplicationStatus.shortlisted,
    ApplicationStatus.interview_scheduled,
    ApplicationStatus.selected,
}

NEXT_ACTION_HINTS: dict[ApplicationStatus, str] = {
    ApplicationStatus.pending_mentor_approval: "Waiting for your mentor to review this application.",
    ApplicationStatus.changes_requested: "Update what your mentor asked for and resubmit.",
    ApplicationStatus.approved: "Approved by your mentor and ready for submission to the company.",
    ApplicationStatus.submitted: "Submitted to the company. Watch for shortlisting updates.",
    ApplicationStatus.shortlisted: "Shortlisted. Prepare for the next round.",
    ApplicationStatus.interview_scheduled: "Interview scheduled. Complete your interview preparation.",
    ApplicationStatus.selected: "Selected. Congratulations!",
    ApplicationStatus.rejected: "Not moving forward for this drive. Review the feedback and try the next drive.",
    ApplicationStatus.withdrawn: "You withdrew this application.",
}


def can_transition(current: ApplicationStatus, target: ApplicationStatus) -> bool:
    return target in ALLOWED_TRANSITIONS.get(current, set())


def allowed_transitions(current: ApplicationStatus) -> list[str]:
    return sorted(status.value for status in ALLOWED_TRANSITIONS.get(current, set()))


def compute_next_action(status: ApplicationStatus) -> str:
    return NEXT_ACTION_HINTS.get(status, "")


def has_approved_resume(db: Session, student_id: int) -> bool:
    return (
        db.query(Resume)
        .filter(Resume.student_id == student_id, Resume.status == ResumeStatus.approved)
        .count()
        > 0
    )
