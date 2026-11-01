from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

import httpx

from app.config import get_settings


class LLMClient(ABC):
    @abstractmethod
    async def complete(
        self,
        system: str,
        messages: list[dict[str, str]],
        json_schema: dict[str, Any] | None = None,
    ) -> str:
        ...


class OpenAICompatibleClient(LLMClient):
    def __init__(self, api_key: str, model: str, base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    async def complete(
        self,
        system: str,
        messages: list[dict[str, str]],
        json_schema: dict[str, Any] | None = None,
    ) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, *messages],
        }
        if json_schema:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "response", "schema": json_schema, "strict": True},
            }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        content = data["choices"][0]["message"]["content"]
        if json_schema and isinstance(content, str):
            json.loads(content)
        return content


class MockLLMClient(LLMClient):
    """Deterministic responses for tests."""

    def __init__(self, responses: list[str] | None = None):
        self.responses = list(responses or [])
        self.calls: list[tuple[str, list[dict[str, str]]]] = []

    async def complete(
        self,
        system: str,
        messages: list[dict[str, str]],
        json_schema: dict[str, Any] | None = None,
    ) -> str:
        self.calls.append((system, messages))
        if self.responses:
            return self.responses.pop(0)
        if json_schema:
            return json.dumps(
                {
                    "summary": "A reflective day.",
                    "themes": ["growth"],
                    "goals": [],
                    "frustrations": [],
                    "intentions": [],
                    "open_questions": ["What would help next?"],
                    "proposed_guidance": [],
                }
            )
        return "I notice you mentioned growth — does that still feel central?"


def get_llm_client() -> LLMClient:
    settings = get_settings()
    if settings.llm_provider == "mock":
        return MockLLMClient()
    if not settings.llm_model:
        raise RuntimeError("LLM_MODEL must be set")
    if not settings.llm_api_key:
        raise RuntimeError("LLM_API_KEY must be set")
    base_urls = {
        "openai": "https://api.openai.com/v1",
        "openrouter": "https://openrouter.ai/api/v1",
    }
    base = base_urls.get(settings.llm_provider, f"https://api.openai.com/v1")
    return OpenAICompatibleClient(settings.llm_api_key, settings.llm_model, base)
