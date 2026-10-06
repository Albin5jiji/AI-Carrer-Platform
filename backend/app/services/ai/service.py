from __future__ import annotations

import ast
import json
import time
from collections.abc import Callable

from sqlalchemy.orm import Session

from ...models import AISkillGapResult, Student
from ...services.readiness import build_skill_gap, load_signals
from .client import AIProvider
from .prompts import build_skill_gap_prompt
from .schemas import AISkillGapAnalysis
from .validation import AIValidationError, validate_skill_gap_analysis


class AIUnavailableError(RuntimeError):
    """Raised when no fresh or previously approved AI result is available."""


class AIService:
    def __init__(
        self,
        provider: AIProvider | None = None,
        *,
        retry_delay_seconds: float = 0.1,
        sleep_fn: Callable[[float], None] = time.sleep,
    ):
        self.provider = provider
        self.retry_delay_seconds = retry_delay_seconds
        self.sleep_fn = sleep_fn

    def _parse_response(self, raw_response: str) -> AISkillGapAnalysis:
        if isinstance(raw_response, dict):
            payload = raw_response
        elif isinstance(raw_response, str):
            text = raw_response.strip()
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                try:
                    payload = ast.literal_eval(text)
                except (ValueError, SyntaxError) as exc:
                    raise AIValidationError(
                        "AI response was not valid JSON",
                        code="invalid_schema",
                    ) from exc
        else:
            raise AIValidationError("AI response was not valid JSON", code="invalid_schema")

        try:
            return AISkillGapAnalysis.from_raw(payload)
        except ValueError as exc:
            raise AIValidationError(
                "AI response did not match the required schema",
                code="invalid_schema",
            ) from exc

    def _persist_validated_result(
        self,
        db: Session,
        student: Student,
        analysis: AISkillGapAnalysis,
        *,
        target_role: str | None = None,
    ) -> AISkillGapAnalysis:
        effective_role = target_role or student.target_role
        result = AISkillGapResult(
            student_id=student.id,
            target_role=effective_role,
            strengths=list(analysis.strengths),
            missing_skills=list(analysis.missing_skills),
            recommendations=list(analysis.recommendations),
            explanation=analysis.explanation,
            validation_status="approved",
            is_outdated=False,
        )
        db.add(result)
        db.commit()
        return analysis.model_copy(update={"outdated": False})

    def _fallback_to_previous_result(self, db: Session, student: Student) -> AISkillGapAnalysis:
        result = (
            db.query(AISkillGapResult)
            .filter(
                AISkillGapResult.student_id == student.id,
                AISkillGapResult.target_role == student.target_role,
                AISkillGapResult.validation_status == "approved",
            )
            .order_by(AISkillGapResult.created_at.desc())
            .first()
        )
        if result is None:
            raise AIUnavailableError("AI recommendations are temporarily unavailable")

        result.is_outdated = True
        db.commit()
        return AISkillGapAnalysis(
            strengths=list(result.strengths or []),
            missing_skills=list(result.missing_skills or []),
            recommendations=list(result.recommendations or []),
            explanation=result.explanation,
            outdated=True,
        )

    def generate_skill_gap_analysis(
        self, db: Session, student: Student, *, target_role: str | None = None
    ) -> AISkillGapAnalysis:
        if self.provider is None:
            raise RuntimeError("AI provider is not configured")

        signals = load_signals(db, student, target_role=target_role)
        gap = build_skill_gap(db, student, signals, target_role=target_role)

        effective_role = target_role or student.target_role
        role_requirements = [item.skill_name for item in gap.items]
        gap_context = {
            "strengths": [item.skill_name for item in gap.items if item.status == "covered"][:5],
            "missing_skills": [item.skill_name for item in gap.items if item.status != "covered"][:10],
        }

        prompt = build_skill_gap_prompt(student, gap_context, role_requirements)
        for attempt in range(2):
            try:
                raw = self.provider.generate(prompt)
            except Exception:
                if attempt == 0:
                    if self.retry_delay_seconds > 0:
                        self.sleep_fn(self.retry_delay_seconds)
                    continue
                return self._fallback_to_previous_result(db, student)

            parsed = self._parse_response(raw)
            validated = validate_skill_gap_analysis(db, student, parsed)
            return self._persist_validated_result(db, student, validated, target_role=target_role)

        return self._fallback_to_previous_result(db, student)
