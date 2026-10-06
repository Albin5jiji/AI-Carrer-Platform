"""Rule based learning path generation.

Recommendations come straight from the student's skill-gap result, mapped to curated
`learning_resources` rows for each skill. There is no AI model behind this: it is a
transparent rule based recommendation, and the API response says so.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..models import LearningPathItem, LearningResource, LearningStatus, Priority, Student
from ..schemas.readiness import LearningPathItemOut, LearningPathResponse
from .eligibility import normalize_skill
from .readiness import build_skill_gap, load_signals

MAX_RESOURCES_PER_SKILL = 2
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def _resources_for_skill(db: Session, skill_name: str) -> list[LearningResource]:
    normalized = normalize_skill(skill_name)
    resources = db.query(LearningResource).order_by(LearningResource.estimated_hours).all()
    matched = [resource for resource in resources if normalize_skill(resource.skill_name) == normalized]
    return matched[:MAX_RESOURCES_PER_SKILL]


def refresh_learning_path(db: Session, student: Student, *, target_role: str | None = None) -> int:
    """Create missing items for current gaps and drop stale untouched ones.

    Progress already recorded by the student is never deleted. Pass ``target_role`` to
    regenerate the path against a role different from the student's currently selected one.
    """

    signals = load_signals(db, student, target_role=target_role)
    gap = build_skill_gap(db, student, signals, target_role=target_role)
    open_gaps = [item for item in gap.items if item.status != "covered"]
    gap_skill_keys = {normalize_skill(item.skill_name) for item in open_gaps}

    existing = db.query(LearningPathItem).filter(LearningPathItem.student_id == student.id).all()
    existing_keys = {normalize_skill(item.skill_name) for item in existing}

    created = 0
    for gap_item in open_gaps:
        if normalize_skill(gap_item.skill_name) in existing_keys:
            continue
        for resource in _resources_for_skill(db, gap_item.skill_name):
            db.add(
                LearningPathItem(
                    student_id=student.id,
                    resource_id=resource.id,
                    skill_name=gap_item.skill_name,
                    priority=gap_item.priority,
                )
            )
            created += 1

    # Remove untouched recommendations for skills that are no longer gaps.
    for item in existing:
        still_relevant = normalize_skill(item.skill_name) in gap_skill_keys
        if not still_relevant and item.status == LearningStatus.not_started and item.progress_percent == 0:
            db.delete(item)

    return created


def default_priority_for(skill_name: str, gap_items) -> Priority:
    for item in gap_items:
        if normalize_skill(item.skill_name) == normalize_skill(skill_name):
            return item.priority
    return Priority.medium


def build_learning_path(db: Session, student: Student, *, target_role: str | None = None) -> LearningPathResponse:
    """Full learning path view model, ordered by priority and then by effort.

    Pass ``target_role`` to view a path for a role different from the student's currently
    selected one. Items are still filtered by ``student_id``.
    """

    items = db.query(LearningPathItem).filter(LearningPathItem.student_id == student.id).all()
    items.sort(
        key=lambda item: (
            PRIORITY_ORDER.get(item.priority.value, 1),
            item.status != LearningStatus.not_started,
            item.resource.estimated_hours if item.resource else 0,
        )
    )

    output: list[LearningPathItemOut] = []
    total_hours = 0.0
    remaining_hours = 0.0
    completed = in_progress = not_started = 0

    for item in items:
        resource = item.resource
        hours = resource.estimated_hours if resource else 0.0
        total_hours += hours
        if item.status != LearningStatus.completed:
            remaining_hours += hours * (1 - item.progress_percent / 100)
        if item.status == LearningStatus.completed:
            completed += 1
        elif item.status == LearningStatus.in_progress:
            in_progress += 1
        else:
            not_started += 1

        output.append(
            LearningPathItemOut(
                id=item.id,
                skill_name=item.skill_name,
                priority=item.priority,
                status=item.status,
                progress_percent=item.progress_percent,
                target_date=item.target_date.isoformat() if item.target_date else None,
                title=resource.title if resource else f"Practise {item.skill_name}",
                provider=resource.provider if resource else None,
                url=resource.url if resource else None,
                resource_type=resource.resource_type if resource else "practice",
                difficulty=resource.difficulty if resource else "beginner",
                estimated_hours=hours,
                description=resource.description if resource else None,
            )
        )

    total = len(output)
    next_item = next((entry for entry in output if entry.status != LearningStatus.completed), None)
    if next_item is None:
        next_action = (
            "Every recommended topic is complete. Recalculate your readiness score and keep your "
            "projects and resume evidence up to date."
        )
    else:
        next_action = (
            f"Start with {next_item.title} ({next_item.estimated_hours:g}h, "
            f"{next_item.difficulty.value}) for {next_item.skill_name}."
        )

    effective_role = target_role or student.target_role
    return LearningPathResponse(
        student_id=student.id,
        target_role=effective_role,
        total_items=total,
        not_started=not_started,
        in_progress=in_progress,
        completed=completed,
        completion_percent=round(completed / total * 100) if total else 0,
        total_estimated_hours=round(total_hours, 1),
        remaining_estimated_hours=round(remaining_hours, 1),
        next_action=next_action,
        items=output,
    )


def update_progress(
    db: Session,
    item: LearningPathItem,
    *,
    status: LearningStatus | None = None,
    progress_percent: int | None = None,
    notes: str | None = None,
    target_date=None,
) -> LearningPathItem:
    if status is not None:
        item.status = status
        if status == LearningStatus.completed:
            item.progress_percent = 100
            item.completed_at = datetime.now(timezone.utc)
        elif status == LearningStatus.not_started:
            item.progress_percent = 0
            item.completed_at = None
        elif item.progress_percent >= 100:
            item.progress_percent = 10
    if progress_percent is not None:
        item.progress_percent = progress_percent
        if progress_percent >= 100:
            item.status = LearningStatus.completed
            item.completed_at = item.completed_at or datetime.now(timezone.utc)
        elif progress_percent > 0:
            item.status = LearningStatus.in_progress
    if notes is not None:
        item.notes = notes
    if target_date is not None:
        item.target_date = target_date
    return item

