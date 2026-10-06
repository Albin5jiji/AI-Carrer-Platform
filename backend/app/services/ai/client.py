from __future__ import annotations

from abc import ABC, abstractmethod

import httpx

from app.config import settings


class AIProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        raise NotImplementedError


class FakeAIProvider(AIProvider):
    """Simple provider implementation used for tests and local validation."""

    def __init__(self, response: str | None = None):
        self.response = response or '{"strengths": [], "missing_skills": [], "recommendations": [], "explanation": "AI advisory only."}'

    def generate(self, prompt: str) -> str:
        return self.response


class OpenAICompatibleProvider(AIProvider):
    """Minimal openai-compatible chat-completions implementation for the advisory AI endpoint."""

    def __init__(self, api_key: str | None = None, model: str | None = None, base_url: str | None = None):
        self.api_key = api_key or settings.ai_api_key
        self.model = model or settings.ai_model
        self.base_url = (base_url or settings.ai_base_url).rstrip("/")

    def generate(self, prompt: str) -> str:
        if not self.api_key:
            raise RuntimeError("AI API key is not configured")

        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        payload = response.json()
        return payload["choices"][0]["message"]["content"]


def build_ai_provider() -> AIProvider:
    if not settings.ai_enabled or not settings.ai_api_key:
        return FakeAIProvider()
    return OpenAICompatibleProvider()
