"""Mentor module: assigned students, monitoring, resume and application review, feedback."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_account, get_current_mentor
from ..models import (
    Account,
    Application,
    ApplicationStatus,
    Feedback,
    FeedbackStatus,
    Mentor,
    MentorAssignment,
    Notification as NotificationModel,
    NotificationType,
    Resume,
    ResumeStatus,
    Student,
)
from ..schemas.mentor import (
    FeedbackCreate,
    FeedbackOut,
    FeedbackUpdate,
    MentorDashboardOut,
    MentorStudentDetail,
)
from ..schemas.notification import NotificationOut
from ..schemas.placement import ApplicationOut
from ..schemas.resume import ResumeDownloadUrl, ResumeOut, ResumeReviewRequest
from ..services.audit import record_audit
from ..services.readiness import build_skill_gap, calculate_readiness, latest_snapshot, snapshot_to_dict
from ..services.notifications import notify
from ..services.resume_storage import create_download
from ..config import settings
from .serializers import (
    application_out,
    feedback_out,
    resume_out,
    student_summary,
)

router = APIRouter(prefix="/mentor", tags=["Mentor"])


def _assigned_students(db: Session, mentor: Mentor) -> list[Student]:
    student_ids = [
        assignment.student_id for assignment in mentor.assignments if assignment.is_active
    ]
    if not student_ids:
        return []
    return db.query(Student).filter(Student.id.in_(student_ids)).all()


def _has_active_assignment(db: Session, mentor_id: int, student_id: int) -> bool:
    return (
        db.query(MentorAssignment.id)
        .filter(
            MentorAssignment.mentor_id == mentor_id,
            MentorAssignment.student_id == student_id,
            MentorAssignment.is_active.is_(True),
        )
        .first()
        is not None
    )


def _mentor_history(db: Session, student: Student, limit: int = 12) -> list[dict]:
    from ..services.readiness import build_history

    return [snapshot_to_dict(snapshot) for snapshot in build_history(db, student, limit=limit)]


@router.get("/dashboard", response_model=MentorDashboardOut)
def mentor_dashboard(
    mentor: Mentor = Depends(get_current_mentor),
    db: Session = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> MentorDashboardOut:
    students = _assigned_students(db, mentor)
    summaries = [student_summary(db, student) for student in students]

    pending_resume_reviews = (
        db.query(Resume)
        .join(Student, Student.id == Resume.student_id)
        .filter(
            Student.id.in_([student.id for student in students]) if students else False,
            Resume.status == ResumeStatus.pending_review,
        )
        .count()
    )
    pending_application_reviews = (
        db.query(Application)
        .filter(
            Application.student_id.in_([student.id for student in students]) if students else False,
            Application.status == ApplicationStatus.pending_mentor_approval,
        )
        .count()
    )

    recent_feedback = (
        db.query(Feedback)
        .filter(Feedback.mentor_id == mentor.id)
        .order_by(Feedback.id.desc())
        .limit(5)
        .all()
    )
    notifications = (
        db.query(NotificationModel)
        .filter(NotificationModel.account_id == account.id)
        .order_by(NotificationModel.id.desc())
        .limit(5)
        .all()
    )

    scored = [summary.overall_score for summary in summaries if summary.overall_score is not None]

    return MentorDashboardOut(
        mentor_name=account.full_name,
        assigned_student_count=len(students),
        pending_resume_reviews=pending_resume_reviews,
        pending_application_reviews=pending_application_reviews,
        students_needing_attention=[summary for summary in summaries if summary.needs_attention][:5],
        recent_feedback=[feedback_out(entry) for entry in recent_feedback],
        recent_notifications=[
            NotificationOut(
                id=row.id,
                title=row.title,
                message=row.message,
                type=row.type,
                entity_type=row.entity_type,
                entity_id=row.entity_id,
                is_read=row.is_read,
                created_at=row.created_at,
            )
            for row in notifications
        ],
        average_readiness=round(sum(scored) / len(scored)) if scored else None,
        unassigned_student_count=(
            db.query(Student).count() - len(students)
        ),
    )


@router.get("/students")
def list_assigned_students(
    search: str | None = None,
    needs_attention: bool = False,
    mentor: Mentor = Depends(get_current_mentor),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Assigned students with readiness, review load and attention flags."""

    students = _assigned_students(db, mentor)
    summaries = [student_summary(db, student) for student in students]

    if search:
        needle = search.strip().lower()
        summaries = [
            summary
            for summary in summaries
            if needle in summary.full_name.lower()
            or needle in summary.registration_number.lower()
            or needle in (summary.target_role or "").lower()
        ]
    if needs_attention:
        summaries = [summary for summary in summaries if summary.needs_attention]

    summaries.sort(key=lambda summary: (not summary.needs_attention, -(summary.overall_score or 0)))
    return [summary.model_dump(mode="json") for summary in summaries]


@router.get("/students/{student_id}", response_model=MentorStudentDetail)
def review_student(
    student_id: int,
    mentor: Mentor = Depends(get_current_mentor),
    db: Session = Depends(get_db),
) -> MentorStudentDetail:
    """Everything a mentor needs to review one student, in a single response."""

    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    assigned_ids = {assignment.student_id for assignment in mentor.assignments if assignment.is_active}
    if student_id not in assigned_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This student is not assigned to you")

    gap = build_skill_gap(db, student)
    readiness = calculate_readiness(db, student, persist=False)
    snapshot = latest_snapshot(db, student.id)

    resumes = (
        db.query(Resume).filter(Resume.student_id == student.id).order_by(Resume.version_number.desc()).all()
    )
    applications = (
        db.query(Application)
        .filter(Application.student_id == student.id)
        .order_by(Application.updated_at.desc())
        .all()
    )
    feedback_rows = (
        db.query(Feedback).filter(Feedback.student_id == student.id).order_by(Feedback.id.desc()).all()
    )

    return MentorStudentDetail(
        student=student_summary(db, student),
        skills=[skill.name for skill in student.skills],
        missing_skills=[item.skill_name for item in gap.items if item.status != "covered"],
        skill_coverage_percent=gap.coverage_percent,
        readiness_components={
            "overall_score": readiness.overall_score,
            "level": readiness.level,
            "last_calculated": snapshot.computed_at.isoformat() if snapshot and snapshot.computed_at else None,
            "components": [component.model_dump(mode="json") for component in readiness.components],
        },
        readiness_history=_mentor_history(db, student),
        resumes=[resume_out(resume) for resume in resumes],
        applications=[application_out(application) for application in applications],
        feedback=[feedback_out(entry) for entry in feedback_rows],
    )


@router.get("/resumes/pending", response_model=list[ResumeOut])
def pending_resumes(
    mentor: Mentor = Depends(get_current_mentor),
    db: Session = Depends(get_db),
) -> list[ResumeOut]:
    students = _assigned_students(db, mentor)
    if not students:
        return []

    rows = (
        db.query(Resume)
        .filter(
            Resume.student_id.in_([student.id for student in students]),
            Resume.status == ResumeStatus.pending_review,
        )
        .order_by(Resume.submitted_at.asc())
        .all()
    )
    return [resume_out(row) for row in rows]


@router.get("/resumes/{resume_id}/download-url", response_model=ResumeDownloadUrl)
def mentor_resume_download_url(
    resume_id: int,
    mentor: Mentor = Depends(get_current_mentor),
    db: Session = Depends(get_db),
) -> ResumeDownloadUrl:
    """Short-lived private PDF link for the student's assigned mentor."""

    resume = db.get(Resume, resume_id)
    is_assigned = resume is not None and _has_active_assignment(db, mentor.id, resume.student_id)
    if resume is None or not is_assigned:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume version not found")
    if not resume.file_url or not resume.file_url.startswith("s3://"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume PDF not found")
    return ResumeDownloadUrl(
        download_url=create_download(resume.file_url.removeprefix("s3://")),
        expires_in=settings.resume_presign_expiry_seconds,
    )


@router.post("/resumes/{resume_id}/review", response_model=ResumeOut)
def review_resume(
    resume_id: int,
    payload: ResumeReviewRequest,
    mentor: Mentor = Depends(get_current_mentor),
    db: Session = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> ResumeOut:
    """Approve a resume version or request changes, with feedback for the student."""

    resume = db.get(Resume, resume_id)
    if resume is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume version not found")

    if not _has_active_assignment(db, mentor.id, resume.student_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This student is not assigned to you")
    if resume.status != ResumeStatus.pending_review:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Only a submitted version can be reviewed (current state: {resume.status.value})",
        )
    if payload.action == "request_changes" and not (payload.feedback or "").strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Add feedback explaining the requested changes",
        )

    approved = payload.action == "approve"
    resume.status = ResumeStatus.approved if approved else ResumeStatus.changes_requested
    resume.mentor_feedback = payload.feedback
    resume.reviewed_by_mentor_id = mentor.id
    resume.reviewed_at = datetime.now(timezone.utc)

    student = resume.student
    notify(
        db,
        account_id=student.account_id if student else None,
        title="Resume approved" if approved else "Changes requested on your resume",
        message=(
            f"'{resume.version_name}' was {'approved' if approved else 'reviewed with requested changes'} "
            f"by your mentor."
            + (f" Feedback: {payload.feedback}" if payload.feedback else "")
        ),
        type_=NotificationType.resume_review,
        entity_type="resume",
        entity_id=resume.id,
    )

    if payload.feedback:
        db.add(
            Feedback(
                student_id=resume.student_id,
                mentor_id=mentor.id,
                resume_id=resume.id,
                title=f"Resume review: {resume.version_name}",
                body=payload.feedback,
                status=FeedbackStatus.resolved if approved else FeedbackStatus.action_needed,
            )
        )

    record_audit(
        db,
        actor=account,
        action="mentor_resume_review",
        entity_type="resume",
        entity_id=resume.id,
        summary=f"Mentor marked resume {resume.version_name} as {resume.status.value}",
    )
    db.commit()
    db.refresh(resume)
    return resume_out(resume)


@router.get("/applications/pending", response_model=list[ApplicationOut])
def pending_applications(
    mentor: Mentor = Depends(get_current_mentor),
    db: Session = Depends(get_db),
) -> list[ApplicationOut]:
    students = _assigned_students(db, mentor)
    if not students:
        return []

    rows = (
        db.query(Application)
        .filter(
            Application.student_id.in_([student.id for student in students]),
            Application.status == ApplicationStatus.pending_mentor_approval,
        )
        .order_by(Application.created_at.asc())
        .all()
    )
    return [application_out(row) for row in rows]


# --- feedback -------------------------------------------------------------------


@router.get("/feedback", response_model=list[FeedbackOut])
def list_feedback(
    student_id: int | None = None,
    status_filter: FeedbackStatus | None = None,
    mentor: Mentor = Depends(get_current_mentor),
    db: Session = Depends(get_db),
) -> list[FeedbackOut]:
    assigned_ids = [assignment.student_id for assignment in mentor.assignments if assignment.is_active]
    if not assigned_ids:
        return []

    query = db.query(Feedback).filter(Feedback.student_id.in_(assigned_ids))
    if student_id is not None:
        if student_id not in assigned_ids:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student not assigned to you")
        query = query.filter(Feedback.student_id == student_id)
    if status_filter is not None:
        query = query.filter(Feedback.status == status_filter)

    return [feedback_out(entry) for entry in query.order_by(Feedback.id.desc()).all()]


@router.post("/feedback", response_model=FeedbackOut, status_code=status.HTTP_201_CREATED)
def create_feedback(
    payload: FeedbackCreate,
    mentor: Mentor = Depends(get_current_mentor),
    db: Session = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> FeedbackOut:
    assigned_ids = {assignment.student_id for assignment in mentor.assignments if assignment.is_active}
    if payload.student_id not in assigned_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student not assigned to you")

    if payload.resume_id is not None:
        resume = db.get(Resume, payload.resume_id)
        if resume is None or resume.student_id != payload.student_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="The resume does not belong to this student",
            )
    if payload.application_id is not None:
        application = db.get(Application, payload.application_id)
        if application is None or application.student_id != payload.student_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="The application does not belong to this student",
            )

    entry = Feedback(
        student_id=payload.student_id,
        mentor_id=mentor.id,
        resume_id=payload.resume_id,
        application_id=payload.application_id,
        title=payload.title.strip(),
        body=payload.body.strip(),
        status=payload.status,
    )
    db.add(entry)
    db.flush()

    student = db.get(Student, payload.student_id)
    notify(
        db,
        account_id=student.account_id if student else None,
        title="New mentor feedback",
        message=f"{account.full_name} left feedback: {entry.title}",
        type_=NotificationType.mentor_feedback,
        entity_type="feedback",
        entity_id=entry.id,
    )
    record_audit(
        db,
        actor=account,
        action="create_feedback",
        entity_type="feedback",
        entity_id=entry.id,
        summary=f"Feedback added for student #{payload.student_id}",
    )
    db.commit()
    db.refresh(entry)
    return feedback_out(entry)


@router.patch("/feedback/{feedback_id}", response_model=FeedbackOut)
def update_feedback(
    feedback_id: int,
    payload: FeedbackUpdate,
    mentor: Mentor = Depends(get_current_mentor),
    db: Session = Depends(get_db),
) -> FeedbackOut:
    entry = db.get(Feedback, feedback_id)
    if entry is None or entry.mentor_id != mentor.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")

    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(entry, field, value)
    if entry.status == FeedbackStatus.resolved and entry.resolved_at is None:
        entry.resolved_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(entry)
    return feedback_out(entry)
