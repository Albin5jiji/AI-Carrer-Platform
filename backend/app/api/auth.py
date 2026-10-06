"""Authentication and session endpoints.

Preserves the original project's `/auth/register`, `/auth/login` and `/auth/me`
contract, and adds one security improvement: administrator accounts can no longer be
self-registered through the public endpoint.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_account
from ..models import Account, Mentor, Student, UserRole
from ..schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from ..security import create_access_token, hash_password, verify_password
from ..services.audit import record_audit
from .serializers import user_response

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    if payload.role == UserRole.administrator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator accounts are created by the placement cell, not through public sign up",
        )

    account = Account(
        full_name=payload.full_name.strip(),
        email=str(payload.email).lower(),
        role=payload.role,
        password_hash=hash_password(payload.password),
    )
    db.add(account)
    db.flush()

    if payload.role == UserRole.student:
        db.add(
            Student(
                account_id=account.id,
                registration_number=payload.identifier.strip().upper(),
                program=payload.department_or_program.strip(),
                profile_completion=0,
            )
        )
    else:
        db.add(
            Mentor(
                account_id=account.id,
                employee_code=payload.identifier.strip().upper(),
                department=payload.department_or_program.strip(),
            )
        )

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That email or identifier is already registered",
        ) from exc

    record_audit(
        db,
        actor=account,
        action="register",
        entity_type="account",
        entity_id=account.id,
        summary=f"{payload.role.value} account created",
    )
    db.commit()
    return TokenResponse(access_token=create_access_token(str(account.id)))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    account = db.scalar(select(Account).where(Account.email == str(payload.email).lower()))
    if account is None or not verify_password(payload.password, account.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not account.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account has been deactivated")

    return TokenResponse(access_token=create_access_token(str(account.id)))


@router.get("/me", response_model=UserResponse)
def read_current_user(account: Account = Depends(get_current_account)) -> UserResponse:
    return user_response(account)
