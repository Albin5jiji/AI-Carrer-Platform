"""Single source of truth for placement eligibility.

Both the student-facing "check my eligibility" endpoint and the application creation
flow call these functions, so a student can never be blocked by one screen and allowed
by another.
"""

from dataclasses import dataclass, field
from datetime import date

from ..models import PlacementDrive, Skill, Student

# Common aliases so "ReactJS" and "React" are treated as the same requirement.
SKILL_ALIASES: dict[str, str] = {
    "reactjs": "react",
    "react.js": "react",
    "react js": "react",
    "node": "node.js",
    "nodejs": "node.js",
    "postgres": "postgresql",
    "psql": "postgresql",
    "js": "javascript",
    "ts": "typescript",
    "ml": "machine learning",
    "dl": "deep learning",
    "dsa": "data structures and algorithms",
    "data structures & algorithms": "data structures and algorithms",
    "rest": "rest api",
    "restful api": "rest api",
    "golang": "go",
    "k8s": "kubernetes",
    "powerbi": "power bi",
    "aws cloud": "aws",
}

PROFICIENCY_RANK = {"beginner": 1, "intermediate": 2, "advanced": 3}


def normalize_skill(name: str) -> str:
    cleaned = " ".join(name.strip().lower().replace("_", " ").split())
    return SKILL_ALIASES.get(cleaned, cleaned)


def skill_matches(required: str, possessed: str) -> bool:
    return normalize_skill(required) == normalize_skill(possessed)


def matched_skill_names(required: list[str], possessed: list[str]) -> tuple[list[str], list[str]]:
    """Split required skills into (matched, missing) using alias aware comparison."""

    normalized_possessed = {normalize_skill(name) for name in possessed}
    matched: list[str] = []
    missing: list[str] = []
    for skill in required:
        if normalize_skill(skill) in normalized_possessed:
            matched.append(skill)
        else:
            missing.append(skill)
    return matched, missing


@dataclass
class EligibilityResult:
    eligible: bool
    reasons: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    matched_skills: list[str] = field(default_factory=list)
    cgpa_ok: bool = True
    department_ok: bool = True
    graduation_year_ok: bool = True
    deadline_open: bool = True

    @property
    def status(self) -> str:
        return "eligible" if self.eligible else "not_eligible"


def check_eligibility(
    *,
    cgpa: float | None,
    department: str | None,
    graduation_year: int | None,
    student_skills: list[str],
    min_cgpa: float | None = None,
    eligible_departments: list[str] | None = None,
    graduation_years: list[int] | None = None,
    required_skills: list[str] | None = None,
    deadline: date | None = None,
) -> EligibilityResult:
    """Evaluate one student against one set of criteria.

    A missing value on the criteria side means "no restriction". A missing value on the
    student side is reported as an explicit, readable reason instead of a silent failure.
    """

    result = EligibilityResult(eligible=True)
    today = date.today()

    if min_cgpa is not None:
        if cgpa is None:
            result.cgpa_ok = False
            result.reasons.append(f"CGPA is not recorded in your profile (requirement: minimum {min_cgpa:.2f})")
        elif cgpa < min_cgpa:
            result.cgpa_ok = False
            result.reasons.append(f"CGPA {cgpa:.2f} is below the required minimum {min_cgpa:.2f}")

    if eligible_departments:
        allowed = {item.strip().lower() for item in eligible_departments}
        if not department:
            result.department_ok = False
            result.reasons.append("Department is not recorded in your profile")
        elif department.strip().lower() not in allowed:
            result.department_ok = False
            result.reasons.append(
                f"Department '{department}' is not in the eligible list: {', '.join(eligible_departments)}"
            )

    if graduation_years:
        if graduation_year is None:
            result.graduation_year_ok = False
            result.reasons.append("Graduation year is not recorded in your profile")
        elif graduation_year not in graduation_years:
            result.graduation_year_ok = False
            years = ", ".join(str(year) for year in sorted(graduation_years))
            result.reasons.append(f"Graduation year {graduation_year} is not in the eligible years: {years}")

    if required_skills:
        matched, missing = matched_skill_names(required_skills, student_skills)
        result.matched_skills = matched
        result.missing_skills = missing
        if missing:
            result.reasons.append(f"Missing required skills: {', '.join(missing)}")

    if deadline is not None and deadline < today:
        result.deadline_open = False
        result.reasons.append(f"The application deadline ({deadline.isoformat()}) has passed")

    result.eligible = (
        result.cgpa_ok and result.department_ok and result.graduation_year_ok and result.deadline_open
    )
    return result


def check_drive_eligibility(
    drive: PlacementDrive,
    *,
    student: Student,
    skills: list[Skill],
    has_approved_resume: bool = False,
    already_applied: bool = False,
) -> EligibilityResult:
    """Bind a stored drive to a stored student and explain every failure reason."""

    result = check_eligibility(
        cgpa=student.cgpa,
        department=student.department,
        graduation_year=student.graduation_year,
        student_skills=[skill.name for skill in skills],
        min_cgpa=drive.min_cgpa,
        eligible_departments=drive.eligible_departments,
        graduation_years=drive.graduation_years,
        required_skills=drive.required_skills,
        deadline=drive.application_deadline,
    )

    if already_applied:
        result.reasons.append("You have already applied to this drive")
    if not has_approved_resume:
        result.reasons.append(
            "You do not have an approved resume version yet; submit one for mentor review first"
        )
    return result


def evaluate_drive_for_student(db, drive: PlacementDrive, student: Student) -> EligibilityResult:
    """Database backed convenience wrapper used by the drive and application routers."""

    from ..models import Application
    from .lifecycle import has_approved_resume

    already_applied = (
        db.query(Application)
        .filter(Application.student_id == student.id, Application.drive_id == drive.id)
        .count()
        > 0
    )
    return check_drive_eligibility(
        drive,
        student=student,
        skills=list(student.skills),
        has_approved_resume=has_approved_resume(db, student.id),
        already_applied=already_applied,
    )

