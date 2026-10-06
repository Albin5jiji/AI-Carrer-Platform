from pydantic import BaseModel, EmailStr, Field

from ..models import UserRole


class RegisterRequest(BaseModel):
    """Public self-registration.

    Only student and mentor accounts can be created through this endpoint; administrator
    accounts are created by an existing administrator, so the platform cannot be opened
    up by anyone picking the highest privilege level.
    """

    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    role: UserRole = UserRole.student
    identifier: str = Field(min_length=2, max_length=30)
    department_or_program: str = Field(min_length=2, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: UserRole
    identifier: str
    department_or_program: str
    profile_id: int | None = None
    is_active: bool = True
