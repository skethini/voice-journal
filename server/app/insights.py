from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from app.db import get_db
from app.embed import embed_texts
from app.llm import LLMClient, get_llm_client
from app.prompts.daily_prompt import DAILY_PROMPT_SCHEMA
from app.prompts.shared import DAILY_PROMPT_USER, SHARED_SYSTEM, SYNTHESIS_USER, THREAD_MATCH_USER
from app.text_format import parse_llm_json, sanitize_display_text


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


async def update_threads_from_analysis(conn, entry_id: int, entry_date: str, data: dict, llm: LLMClient) -> None:
    items: list[tuple[str, str, str]] = []
    for theme in data.get("themes", []):
        items.append(("theme", theme, theme))
    for key in ("goals", "frustrations", "intentions"):
        for item in data.get(key, []):
            items.append((key[:-1] if key.endswith("s") else key, item.get("text", ""), item.get("quote", "")))

    for typ, text, quote in items:
        if not text:
            continue
        candidates = _thread_candidates(conn, text)
        cand_text = "\n".join(f"- id={c['id']} [{c['type']}] {c['label']}" for c in candidates) or "(none)"
        resp = await llm.complete(
            SHARED_SYSTEM.format(guidance="(internal)", rejected="(none)"),
            [
                {
                    "role": "user",
                    "content": THREAD_MATCH_USER.format(
                        type=typ, text=text, quote=quote, candidates=cand_text
                    ),
                }
            ],
        )
        try:
            decision = parse_llm_json(resp)
        except (json.JSONDecodeError, ValueError):
            decision = {"action": "new", "label": text}

        if decision.get("action") == "match" and decision.get("thread_id"):
            thread_id = int(decision["thread_id"])
            conn.execute(
                "UPDATE threads SET last_seen = ? WHERE id = ?",
                (entry_date, thread_id),
            )
        else:
            cur = conn.execute(
                "INSERT INTO threads (type, label, first_seen, last_seen) VALUES (?, ?, ?, ?)",
                (typ, decision.get("label") or text, entry_date, entry_date),
            )
            thread_id = cur.lastrowid
        conn.execute(
            "INSERT OR REPLACE INTO thread_entries (thread_id, entry_id, quote) VALUES (?, ?, ?)",
            (thread_id, entry_id, quote or text),
        )


def _thread_candidates(conn, text: str, k: int = 5) -> list[dict]:
    rows = conn.execute("SELECT id, type, label FROM threads ORDER BY last_seen DESC LIMIT 50").fetchall()
    if not rows:
        return []
    labels = [r["label"] for r in rows]
    qvec = embed_texts([text])[0]
    lvecs = embed_texts(labels)
    scored = []
    for row, vec in zip(rows, lvecs):
        dist = sum((a - b) ** 2 for a, b in zip(qvec, vec))
        scored.append((dist, dict(row)))
    scored.sort(key=lambda x: x[0])
    return [s[1] for s in scored[:k]]


async def ensure_daily_prompt(llm: LLMClient | None = None) -> dict | None:
    llm = llm or get_llm_client()
    today = datetime.now(timezone.utc).date().isoformat()
    with get_db() as conn:
        existing = conn.execute("SELECT * FROM prompts WHERE date = ?", (today,)).fetchone()
        if existing:
            return dict(existing)

        summaries = conn.execute(
            """
            SELECT e.created_at, a.summary FROM entries e
            JOIN entry_analysis a ON a.entry_id = e.id
            WHERE e.created_at >= datetime('now', '-7 days')
            ORDER BY e.created_at DESC
            """
        ).fetchall()
        summary_text = "\n".join(f"- {r['created_at']}: {r['summary']}" for r in summaries) or "(none)"
        threads = conn.execute(
            "SELECT type, label, last_seen FROM threads ORDER BY last_seen DESC LIMIT 15"
        ).fetchall()
        thread_text = "\n".join(f"- [{r['type']}] {r['label']} (last {r['last_seen']})" for r in threads) or "(none)"
        recent = conn.execute("SELECT text FROM prompts ORDER BY date DESC LIMIT 5").fetchall()
        recent_text = "\n".join(r["text"] for r in recent) or "(none)"
        guidance_rows = conn.execute("SELECT text FROM guidance WHERE active = 1").fetchall()
        guidance = "\n".join(r["text"] for r in guidance_rows) or "(none)"

        system = SHARED_SYSTEM.format(guidance=guidance, rejected="(none)")
        resp = await llm.complete(
            system,
            [
                {
                    "role": "user",
                    "content": DAILY_PROMPT_USER.format(
                        date=today,
                        summaries=summary_text,
                        threads=thread_text,
                        recent_prompts=recent_text,
                    ),
                }
            ],
            json_schema=DAILY_PROMPT_SCHEMA,
        )
        try:
            payload = parse_llm_json(resp)
            text = sanitize_display_text(payload.get("text") or "")
            alts = [sanitize_display_text(a) for a in payload.get("alternates", []) if a]
            alternates = json.dumps(alts)
        except (json.JSONDecodeError, ValueError):
            text = sanitize_display_text(resp)
            alternates = "[]"

        conn.execute(
            "INSERT INTO prompts (date, text, alternates) VALUES (?, ?, ?)",
            (today, text, alternates),
        )
        row = conn.execute("SELECT * FROM prompts WHERE date = ?", (today,)).fetchone()
        return dict(row) if row else None


async def generate_synthesis(period: str, llm: LLMClient | None = None) -> dict:
    llm = llm or get_llm_client()
    now = datetime.now(timezone.utc)
    if period == "week":
        start = (now - timedelta(days=7)).date().isoformat()
        end = now.date().isoformat()
    else:
        start = (now.replace(day=1) - timedelta(days=1)).replace(day=1).date().isoformat()
        end = now.date().isoformat()

    with get_db() as conn:
        summaries = conn.execute(
            """
            SELECT e.created_at, a.summary FROM entries e
            JOIN entry_analysis a ON a.entry_id = e.id
            WHERE date(e.created_at) BETWEEN date(?) AND date(?)
            ORDER BY e.created_at
            """,
            (start, end),
        ).fetchall()
        summary_text = "\n".join(f"- {r['created_at']}: {r['summary']}" for r in summaries) or "(none)"
        threads = conn.execute("SELECT type, label, first_seen, last_seen FROM threads").fetchall()
        thread_text = "\n".join(
            f"- [{r['type']}] {r['label']} ({r['first_seen']} → {r['last_seen']})" for r in threads
        ) or "(none)"
        guidance_rows = conn.execute("SELECT text FROM guidance WHERE active = 1").fetchall()
        guidance = "\n".join(r["text"] for r in guidance_rows) or "(none)"
        system = SHARED_SYSTEM.format(guidance=guidance, rejected="(none)")
        markdown = sanitize_display_text(
            await llm.complete(
                system,
                [
                    {
                        "role": "user",
                        "content": SYNTHESIS_USER.format(
                            period=period,
                            start=start,
                            end=end,
                            summaries=summary_text,
                            threads=thread_text,
                        ),
                    }
                ],
            )
        )
        cur = conn.execute(
            """
            INSERT INTO syntheses (period, start, end, markdown, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (period, start, end, markdown, _utc_now()),
        )
        return {
            "id": cur.lastrowid,
            "period": period,
            "start": start,
            "end": end,
            "markdown": markdown,
        }
