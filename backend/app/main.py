"""FastAPI application entry point.

Routing
-------
* Every feature lives under `/api`.
* `/auth/*` and `/health` are additionally mounted at the root, so the original
  registration/login contract used by `src/authApi.ts` keeps working unchanged.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from .api import auth as auth_router
from .api.router import api_router
from .config import settings
from .database import Base, SessionLocal, engine
from .services.seed import seed_reference_data


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Create missing tables (development convenience) and seed the reference dataset."""

    if settings.auto_create_tables:
        from . import models  # noqa: F401  registers every table on Base.metadata

        Base.metadata.create_all(bind=engine)

    if settings.seed_reference_data:
        session = SessionLocal()
        try:
            seed_reference_data(session)
        except SQLAlchemyError:
            session.rollback()
        finally:
            session.close()

    yield


app = FastAPI(
    title=settings.app_name,
    version="2.0.0",
    description=(
        "Student Career Intelligence and Placement Management Platform API: career readiness "
        "score, skill gaps, learning paths, interview preparation, placement drives, "
        "applications, mentor review, notifications and admin reporting."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(auth_router.router)  # root level auth paths kept for compatibility


@app.get("/health", tags=["System"])
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}


@app.get("/", tags=["System"])
def root() -> dict[str, str]:
    return {"name": settings.app_name, "docs": "/docs", "api": "/api", "health": "/health"}


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Collapse Pydantic validation output into one readable message."""

    problems: list[str] = []
    for error in exc.errors():
        location = ".".join(str(part) for part in error.get("loc", []) if part != "body")
        problems.append(f"{location or 'request'}: {error.get('msg', 'invalid value')}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "; ".join(problems) or "Invalid request body"},
    )


@app.exception_handler(IntegrityError)
async def integrity_error_handler(_: Request, __: IntegrityError) -> JSONResponse:
    """Duplicate keys and constraint violations become a clean 409."""

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "That operation conflicts with existing data"},
    )


@app.exception_handler(SQLAlchemyError)
async def database_error_handler(_: Request, __: SQLAlchemyError) -> JSONResponse:
    """Never leak raw SQL or connection strings to the client."""

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": (
                "A database error occurred while processing the request. "
                "Check the API logs for the full traceback."
            )
        },
    )
