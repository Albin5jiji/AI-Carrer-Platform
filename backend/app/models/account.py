from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .base import TimestampMixin
from .enums import UserRole

if TYPE_CHECKING:
    from .mentor import Mentor
    from .student import Student


class Account(Base, TimestampMixin):
    """The one user table shared by students, mentors and administrators.

    Every module (student career data, placement data, mentor reviews and admin
    audit logs) references this single table so roles stay consistent.
    """

    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    student: Mapped[Student | None] = relationship(
        back_populates="account", uselist=False, cascade="all, delete-orphan"
    )
    mentor: Mapped[Mentor | None] = relationship(
        back_populates="account", uselist=False, cascade="all, delete-orphan"
    )
    administrator: Mapped[Administrator | None] = relationship(
        back_populates="account", uselist=False, cascade="all, delete-orphan"
    )

    @property
    def identifier(self) -> str:
        if self.student is not None:
            return self.student.registration_number
        if self.mentor is not None:
            return self.mentor.employee_code
        if self.administrator is not None:
            return self.administrator.staff_code
        return f"ACC-{self.id}"

    @property
    def department_or_program(self) -> str:
        if self.student is not None:
            return self.student.department or self.student.program
        if self.mentor is not None:
            return self.mentor.department
        if self.administrator is not None:
            return self.administrator.office
        return ""


class Administrator(Base, TimestampMixin):
    """Placement-cell staff profile linked to an `Account` with the administrator role."""

    __tablename__ = "administrators"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), index=True, unique=True, nullable=False
    )
    staff_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    office: Mapped[str] = mapped_column(String(120), nullable=False, default="Placement Cell")

    account: Mapped[Account] = relationship(back_populates="administrator")
