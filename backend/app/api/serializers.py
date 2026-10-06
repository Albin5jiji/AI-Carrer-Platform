"""Mapping helpers between SQLAlchemy rows and API response schemas.

Keeping this in one module means the student, mentor and admin routers all return
identical shapes for the same entity.
"""

from datetime import date

from sqlalchemy.orm import Session

from ..models import (
    Account,
    Application,
    ApplicationStatus,
    Company,
    Feedback,
    JobPosting,
    PlacementDrive,
    Resume,
    ResumeStatus,
    Student,
)
from ..schemas.admin import AdminUserOut
from ..schemas.auth import UserResponse
from ..schemas.mentor import FeedbackOut, MentorStudentSummary
from ..schemas.placement import ApplicationOut, CompanyOut, JobPostingOut, PlacementDriveOut
from ..schemas.resume import ResumeOut
from ..schemas.student import StudentProfileOut
from ..services.lifecycle import ACTIVE_APPLICATION_STATUSES, compute_next_action
from ..services.readiness import resume_completeness


def user_response(account: Account) -> UserResponse:
    profile_id = None
    if account.student is not None:
        profile_id = account.student.id
    elif account.mentor is not None:
        profile_id = account.mentor.id
    elif account.administrator is not None:
        profile_id = account.administrator.id

    return UserResponse(
        id=account.id,
        full_name=account.full_name,
        email=account.email,
        role=account.role,
        identifier=account.identifier,
        department_or_program=account.department_or_program,
        profile_id=profile_id,
        is_active=account.is_active,
    )


def admin_user_out(account: Account) -> AdminUserOut:
    return AdminUserOut(
        id=account.id,
        full_name=account.full_name,
        email=account.email,
        role=account.role,
        identifier=account.identifier,
        department_or_program=account.department_or_program,
        is_active=account.is_active,
        created_at=account.created_at,
    )


def student_profile_out(student: Student) -> StudentProfileOut:
    account = student.account
    return StudentProfileOut(
        id=student.id,
        account_id=student.account_id,
        full_name=account.full_name,
        email=account.email,
        registration_number=student.registration_number,
        program=student.program,
        phone=student.phone,
        degree=student.degree,
        department=student.department,
        graduation_year=student.graduation_year,
        cgpa=student.cgpa,
        location=student.location,
        bio=student.bio,
        target_role=student.target_role,
        target_roles=list(student.target_roles or []),
        career_interests=list(student.career_interests or []),
        preferred_locations=list(student.preferred_locations or []),
        github_url=student.github_url,
        linkedin_url=student.linkedin_url,
        portfolio_url=student.portfolio_url,
        profile_completion=student.profile_completion,
        skills=student.skills,
        projects=student.projects,
        certifications=student.certifications,
    )


def resume_out(resume: Resume) -> ResumeOut:
    return ResumeOut(
        id=resume.id,
        student_id=resume.student_id,
        version_number=resume.version_number,
        version_name=resume.version_name,
        title=resume.title,
        target_role=resume.target_role,
        summary=resume.summary,
        content=resume.content or {},
        file_url=resume.file_url,
        status=resume.status,
        mentor_feedback=resume.mentor_feedback,
        reviewer_name=resume.reviewer.account.full_name if resume.reviewer and resume.reviewer.account else None,
        submitted_at=resume.submitted_at,
        reviewed_at=resume.reviewed_at,
        created_at=resume.created_at,
        updated_at=resume.updated_at,
        completeness=resume_completeness(resume),
    )


def company_out(company: Company) -> CompanyOut:
    return CompanyOut(
        id=company.id,
        name=company.name,
        description=company.description,
        industry=company.industry,
        website=company.website,
        location=company.location,
        contact_person=company.contact_person,
        contact_email=company.contact_email,
        contact_phone=company.contact_phone,
        status=company.status,
        created_at=company.created_at,
        job_count=len(company.jobs),
        drive_count=len(company.drives),
    )


def job_out(job: JobPosting) -> JobPostingOut:
    return JobPostingOut(
        id=job.id,
        company_id=job.company_id,
        company_name=job.company.name if job.company else None,
        title=job.title,
        description=job.description,
        required_skills=list(job.required_skills or []),
        min_cgpa=job.min_cgpa,
        eligible_departments=list(job.eligible_departments or []),
        graduation_years=list(job.graduation_years or []),
        job_type=job.job_type,
        location=job.location,
        salary_range=job.salary_range,
        application_deadline=job.application_deadline,
        status=job.status,
        created_at=job.created_at,
        drive_count=len(job.drives),
    )


def drive_out(drive: PlacementDrive, *, eligible_student_count: int = 0) -> PlacementDriveOut:
    days_to_deadline = None
    if drive.application_deadline is not None:
        days_to_deadline = (drive.application_deadline - date.today()).days

    return PlacementDriveOut(
        id=drive.id,
        company_id=drive.company_id,
        company_name=drive.company.name if drive.company else None,
        job_posting_id=drive.job_posting_id,
        job_title=drive.job_posting.title if drive.job_posting else None,
        name=drive.name,
        description=drive.description,
        drive_date=drive.drive_date,
        application_deadline=drive.application_deadline,
        min_cgpa=drive.min_cgpa,
        eligible_departments=list(drive.eligible_departments or []),
        graduation_years=list(drive.graduation_years or []),
        required_skills=list(drive.required_skills or []),
        location=drive.location,
        requires_mentor_approval=drive.requires_mentor_approval,
        status=drive.status,
        created_at=drive.created_at,
        application_count=len(drive.applications),
        eligible_student_count=eligible_student_count,
        days_to_deadline=days_to_deadline,
    )


def application_out(application: Application) -> ApplicationOut:
    student = application.student
    account = student.account if student else None
    drive = application.drive

    return ApplicationOut(
        id=application.id,
        code=application.code,
        student_id=application.student_id,
        student_name=account.full_name if account else None,
        registration_number=student.registration_number if student else None,
        department=student.department if student else None,
        cgpa=student.cgpa if student else None,
        target_role=student.target_role if student else None,
        drive_id=application.drive_id,
        drive_name=drive.name if drive else None,
        company_id=application.company_id,
        company_name=application.company.name if application.company else None,
        job_title=application.job_posting.title if application.job_posting else None,
        resume_id=application.resume_id,
        resume_version_name=application.resume.version_name if application.resume else None,
        eligibility_status=application.eligibility_status,
        eligibility_reasons=list(application.eligibility_reasons or []),
        missing_skills=list(application.missing_skills or []),
        status=application.status,
        mentor_feedback=application.mentor_feedback,
        mentor_name=(
            application.mentor.account.full_name if application.mentor and application.mentor.account else None
        ),
        note_to_mentor=application.note_to_mentor,
        admin_note=application.admin_note,
        created_at=application.created_at,
        updated_at=application.updated_at,
        decided_at=application.decided_at,
        next_action=compute_next_action(application.status),
    )


def feedback_out(entry: Feedback) -> FeedbackOut:
    return FeedbackOut(
        id=entry.id,
        student_id=entry.student_id,
        student_name=entry.student.account.full_name if entry.student and entry.student.account else None,
        mentor_id=entry.mentor_id,
        mentor_name=entry.mentor.account.full_name if entry.mentor and entry.mentor.account else None,
        resume_id=entry.resume_id,
        application_id=entry.application_id,
        title=entry.title,
        body=entry.body,
        status=entry.status,
        created_at=entry.created_at,
    )


def student_summary(db: Session, student: Student, *, include_readiness: bool = True) -> MentorStudentSummary:
    """Mentor and admin view of a student: profile, readiness, review load and warnings."""

    from ..services.readiness import calculate_readiness, latest_snapshot

    account = student.account
    resumes = db.query(Resume).filter(Resume.student_id == student.id).all()
    latest_resume = max(resumes, key=lambda item: item.version_number, default=None)
    pending_resumes = len([item for item in resumes if item.status == ResumeStatus.pending_review])

    applications = db.query(Application).filter(Application.student_id == student.id).all()
    pending_applications = len(
        [item for item in applications if item.status == ApplicationStatus.pending_mentor_approval]
    )
    open_applications = len([item for item in applications if item.status in ACTIVE_APPLICATION_STATUSES])

    overall_score = None
    if include_readiness:
        snapshot = latest_snapshot(db, student.id)
        overall_score = (
            snapshot.overall_score if snapshot is not None else calculate_readiness(db, student, persist=False).overall_score
        )

    reasons: list[str] = []
    if student.cgpa is None:
        reasons.append("CGPA not recorded")
    if student.profile_completion < 60:
        reasons.append(f"Profile only {student.profile_completion}% complete")
    if not resumes:
        reasons.append("No resume version created")
    elif latest_resume is not None and latest_resume.status == ResumeStatus.changes_requested:
        reasons.append("Resume changes requested and not resubmitted")
    if pending_resumes:
        reasons.append(f"{pending_resumes} resume review(s) waiting")
    if pending_applications:
        reasons.append(f"{pending_applications} application(s) waiting for approval")
    if overall_score is not None and overall_score < 50:
        reasons.append(f"Readiness score {overall_score} is below the guidance threshold")

    return MentorStudentSummary(
        student_id=student.id,
        account_id=student.account_id,
        full_name=account.full_name if account else f"Student #{student.id}",
        email=account.email if account else "",
        registration_number=student.registration_number,
        program=student.program,
        department=student.department,
        graduation_year=student.graduation_year,
        cgpa=student.cgpa,
        target_role=student.target_role,
        profile_completion=student.profile_completion,
        overall_score=overall_score,
        resume_status=latest_resume.status if latest_resume else None,
        pending_resume_reviews=pending_resumes,
        pending_application_reviews=pending_applications,
        open_applications=open_applications,
        needs_attention=len(reasons) > 0,
        attention_reasons=reasons,
    )



