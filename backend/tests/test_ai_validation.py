from unittest.mock import MagicMock
from types import SimpleNamespace

import pytest

from app.models import Priority, ProficiencyLevel
from app.services.ai.schemas import AISkillGapAnalysis
from app.services.ai.service import AIService
from app.services.ai.validation import AIValidationError, validate_skill_gap_analysis


def make_student(*, skills=None, projects=None, certifications=None, target_role="Backend Engineer"):
    student = SimpleNamespace()
    student.id = 10
    student.target_role = target_role
    student.skills = skills or []
    student.projects = projects or []
    student.certifications = certifications or []
    student.resumes = []
    return student


def make_role_skill(name):
    row = SimpleNamespace()
    row.skill_name = name
    row.display_order = 1
    row.role_name = "Backend Engineer"
    row.priority = Priority.high
    row.target_proficiency = ProficiencyLevel.intermediate
    return row


def make_db(*role_skills):
    db = MagicMock()
    query = db.query.return_value
    query.filter.return_value.order_by.return_value.all.return_value = list(role_skills)
    return db


def analysis(**updates):
    payload = {
        "strengths": ["Python"],
        "missing_skills": ["FastAPI"],
        "recommendations": ["Practice FastAPI", "Practice FastAPI"],
        "explanation": "Python is recorded and FastAPI is the main role gap.",
    }
    payload.update(updates)
    return AISkillGapAnalysis.model_validate(payload)


def test_valid_ai_response_passes_validation_and_deduplicates_recommendations():
    student = make_student(skills=[SimpleNamespace(name="Python", proficiency=ProficiencyLevel.intermediate)])
    result = validate_skill_gap_analysis(make_db(make_role_skill("FastAPI")), student, analysis())

    assert result.missing_skills == ["FastAPI"]
    assert result.recommendations == ["Practice FastAPI"]


def test_malformed_response_is_rejected():
    with pytest.raises(ValueError):
        AISkillGapAnalysis.model_validate({"strengths": "Python"})


def test_existing_student_skill_cannot_be_missing():
    student = make_student(skills=[SimpleNamespace(name="Python", proficiency=ProficiencyLevel.intermediate)])
    response = analysis(missing_skills=["Python"])

    with pytest.raises(AIValidationError, match="existing student skill"):
        validate_skill_gap_analysis(make_db(make_role_skill("Python")), student, response)


def test_hallucinated_student_fact_is_rejected():
    student = make_student(skills=[SimpleNamespace(name="Python", proficiency=ProficiencyLevel.intermediate)])
    response = analysis(strengths=["Built the NASA Project"])

    with pytest.raises(AIValidationError, match="unsupported student profile claim"):
        validate_skill_gap_analysis(make_db(make_role_skill("FastAPI")), student, response)


def test_irrelevant_missing_skill_is_removed():
    student = make_student(skills=[SimpleNamespace(name="Python", proficiency=ProficiencyLevel.intermediate)])
    response = analysis(missing_skills=["FastAPI", "Kubernetes"])

    result = validate_skill_gap_analysis(make_db(make_role_skill("FastAPI")), student, response)

    assert result.missing_skills == ["FastAPI"]


def test_service_validation_does_not_modify_profile_or_readiness_data():
    student = make_student(skills=[SimpleNamespace(name="Python", proficiency=ProficiencyLevel.intermediate)])
    student.profile_completion = 55
    student.target_role = "Backend Engineer"
    student.applications = [MagicMock(status="submitted")]
    db = make_db(make_role_skill("FastAPI"))
    provider = MagicMock()
    provider.generate.return_value = str(
        {
            "strengths": ["Python"],
            "missing_skills": ["FastAPI"],
            "recommendations": ["Practice FastAPI"],
            "explanation": "Python is recorded and FastAPI is the main role gap.",
        }
    )

    result = AIService(provider=provider).generate_skill_gap_analysis(db, student)

    assert result.missing_skills == ["FastAPI"]
    assert student.target_role == "Backend Engineer"
    assert student.profile_completion == 55
    assert student.applications[0].status == "submitted"
    db.commit.assert_called_once()
    persisted = db.add.call_args.args[0]
    assert persisted.validation_status == "approved"
    assert persisted.is_outdated is False
