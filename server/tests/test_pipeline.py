import os

import pytest

from app.db import get_db
from app.llm import MockLLMClient
from app.pipeline import analyze_entry


@pytest.mark.asyncio
async def test_analyze_entry_writes_markdown(tmp_path, monkeypatch):
    monkeypatch.setenv("EMBED_MOCK", "1")
    with get_db() as conn:
        conn.execute(
            "INSERT INTO entries (created_at, transcript, status) VALUES ('2025-01-01T12:00:00+00:00', 'I want to exercise more.', 'transcribed')"
        )
        entry_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    llm = MockLLMClient()
    await analyze_entry(entry_id, llm=llm)
    md_files = list((tmp_path / "entries").rglob("*.md"))
    assert md_files
    body = md_files[0].read_text().lower()
    assert "exercise" in body or "reflective" in body
