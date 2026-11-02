import math
import os
import sqlite3
from typing import Any

import httpx

from app.config import get_settings

_model = None
DIM = 384


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    return _model


def chunk_text(text: str, max_chars: int = 500) -> list[str]:
    words = text.split()
    chunks: list[str] = []
    current: list[str] = []
    length = 0
    for w in words:
        if length + len(w) + 1 > max_chars and current:
            chunks.append(" ".join(current))
            current = []
            length = 0
        current.append(w)
        length += len(w) + 1
    if current:
        chunks.append(" ".join(current))
    return chunks or [text] if text else []


def embed_texts(texts: list[str]) -> list[list[float]]:
    if os.environ.get("EMBED_MOCK"):
        return [[0.0] * DIM for _ in texts]
    settings = get_settings()
    if settings.embed_provider == "openai":
        return _embed_openai(texts)
    model = _get_model()
    vectors = model.encode(texts, normalize_embeddings=True)
    return [v.tolist() for v in vectors]


def _embed_openai(texts: list[str]) -> list[list[float]]:
    settings = get_settings()
    if not settings.llm_api_key:
        raise RuntimeError("LLM_API_KEY required for OpenAI embeddings")
    resp = httpx.post(
        "https://api.openai.com/v1/embeddings",
        headers={"Authorization": f"Bearer {settings.llm_api_key}"},
        json={"model": "text-embedding-3-small", "input": texts, "dimensions": DIM},
        timeout=60.0,
    )
    resp.raise_for_status()
    data = sorted(resp.json()["data"], key=lambda x: x["index"])
    return [row["embedding"] for row in data]


def store_entry_embeddings(conn: sqlite3.Connection, entry_id: int, transcript: str) -> None:
    chunks = chunk_text(transcript)
    if not chunks:
        return
    vectors = embed_texts(chunks)
    conn.execute("DELETE FROM entry_embedding_chunks WHERE entry_id = ?", (entry_id,))
    try:
        conn.execute("DELETE FROM entry_embeddings WHERE entry_id = ?", (entry_id,))
    except sqlite3.OperationalError:
        pass
    for idx, (chunk, vec) in enumerate(zip(chunks, vectors)):
        conn.execute(
            "INSERT INTO entry_embedding_chunks (entry_id, chunk_idx, text) VALUES (?, ?, ?)",
            (entry_id, idx, chunk),
        )
        try:
            conn.execute(
                "INSERT INTO entry_embeddings(entry_id, chunk_idx, embedding) VALUES (?, ?, ?)",
                (entry_id, idx, serialize_f32(vec)),
            )
        except sqlite3.OperationalError:
            break


def serialize_f32(vec: list[float]) -> bytes:
    import struct

    return struct.pack(f"{len(vec)}f", *vec)


def search_entries(conn: sqlite3.Connection, query: str, k: int = 8) -> list[dict[str, Any]]:
    qvec = embed_texts([query])[0]
    results: list[dict[str, Any]] = []
    try:
        rows = conn.execute(
            """
            SELECT entry_id, chunk_idx, distance
            FROM entry_embeddings
            WHERE embedding MATCH ?
            ORDER BY distance
            LIMIT ?
            """,
            (serialize_f32(qvec), k),
        ).fetchall()
        for row in rows:
            chunk = conn.execute(
                "SELECT text FROM entry_embedding_chunks WHERE entry_id = ? AND chunk_idx = ?",
                (row["entry_id"], row["chunk_idx"]),
            ).fetchone()
            results.append(
                {
                    "entry_id": row["entry_id"],
                    "chunk_idx": row["chunk_idx"],
                    "text": chunk["text"] if chunk else "",
                    "score": row["distance"],
                }
            )
    except sqlite3.OperationalError:
        pass
    fts = conn.execute(
        """
        SELECT e.id, snippet(entries_fts, 0, '…', '…', '…', 20) AS snippet
        FROM entries_fts
        JOIN entries e ON e.id = entries_fts.rowid
        WHERE entries_fts MATCH ?
        LIMIT ?
        """,
        (query, k),
    ).fetchall()
    for row in fts:
        results.append({"entry_id": row["id"], "text": row["snippet"], "score": 0.0, "source": "fts"})
    seen = set()
    merged: list[dict[str, Any]] = []
    for r in sorted(results, key=lambda x: x.get("score", 0)):
        key = (r["entry_id"], r.get("chunk_idx", -1))
        if key in seen:
            continue
        seen.add(key)
        merged.append(r)
        if len(merged) >= k:
            break
    return merged
