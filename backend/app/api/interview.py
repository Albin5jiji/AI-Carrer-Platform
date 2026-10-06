"""Interview preparation: question bank, practice records and mock interviews."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_student
from ..models import (
    Difficulty,
    InterviewCategory,
    InterviewPractice,
    InterviewQuestion,
    MockInterview,
    PracticeStatus,
    Student,
)
from ..schemas.interview import (
    InterviewOverview,
    InterviewQuestionOut,
    MockInterviewCreate,
    MockInterviewOut,
    PracticeUpdate,
)
from ..services.interview import build_overview, practice_index, questions_for_student

router = APIRouter(prefix="/interview", tags=["Interview preparation"])


@router.get("/me/overview", response_model=InterviewOverview)
def my_overview(
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> InterviewOverview:
    return build_overview(db, student)


@router.get("/me/questions", response_model=list[InterviewQuestionOut])
def my_questions(
    category: InterviewCategory | None = None,
    difficulty: Difficulty | None = None,
    only_unpractised: bool = False,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> list[InterviewQuestionOut]:
    questions = questions_for_student(db, student)
    practices = practice_index(db, student.id)

    output: list[InterviewQuestionOut] = []
    for question in questions:
        if category is not None and question.category != category:
            continue
        if difficulty is not None and question.difficulty != difficulty:
            continue
        record = practices.get(question.id)
        if only_unpractised and record is not None and record.status != PracticeStatus.not_started:
            continue
        output.append(
            InterviewQuestionOut(
                id=question.id,
                category=question.category,
                target_role=question.target_role,
                difficulty=question.difficulty,
                question=question.question,
                guidance=question.guidance,
                skill_tags=list(question.skill_tags or []),
                practice_status=record.status if record else PracticeStatus.not_started,
                self_rating=record.self_rating if record else None,
                practiced_at=record.practiced_at if record else None,
            )
        )
    return output


@router.post("/me/practice/{question_id}", response_model=InterviewOverview)
def record_practice(
    question_id: int,
    payload: PracticeUpdate,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> InterviewOverview:
    question = db.get(InterviewQuestion, question_id)
    if question is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview question not found")

    record = (
        db.query(InterviewPractice)
        .filter(InterviewPractice.student_id == student.id, InterviewPractice.question_id == question_id)
        .one_or_none()
    )
    if record is None:
        record = InterviewPractice(student_id=student.id, question_id=question_id)
        db.add(record)

    record.status = payload.status
    record.self_rating = payload.self_rating
    record.notes = payload.notes
    if payload.status == PracticeStatus.not_started:
        record.practiced_at = None
    else:
        record.practiced_at = datetime.now(timezone.utc)

    db.commit()
    return build_overview(db, student)


@router.post("/me/mock", response_model=list[MockInterviewOut], status_code=status.HTTP_201_CREATED)
def create_mock_interview(
    payload: MockInterviewCreate,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> list[MockInterviewOut]:
    if payload.completed and payload.score is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Record a score between 0 and 100 for a completed mock interview",
        )

    db.add(
        MockInterview(
            student_id=student.id,
            target_role=payload.target_role or student.target_role,
            mode=payload.mode,
            scheduled_for=payload.scheduled_for,
            completed=payload.completed,
            score=payload.score,
            strengths=payload.strengths,
            improvements=payload.improvements,
        )
    )
    db.commit()

    rows = (
        db.query(MockInterview)
        .filter(MockInterview.student_id == student.id)
        .order_by(MockInterview.id.desc())
        .all()
    )
    return [
        MockInterviewOut(
            id=row.id,
            target_role=row.target_role,
            mode=row.mode,
            scheduled_for=row.scheduled_for,
            completed=row.completed,
            score=row.score,
            strengths=row.strengths,
            improvements=row.improvements,
            feedback=row.feedback,
            created_at=row.created_at,
        )
        for row in rows
    ]
