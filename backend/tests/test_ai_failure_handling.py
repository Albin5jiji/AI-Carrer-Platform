from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.api import readiness
from app.models import Priority, ProficiencyLevel
from fastapi import Query
from app.services.ai.service import AIService, AIUnavailableError
from app.services.ai.validation import AIValidationError


VALID_RESPONSE = {
    "strengths": ["Python"],
    "missing_skills": ["FastAPI"],
    "recommendations": ["Practice FastAPI"],
    "explanation": "Python is recorded and FastAPI is the main role gap.",
}


def make_student():
    return SimpleNamespace(
        id=10,
        target_role="Backend Engineer",
        skills=[SimpleNamespace(name="Python", proficiency=ProficiencyLevel.intermediate)],
        projects=[],
        certifications=[],
        resumes=[],
    )


def make_role_skill():
    return SimpleNamespace(
        skill_name="FastAPI",
        display_order=1,
        role_name="Backend Engineer",
        priority=Priority.high,
        target_proficiency=ProficiencyLevel.intermediate,
    )


def make_db(*, previous=None):
    db = MagicMock()
    query = db.query.return_value
    query.filter.return_value.order_by.return_value.all.return_value = [make_role_skill()]
    query.filter.return_value.order_by.return_value.first.return_value = previous
    return db


def configure_service_dependencies(monkeypatch):
    monkeypatch.setattr(
        "app.services.ai.service.load_signals",
        lambda db, student, *, target_role=None: SimpleNamespace(requirements=[make_role_skill()]),
    )
    monkeypatch.setattr(
        "app.services.ai.service.build_skill_gap",
        lambda db, student, signals, *, target_role=None: SimpleNamespace(
            items=[SimpleNamespace(skill_name="FastAPI", status="missing")]
        ),
    )
    monkeypatch.setattr("app.services.ai.service.build_skill_gap_prompt", lambda *args: "prompt")


class FakeProvider:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = 0

    def generate(self, prompt):
        self.calls += 1
        response = next(self.responses)
        if isinstance(response, Exception):
            raise response
        return str(response)


def test_first_ai_attempt_succeeds_and_persists_validated_result(monkeypatch):
    configure_service_dependencies(monkeypatch)
    db = make_db()
    provider = FakeProvider([VALID_RESPONSE])

    result = AIService(provider=provider, retry_delay_seconds=0).generate_skill_gap_analysis(db, make_student())

    assert provider.calls == 1
    assert result.outdated is False
    persisted = db.add.call_args.args[0]
    assert persisted.validation_status == "approved"
    assert persisted.is_outdated is False
    assert persisted.missing_skills == ["FastAPI"]
    db.commit.assert_called_once()


def test_first_attempt_fails_and_retry_succeeds_exactly_once(monkeypatch):
    configure_service_dependencies(monkeypatch)
    db = make_db()
    provider = FakeProvider([RuntimeError("private provider failure"), VALID_RESPONSE])
    delays = []

    result = AIService(
        provider=provider,
        retry_delay_seconds=0.25,
        sleep_fn=delays.append,
    ).generate_skill_gap_analysis(db, make_student())

    assert provider.calls == 2
    assert delays == [0.25]
    assert result.outdated is False


def test_both_attempts_fail_return_previous_approved_result_as_outdated(monkeypatch):
    configure_service_dependencies(monkeypatch)
    previous = SimpleNamespace(
        strengths=["Python"],
        missing_skills=["FastAPI"],
        recommendations=["Practice FastAPI"],
        explanation="Previously approved guidance.",
        is_outdated=False,
    )
    db = make_db(previous=previous)
    provider = FakeProvider([RuntimeError("first"), RuntimeError("second")])

    result = AIService(provider=provider, retry_delay_seconds=0).generate_skill_gap_analysis(db, make_student())

    assert provider.calls == 2
    assert result.outdated is True
    assert previous.is_outdated is True
    db.add.assert_not_called()
    db.commit.assert_called_once()


def test_both_attempts_fail_without_previous_result_raise_clean_unavailable_error(monkeypatch):
    configure_service_dependencies(monkeypatch)
    provider = FakeProvider([RuntimeError("first"), RuntimeError("second")])

    with pytest.raises(AIUnavailableError, match="temporarily unavailable"):
        AIService(provider=provider, retry_delay_seconds=0).generate_skill_gap_analysis(make_db(), make_student())

    assert provider.calls == 2


def test_invalid_validated_response_is_never_persisted(monkeypatch):
    configure_service_dependencies(monkeypatch)
    db = make_db()
    provider = FakeProvider([
        {
            **VALID_RESPONSE,
            "missing_skills": ["Python"],
        }
    ])

    with pytest.raises(AIValidationError):
        AIService(provider=provider, retry_delay_seconds=0).generate_skill_gap_analysis(db, make_student())

    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_provider_error_is_not_exposed_by_api(monkeypatch):
    class FailingService:
        def __init__(self, provider):
            pass

        def generate_skill_gap_analysis(self, db, student):
            raise AIUnavailableError("provider secret should not be exposed")

    monkeypatch.setattr(readiness, "AIService", FailingService)

    with pytest.raises(Exception) as error:
        readiness.my_ai_skill_gap(make_student(), MagicMock())

    assert error.value.status_code == 503
    assert error.value.detail["message"] == "AI recommendations are temporarily unavailable"
    assert "provider secret" not in str(error.value.detail).lower()
