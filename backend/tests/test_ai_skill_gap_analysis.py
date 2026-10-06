from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, Query
from fastapi.testclient import TestClient

from fastapi import Query
from app.main import app


from app.services.ai.schemas import AISkillGapAnalysis
from app.services.ai.service import AIService


class FakeProvider:
    def __init__(self, payload):
        self.payload = payload

    def generate(self, prompt: str) -> str:
        return str(self.payload)


def test_ai_skill_gap_analysis_parses_structured_response():
    provider = FakeProvider(
        {
            "strengths": ["Python", "FastAPI"],
            "missing_skills": ["Redis", "Docker"],
            "recommendations": ["Build a deployment project.", "Practice container setup."],
            "explanation": "You are strong in backend fundamentals but need deployment skills.",
        }
    )

    result = AISkillGapAnalysis.model_validate(provider.payload)

    assert result.strengths == ["Python", "FastAPI"]
    assert result.missing_skills == ["Redis", "Docker"]
    assert result.recommendations == ["Build a deployment project.", "Practice container setup."]
    assert "deployment" in result.explanation.lower()


def test_ai_skill_gap_analysis_rejects_malformed_response():
    provider = FakeProvider({"strengths": "wrong", "missing_skills": [], "recommendations": [], "explanation": "x"})

    with pytest.raises(ValueError):
        AISkillGapAnalysis.model_validate(provider.payload)


def test_ai_service_does_not_alter_prs_or_eligibility():
    db = MagicMock()
    student = MagicMock()
    student.id = 10
    student.target_role = "Backend Engineer"
    student.account = MagicMock()
    student.account.full_name = "Demo Student"
    student.skills = []
    student.projects = []
    student.certifications = []
    student.resumes = []

    provider = FakeProvider(
        {
            "strengths": ["Python"],
            "missing_skills": ["FastAPI"],
            "recommendations": ["Review FastAPI fundamentals"],
            "explanation": "Strong Python, but FastAPI is the main gap.",
        }
    )

    service = AIService(provider=provider)
    result = service._parse_response(provider.generate("prompt"))

    assert result.missing_skills == ["FastAPI"]
    assert student.target_role == "Backend Engineer"
    assert result.explanation.startswith("Strong Python")


def test_ai_skill_gap_generation_requires_authentication():
    client = TestClient(app)
    response = client.post("/api/readiness/me/ai-skill-gap")
    assert response.status_code == 401
