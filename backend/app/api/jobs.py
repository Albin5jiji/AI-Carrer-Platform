"""Job posting management. Read for signed-in users, write for administrators."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_account, require_admin
from ..models import Account, Company, JobPosting, JobPostingStatus, UserRole
from ..schemas.common import Message
from ..schemas.placement import JobPostingCreate, JobPostingOut, JobPostingUpdate
from ..services.audit import record_audit
from .serializers import job_out

router = APIRouter(prefix="/jobs", tags=["Job postings"])


@router.get("", response_model=list[JobPostingOut])
def list_jobs(
    search: str | None = None,
    company_id: int | None = None,
    status_filter: JobPostingStatus | None = None,
    db: Session = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> list[JobPostingOut]:
    query = db.query(JobPosting)

    if account.role == UserRole.student:
        query = query.filter(JobPosting.status == JobPostingStatus.published)
    elif status_filter is not None:
        query = query.filter(JobPosting.status == status_filter)

    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(JobPosting.title.ilike(pattern))
    if company_id is not None:
        query = query.filter(JobPosting.company_id == company_id)

    return [job_out(job) for job in query.order_by(JobPosting.id.desc()).all()]


@router.get("/{job_id}", response_model=JobPostingOut)
def read_job(
    job_id: int,
    db: Session = Depends(get_db),
    _: Account = Depends(get_current_account),
) -> JobPostingOut:
    job = db.get(JobPosting, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job posting not found")
    return job_out(job)


@router.post("", response_model=JobPostingOut, status_code=status.HTTP_201_CREATED)
def create_job(
    payload: JobPostingCreate,
    db: Session = Depends(get_db),
    account: Account = Depends(require_admin),
) -> JobPostingOut:
    company = db.get(Company, payload.company_id)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    job = JobPosting(**payload.model_dump(), created_by_account_id=account.id)
    db.add(job)
    db.flush()
    record_audit(
        db,
        actor=account,
        action="create_job",
        entity_type="job_posting",
        entity_id=job.id,
        summary=f"Created job posting '{job.title}' for {company.name}",
    )
    db.commit()
    db.refresh(job)
    return job_out(job)


@router.patch("/{job_id}", response_model=JobPostingOut)
def update_job(
    job_id: int,
    payload: JobPostingUpdate,
    db: Session = Depends(get_db),
    account: Account = Depends(require_admin),
) -> JobPostingOut:
    job = db.get(JobPosting, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job posting not found")

    changes = payload.model_dump(exclude_unset=True)
    if changes.get("company_id") is not None and db.get(Company, changes["company_id"]) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    for field, value in changes.items():
        setattr(job, field, value)

    record_audit(
        db,
        actor=account,
        action="update_job",
        entity_type="job_posting",
        entity_id=job.id,
        summary=f"Updated job posting '{job.title}'",
        meta={"fields": sorted(changes.keys())},
    )
    db.commit()
    db.refresh(job)
    return job_out(job)


@router.post("/{job_id}/publish", response_model=JobPostingOut)
def publish_job(
    job_id: int,
    db: Session = Depends(get_db),
    account: Account = Depends(require_admin),
) -> JobPostingOut:
    job = db.get(JobPosting, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job posting not found")
    if job.status == JobPostingStatus.closed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="A closed job posting cannot be republished"
        )

    job.status = JobPostingStatus.published
    record_audit(
        db,
        actor=account,
        action="publish_job",
        entity_type="job_posting",
        entity_id=job.id,
        summary=f"Published '{job.title}'",
    )
    db.commit()
    db.refresh(job)
    return job_out(job)


@router.post("/{job_id}/close", response_model=JobPostingOut)
def close_job(
    job_id: int,
    db: Session = Depends(get_db),
    account: Account = Depends(require_admin),
) -> JobPostingOut:
    job = db.get(JobPosting, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job posting not found")

    job.status = JobPostingStatus.closed
    record_audit(
        db,
        actor=account,
        action="close_job",
        entity_type="job_posting",
        entity_id=job.id,
        summary=f"Closed '{job.title}'",
    )
    db.commit()
    db.refresh(job)
    return job_out(job)


@router.delete("/{job_id}", response_model=Message)
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    account: Account = Depends(require_admin),
) -> Message:
    job = db.get(JobPosting, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job posting not found")
    if job.drives:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This posting is used by a placement drive. Close it instead of deleting.",
        )

    title = job.title
    db.delete(job)
    record_audit(
        db,
        actor=account,
        action="delete_job",
        entity_type="job_posting",
        entity_id=job_id,
        summary=f"Deleted job posting '{title}'",
    )
    db.commit()
    return Message(message=f"Job posting '{title}' deleted")
