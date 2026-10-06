"""Application lifecycle: student apply/withdraw, mentor review, admin monitoring."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_account, get_current_student, require_mentor
from ..models import (
    Account,
    Application,
    ApplicationStatus,
    DriveStatus,
    Mentor,
    MentorAssignment,
    NotificationType,
    PlacementDrive,
    Resume,
    ResumeStatus,
    Student,
    UserRole,
)
from ..schemas.common import Message
from ..schemas.placement import AdminApplicationUpdate, ApplicationCreate, ApplicationOut
from ..services.audit import record_audit
from ..services.eligibility import evaluate_drive_for_student
from ..services.lifecycle import allowed_transitions, can_transition
from ..services.notifications import notify
from .serializers import application_out

router = APIRouter(prefix="/applications", tags=["Applications"])


def _assigned_mentor(db: Session, student_id: int) -> Mentor | None:
    assignment = (
        db.query(MentorAssignment)
        .filter(MentorAssignment.student_id == student_id, MentorAssignment.is_active.is_(True))
        .first()
    )
    return db.get(Mentor, assignment.mentor_id) if assignment is not None else None


@router.get("/me", response_model=list[ApplicationOut])
def my_applications(
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> list[ApplicationOut]:
    rows = (
        db.query(Application)
        .filter(Application.student_id == student.id)
        .order_by(Application.updated_at.desc())
        .all()
    )
    return [application_out(row) for row in rows]


@router.post("/me", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
def apply_to_drive(
    payload: ApplicationCreate,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> ApplicationOut:
    drive = db.get(PlacementDrive, payload.drive_id)
    if drive is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Placement drive not found")
    if drive.status != DriveStatus.open:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="This drive is not open for applications"
        )

    eligibility = evaluate_drive_for_student(db, drive, student)
    if not eligibility.eligible:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not eligible for this drive: " + "; ".join(eligibility.reasons),
        )

    existing = (
        db.query(Application)
        .filter(Application.student_id == student.id, Application.drive_id == drive.id)
        .one_or_none()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="You have already applied to this drive"
        )

    resume: Resume | None = None
    if payload.resume_id is not None:
        resume = db.get(Resume, payload.resume_id)
        if resume is None or resume.student_id != student.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume version not found")
        if resume.status != ResumeStatus.approved:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only an approved resume version can be attached to an application",
            )
    else:
        resume = (
            db.query(Resume)
            .filter(Resume.student_id == student.id, Resume.status == ResumeStatus.approved)
            .order_by(Resume.version_number.desc())
            .first()
        )

    mentor = _assigned_mentor(db, student.id)
    application = Application(
        code=f"APP-{drive.id:04d}-{student.id:05d}",
        student_id=student.id,
        drive_id=drive.id,
        company_id=drive.company_id,
        job_posting_id=drive.job_posting_id,
        resume_id=resume.id if resume else None,
        eligibility_status=eligibility.status,
        eligibility_reasons=eligibility.reasons,
        missing_skills=eligibility.missing_skills,
        status=(
            ApplicationStatus.pending_mentor_approval
            if drive.requires_mentor_approval
            else ApplicationStatus.approved
        ),
        mentor_id=mentor.id if mentor else None,
        note_to_mentor=payload.note_to_mentor,
    )
    db.add(application)
    db.flush()

    if mentor is not None and mentor.account_id and drive.requires_mentor_approval:
        notify(
            db,
            account_id=mentor.account_id,
            title="Application awaiting your approval",
            message=(
                f"{account.full_name} ({student.registration_number}) applied to '{drive.name}' "
                "and needs mentor approval."
            ),
            type_=NotificationType.application_status,
            entity_type="application",
            entity_id=application.id,
        )
    record_audit(
        db,
        actor=account,
        action="apply_to_drive",
        entity_type="application",
        entity_id=application.id,
        summary=f"Applied to drive '{drive.name}'",
        meta={"eligibility": eligibility.status},
    )
    db.commit()
    db.refresh(application)
    return application_out(application)


@router.post("/{application_id}/withdraw", response_model=ApplicationOut)
def withdraw_application(
    application_id: int,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> ApplicationOut:
    application = db.get(Application, application_id)
    if application is None or application.student_id != student.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    if not can_transition(application.status, ApplicationStatus.withdrawn):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"An application in state '{application.status.value}' cannot be withdrawn. "
                f"Allowed: {', '.join(allowed_transitions(application.status)) or 'none'}"
            ),
        )

    application.status = ApplicationStatus.withdrawn
    application.decided_at = date.today()
    record_audit(
        db,
        actor=account,
        action="withdraw_application",
        entity_type="application",
        entity_id=application.id,
        summary=f"Withdrew application {application.code}",
    )
    db.commit()
    db.refresh(application)
    return application_out(application)


@router.post("/{application_id}/decision", response_model=ApplicationOut)
def mentor_decision(
    application_id: int,
    action: str = Query(pattern="^(approve|request_changes)$"),
    feedback: str | None = Query(default=None, max_length=2000),
    mentor: Mentor = Depends(require_mentor),
    db: Session = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> ApplicationOut:
    """Mentor approval or change request for an application awaiting review."""

    from ..models import Feedback, FeedbackStatus

    application = db.get(Application, application_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    assigned = any(
        assignment.student_id == application.student_id and assignment.is_active
        for assignment in mentor.assignments
    )
    if not assigned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This application belongs to a student you do not mentor",
        )

    target = ApplicationStatus.approved if action == "approve" else ApplicationStatus.changes_requested
    if not can_transition(application.status, target):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"An application in state '{application.status.value}' cannot move to '{target.value}'. "
                f"Allowed: {', '.join(allowed_transitions(application.status)) or 'none'}"
            ),
        )
    if target == ApplicationStatus.changes_requested and not (feedback or "").strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Explain what the student should change before requesting changes",
        )

    application.status = target
    application.mentor_id = mentor.id
    application.mentor_feedback = feedback or application.mentor_feedback
    application.decided_at = date.today()

    drive_name = application.drive.name if application.drive else "the drive"
    approved = target == ApplicationStatus.approved
    notify(
        db,
        account_id=application.student.account_id if application.student else None,
        title="Application approved by your mentor" if approved else "Changes requested on your application",
        message=(
            f"Your application for '{drive_name}' was "
            f"{'approved' if approved else 'sent back with requested changes'}."
            + (f" Feedback: {feedback}" if feedback else "")
        ),
        type_=NotificationType.application_status,
        entity_type="application",
        entity_id=application.id,
    )

    if feedback:
        db.add(
            Feedback(
                student_id=application.student_id,
                mentor_id=mentor.id,
                application_id=application.id,
                title=f"Application review: {drive_name}",
                body=feedback,
                status=FeedbackStatus.resolved if approved else FeedbackStatus.action_needed,
            )
        )

    record_audit(
        db,
        actor=account,
        action="mentor_application_decision",
        entity_type="application",
        entity_id=application.id,
        summary=f"Mentor set application {application.code} to {target.value}",
    )
    db.commit()
    db.refresh(application)
    return application_out(application)

