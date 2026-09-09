from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .config import settings
from .database import Base, engine, get_db
from .models import Account, Administrator, Mentor, Student, UserRole
from .schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from .security import create_access_token, decode_access_token, hash_password, verify_password

app = FastAPI(title=settings.app_name)
bearer_scheme = HTTPBearer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def create_tables() -> None:
    Base.metadata.create_all(bind=engine)


def profile_for_account(db: Session, account: Account) -> tuple[str, str]:
    if account.role == UserRole.student:
        profile = db.scalar(select(Student).where(Student.account_id == account.id))
        return profile.registration_number, profile.program

    if account.role == UserRole.mentor:
        profile = db.scalar(select(Mentor).where(Mentor.account_id == account.id))
        return profile.employee_code, profile.department

    profile = db.scalar(select(Administrator).where(Administrator.account_id == account.id))
    return profile.staff_code, profile.office


def to_user_response(db: Session, account: Account) -> UserResponse:
    identifier, department_or_program = profile_for_account(db, account)
    return UserResponse(
        id=account.id,
        full_name=account.full_name,
        email=account.email,
        role=account.role,
        identifier=identifier,
        department_or_program=department_or_program,
    )


def get_current_account(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Account:
    subject = decode_access_token(credentials.credentials)
    if subject is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    account = db.get(Account, int(subject))
    if account is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account no longer exists")

    return account


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    account = Account(
        full_name=payload.full_name,
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
                registration_number=payload.identifier,
                program=payload.department_or_program,
            ),
        )
    elif payload.role == UserRole.mentor:
        db.add(
            Mentor(
                account_id=account.id,
                employee_code=payload.identifier,
                department=payload.department_or_program,
            ),
        )
    else:
        db.add(
            Administrator(
                account_id=account.id,
                staff_code=payload.identifier,
                office=payload.department_or_program,
            ),
        )

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email or identifier already exists") from exc

    return TokenResponse(access_token=create_access_token(str(account.id)))


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    account = db.scalar(select(Account).where(Account.email == str(payload.email).lower()))
    if account is None or not verify_password(payload.password, account.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    return TokenResponse(access_token=create_access_token(str(account.id)))


@app.get("/auth/me", response_model=UserResponse)
def read_current_user(
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
) -> UserResponse:
    return to_user_response(db, account)
