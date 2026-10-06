"""Placement drive management and student eligibility checking."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_account, get_current_student, require_admin, require_mentor_or_admin
from ..models import (
    Account,
    Application,
    ApplicationStatus,
    Company,
    DriveStatus,
    JobPosting,
    PlacementDrive,
    Student,
    UserRole,
)
from ..schemas.common import Message
from ..schemas.placement import (
    DriveEligibilityRow,
    DriveStatusUpdate,
    EligibilityResponse,
    PlacementDriveCreate,
    PlacementDriveOut,
    PlacementDriveUpdate,
)
from ..services.audit import record_audit
from ..services.eligibility import evaluate_drive_for_student
from ..services.notifications import notify_many
from .serializers import drive_out

router = APIRouter(prefix="/drives", tags=["Placement drives"])


def _eligible_student_ids(db: Session, drive: PlacementDrive) -> list[int]:
    """Student ids that pass the drive criteria, used for counts and announcements."""

    eligible: list[int] = []
    for student in db.query(Student).all():
        if evaluate_drive_for_student(db, drive, student).eligible:
            eligible.append(student.id)
    return eligible


def _visible_drives(query, account: Account):
    if account.role == UserRole.student:
        return query.filter(PlacementDrive.status == DriveStatus.open)
    return query


@router.get("", response_model=list[PlacementDriveOut])
def list_drives(
    search: str | None = None,
    company_id: int | None = None,
    status_filter: DriveStatus | None = None,
    db: Session = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> list[PlacementDriveOut]:
    query = db.query(PlacementDrive)

    if status_filter is not None and account.role != UserRole.student:
        query = query.filter(PlacementDrive.status == status_filter)
    query = _visible_drives(query, account)

    if company_id is not None:
        query = query.filter(PlacementDrive.company_id == company_id)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(PlacementDrive.name.ilike(pattern))

    drives = query.order_by(PlacementDrive.id.desc()).all()
    if account.role == UserRole.student:
        return [drive_out(drive) for drive in drives]
    return [drive_out(drive, eligible_student_count=len(_eligible_student_ids(db, drive))) for drive in drives]


@router.get("/{drive_id}", response_model=PlacementDriveOut)
def read_drive(
    drive_id: int,
    db: Session = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> PlacementDriveOut:
    drive = db.get(PlacementDrive, drive_id)
    if drive is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Placement drive not found")
    if account.role == UserRole.student and drive.status != DriveStatus.open:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This drive is not open")

    eligible_count = 0 if account.role == UserRole.student else len(_eligible_student_ids(db, drive))
    return drive_out(drive, eligible_student_count=eligible_count)


@router.get("/{drive_id}/eligible-students")
def eligible_students(
    drive_id: int,
    db: Session = Depends(get_db),
    _: Account = Depends(require_mentor_or_admin),
) -> dict:
    """Count plus names of eligible students. Mentors and administrators only."""

    drive = db.get(PlacementDrive, drive_id)
    if drive is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Placement drive not found")

    rows = []
    for student in db.query(Student).all():
        if evaluate_drive_for_student(db, drive, student).eligible:
            rows.append(
                {
                    "student_id": student.id,
                    "full_name": student.account.full_name if student.account else None,
                    "registration_number": student.registration_number,
                    "department": student.department,
                    "cgpa": student.cgpa,
                }
            )
    return {"drive_id": drive_id, "count": len(rows), "students": rows}



@router.get("/me/eligibility", response_model=list[DriveEligibilityRow])
def my_drive_eligibility(
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> list[DriveEligibilityRow]:
    """Eligibility for every open drive, including the reasons a student is blocked."""

    drives = (
        db.query(PlacementDrive)
        .filter(PlacementDrive.status == DriveStatus.open)
        .order_by(PlacementDrive.application_deadline.asc().nullslast(), PlacementDrive.id.desc())
        .all()
    )
    rows: list[DriveEligibilityRow] = []
    for drive in drives:
        result = evaluate_drive_for_student(db, drive, student)
        rows.append(
            DriveEligibilityRow(
                drive_id=drive.id,
                eligibility=EligibilityResponse(
                    eligible=result.eligible,
                    status=result.status,
                    reasons=result.reasons,
                    missing_skills=result.missing_skills,
                    matched_skills=result.matched_skills,
                    cgpa_ok=result.cgpa_ok,
                    department_ok=result.department_ok,
                    graduation_year_ok=result.graduation_year_ok,
                    deadline_open=result.deadline_open,
                    already_applied=any(app.drive_id == drive.id for app in student.applications),
                    has_approved_resume=not any("approved resume" in reason for reason in result.reasons),
                ),
            )
        )
    return rows


@router.post("", response_model=PlacementDriveOut, status_code=status.HTTP_201_CREATED)
def create_drive(
    payload: PlacementDriveCreate,
    db: Session = Depends(get_db),
    account: Account = Depends(require_admin),
) -> PlacementDriveOut:
    company = db.get(Company, payload.company_id)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    if payload.job_posting_id is not None:
        job = db.get(JobPosting, payload.job_posting_id)
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job posting not found")
        if job.company_id != payload.company_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="The selected job posting belongs to a different company",
            )
    if (
        payload.drive_date is not None
        and payload.application_deadline is not None
        and payload.drive_date < payload.application_deadline
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The drive date must be on or after the application deadline",
        )

    drive = PlacementDrive(**payload.model_dump(), created_by_account_id=account.id)
    db.add(drive)
    db.flush()
    record_audit(
        db,
        actor=account,
        action="create_drive",
        entity_type="placement_drive",
        entity_id=drive.id,
        summary=f"Created drive '{drive.name}' for {company.name}",
    )
    db.commit()
    db.refresh(drive)
    return drive_out(drive, eligible_student_count=len(_eligible_student_ids(db, drive)))


@router.patch("/{drive_id}", response_model=PlacementDriveOut)
def update_drive(
    drive_id: int,
    payload: PlacementDriveUpdate,
    db: Session = Depends(get_db),
    account: Account = Depends(require_admin),
) -> PlacementDriveOut:
    drive = db.get(PlacementDrive, drive_id)
    if drive is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Placement drive not found")

    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(drive, field, value)

    if drive.drive_date and drive.application_deadline and drive.drive_date < drive.application_deadline:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The drive date must be on or after the application deadline",
        )

    record_audit(
        db,
        actor=account,
        action="update_drive",
        entity_type="placement_drive",
        entity_id=drive.id,
        summary=f"Updated drive '{drive.name}'",
        meta={"fields": sorted(changes.keys())},
    )
    db.commit()
    db.refresh(drive)
    return drive_out(drive, eligible_student_count=len(_eligible_student_ids(db, drive)))


@router.post("/{drive_id}/status", response_model=PlacementDriveOut)
def change_drive_status(
    drive_id: int,
    payload: DriveStatusUpdate,
    db: Session = Depends(get_db),
    account: Account = Depends(require_admin),
) -> PlacementDriveOut:
    drive = db.get(PlacementDrive, drive_id)
    if drive is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Placement drive not found")
    if drive.status == DriveStatus.completed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="A completed drive can no longer change status"
        )

    drive.status = payload.status
    if payload.note:
        drive.description = f"{drive.description or ''}\n\n[Status note] {payload.note}".strip()

    if payload.status == DriveStatus.open:
        eligible_accounts = [
            student.account_id
            for student in db.query(Student).all()
            if evaluate_drive_for_student(db, drive, student).eligible and student.account_id
        ]
        notify_many(
            db,
            eligible_accounts,
            title="New placement drive published",
            message=f"'{drive.name}' is open for applications. Check your eligibility and apply.",
            type_=NotificationType.drive_announcement,
            entity_type="placement_drive",
            entity_id=drive.id,
        )

    record_audit(
        db,
        actor=account,
        action="change_drive_status",
        entity_type="placement_drive",
        entity_id=drive.id,
        summary=f"Drive '{drive.name}' set to {payload.status.value}",
    )
    db.commit()
    db.refresh(drive)
    return drive_out(drive, eligible_student_count=len(_eligible_student_ids(db, drive)))


@router.delete("/{drive_id}", response_model=Message)
def delete_drive(
    drive_id: int,
    db: Session = Depends(get_db),
    account: Account = Depends(require_admin),
) -> Message:
    drive = db.get(PlacementDrive, drive_id)
    if drive is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Placement drive not found")

    open_applications = [
        application
        for application in drive.applications
        if application.status != ApplicationStatus.withdrawn
    ]
    if open_applications:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{len(open_applications)} application(s) exist for this drive. Close it instead of deleting.",
        )

    name = drive.name
    db.delete(drive)
    record_audit(
        db,
        actor=account,
        action="delete_drive",
        entity_type="placement_drive",
        entity_id=drive_id,
        summary=f"Deleted drive '{name}'",
    )
    db.commit()
    return Message(message=f"Placement drive '{name}' deleted")
