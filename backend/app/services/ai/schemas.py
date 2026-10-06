from __future__ import annotations

from pydantic import BaseModel, Field


class AISkillGapAnalysis(BaseModel):
    strengths: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    explanation: str = Field(min_length=1, max_length=2000)
    outdated: bool = False

    @classmethod
    def from_raw(cls, raw: object) -> "AISkillGapAnalysis":
        if not isinstance(raw, dict):
            raise ValueError("AI response must be a JSON object")
        return cls.model_validate(raw)
