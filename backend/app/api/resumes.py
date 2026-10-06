"""Resume versions and the submit-for-review workflow."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..config import settings
from ..deps import get_current_account, get_current_student
from ..models import (
    Account,
    Application,
    Mentor,
    MentorAssignment,
    NotificationType,
    Resume,
    ResumeStatus,
    Student,
)
from ..schemas.common import Message
from ..schemas.resume import ResumeCreate, ResumeDownloadUrl, ResumeOut, ResumeUpdate, ResumeUploadRequest, ResumeUploadUrl
from ..services.audit import record_audit
from ..services.notifications import notify
from ..services.readiness import resume_completeness
from ..services.resume_storage import create_download, create_upload, delete_object, validate_upload
from ..services.resume_storage import read_object
from ..services.resume_parser import extract_summary, parse_pdf
from .serializers import resume_out

router = APIRouter(prefix="/resumes", tags=["Resumes"])

EDITABLE_STATUSES = {ResumeStatus.draft, ResumeStatus.changes_requested}


def _ordered_resumes(db: Session, student_id: int) -> list[Resume]:
    return (
        db.query(Resume).filter(Resume.student_id == student_id).order_by(Resume.version_number.desc()).all()
    )


def _next_version_number(db: Session, student_id: int) -> int:
    latest = (
        db.query(Resume).filter(Resume.student_id == student_id).order_by(Resume.version_number.desc()).first()
    )
    return (latest.version_number + 1) if latest else 1


def _mentor_account_ids(db: Session, student_id: int) -> list[int]:
    """Account ids of assigned mentors, or of every mentor when nobody is assigned yet."""

    assignments = (
        db.query(MentorAssignment)
        .filter(MentorAssignment.student_id == student_id, MentorAssignment.is_active.is_(True))
        .all()
    )
    if assignments:
        mentor_ids = [assignment.mentor_id for assignment in assignments]
        rows = db.query(Mentor).filter(Mentor.id.in_(mentor_ids)).all()
        return [mentor.account_id for mentor in rows if mentor.account_id]

    return [mentor.account_id for mentor in db.query(Mentor).all() if mentor.account_id]


@router.get("/me", response_model=list[ResumeOut])
def list_my_resumes(
    student: Student = Depends(get_current_student), db: Session = Depends(get_db)
) -> list[ResumeOut]:
    return [resume_out(resume) for resume in _ordered_resumes(db, student.id)]


@router.post("/me", response_model=ResumeOut, status_code=status.HTTP_201_CREATED)
def create_resume(
    payload: ResumeCreate,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> ResumeOut:
    resume = Resume(
        student_id=student.id,
        version_number=_next_version_number(db, student.id),
        version_name=(payload.version_name or f"Resume v{_next_version_number(db, student.id)}").strip(),
        title=(payload.title or payload.version_name or "Uploaded resume").strip(),
        target_role=(payload.target_role or student.target_role or "General").strip(),
        summary=payload.summary,
        content=payload.content.model_dump(),
        file_url=payload.file_url,
        status=ResumeStatus.draft,
    )
    db.add(resume)
    db.flush()
    record_audit(
        db,
        actor=account,
        action="create_resume",
        entity_type="resume",
        entity_id=resume.id,
        summary=f"Created resume version {resume.version_name}",
    )
    db.commit()
    db.refresh(resume)
    return resume_out(resume)


@router.get("/me/{resume_id}", response_model=ResumeOut)
def read_resume(
    resume_id: int,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> ResumeOut:
    resume = db.get(Resume, resume_id)
    if resume is None or resume.student_id != student.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume version not found")
    return resume_out(resume)


@router.post("/me/{resume_id}/upload-url", response_model=ResumeUploadUrl)
def resume_upload_url(resume_id: int, payload: ResumeUploadRequest, student: Student = Depends(get_current_student), db: Session = Depends(get_db)) -> ResumeUploadUrl:
    resume = db.get(Resume, resume_id)
    if resume is None or resume.student_id != student.id:
        raise HTTPException(status_code=404, detail="Resume version not found")
    if resume.status not in EDITABLE_STATUSES:
        raise HTTPException(status_code=409, detail="This resume version cannot be changed")
    validate_upload(payload.filename, payload.content_type, payload.size)
    key, upload_url = create_upload(student.id, resume.id, payload.filename, payload.content_type)
    resume.file_url = f"s3://{key}"
    db.commit()
    return ResumeUploadUrl(storage_key=key, upload_url=upload_url, expires_in=settings.resume_presign_expiry_seconds)


@router.get("/me/{resume_id}/download-url", response_model=ResumeDownloadUrl)
def resume_download_url(resume_id: int, student: Student = Depends(get_current_student), db: Session = Depends(get_db)) -> ResumeDownloadUrl:
    resume = db.get(Resume, resume_id)
    if resume is None or resume.student_id != student.id or not resume.file_url or not resume.file_url.startswith("s3://"):
        raise HTTPException(status_code=404, detail="Resume file not found")
    return ResumeDownloadUrl(download_url=create_download(resume.file_url.removeprefix("s3://")), expires_in=settings.resume_presign_expiry_seconds)


@router.post("/me/{resume_id}/parse", response_model=ResumeOut)
def parse_uploaded_resume(resume_id: int, student: Student = Depends(get_current_student), db: Session = Depends(get_db)) -> ResumeOut:
    resume = db.get(Resume, resume_id)
    if resume is None or resume.student_id != student.id:
        raise HTTPException(status_code=404, detail="Resume version not found")
    if not resume.file_url or not resume.file_url.startswith("s3://"):
        raise HTTPException(status_code=422, detail="Upload a resume PDF before parsing")
    try:
        pdf_data = read_object(resume.file_url.removeprefix("s3://"))
        resume.content = parse_pdf(pdf_data)
        if not resume.summary:
            resume.summary = extract_summary(pdf_data)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=422, detail="The uploaded PDF could not be parsed") from exc
    db.commit(); db.refresh(resume)
    return resume_out(resume)


@router.patch("/me/{resume_id}", response_model=ResumeOut)
def update_resume(
    resume_id: int,
    payload: ResumeUpdate,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> ResumeOut:
    resume = db.get(Resume, resume_id)
    if resume is None or resume.student_id != student.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume version not found")
    if resume.status not in EDITABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only draft versions, or versions with requested changes, can be edited.",
        )

    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(resume, field, value)
    resume.status = ResumeStatus.draft

    db.commit()
    db.refresh(resume)
    return resume_out(resume)


@router.post("/me/{resume_id}/submit", response_model=ResumeOut)
def submit_resume(
    resume_id: int,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> ResumeOut:
    resume = db.get(Resume, resume_id)
    if resume is None or resume.student_id != student.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume version not found")
    if resume.status not in EDITABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"This version is already {resume.status.value.replace('_', ' ')}",
        )
    if not resume.file_url or not resume.file_url.startswith("s3://"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Upload and parse a resume PDF before submitting it for review",
        )
    if not any((resume.content or {}).get(section) for section in ("education", "experience", "projects", "skills", "achievements")):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No resume details were extracted. Upload a text-based PDF, then try parsing it again before submitting",
        )
    if resume_completeness(resume) < 40:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Fill in the summary, skills, projects and education sections before submitting",
        )

    resume.status = ResumeStatus.pending_review
    resume.submitted_at = datetime.now(timezone.utc)

    for account_id in _mentor_account_ids(db, student.id):
        notify(
            db,
            account_id=account_id,
            title="Resume submitted for review",
            message=(
                f"{account.full_name} ({student.registration_number}) submitted "
                f"'{resume.version_name}' for review."
            ),
            type_=NotificationType.resume_review,
            entity_type="resume",
            entity_id=resume.id,
        )
    record_audit(
        db,
        actor=account,
        action="submit_resume",
        entity_type="resume",
        entity_id=resume.id,
        summary=f"Submitted {resume.version_name} for mentor review",
    )
    db.commit()
    db.refresh(resume)
    return resume_out(resume)


@router.delete("/me/{resume_id}", response_model=Message)
def delete_resume(
    resume_id: int,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> Message:
    resume = db.get(Resume, resume_id)
    if resume is None or resume.student_id != student.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume version not found")
    linked = db.query(Application).filter(Application.resume_id == resume.id).count()
    if linked:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This version is attached to an application and cannot be deleted",
        )

    if resume.file_url and resume.file_url.startswith("s3://"):
        delete_object(resume.file_url.removeprefix("s3://"))
    record_audit(
        db,
        actor=account,
        action="delete_resume",
        entity_type="resume",
        entity_id=resume.id,
        summary=f"Deleted resume version {resume.version_name}",
    )
    db.delete(resume)
    db.commit()
    return Message(message="Resume version deleted")

