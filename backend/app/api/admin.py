"""Admin module: dashboard, user management, mentor assignments, monitoring and audit."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_account, require_admin
from ..models import (
    Account,
    Administrator,
    Application,
    ApplicationStatus,
    AuditLog,
    Company,
    CompanyStatus,
    DriveStatus,
    Feedback,
    JobPosting,
    Mentor,
    MentorAssignment,
    Notification,
    NotificationType,
    PlacementDrive,
    Resume,
    ResumeStatus,
    Student,
    UserRole,
)
from ..schemas.admin import (
    AdminDashboardOut,
    AdminUserCreate,
    AdminUserOut,
    AdminUserUpdate,
    AuditLogOut,
    AuditLogPage,
    DashboardCounts,
)
from ..schemas.common import Message, Page
from ..schemas.mentor import AssignmentCreate, AssignmentOut
from ..schemas.placement import AdminApplicationUpdate, ApplicationOut
from ..security import hash_password
from ..services.audit import record_audit
from ..services.lifecycle import allowed_transitions, can_transition
from ..services.notifications import notify
from ..services.seed import seed_reference_data
from .serializers import admin_user_out, application_out, student_summary

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/dashboard", response_model=AdminDashboardOut)
def admin_dashboard(
    db: Session = Depends(get_db),
    _: Account = Depends(require_admin),
) -> AdminDashboardOut:
    status_counts = {
        row[0].value: row[1]
        for row in db.query(Application.status, func.count(Application.id))
        .group_by(Application.status)
        .all()
    }

    assigned_student_ids = {
        row[0] for row in db.query(MentorAssignment.student_id).filter(MentorAssignment.is_active.is_(True)).all()
    }
    total_students = db.query(Student).count()

    upcoming = (
        db.query(PlacementDrive)
        .filter(
            PlacementDrive.application_deadline.isnot(None),
            PlacementDrive.application_deadline >= date.today(),
            PlacementDrive.status.in_([DriveStatus.open, DriveStatus.draft]),
        )
        .order_by(PlacementDrive.application_deadline.asc())
        .limit(5)
        .all()
    )

    recent_applications = (
        db.query(Application).order_by(Application.updated_at.desc()).limit(6).all()
    )
    recent_logs = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(10).all()

    top_companies = [
        {"company_id": row[0], "company_name": row[1], "drives": row[2]}
        for row in db.query(Company.id, Company.name, func.count(PlacementDrive.id))
        .join(PlacementDrive, PlacementDrive.company_id == Company.id)
        .group_by(Company.id, Company.name)
        .order_by(func.count(PlacementDrive.id).desc())
        .limit(5)
        .all()
    ]

    counts = DashboardCounts(
        students=total_students,
        mentors=db.query(Mentor).count(),
        administrators=db.query(Administrator).count(),
        companies=db.query(Company).count(),
        active_companies=db.query(Company).filter(Company.status == CompanyStatus.active).count(),
        job_postings=db.query(JobPosting).count(),
        published_job_postings=db.query(JobPosting)
        .filter(JobPosting.status.value == "published")
        .count(),
        placement_drives=db.query(PlacementDrive).count(),
        open_drives=db.query(PlacementDrive).filter(PlacementDrive.status == DriveStatus.open).count(),
        applications=db.query(Application).count(),
        applications_by_status=status_counts,
        pending_mentor_reviews=db.query(Application)
        .filter(Application.status == ApplicationStatus.pending_mentor_approval)
        .count(),
        pending_resume_reviews=db.query(Resume).filter(Resume.status == ResumeStatus.pending_review).count(),
        students_without_mentor=max(0, total_students - len(assigned_student_ids)),
        notifications_unread=db.query(Notification).filter(Notification.is_read.is_(False)).count(),
    )

    return AdminDashboardOut(
        counts=counts,
        upcoming_deadlines=[
            {
                "drive_id": drive.id,
                "drive_name": drive.name,
                "company_name": drive.company.name if drive.company else None,
                "application_deadline": drive.application_deadline.isoformat()
                if drive.application_deadline
                else None,
                "status": drive.status.value,
                "applications": len(drive.applications),
            }
            for drive in upcoming
        ],
        recent_applications=[application_out(row) for row in recent_applications],
        recent_audit_logs=[
            AuditLogOut(
                id=row.id,
                actor_account_id=row.actor_account_id,
                actor_email=row.actor_email,
                actor_role=row.actor_role,
                action=row.action,
                entity_type=row.entity_type,
                entity_id=row.entity_id,
                summary=row.summary,
                meta=row.meta or {},
                created_at=row.created_at,
            )
            for row in recent_logs
        ],
        top_companies_by_drives=top_companies,
    )


# --- user management ------------------------------------------------------------


@router.get("/users", response_model=Page[AdminUserOut])
def list_users(
    role: UserRole | None = None,
    search: str | None = None,
    is_active: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
    _: Account = Depends(require_admin),
) -> Page[AdminUserOut]:
    query = db.query(Account)
    if role is not None:
        query = query.filter(Account.role == role)
    if is_active is not None:
        query = query.filter(Account.is_active == is_active)
    if search:
        needle = f"%{search.strip()}%"
        query = query.filter(Account.full_name.ilike(needle) | Account.email.ilike(needle))

    total = query.count()
    rows = query.order_by(Account.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return Page[AdminUserOut](
        items=[admin_user_out(row) for row in rows], total=total, page=page, page_size=page_size
    )


@router.post("/users", response_model=AdminUserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: AdminUserCreate,
    db: Session = Depends(get_db),
    account: Account = Depends(require_admin),
) -> AdminUserOut:
    """Administrators can create any role, including other administrators."""

    new_account = Account(
        full_name=payload.full_name.strip(),
        email=str(payload.email).lower(),
        role=payload.role,
        password_hash=hash_password(payload.password),
    )
    db.add(new_account)
    db.flush()

    if payload.role == UserRole.student:
        db.add(
            Student(
                account_id=new_account.id,
                registration_number=payload.identifier.strip().upper(),
                program=payload.department_or_program.strip(),
            )
        )
    elif payload.role == UserRole.mentor:
        db.add(
            Mentor(
                account_id=new_account.id,
                employee_code=payload.identifier.strip().upper(),
                department=payload.department_or_program.strip(),
            )
        )
    else:
        db.add(
            Administrator(
                account_id=new_account.id,
                staff_code=payload.identifier.strip().upper(),
                office=payload.department_or_program.strip(),
            )
        )

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="That email or identifier is already in use"
        ) from exc

    db.refresh(new_account)
    record_audit(
        db,
        actor=account,
        action="create_user",
        entity_type="account",
        entity_id=new_account.id,
        summary=f"Created {payload.role.value} account {new_account.email}",
    )
    db.commit()
    return admin_user_out(new_account)


@router.patch("/users/{account_id}", response_model=AdminUserOut)
def update_user(
    account_id: int,
    payload: AdminUserUpdate,
    db: Session = Depends(get_db),
    account: Account = Depends(require_admin),
) -> AdminUserOut:
    target = db.get(Account, account_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    changes = payload.model_dump(exclude_unset=True)

    if "is_active" in changes and changes["is_active"] is False and target.id == account.id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="You cannot deactivate your own account"
        )
    if "role" in changes and changes["role"] != target.role:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Changing an existing account's role is not allowed. Create a new account with the "
                "correct role instead, so profile data stays consistent."
            ),
        )

    for field, value in changes.items():
        if field == "department_or_program":
            if target.student is not None:
                target.student.department = value
            elif target.mentor is not None:
                target.mentor.department = value
            elif target.administrator is not None:
                target.administrator.office = value
            continue
        setattr(target, field, value)

    record_audit(
        db,
        actor=account,
        action="update_user",
        entity_type="account",
        entity_id=target.id,
        summary=f"Updated account {target.email}",
        meta={"fields": sorted(changes.keys())},
    )
    db.commit()
    db.refresh(target)
    return admin_user_out(target)


@router.post("/users/{account_id}/reset-password", response_model=Message)
def reset_password(
    account_id: int,
    new_password: str = Query(min_length=8, max_length=72),
    db: Session = Depends(get_db),
    account: Account = Depends(require_admin),
) -> Message:
    """Administrator initiated password reset. The password is hashed, never logged."""

    target = db.get(Account, account_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    target.password_hash = hash_password(new_password)
    record_audit(
        db,
        actor=account,
        action="reset_password",
        entity_type="account",
        entity_id=target.id,
        summary=f"Password reset for {target.email}",
    )
    db.commit()
    return Message(message=f"Password reset for {target.email}")


# --- mentor assignments ---------------------------------------------------------


def _assignment_out(db: Session, assignment: MentorAssignment) -> AssignmentOut:
    mentor = db.get(Mentor, assignment.mentor_id)
    student = db.get(Student, assignment.student_id)
    return AssignmentOut(
        id=assignment.id,
        mentor_id=assignment.mentor_id,
        mentor_name=mentor.account.full_name if mentor and mentor.account else None,
        student_id=assignment.student_id,
        student_name=student.account.full_name if student and student.account else None,
        registration_number=student.registration_number if student else None,
        is_active=assignment.is_active,
        notes=assignment.notes,
        created_at=assignment.created_at,
    )


@router.get("/assignments", response_model=list[AssignmentOut])
def list_assignments(
    mentor_id: int | None = None,
    student_id: int | None = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    _: Account = Depends(require_admin),
) -> list[AssignmentOut]:
    query = db.query(MentorAssignment)
    if mentor_id is not None:
        query = query.filter(MentorAssignment.mentor_id == mentor_id)
    if student_id is not None:
        query = query.filter(MentorAssignment.student_id == student_id)
    if active_only:
        query = query.filter(MentorAssignment.is_active.is_(True))

    return [_assignment_out(db, row) for row in query.order_by(MentorAssignment.id.desc()).all()]


@router.post("/assignments", response_model=AssignmentOut, status_code=status.HTTP_201_CREATED)
def create_assignment(
    payload: AssignmentCreate,
    db: Session = Depends(get_db),
    account: Account = Depends(require_admin),
) -> AssignmentOut:
    mentor = db.get(Mentor, payload.mentor_id)
    if mentor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mentor not found")
    student = db.get(Student, payload.student_id)
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    existing = (
        db.query(MentorAssignment)
        .filter(
            MentorAssignment.mentor_id == payload.mentor_id,
            MentorAssignment.student_id == payload.student_id,
        )
        .one_or_none()
    )
    if existing is not None:
        existing.is_active = True
        existing.notes = payload.notes or existing.notes
        db.commit()
        db.refresh(existing)
        return _assignment_out(db, existing)

    assignment = MentorAssignment(
        mentor_id=payload.mentor_id, student_id=payload.student_id, notes=payload.notes
    )
    db.add(assignment)
    db.flush()

    if student.account_id and mentor.account_id:
        notify(
            db,
            account_id=mentor.account_id,
            title="New student assigned",
            message=(
                f"{student.account.full_name if student.account else 'A student'} is now in your mentee list."
            ),
            type_=NotificationType.general,
            entity_type="mentor_assignment",
            entity_id=assignment.id,
        )
    record_audit(
        db,
        actor=account,
        action="create_assignment",
        entity_type="mentor_assignment",
        entity_id=assignment.id,
        summary=f"Assigned student #{payload.student_id} to mentor #{payload.mentor_id}",
    )
    db.commit()
    db.refresh(assignment)
    return _assignment_out(db, assignment)


@router.delete("/assignments/{assignment_id}", response_model=Message)
def delete_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    account: Account = Depends(require_admin),
) -> Message:
    assignment = db.get(MentorAssignment, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    assignment.is_active = False
    record_audit(
        db,
        actor=account,
        action="end_assignment",
        entity_type="mentor_assignment",
        entity_id=assignment.id,
        summary=f"Ended assignment #{assignment.id}",
    )
    db.commit()
    return Message(message="Assignment ended")


# --- student overview -----------------------------------------------------------


@router.get("/students", response_model=list[dict])
def list_students(
    search: str | None = None,
    needs_attention: bool = False,
    without_mentor: bool = False,
    db: Session = Depends(get_db),
    _: Account = Depends(require_admin),
) -> list[dict]:
    """Every student with the mentor-level readiness view, plus their mentor names."""

    mentors_by_student: dict[int, list[str]] = {}
    for assignment in db.query(MentorAssignment).filter(MentorAssignment.is_active.is_(True)).all():
        mentor = db.get(Mentor, assignment.mentor_id)
        if mentor and mentor.account:
            mentors_by_student.setdefault(assignment.student_id, []).append(mentor.account.full_name)

    rows = []
    for student in db.query(Student).all():
        summary = student_summary(db, student)
        mentor_names = mentors_by_student.get(student.id, [])
        if without_mentor and mentor_names:
            continue
        if needs_attention and not summary.needs_attention:
            continue
        if search:
            needle = search.strip().lower()
            haystack = f"{summary.full_name} {summary.registration_number} {summary.department or ''}".lower()
            if needle not in haystack:
                continue

        payload = summary.model_dump(mode="json")
        payload["mentor_names"] = mentor_names
        payload["applications_count"] = (
            db.query(Application).filter(Application.student_id == student.id).count()
        )
        rows.append(payload)

    rows.sort(key=lambda row: (not row["needs_attention"], -(row["overall_score"] or 0)))
    return rows


# --- application monitoring -----------------------------------------------------


@router.get("/applications", response_model=Page[ApplicationOut])
def monitor_applications(
    status_filter: ApplicationStatus | None = None,
    company_id: int | None = None,
    drive_id: int | None = None,
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
    _: Account = Depends(require_admin),
) -> Page[ApplicationOut]:
    query = db.query(Application).join(Student, Student.id == Application.student_id)

    if status_filter is not None:
        query = query.filter(Application.status == status_filter)
    if company_id is not None:
        query = query.filter(Application.company_id == company_id)
    if drive_id is not None:
        query = query.filter(Application.drive_id == drive_id)
    if search:
        needle = f"%{search.strip()}%"
        query = query.join(Account, Account.id == Student.account_id).filter(
            Account.full_name.ilike(needle)
            | Student.registration_number.ilike(needle)
            | Application.code.ilike(needle)
        )

    total = query.count()
    rows = (
        query.order_by(Application.updated_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    )
    return Page[ApplicationOut](
        items=[application_out(row) for row in rows], total=total, page=page, page_size=page_size
    )


@router.patch("/applications/{application_id}/status", response_model=ApplicationOut)
def update_application_status(
    application_id: int,
    payload: AdminApplicationUpdate,
    db: Session = Depends(get_db),
    account: Account = Depends(require_admin),
) -> ApplicationOut:
    application = db.get(Application, application_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    if not can_transition(application.status, payload.status):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"'{application.status.value}' cannot move to '{payload.status.value}'. "
                f"Allowed: {', '.join(allowed_transitions(application.status)) or 'none'}"
            ),
        )

    application.status = payload.status
    application.admin_note = payload.note or application.admin_note
    application.decided_at = date.today()

    student = application.student
    drive_name = application.drive.name if application.drive else "the drive"
    notify(
        db,
        account_id=student.account_id if student else None,
        title="Application status updated",
        message=(
            f"Your application for '{drive_name}' is now "
            f"'{payload.status.value.replace('_', ' ')}'."
            + (f" Note: {payload.note}" if payload.note else "")
        ),
        type_=NotificationType.application_status,
        entity_type="application",
        entity_id=application.id,
    )
    record_audit(
        db,
        actor=account,
        action="update_application_status",
        entity_type="application",
        entity_id=application.id,
        summary=f"Application {application.code} set to {payload.status.value}",
    )
    db.commit()
    db.refresh(application)
    return application_out(application)


# --- audit log and reference data -----------------------------------------------


@router.get("/audit-logs", response_model=AuditLogPage)
def read_audit_logs(
    action: str | None = None,
    entity_type: str | None = None,
    actor_email: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=30, ge=1, le=100),
    db: Session = Depends(get_db),
    _: Account = Depends(require_admin),
) -> AuditLogPage:
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if actor_email:
        query = query.filter(AuditLog.actor_email.ilike(f"%{actor_email.strip()}%"))

    total = query.count()
    rows = query.order_by(AuditLog.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return AuditLogPage(
        items=[
            AuditLogOut(
                id=row.id,
                actor_account_id=row.actor_account_id,
                actor_email=row.actor_email,
                actor_role=row.actor_role,
                action=row.action,
                entity_type=row.entity_type,
                entity_id=row.entity_id,
                summary=row.summary,
                meta=row.meta or {},
                created_at=row.created_at,
            )
            for row in rows
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/reference/seed", response_model=dict)
def reseed_reference_data(
    db: Session = Depends(get_db),
    account: Account = Depends(require_admin),
) -> dict:
    """Insert any missing role, role skill, learning resource or interview question."""

    created = seed_reference_data(db)
    record_audit(
        db,
        actor=account,
        action="seed_reference_data",
        entity_type="system",
        summary="Reference dataset refreshed",
        meta=created,
    )
    db.commit()
    return {"message": "Reference dataset refreshed", "created": created}




