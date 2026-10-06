"""Skill-gap and readiness computation.

Design notes
------------
* `READINESS_WEIGHTS` is the only place the Personal Readiness Score weights live.
  They sum to 100, and every component is normalised to 0-100 before weighting.
* Every component has a documented, measurable input:
    - academics      : CGPA mapped to a 0-100 scale (cgpa / 10 * 100)
    - skills         : coverage of the target role's required skills (role_skills table),
                       weighted by skill priority and by the student's proficiency level
    - projects       : number of projects + how many target-role skills they demonstrate
                       + whether repository/demo links exist
    - certifications : number of certifications + how many are relevant to the target role
    - resume         : best resume status (approved/draft/...) + completeness of its content
    - interview      : practice coverage across question categories + mock interview scores
* The score is an internal readiness indicator. It never claims to guarantee selection.
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..models import (
    InterviewPractice,
    InterviewQuestion,
    LearningResource,
    MockInterview,
    PracticeStatus,
    ProficiencyLevel,
    ReadinessSnapshot,
    Resume,
    ResumeStatus,
    RoleSkill,
    Student,
)
from ..schemas.readiness import ReadinessComponent, ReadinessResponse, SkillGapItem, SkillGapResponse
from .eligibility import PROFICIENCY_RANK, normalize_skill

READINESS_WEIGHTS: dict[str, int] = {
    "academics": 15,
    "skills": 30,
    "projects": 20,
    "certifications": 10,
    "resume": 10,
    "interview": 15,
}

COMPONENT_LABELS: dict[str, str] = {
    "academics": "Academic Performance",
    "skills": "Skill Match",
    "projects": "Project Relevance",
    "certifications": "Certifications",
    "resume": "Resume Quality",
    "interview": "Interview Preparation",
}

PRIORITY_WEIGHT = {"high": 3.0, "medium": 2.0, "low": 1.0}
PROFICIENCY_VALUE = {"beginner": 0.5, "intermediate": 0.8, "advanced": 1.0}

DISCLAIMER = (
    "The Personal Readiness Score is an internal career-readiness indicator calculated from "
    "your profile data. It is a guidance tool and does not guarantee a job offer or selection."
)


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> int:
    return int(round(max(low, min(high, value))))


def _role_requirements(db: Session, target_role: str | None) -> list[RoleSkill]:
    if not target_role:
        return []
    return (
        db.query(RoleSkill)
        .filter(RoleSkill.role_name == target_role.strip())
        .order_by(RoleSkill.display_order)
        .all()
    )


@dataclass
class StudentSignals:
    """Everything the six components need, loaded once per calculation."""

    student: Student
    skills: list
    projects: list
    certifications: list
    resumes: list
    practices: list
    questions: list
    mock_interviews: list
    requirements: list


def load_signals(db: Session, student: Student, *, target_role: str | None = None) -> StudentSignals:
    effective_role = target_role or student.target_role
    return StudentSignals(
        student=student,
        skills=list(student.skills),
        projects=list(student.projects),
        certifications=list(student.certifications),
        resumes=list(student.resumes),
        practices=db.query(InterviewPractice).filter(InterviewPractice.student_id == student.id).all(),
        questions=db.query(InterviewQuestion).all(),
        mock_interviews=db.query(MockInterview).filter(MockInterview.student_id == student.id).all(),
        requirements=_role_requirements(db, effective_role),
    )


def resume_completeness(resume: Resume) -> int:
    """Share of the key resume sections that actually contain content."""

    content = resume.content or {}

    def filled(value) -> bool:
        if isinstance(value, list):
            return len(value) > 0
        return bool(value and str(value).strip())

    checks = [
        filled(resume.summary),
        filled(resume.target_role),
        filled(content.get("education")),
        filled(content.get("skills")),
        filled(content.get("projects")),
        filled(content.get("experience")),
        filled(content.get("achievements")),
    ]
    return _clamp(sum(1 for check in checks if check) / len(checks) * 100)


def calculate_profile_completion(student: Student) -> int:
    """Profile completion percentage used by the profile header and mentor view."""

    checks = [
        bool(student.program),
        bool(student.degree),
        bool(student.department),
        student.graduation_year is not None,
        student.cgpa is not None,
        bool(student.phone),
        bool(student.target_role),
        len(student.target_roles or []) > 0,
        len(student.career_interests or []) > 0,
        len(student.preferred_locations or []) > 0,
        bool(student.github_url or student.linkedin_url or student.portfolio_url),
        len(student.skills) > 0,
        len(student.projects) > 0,
        len(student.certifications) > 0,
        bool(student.bio),
    ]
    return _clamp(sum(1 for check in checks if check) / len(checks) * 100)


# --- six components -----------------------------------------------------------


def _academics_component(signals: StudentSignals) -> tuple[int, str]:
    cgpa = signals.student.cgpa
    if cgpa is None:
        return 0, "CGPA is not recorded in your profile yet."
    return _clamp(cgpa / 10 * 100), f"CGPA {cgpa:.2f} on a 10 point scale."


def _skills_component(signals: StudentSignals) -> tuple[int, str]:
    if not signals.requirements:
        score = _clamp(len(signals.skills) * 10)
        return score, (
            "No target role is selected, so this is based on the number of skills recorded "
            f"({len(signals.skills)} skills). Select a target role for an accurate skill match."
        )

    possessed = {normalize_skill(skill.name): skill for skill in signals.skills}
    total_weight = 0.0
    earned = 0.0
    covered = 0
    missing: list[str] = []

    for requirement in signals.requirements:
        weight = PRIORITY_WEIGHT.get(requirement.priority.value, 2.0)
        total_weight += weight
        match = possessed.get(normalize_skill(requirement.skill_name))
        if match is None:
            missing.append(requirement.skill_name)
            continue
        covered += 1
        earned += weight * PROFICIENCY_VALUE.get(match.proficiency.value, 0.8)

    score = _clamp(earned / total_weight * 100) if total_weight else 0
    explanation = (
        f"{covered} of {len(signals.requirements)} required skills for "
        f"'{signals.student.target_role}' are covered."
    )
    if missing:
        explanation += f" Missing: {', '.join(missing[:6])}."
    return score, explanation


def _projects_component(signals: StudentSignals) -> tuple[int, str]:
    projects = signals.projects
    if not projects:
        return 0, "No projects recorded. Add at least two projects with repository links."

    role_skills = {normalize_skill(skill.skill_name) for skill in signals.requirements}
    relevant = 0
    linked = 0
    for project in projects:
        stack = {normalize_skill(item) for item in (project.tech_stack or [])}
        if (role_skills and stack & role_skills) or (not role_skills and stack):
            relevant += 1
        if project.repo_url or project.live_url:
            linked += 1

    count_score = min(60.0, len(projects) * 20.0)
    relevance_score = relevant / len(projects) * 25.0
    link_score = linked / len(projects) * 15.0
    score = _clamp(count_score + relevance_score + link_score)
    return score, (
        f"{len(projects)} project(s) recorded, {relevant} demonstrably relevant to "
        f"'{signals.student.target_role or 'your goals'}', {linked} with a repository or demo link."
    )


def _certifications_component(signals: StudentSignals) -> tuple[int, str]:
    certifications = signals.certifications
    if not certifications:
        return 0, "No certifications recorded yet."

    role_skills = {normalize_skill(skill.skill_name) for skill in signals.requirements}
    relevant = 0
    for certification in certifications:
        tags = {normalize_skill(tag) for tag in (certification.skill_tags or [])}
        if role_skills and tags & role_skills:
            relevant += 1

    count_score = min(60.0, len(certifications) * 20.0)
    relevance_score = (relevant / len(certifications) * 40.0) if role_skills else 20.0
    score = _clamp(count_score + relevance_score)
    return score, (
        f"{len(certifications)} certification(s) recorded, {relevant} tagged with skills "
        "required by your target role."
    )


RESUME_STATUS_VALUE = {
    ResumeStatus.approved: 60.0,
    ResumeStatus.pending_review: 45.0,
    ResumeStatus.draft: 25.0,
    ResumeStatus.changes_requested: 15.0,
}


def _resume_component(signals: StudentSignals) -> tuple[int, str]:
    if not signals.resumes:
        return 0, "No resume version created yet. Create a version and submit it for mentor review."

    best = max(
        signals.resumes,
        key=lambda resume: (RESUME_STATUS_VALUE.get(resume.status, 0.0), resume_completeness(resume)),
    )
    status_score = RESUME_STATUS_VALUE.get(best.status, 0.0)
    completeness = resume_completeness(best)
    score = _clamp(status_score + completeness * 0.4)
    return score, (
        f"Best version '{best.version_name}' is {best.status.value.replace('_', ' ')} "
        f"with {completeness}% of its sections filled."
    )


def _interview_component(signals: StudentSignals) -> tuple[int, str]:
    target_role = signals.student.target_role
    questions = [
        question
        for question in signals.questions
        if question.target_role is None or (target_role and question.target_role == target_role)
    ]
    if not questions:
        questions = signals.questions

    practiced_ids = {
        practice.question_id
        for practice in signals.practices
        if practice.status in {PracticeStatus.practiced, PracticeStatus.needs_revision}
    }
    covered = len([question for question in questions if question.id in practiced_ids])
    coverage_score = (covered / len(questions) * 100.0) if questions else 0.0

    scored_mocks = [
        interview.score for interview in signals.mock_interviews if interview.completed and interview.score is not None
    ]
    mock_score = sum(scored_mocks) / len(scored_mocks) if scored_mocks else 0.0

    score = _clamp(coverage_score * 0.6 + mock_score * 0.4)
    parts = [f"{covered} of {len(questions)} relevant questions practised"]
    if scored_mocks:
        parts.append(f"average mock interview score {mock_score:.0f}/100 over {len(scored_mocks)} round(s)")
    else:
        parts.append("no completed mock interview recorded yet")
    return score, "; ".join(parts) + "."


COMPONENT_EVALUATORS = {
    "academics": _academics_component,
    "skills": _skills_component,
    "projects": _projects_component,
    "certifications": _certifications_component,
    "resume": _resume_component,
    "interview": _interview_component,
}


def evaluate_components(signals: StudentSignals) -> dict[str, tuple[int, str]]:
    return {key: evaluator(signals) for key, evaluator in COMPONENT_EVALUATORS.items()}


def compute_overall(components: dict[str, tuple[int, str]]) -> int:
    """Weighted sum of the six normalised component scores (weights total 100)."""

    total = sum(score * (READINESS_WEIGHTS[key] / 100) for key, (score, _) in components.items())
    return _clamp(total)


def readiness_level(score: int) -> str:
    if score >= 85:
        return "Placement Ready"
    if score >= 70:
        return "Nearly Ready"
    if score >= 50:
        return "Developing"
    return "Needs Guided Improvement"


def _improvement_suggestions(components: dict[str, tuple[int, str]]) -> list[str]:
    """Order suggestions by how many weighted points are being lost."""

    losses = []
    for key, (score, explanation) in components.items():
        lost = (100 - score) * (READINESS_WEIGHTS[key] / 100)
        losses.append((lost, key, score, explanation))
    losses.sort(reverse=True)

    suggestions: list[str] = []
    actionable = {
        "academics": "Keep your CGPA on record and up to date in your profile.",
        "skills": "Work through the missing target-role skills listed on the Skill Gap page.",
        "projects": "Add two role-relevant projects with repository or demo links.",
        "certifications": "Complete a certification tagged with your target-role skills.",
        "resume": "Create a resume version, complete every section and submit it for mentor review.",
        "interview": "Practise interview questions and record a mock interview round.",
    }
    for _, key, score, _ in losses[:3]:
        if score < 95:
            suggestions.append(f"{COMPONENT_LABELS[key]}: {actionable[key]}")
    if not suggestions:
        suggestions.append("Every component is in good shape. Keep your evidence current and apply to open drives.")
    return suggestions


# --- skill gap ------------------------------------------------------------------


def _learning_resource_for_skill(db: Session, skill_name: str) -> LearningResource | None:
    normalized = normalize_skill(skill_name)
    resources = db.query(LearningResource).order_by(LearningResource.estimated_hours).all()
    for resource in resources:
        if normalize_skill(resource.skill_name) == normalized:
            return resource
    return None


def build_skill_gap(
    db: Session, student: Student, signals: StudentSignals | None = None, *, target_role: str | None = None
) -> SkillGapResponse:
    """Compare the student's skills with the database backed requirements of the target role.

    Pass ``target_role`` to analyse a role different from the student's currently selected one.
    """

    signals = signals or load_signals(db, student, target_role=target_role)
    owned = {normalize_skill(skill.name): skill for skill in signals.skills}
    items: list[SkillGapItem] = []
    covered = 0

    for requirement in signals.requirements:
        match = owned.get(normalize_skill(requirement.skill_name))
        target_rank = PROFICIENCY_RANK.get(requirement.target_proficiency.value, 2)

        if match is None:
            items.append(
                SkillGapItem(
                    skill_name=requirement.skill_name,
                    priority=requirement.priority,
                    target_proficiency=requirement.target_proficiency,
                    current_proficiency=None,
                    status="missing",
                    score=0,
                    action=f"Learn {requirement.skill_name} and add it to your profile skills.",
                )
            )
            continue

        current_rank = PROFICIENCY_RANK.get(match.proficiency.value, 2)
        if current_rank >= target_rank:
            covered += 1
            status = "covered"
            action = f"{requirement.skill_name} already meets the {requirement.target_proficiency.value} requirement."
        else:
            status = "partial"
            action = (
                f"Strengthen {requirement.skill_name} from {match.proficiency.value} "
                f"to {requirement.target_proficiency.value} level."
            )

        items.append(
            SkillGapItem(
                skill_name=requirement.skill_name,
                priority=requirement.priority,
                target_proficiency=requirement.target_proficiency,
                current_proficiency=match.proficiency,
                status=status,
                score=_clamp(PROFICIENCY_VALUE.get(match.proficiency.value, 0.8) * 100),
                action=action,
            )
        )

    required_count = len(signals.requirements)
    skills_score, _ = _skills_component(signals)
    effective_role = target_role or student.target_role
    return SkillGapResponse(
            target_role=effective_role or "Not selected",
            has_role_data=required_count > 0,
            required_skill_count=required_count,
            covered_skill_count=covered,
            missing_skill_count=required_count - covered,
            coverage_percent=_clamp((covered / required_count * 100) if required_count else 0),
            skills_component_score=skills_score,
            items=items,
        )


# --- persistence and public API -------------------------------------------------


def calculate_readiness(db: Session, student: Student, *, persist: bool = True, target_role: str | None = None) -> ReadinessResponse:
    """The only entry point other modules should use to compute the PRS.

    Pass ``target_role`` to compute a one-off score against a role different from the
    student's currently selected one. The returned response still uses the passed role, but
    no persistent snapshot is written for it.
    """

    signals = load_signals(db, student, target_role=target_role)
    components = evaluate_components(signals)
    overall = compute_overall(components)
    computed_at = datetime.now(timezone.utc)

    effective_role = target_role or student.target_role
    student.profile_completion = calculate_profile_completion(student)
    if student.target_role and not student.target_roles:
        student.target_roles = [student.target_role]

    response = ReadinessResponse(
        student_id=student.id,
        overall_score=overall,
        level=readiness_level(overall),
        target_role=effective_role,
        components=[
            ReadinessComponent(
                key=key,
                label=COMPONENT_LABELS[key],
                score=score,
                weight=READINESS_WEIGHTS[key],
                weighted_points=round(score * READINESS_WEIGHTS[key] / 100, 2),
                explanation=explanation,
            )
            for key, (score, explanation) in components.items()
        ],
        suggestions=_improvement_suggestions(components),
        explanation=[explanation for _, (_, explanation) in components.items()],
        disclaimer=DISCLAIMER,
        computed_at=computed_at,
    )

    if persist and target_role is None:
        snapshot = ReadinessSnapshot(
            student_id=student.id,
            overall_score=overall,
            **{key: score for key, (score, _) in components.items()},
            weights=dict(READINESS_WEIGHTS),
            target_role=student.target_role,
            explanation={key: explanation for key, (_, explanation) in components.items()},
            computed_at=computed_at,
        )
        db.add(snapshot)

    return response


def latest_snapshot(db: Session, student_id: int) -> ReadinessSnapshot | None:
    return (
        db.query(ReadinessSnapshot)
        .filter(ReadinessSnapshot.student_id == student_id)
        .order_by(ReadinessSnapshot.computed_at.desc(), ReadinessSnapshot.id.desc())
        .first()
    )


def snapshot_to_dict(snapshot: ReadinessSnapshot) -> dict:
    return {
        "id": snapshot.id,
        "overall_score": snapshot.overall_score,
        "academics": snapshot.academics,
        "skills": snapshot.skills,
        "projects": snapshot.projects,
        "certifications": snapshot.certifications,
        "resume": snapshot.resume,
        "interview": snapshot.interview,
        "target_role": snapshot.target_role,
        "computed_at": snapshot.computed_at.isoformat() if snapshot.computed_at else None,
    }


def build_history(db: Session, student: Student, limit: int = 40) -> list[ReadinessSnapshot]:
    """Oldest first, so charts can plot left to right."""

    snapshots = (
        db.query(ReadinessSnapshot)
        .filter(ReadinessSnapshot.student_id == student.id)
        .order_by(ReadinessSnapshot.computed_at.desc(), ReadinessSnapshot.id.desc())
        .limit(limit)
        .all()
    )
    return list(reversed(snapshots))




