"""Interview preparation helpers: practice coverage and mock interview statistics."""

from sqlalchemy.orm import Session

from ..models import InterviewCategory, InterviewPractice, InterviewQuestion, MockInterview, PracticeStatus, Student
from ..schemas.interview import InterviewCategoryProgress, InterviewOverview, MockInterviewOut
from .eligibility import normalize_skill


def questions_for_student(db: Session, student: Student) -> list[InterviewQuestion]:
    """Role specific questions first, then questions that apply to every role."""

    target_role = (student.target_role or "").strip().lower()
    questions = db.query(InterviewQuestion).order_by(InterviewQuestion.id).all()
    if not target_role:
        return [question for question in questions if question.target_role is None]

    relevant = [
        question
        for question in questions
        if question.target_role is None or question.target_role.strip().lower() == target_role
    ]
    return relevant or questions


def practice_index(db: Session, student_id: int) -> dict[int, InterviewPractice]:
    rows = db.query(InterviewPractice).filter(InterviewPractice.student_id == student_id).all()
    return {row.question_id: row for row in rows}


def build_overview(db: Session, student: Student) -> InterviewOverview:
    questions = questions_for_student(db, student)
    practices = practice_index(db, student.id)
    targeted_skills = {normalize_skill(skill.name) for skill in student.skills}

    categories: list[InterviewCategoryProgress] = []
    suggestions: list[str] = []
    practiced_total = 0
    revision_total = 0

    for category in InterviewCategory:
        bucket = [question for question in questions if question.category == category]
        practised = 0
        revision = 0
        for question in bucket:
            record = practices.get(question.id)
            if record is None:
                continue
            if record.status == PracticeStatus.practiced:
                practised += 1
            elif record.status == PracticeStatus.needs_revision:
                revision += 1
        practiced_total += practised
        revision_total += revision
        total = len(bucket)
        categories.append(
            InterviewCategoryProgress(
                category=category,
                total=total,
                practiced=practised,
                needs_revision=revision,
                progress_percent=round(practised / total * 100) if total else 0,
            )
        )
        if total and practised == 0:
            label = category.value.replace("_", " ")
            suggestions.append(f"Record at least one {label} practice session.")

    mock_rows = (
        db.query(MockInterview)
        .filter(MockInterview.student_id == student.id)
        .order_by(MockInterview.id.desc())
        .all()
    )
    completed_mocks = [row for row in mock_rows if row.completed and row.score is not None]
    average_mock = round(sum(row.score for row in completed_mocks) / len(completed_mocks)) if completed_mocks else None

    if not completed_mocks:
        suggestions.append("Complete one mock interview round and record the score.")
    elif average_mock is not None and average_mock < 70:
        suggestions.append("Your average mock score is below 70. Repeat the weakest category before the next drive.")

    untagged = [
        question
        for question in questions
        if question.id not in practices and (set(map(normalize_skill, question.skill_tags)) & targeted_skills)
    ]
    if untagged:
        suggestions.append(
            f"{len(untagged)} question(s) match skills you already list but are not practised yet."
        )

    total_questions = len(questions)
    coverage = round(practiced_total / total_questions * 100) if total_questions else 0
    interview_score = round(coverage * 0.6 + (average_mock or 0) * 0.4)

    return InterviewOverview(
        student_id=student.id,
        target_role=student.target_role,
        total_questions=total_questions,
        practiced_count=practiced_total,
        needs_revision_count=revision_total,
        progress_percent=coverage,
        interview_component_score=min(100, interview_score),
        categories=categories,
        mock_interviews=[
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
            for row in mock_rows
        ],
        completed_mock_interviews=len(completed_mocks),
        average_mock_score=average_mock,
        suggestions=suggestions
        or ["Keep practising weekly: coverage and mock interview scores both feed your readiness score."],
    )
