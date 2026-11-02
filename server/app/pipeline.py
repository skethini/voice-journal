from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from app.config import get_settings
from app.db import get_db
from app.embed import store_entry_embeddings
from app.export import export_entry_markdown
from app.insights import update_threads_from_analysis
from app.llm import LLMClient, get_llm_client
from app.prompts.entry_analysis import ENTRY_ANALYSIS_SCHEMA
from app.prompts.shared import ENTRY_USER, SHARED_SYSTEM
from app.redact import redact_text
from app.text_format import sanitize_display_text
from app.transcribe import transcribe_uploaded_audio

logger = logging.getLogger("voice_journal.pipeline")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _context_blocks(conn) -> tuple[str, str]:
    guidance_rows = conn.execute(
        "SELECT text FROM guidance WHERE active = 1 ORDER BY created_at DESC"
    ).fetchall()
    guidance = "\n".join(r["text"] for r in guidance_rows) or "(none)"
    rejected_rows = conn.execute(
        """
        SELECT note FROM insight_feedback
        WHERE note IS NOT NULL AND note != ''
        ORDER BY created_at DESC LIMIT 10
        """
    ).fetchall()
    rejected = "\n".join(r["note"] for r in rejected_rows) or "(none)"
    return guidance, rejected


def set_entry_status(entry_id: int, status: str) -> None:
    with get_db() as conn:
        conn.execute("UPDATE entries SET status = ? WHERE id = ?", (status, entry_id))


async def analyze_entry(entry_id: int, llm: LLMClient | None = None) -> None:
    llm = llm or get_llm_client()
    settings = get_settings()
    with get_db() as conn:
        row = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
        if not row or not row["transcript"]:
            return
        guidance, rejected = _context_blocks(conn)
        system = SHARED_SYSTEM.format(guidance=guidance, rejected=rejected)
        transcript = redact_text(row["transcript"])
        user_msg = ENTRY_USER.format(date=row["created_at"], transcript=transcript)
        response = await llm.complete(
            system,
            [{"role": "user", "content": user_msg}],
            json_schema=ENTRY_ANALYSIS_SCHEMA,
        )
        data = json.loads(response)
        if data.get("summary"):
            data["summary"] = sanitize_display_text(data["summary"])
            response = json.dumps(data)
        conn.execute(
            """
            INSERT INTO entry_analysis (entry_id, summary, json, model, created_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(entry_id) DO UPDATE SET
                summary = excluded.summary,
                json = excluded.json,
                model = excluded.model,
                created_at = excluded.created_at
            """,
            (entry_id, data.get("summary"), response, settings.llm_model or "mock", _utc_now()),
        )
        conn.execute("UPDATE entries SET status = 'analyzed' WHERE id = ?", (entry_id,))
        store_entry_embeddings(conn, entry_id, row["transcript"])
        await update_threads_from_analysis(conn, entry_id, row["created_at"], data, llm)

    export_entry_markdown(entry_id)


async def process_entry_pipeline(entry_id: int, llm: LLMClient | None = None) -> None:
    """Transcribe (if needed) → embed → analyze → export."""
    settings = get_settings()
    llm = llm or get_llm_client()
    with get_db() as conn:
        row = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
        if not row:
            return
        audio_path = row["audio_path"]

    try:
        if audio_path and Path(audio_path).is_file():
            raw, cleaned = await transcribe_uploaded_audio(Path(audio_path))
            with get_db() as conn:
                conn.execute(
                    """
                    UPDATE entries SET transcript = ?, transcript_raw = ?, status = 'transcribed' WHERE id = ?
                    """,
                    (cleaned, raw, entry_id),
                )
                if not settings.keep_audio:
                    Path(audio_path).unlink(missing_ok=True)
                    conn.execute("UPDATE entries SET audio_path = NULL WHERE id = ?", (entry_id,))
        elif row["transcript"]:
            with get_db() as conn:
                conn.execute("UPDATE entries SET status = 'transcribed' WHERE id = ?", (entry_id,))

        await analyze_entry(entry_id, llm=llm)
    except Exception:
        logger.exception("entry_id=%s status=error", entry_id)
        set_entry_status(entry_id, "error")
        raise
