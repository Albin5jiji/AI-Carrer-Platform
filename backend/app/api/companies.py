"""Company management. Read for every signed-in user, write for administrators."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_account, require_admin
from ..models import Account, Company, CompanyStatus, PlacementDrive
from ..schemas.common import Message
from ..schemas.placement import CompanyCreate, CompanyOut, CompanyUpdate
from ..services.audit import record_audit
from .serializers import company_out

router = APIRouter(prefix="/companies", tags=["Companies"])


@router.get("", response_model=list[CompanyOut])
def list_companies(
    search: str | None = None,
    industry: str | None = None,
    status_filter: CompanyStatus | None = None,
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> list[CompanyOut]:
    query = db.query(Company)

    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(Company.name.ilike(pattern) | Company.industry.ilike(pattern))

    if industry:
        query = query.filter(Company.industry == industry)

    if status_filter is not None:
        query = query.filter(Company.status == status_filter)
    elif not include_inactive or account.role.value == "student":
        query = query.filter(Company.status == CompanyStatus.active)

    return [company_out(company) for company in query.order_by(Company.name).all()]


@router.get("/{company_id}", response_model=CompanyOut)
def read_company(
    company_id: int,
    db: Session = Depends(get_db),
    _: Account = Depends(get_current_account),
) -> CompanyOut:
    company = db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return company_out(company)


@router.post("", response_model=CompanyOut, status_code=status.HTTP_201_CREATED)
def create_company(
    payload: CompanyCreate,
    db: Session = Depends(get_db),
    account: Account = Depends(require_admin),
) -> CompanyOut:
    if db.query(Company).filter(Company.name.ilike(payload.name.strip())).count():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A company with that name already exists")

    data = payload.model_dump()
    data["contact_email"] = str(data["contact_email"]) if data.get("contact_email") else None
    company = Company(**data)
    db.add(company)
    db.flush()
    record_audit(
        db,
        actor=account,
        action="create_company",
        entity_type="company",
        entity_id=company.id,
        summary=f"Created company {company.name}",
    )
    db.commit()
    db.refresh(company)
    return company_out(company)


@router.patch("/{company_id}", response_model=CompanyOut)
def update_company(
    company_id: int,
    payload: CompanyUpdate,
    db: Session = Depends(get_db),
    account: Account = Depends(require_admin),
) -> CompanyOut:
    company = db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    changes = payload.model_dump(exclude_unset=True)
    if "name" in changes and changes["name"]:
        duplicate = (
            db.query(Company)
            .filter(Company.name.ilike(changes["name"].strip()), Company.id != company_id)
            .count()
        )
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Another company already uses that name"
            )
        changes["name"] = changes["name"].strip()
    if "contact_email" in changes and changes["contact_email"]:
        changes["contact_email"] = str(changes["contact_email"])

    for field, value in changes.items():
        setattr(company, field, value)

    record_audit(
        db,
        actor=account,
        action="update_company",
        entity_type="company",
        entity_id=company.id,
        summary=f"Updated company {company.name}",
        meta={"fields": sorted(changes.keys())},
    )
    db.commit()
    db.refresh(company)
    return company_out(company)


@router.delete("/{company_id}", response_model=Message)
def deactivate_company(
    company_id: int,
    db: Session = Depends(get_db),
    account: Account = Depends(require_admin),
) -> Message:
    """Soft delete: companies referenced by drives are deactivated, never destroyed."""

    company = db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    referenced = db.query(PlacementDrive).filter(PlacementDrive.company_id == company_id).count()
    if referenced:
        company.status = CompanyStatus.inactive
        message = f"{company.name} deactivated. {referenced} drive(s) keep their history."
    else:
        db.delete(company)
        message = f"{company.name} deleted."

    record_audit(
        db,
        actor=account,
        action="deactivate_company",
        entity_type="company",
        entity_id=company_id,
        summary=message,
    )
    db.commit()
    return Message(message=message)
