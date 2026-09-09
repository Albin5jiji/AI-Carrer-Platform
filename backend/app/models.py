import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class UserRole(str, enum.Enum):
    student = "student"
    mentor = "mentor"
    administrator = "administrator"


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), index=True, unique=True)
    registration_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    program: Mapped[str] = mapped_column(String(120), nullable=False)


class Mentor(Base):
    __tablename__ = "mentors"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), index=True, unique=True)
    employee_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    department: Mapped[str] = mapped_column(String(120), nullable=False)


class Administrator(Base):
    __tablename__ = "administrators"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), index=True, unique=True)
    staff_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    office: Mapped[str] = mapped_column(String(120), nullable=False)
