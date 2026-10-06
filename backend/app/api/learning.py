"""Learning path recommendations and progress tracking."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_student
from ..models import LearningPathItem, Student
from ..schemas.readiness import LearningPathResponse, LearningProgressUpdate
from ..services.learning import build_learning_path, refresh_learning_path, update_progress

router = APIRouter(prefix="/learning", tags=["Learning path"])


@router.get("/me/path", response_model=LearningPathResponse)
def my_learning_path(
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
    target_role: str | None = Query(default=None),
) -> LearningPathResponse:
    """Rule based learning path generated from the current skill gap.

    If nothing has been generated yet (or the target role changed), the path is
    refreshed automatically before returning.
    """

    effective_role = target_role or student.target_role
    path = build_learning_path(db, student, target_role=effective_role)
    if path.total_items == 0:
        created = refresh_learning_path(db, student, target_role=effective_role)
        if created:
            db.commit()
            path = build_learning_path(db, student, target_role=effective_role)
    return path


@router.post("/me/refresh", response_model=LearningPathResponse)
def refresh_my_learning_path(
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> LearningPathResponse:
    refresh_learning_path(db, student)
    db.commit()
    return build_learning_path(db, student)


@router.patch("/me/items/{item_id}", response_model=LearningPathResponse)
def update_item_progress(
    item_id: int,
    payload: LearningProgressUpdate,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> LearningPathResponse:
    item = db.get(LearningPathItem, item_id)
    if item is None or item.student_id != student.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Learning path item not found")

    target_date = None
    if payload.target_date:
        try:
            target_date = date.fromisoformat(payload.target_date)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="target_date must use the YYYY-MM-DD format",
            ) from exc

    update_progress(
        db,
        item,
        status=payload.status,
        progress_percent=payload.progress_percent,
        notes=payload.notes,
        target_date=target_date,
    )
    db.commit()
    return build_learning_path(db, student)
