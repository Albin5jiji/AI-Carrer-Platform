from __future__ import annotations

import re

from sqlalchemy.orm import Session

from ...models import RoleSkill, Student
from ...services.eligibility import normalize_skill
from .schemas import AISkillGapAnalysis


class AIValidationError(ValueError):
    """A deterministic validation failure for an advisory AI response."""

    def __init__(self, message: str, *, code: str = "invalid_ai_response"):
        super().__init__(message)
        self.code = code


def _clean(value: str) -> str:
    return " ".join(value.split()).strip()


def _contains_known_phrase(text: str, phrases: set[str]) -> bool:
    normalized_text = normalize_skill(text)
    return any(
        normalize_skill(phrase) in normalized_text or normalized_text in normalize_skill(phrase)
        for phrase in phrases
        if phrase
    )


def _profile_claim_is_hallucinated(claim: str, known_projects: set[str], known_certifications: set[str]) -> bool:
    normalized_claim = normalize_skill(claim)
    profile_markers = (
        "project",
        "certification",
        "certificate",
        "cgpa",
        "grade",
        "gpa",
        "internship",
        "experience",
    )
    if any(marker in normalized_claim for marker in profile_markers):
        return not _contains_known_phrase(normalized_claim, known_projects | known_certifications)
    return False


def _validate_strengths(
    strengths: list[str],
    owned_skills: set[str],
    known_projects: set[str],
    known_certifications: set[str],
) -> list[str]:
    validated: list[str] = []
    for strength in strengths:
        if not isinstance(strength, str):
            raise AIValidationError("Each strength must be a string", code="invalid_strength")
        strength = _clean(strength)
        if not strength or len(strength) > 160:
            raise AIValidationError("Strengths must be non-empty strings under 160 characters", code="invalid_strength")
        normalized = normalize_skill(strength)
        if _profile_claim_is_hallucinated(normalized, known_projects, known_certifications):
            raise AIValidationError(
                f"Strength contains an unsupported student profile claim: {strength}",
                code="hallucinated_profile_fact",
            )
        if not _contains_known_phrase(normalized, owned_skills | known_projects | known_certifications):
            raise AIValidationError(
                f"Strength is not supported by the student profile: {strength}",
                code="unsupported_strength",
            )
        if normalized not in {normalize_skill(item) for item in validated}:
            validated.append(strength)
    return validated


def _validate_missing_skills(
    missing_skills: list[str],
    owned_skills: set[str],
    role_requirements: dict[str, str],
) -> list[str]:
    validated: list[str] = []
    for missing in missing_skills:
        if not isinstance(missing, str):
            raise AIValidationError("Each missing skill must be a string", code="invalid_missing_skill")
        missing = _clean(missing)
        if not missing or len(missing) > 100:
            raise AIValidationError(
                "Missing skills must be non-empty strings under 100 characters",
                code="invalid_missing_skill",
            )
        normalized = normalize_skill(missing)
        if normalized in owned_skills:
            raise AIValidationError(
                f"AI marked an existing student skill as missing: {missing}",
                code="contradictory_skill_gap",
            )
        if role_requirements and normalized not in role_requirements:
            continue
        if not role_requirements:
            raise AIValidationError(
                "Missing skills cannot be validated because the student has no role requirements",
                code="unverifiable_skill_gap",
            )
        validated.append(role_requirements[normalized])
    return list(dict.fromkeys(validated))


def _validate_recommendations(
    recommendations: list[str],
    gap_skills: set[str],
    role_skills: set[str],
) -> list[str]:
    validated: list[str] = []
    for recommendation in recommendations:
        if not isinstance(recommendation, str):
            raise AIValidationError("Each recommendation must be a string", code="invalid_recommendation")
        recommendation = _clean(recommendation)
        if not recommendation or len(recommendation) > 500:
            raise AIValidationError(
                "Recommendations must be non-empty strings under 500 characters",
                code="invalid_recommendation",
            )
        normalized = normalize_skill(recommendation)
        if not _contains_known_phrase(normalized, gap_skills | role_skills):
            raise AIValidationError(
                f"Recommendation is not tied to a target-role skill gap: {recommendation}",
                code="unrelated_recommendation",
            )
        if normalized not in {normalize_skill(item) for item in validated}:
            validated.append(recommendation)
    return validated


def validate_skill_gap_analysis(
    db: Session,
    student: Student,
    analysis: AISkillGapAnalysis,
) -> AISkillGapAnalysis:
    """Validate advisory output against immutable, database-backed student facts."""

    if not isinstance(analysis, AISkillGapAnalysis):
        raise AIValidationError("AI response did not match the required schema", code="invalid_schema")
    if not analysis.explanation.strip() or len(analysis.explanation.strip()) > 2000:
        raise AIValidationError("AI explanation must be non-empty and under 2000 characters", code="invalid_explanation")

    owned_skills = {normalize_skill(skill.name) for skill in (student.skills or []) if skill.name}
    known_projects = {normalize_skill(project.title) for project in (student.projects or []) if project.title}
    known_certifications = {normalize_skill(certification.name) for certification in (student.certifications or []) if certification.name}

    role_rows = (
        db.query(RoleSkill)
        .filter(RoleSkill.role_name == student.target_role.strip() if student.target_role else False)
        .order_by(RoleSkill.display_order)
        .all()
    )
    role_requirements = {
        normalize_skill(row.skill_name): row.skill_name
        for row in role_rows
        if row.skill_name
    }

    strengths = _validate_strengths(
        analysis.strengths,
        owned_skills,
        known_projects,
        known_certifications,
    )
    missing_skills = _validate_missing_skills(analysis.missing_skills, owned_skills, role_requirements)
    recommendations = _validate_recommendations(
        analysis.recommendations,
        set(missing_skills),
        set(role_requirements.values()),
    )

    if re.search(r"\b(?:I|the student)\s+(?:has|completed|earned|built|worked on)\b", analysis.explanation, re.IGNORECASE):
        if _profile_claim_is_hallucinated(analysis.explanation, known_projects, known_certifications):
            raise AIValidationError(
                "Explanation contains an unsupported student profile claim",
                code="hallucinated_profile_fact",
            )

    return analysis.model_copy(
        update={
            "strengths": strengths,
            "missing_skills": missing_skills,
            "recommendations": recommendations,
            "explanation": _clean(analysis.explanation),
        }
    )
