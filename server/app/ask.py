from __future__ import annotations

from app.db import get_db
from app.embed import search_entries
from app.text_format import sanitize_display_text
from app.llm import LLMClient, get_llm_client
from app.prompts.shared import ASK_USER, SHARED_SYSTEM


async def answer_question(question: str, llm: LLMClient | None = None) -> dict:
    llm = llm or get_llm_client()
    with get_db() as conn:
        hits = search_entries(conn, question, k=10)
        if not hits:
            return {
                "answer": "I don't have enough in your journal yet to answer that with evidence.",
                "citations": [],
            }
        excerpts = []
        citations = []
        for h in hits:
            entry = conn.execute(
                "SELECT id, created_at, transcript FROM entries WHERE id = ?",
                (h["entry_id"],),
            ).fetchone()
            if not entry:
                continue
            snippet = h.get("text") or entry["transcript"][:200]
            excerpts.append(f"[{entry['created_at']}] entry #{entry['id']}: {snippet}")
            citations.append({"entry_id": entry["id"], "date": entry["created_at"], "quote": snippet})

        threads = conn.execute(
            "SELECT type, label FROM threads ORDER BY last_seen DESC LIMIT 10"
        ).fetchall()
        thread_text = "\n".join(f"- [{r['type']}] {r['label']}" for r in threads) or "(none)"
        guidance_rows = conn.execute("SELECT text FROM guidance WHERE active = 1").fetchall()
        guidance = "\n".join(r["text"] for r in guidance_rows) or "(none)"
        system = SHARED_SYSTEM.format(guidance=guidance, rejected="(none)")
        answer = await llm.complete(
            system,
            [
                {
                    "role": "user",
                    "content": ASK_USER.format(
                        question=question,
                        excerpts="\n".join(excerpts),
                        threads=thread_text,
                    ),
                }
            ],
        )
        if len(citations) < 2 and "not enough" not in answer.lower():
            answer = (
                "There isn't much in your journal that speaks to this directly — "
                "here's what I could find tentatively:\n\n" + answer
            )
        return {"answer": sanitize_display_text(answer), "citations": citations}
