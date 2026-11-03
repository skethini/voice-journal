"""Extract journal text from photos (OpenAI vision)."""
from __future__ import annotations

import base64
import httpx

from app.config import get_settings
from app.text_format import readable_transcript

OCR_PROMPT = """You transcribe photos of handwritten or typed journal pages.
Return ONLY the journal text, in reading order. Preserve the writer's words and meaning.
Do not summarize, add commentary, or wrap in markdown/code fences."""


async def extract_text_from_image(data: bytes, content_type: str) -> tuple[str, str]:
    settings = get_settings()
    if settings.llm_provider == "mock":
        raw = "Mock scan: Today I felt overwhelmed about work but noticed I want more quiet mornings."
        return raw, readable_transcript(raw)

    if not settings.llm_api_key:
        raise RuntimeError("LLM_API_KEY required for journal photo OCR")

    mime = content_type if content_type.startswith("image/") else "image/jpeg"
    b64 = base64.standard_b64encode(data).decode("ascii")
    model = settings.llm_model or "gpt-4o-mini"
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": OCR_PROMPT},
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                ],
            }
        ],
        "max_tokens": 4096,
    }
    async with httpx.AsyncClient(timeout=180.0) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.llm_api_key}"},
            json=payload,
        )
        resp.raise_for_status()
    raw = resp.json()["choices"][0]["message"]["content"].strip()
    return raw, readable_transcript(raw)
