"""Shared FastAPI dependencies: authentication and role based access control."""

from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import Account, Mentor, Student, UserRole
from .security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)

CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_account(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Account:
    """Resolve the JWT bearer token to an active account."""

    if credentials is None:
        raise CREDENTIALS_ERROR

    subject = decode_access_token(credentials.credentials)
    if subject is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    try:
        account_id = int(subject)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject") from exc

    account = db.get(Account, account_id)
    if account is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account no longer exists")
    if not account.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")
    return account


def require_roles(*roles: UserRole) -> Callable[[Account], Account]:
    """Dependency factory enforcing that the caller holds one of the given roles."""

    allowed = set(roles)

    def dependency(account: Account = Depends(get_current_account)) -> Account:
        if account.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return account

    return dependency


require_student = require_roles(UserRole.student)
require_mentor = require_roles(UserRole.mentor)
require_admin = require_roles(UserRole.administrator)
require_mentor_or_admin = require_roles(UserRole.mentor, UserRole.administrator)


def get_current_student(
    account: Account = Depends(require_student),
    db: Session = Depends(get_db),
) -> Student:
    student = db.query(Student).filter(Student.account_id == account.id).one_or_none()
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")
    return student


def get_current_mentor(
    account: Account = Depends(require_mentor),
    db: Session = Depends(get_db),
) -> Mentor:
    mentor = db.query(Mentor).filter(Mentor.account_id == account.id).one_or_none()
    if mentor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mentor profile not found")
    return mentor
