"""Aggregates every feature router under a single `/api` prefix."""

from fastapi import APIRouter

from . import (
    admin,
    applications,
    auth,
    companies,
    drives,
    interview,
    jobs,
    learning,
    mentor,
    notifications,
    readiness,
    resumes,
    students,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(students.router)
api_router.include_router(resumes.router)
api_router.include_router(readiness.router)
api_router.include_router(learning.router)
api_router.include_router(interview.router)
api_router.include_router(companies.router)
api_router.include_router(jobs.router)
api_router.include_router(drives.router)
api_router.include_router(applications.router)
api_router.include_router(mentor.router)
api_router.include_router(admin.router)
api_router.include_router(notifications.router)
