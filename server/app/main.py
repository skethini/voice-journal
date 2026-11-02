from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.ask import answer_question
from app.auth import (
    AuthDep,
    clear_session,
    create_session,
    hash_passcode,
    record_failed_login,
    verify_passcode,
    _check_rate_limit,
    effective_passcode_hash,
)
from app.config import get_settings
from app.db import get_db, init_db
from app.export import build_export_zip, nightly_backup
from app.insights import ensure_daily_prompt, generate_synthesis
from app.pipeline import process_entry_pipeline
from app.text_format import readable_transcript, sanitize_display_text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voice_journal")

app = FastAPI(title="Private Voice Journal", docs_url=None, redoc_url=None)
settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup() -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.audio_dir.mkdir(parents=True, exist_ok=True)
    init_db()
    if settings.public_url and not effective_passcode_hash():
        logger.warning("PUBLIC_URL is set but PASSCODE_HASH is empty — set a passcode before sharing the link")
    scheduler = AsyncIOScheduler(timezone=settings.timezone)
    scheduler.add_job(lambda: asyncio.create_task(ensure_daily_prompt()), "cron", hour=6)
    scheduler.add_job(lambda: asyncio.create_task(generate_synthesis("week")), "cron", day_of_week="sun", hour=7)
    scheduler.add_job(lambda: asyncio.create_task(generate_synthesis("month")), "cron", day=1, hour=7)
    scheduler.add_job(nightly_backup, "cron", hour=3)
    scheduler.start()
    app.state.scheduler = scheduler


class LoginBody(BaseModel):
    passcode: str


@app.post("/auth/login")
async def login(body: LoginBody, request: Request, response: Response) -> dict:
    _check_rate_limit(request)
    cfg = get_settings()
    if effective_passcode_hash() and not verify_passcode(body.passcode, effective_passcode_hash()):
        record_failed_login(request)
        raise HTTPException(status_code=401, detail="Invalid passcode")
    create_session(response)
    return {"ok": True}


class PasscodePatch(BaseModel):
    passcode: str


@app.patch("/settings/passcode")
async def set_passcode(body: PasscodePatch, _: AuthDep) -> dict:
    h = hash_passcode(body.passcode)
    with get_db() as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES ('passcode_hash', ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (h,),
        )
    return {"ok": True}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@app.post("/entries")
async def create_entry(
    _: AuthDep,
    background_tasks: BackgroundTasks,
    audio: UploadFile = File(...),
    duration_s: Optional[float] = Form(None),
) -> dict:
    settings = get_settings()
    ext = Path(audio.filename or "audio.webm").suffix or ".webm"
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO entries (created_at, duration_s, status)
            VALUES (?, ?, 'uploaded')
            """,
            (_utc_now(), duration_s),
        )
        entry_id = cur.lastrowid
    dest = settings.audio_dir / f"{entry_id}{ext}"
    dest.write_bytes(await audio.read())
    with get_db() as conn:
        conn.execute("UPDATE entries SET audio_path = ? WHERE id = ?", (str(dest), entry_id))
    background_tasks.add_task(process_entry_pipeline, entry_id)
    logger.info("entry_id=%s status=uploaded", entry_id)
    return {"id": entry_id}


@app.get("/entries")
async def list_entries(_: AuthDep, query: str = "", limit: int = 30, cursor: Optional[int] = None) -> dict:
    limit = min(max(limit, 1), 100)
    with get_db() as conn:
        if query:
            rows = conn.execute(
                """
                SELECT e.id, e.created_at, e.status, a.summary
                FROM entries_fts
                JOIN entries e ON e.id = entries_fts.rowid
                LEFT JOIN entry_analysis a ON a.entry_id = e.id
                WHERE entries_fts MATCH ?
                ORDER BY e.created_at DESC
                LIMIT ?
                """,
                (query, limit),
            ).fetchall()
        else:
            sql = """
                SELECT e.id, e.created_at, e.status, a.summary
                FROM entries e
                LEFT JOIN entry_analysis a ON a.entry_id = e.id
            """
            params: list = []
            if cursor:
                sql += " WHERE e.id < ?"
                params.append(cursor)
            sql += " ORDER BY e.id DESC LIMIT ?"
            params.append(limit)
            rows = conn.execute(sql, params).fetchall()
    items = [dict(r) for r in rows]
    for item in items:
        if item.get("summary"):
            item["summary"] = sanitize_display_text(item["summary"])
    next_cursor = items[-1]["id"] if len(items) == limit else None
    return {"items": items, "next_cursor": next_cursor}


@app.get("/entries/{entry_id}")
async def get_entry(entry_id: int, _: AuthDep) -> dict:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
        if not row:
            raise HTTPException(404)
        analysis = conn.execute(
            "SELECT summary, json, model, created_at FROM entry_analysis WHERE entry_id = ?",
            (entry_id,),
        ).fetchone()
    out = dict(row)
    raw = out.get("transcript_raw") or ""
    readable = out.get("transcript") or readable_transcript(raw)
    out["transcript_display"] = readable_transcript(readable)
    out["analysis"] = dict(analysis) if analysis else None
    if out["analysis"]:
        if out["analysis"].get("summary"):
            out["analysis"]["summary"] = sanitize_display_text(out["analysis"]["summary"])
        if out["analysis"].get("json"):
            out["analysis"]["parsed"] = json.loads(out["analysis"]["json"])
            if out["analysis"]["parsed"].get("summary"):
                out["analysis"]["parsed"]["summary"] = sanitize_display_text(
                    out["analysis"]["parsed"]["summary"]
                )
    return out


class EntryPatch(BaseModel):
    transcript: str


@app.patch("/entries/{entry_id}")
async def patch_entry(entry_id: int, body: EntryPatch, _: AuthDep, background_tasks: BackgroundTasks) -> dict:
    with get_db() as conn:
        row = conn.execute("SELECT id FROM entries WHERE id = ?", (entry_id,)).fetchone()
        if not row:
            raise HTTPException(404)
        cleaned = readable_transcript(body.transcript)
        conn.execute(
            "UPDATE entries SET transcript = ?, transcript_edited = 1, status = 'transcribed' WHERE id = ?",
            (cleaned, entry_id),
        )
    from app.pipeline import analyze_entry

    background_tasks.add_task(analyze_entry, entry_id)
    return {"ok": True}


@app.delete("/entries/{entry_id}")
async def delete_entry(entry_id: int, _: AuthDep) -> dict:
    with get_db() as conn:
        row = conn.execute("SELECT audio_path FROM entries WHERE id = ?", (entry_id,)).fetchone()
        if not row:
            raise HTTPException(404)
        if row["audio_path"]:
            Path(row["audio_path"]).unlink(missing_ok=True)
        conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
    return {"ok": True}


@app.get("/prompts/today")
async def prompts_today(_: AuthDep) -> dict:
    row = await ensure_daily_prompt()
    if not row:
        raise HTTPException(404)
    row = dict(row)
    row["text"] = sanitize_display_text(row.get("text") or "")
    row["alternates_list"] = [
        sanitize_display_text(a) for a in json.loads(row.get("alternates") or "[]")
    ]
    return row


class PromptFeedback(BaseModel):
    feedback: str


@app.post("/prompts/{prompt_id}/feedback")
async def prompt_feedback(prompt_id: int, body: PromptFeedback, _: AuthDep) -> dict:
    with get_db() as conn:
        conn.execute("UPDATE prompts SET feedback = ? WHERE id = ?", (body.feedback, prompt_id))
    return {"ok": True}


@app.get("/insights")
async def list_insights(_: AuthDep, period: str = "week") -> dict:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM syntheses WHERE period = ? ORDER BY created_at DESC LIMIT 5",
            (period,),
        ).fetchall()
    return {"items": [dict(r) for r in rows]}


class GenerateBody(BaseModel):
    period: str


@app.post("/insights/generate")
async def insights_generate(body: GenerateBody, _: AuthDep) -> dict:
    if body.period not in ("week", "month"):
        raise HTTPException(400, detail="period must be week or month")
    return await generate_synthesis(body.period)


class AskBody(BaseModel):
    question: str


@app.post("/ask")
async def ask(body: AskBody, _: AuthDep) -> dict:
    return await answer_question(body.question)


class GuidanceBody(BaseModel):
    text: str
    active: bool = True
    source_entry_id: Optional[int] = None


@app.get("/guidance")
async def list_guidance(_: AuthDep) -> dict:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM guidance ORDER BY created_at DESC").fetchall()
    return {"items": [dict(r) for r in rows]}


@app.post("/guidance")
async def create_guidance(body: GuidanceBody, _: AuthDep) -> dict:
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO guidance (text, created_at, active, source_entry_id)
            VALUES (?, ?, ?, ?)
            """,
            (body.text, _utc_now(), 1 if body.active else 0, body.source_entry_id),
        )
        gid = cur.lastrowid
    return {"id": gid}


class GuidancePatch(BaseModel):
    text: Optional[str] = None
    active: Optional[bool] = None


@app.patch("/guidance/{guidance_id}")
async def patch_guidance(guidance_id: int, body: GuidancePatch, _: AuthDep) -> dict:
    with get_db() as conn:
        row = conn.execute("SELECT id FROM guidance WHERE id = ?", (guidance_id,)).fetchone()
        if not row:
            raise HTTPException(404)
        if body.text is not None:
            conn.execute("UPDATE guidance SET text = ? WHERE id = ?", (body.text, guidance_id))
        if body.active is not None:
            conn.execute("UPDATE guidance SET active = ? WHERE id = ?", (1 if body.active else 0, guidance_id))
    return {"ok": True}


@app.delete("/guidance/{guidance_id}")
async def delete_guidance(guidance_id: int, _: AuthDep) -> dict:
    with get_db() as conn:
        conn.execute("DELETE FROM guidance WHERE id = ?", (guidance_id,))
    return {"ok": True}


class FeedbackBody(BaseModel):
    target_type: str
    target_id: int
    note: Optional[str] = None


@app.post("/feedback")
async def post_feedback(body: FeedbackBody, _: AuthDep) -> dict:
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO insight_feedback (target_type, target_id, note, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (body.target_type, body.target_id, body.note, _utc_now()),
        )
        return {"id": cur.lastrowid}


@app.get("/export")
async def export_zip(_: AuthDep) -> StreamingResponse:
    data = build_export_zip()
    return StreamingResponse(
        iter([data]),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=journal-export.zip"},
    )


@app.get("/settings")
async def get_settings_route(_: AuthDep) -> dict:
    cfg = get_settings()
    with get_db() as conn:
        rows = conn.execute("SELECT key, value FROM settings").fetchall()
    stored = {r["key"]: r["value"] for r in rows}
    return {
        "keep_audio": cfg.keep_audio,
        "llm_provider": cfg.llm_provider,
        "llm_model": cfg.llm_model,
        "timezone": cfg.timezone,
        "has_passcode": bool(effective_passcode_hash()),
        "backup_configured": bool(cfg.age_recipient),
    }


class SettingsPatch(BaseModel):
    keep_audio: Optional[bool] = None


@app.patch("/settings")
async def patch_settings(body: SettingsPatch, _: AuthDep) -> dict:
    if body.keep_audio is not None:
        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO settings (key, value) VALUES ('keep_audio', ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                ("true" if body.keep_audio else "false",),
            )
    return {"ok": True}


@app.get("/health")
async def health() -> dict:
    return {"ok": True}


def _client_dist_dir() -> Path | None:
    here = Path(__file__).resolve()
    for base in (here.parents[1], here.parents[2]):
        dist = base / "client" / "dist"
        if dist.is_dir():
            return dist
    return None


def _mount_client_spa() -> None:
    """Serve built PWA from client/dist (same origin as API for Tailscale HTTPS)."""
    dist = _client_dist_dir()
    if not dist:
        logger.info("client/dist missing — run: cd client && VITE_API_BASE= npm run build")
        return
    from fastapi.staticfiles import StaticFiles

    app.mount("/", StaticFiles(directory=dist, html=True), name="spa")


_mount_client_spa()
