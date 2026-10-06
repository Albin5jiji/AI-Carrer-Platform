"""Personal Readiness Score, skill gap and readiness history."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_student
from ..models import Student
from ..schemas.readiness import (
    AISkillGapAnalysisOut,
    ReadinessHistoryResponse,
    ReadinessResponse,
    ReadinessSnapshotOut,
    SkillGapResponse,
)
from ..services.ai import AIService
from ..services.ai.client import build_ai_provider
from ..services.ai.service import AIUnavailableError
from ..services.ai.validation import AIValidationError
from ..services.readiness import (
    READINESS_WEIGHTS,
    build_history,
    build_skill_gap,
    calculate_readiness,
)

router = APIRouter(prefix="/readiness", tags=["Readiness and skill gap"])


@router.get("/weights")
def readiness_weights() -> dict:
    """The exact weights behind the score, published so the calculation is transparent."""

    return {
        "weights": READINESS_WEIGHTS,
        "total": sum(READINESS_WEIGHTS.values()),
        "component_order": list(READINESS_WEIGHTS.keys()),
        "scale": "each component is normalised to 0-100 before weighting",
    }


@router.get("/me", response_model=ReadinessResponse)
def my_readiness(
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
    target_role: str | None = None,
) -> ReadinessResponse:
    """Recalculate the PRS from live data and store a history snapshot.

    Pass ``target_role`` to compute a one-off score against a role different from the
    student's currently selected one. The response reports that role, but no persistent
    snapshot is written for it.
    """

    effective_role = target_role or student.target_role
    response = calculate_readiness(db, student, persist=True, target_role=effective_role)
    db.commit()
    return response


@router.get("/me/skill-gap", response_model=SkillGapResponse)
def my_skill_gap(
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
    target_role: str | None = None,
) -> SkillGapResponse:
    effective_role = target_role or student.target_role
    return build_skill_gap(db, student, target_role=effective_role)


@router.post("/me/ai-skill-gap", response_model=AISkillGapAnalysisOut)
def my_ai_skill_gap(
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> AISkillGapAnalysisOut:
    """Generate advisory AI guidance based on the deterministic skill-gap context.

    This endpoint never mutates the student's PRS, eligibility, profile, or application status.
    It simply enriches the existing deterministic gap analysis with a model-generated explanation.
    """

    ai_service = AIService(provider=build_ai_provider())
    try:
        result = ai_service.generate_skill_gap_analysis(db, student)
    except AIValidationError as exc:
        raise HTTPException(status_code=422, detail={"code": exc.code, "message": str(exc)}) from exc
    except AIUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "ai_temporarily_unavailable",
                "message": "AI recommendations are temporarily unavailable",
            },
        ) from exc
    return AISkillGapAnalysisOut.model_validate(result.model_dump())


@router.get("/me/history", response_model=ReadinessHistoryResponse)
def my_history(
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> ReadinessHistoryResponse:
    snapshots = build_history(db, student)

    latest = snapshots[-1] if snapshots else None
    previous = snapshots[-2] if len(snapshots) > 1 else None

    timeline: list[str] = []
    for index in range(1, len(snapshots)):
        before, after = snapshots[index - 1], snapshots[index]
        delta = after.overall_score - before.overall_score
        stamp = after.computed_at.strftime("%d %b %Y") if after.computed_at else "snapshot"
        direction = "improved" if delta > 0 else "dropped" if delta < 0 else "stayed level"
        timeline.append(f"{stamp}: readiness {direction} by {abs(delta)} points to {after.overall_score}.")
    timeline.reverse()

    if not snapshots:
        timeline.append(
            "No readiness history yet. Recalculate your readiness score to start tracking progress."
        )
    elif len(snapshots) == 1:
        timeline.append(
            "This is your first snapshot. Recalculate after each improvement to build a trend."
        )

    return ReadinessHistoryResponse(
        student_id=student.id,
        target_role=student.target_role,
        latest_score=latest.overall_score if latest else None,
        previous_score=previous.overall_score if previous else None,
        change=(latest.overall_score - previous.overall_score) if latest and previous else None,
        snapshot_count=len(snapshots),
        snapshots=[
            ReadinessSnapshotOut(
                id=snapshot.id,
                overall_score=snapshot.overall_score,
                academics=snapshot.academics,
                skills=snapshot.skills,
                projects=snapshot.projects,
                certifications=snapshot.certifications,
                resume=snapshot.resume,
                interview=snapshot.interview,
                target_role=snapshot.target_role,
                computed_at=snapshot.computed_at,
            )
            for snapshot in snapshots
        ],
        improvement_timeline=timeline,
    )
