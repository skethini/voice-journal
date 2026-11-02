"""Clean LLM output and spoken transcripts for display."""
from __future__ import annotations

import json
import re

_JSON_FENCE = re.compile(r"^```(?:json)?\s*\n?([\s\S]*?)\n?```\s*$", re.IGNORECASE)
_MD_FENCE = re.compile(r"^```(?:markdown)?\s*\n?([\s\S]*?)\n?```\s*$", re.IGNORECASE)

FILLER = re.compile(
    r"\b(u+h+m*|um+|erm+|like,?\s|you know,?\s|i mean,?\s|sort of|kind of)\b",
    re.IGNORECASE,
)
FILLER_START = re.compile(r"^(uh+|um+|like,?\s)+", re.IGNORECASE)
SPACE = re.compile(r"\s+")


def strip_code_fences(text: str) -> str:
    if not text:
        return ""
    t = text.strip()
    for pat in (_JSON_FENCE, _MD_FENCE):
        m = pat.match(t)
        if m:
            return m.group(1).strip()
    if t.startswith("```"):
        lines = t.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return t


def parse_llm_json(raw: str) -> dict:
    cleaned = strip_code_fences(raw)
    return json.loads(cleaned)


def sanitize_display_text(text: str) -> str:
    """Remove accidental markdown/code fences from text shown in the UI."""
    if not text:
        return ""
    t = strip_code_fences(text)
    t = t.replace("```json", "").replace("```", "")
    return t.strip()


def readable_transcript(raw: str) -> str:
    if not raw or not raw.strip():
        return ""
    text = raw.strip()
    text = FILLER.sub("", text)
    text = FILLER_START.sub("", text)
    text = SPACE.sub(" ", text).strip()
    # Split on natural pauses / run-ons
    parts = re.split(r"(?<=[.!?])\s+|(?<=\w)\s*—\s*|;\s*", text)
    sentences: list[str] = []
    for part in parts:
        s = part.strip()
        if not s:
            continue
        if s and s[0].islower():
            s = s[0].upper() + s[1:]
        if s and s[-1] not in ".!?":
            s += "."
        sentences.append(s)
    if not sentences:
        return text
    return " ".join(sentences)
