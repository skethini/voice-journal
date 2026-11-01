from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from app.config import get_settings

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    duration_s REAL,
    audio_path TEXT,
    transcript TEXT,
    transcript_edited INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'uploaded'
);

CREATE TABLE IF NOT EXISTS entry_analysis (
    entry_id INTEGER PRIMARY KEY REFERENCES entries(id) ON DELETE CASCADE,
    summary TEXT,
    json TEXT,
    model TEXT,
    created_at TEXT
);

CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts USING fts5(
    transcript,
    content='entries',
    content_rowid='id'
);

CREATE TABLE IF NOT EXISTS threads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    label TEXT NOT NULL,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS thread_entries (
    thread_id INTEGER NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
    entry_id INTEGER NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
    quote TEXT,
    PRIMARY KEY (thread_id, entry_id)
);

CREATE TABLE IF NOT EXISTS guidance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    created_at TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    source_entry_id INTEGER REFERENCES entries(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL UNIQUE,
    text TEXT NOT NULL,
    alternates TEXT,
    feedback TEXT
);

CREATE TABLE IF NOT EXISTS syntheses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    period TEXT NOT NULL,
    start TEXT NOT NULL,
    end TEXT NOT NULL,
    markdown TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS insight_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_type TEXT NOT NULL,
    target_id INTEGER NOT NULL,
    note TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path | None = None) -> None:
    settings = get_settings()
    path = db_path or settings.db_path
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = _connect(path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
        _init_vec(conn)
        _sync_fts(conn)
    finally:
        conn.close()


def _init_vec(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS entry_embedding_chunks (
            entry_id INTEGER NOT NULL,
            chunk_idx INTEGER NOT NULL,
            text TEXT NOT NULL,
            PRIMARY KEY (entry_id, chunk_idx)
        )
        """
    )
    conn.commit()
    try:
        import sqlite_vec

        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
        conn.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS entry_embeddings USING vec0(
                entry_id INTEGER,
                chunk_idx INTEGER,
                embedding float[384]
            )
            """
        )
        conn.commit()
    except Exception:
        pass


def _sync_fts(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TRIGGER IF NOT EXISTS entries_ai AFTER INSERT ON entries BEGIN
            INSERT INTO entries_fts(rowid, transcript) VALUES (new.id, new.transcript);
        END
        """
    )
    conn.execute(
        """
        CREATE TRIGGER IF NOT EXISTS entries_au AFTER UPDATE OF transcript ON entries BEGIN
            INSERT INTO entries_fts(entries_fts, rowid, transcript)
            VALUES ('delete', old.id, old.transcript);
            INSERT INTO entries_fts(rowid, transcript) VALUES (new.id, new.transcript);
        END
        """
    )
    conn.execute(
        """
        CREATE TRIGGER IF NOT EXISTS entries_ad AFTER DELETE ON entries BEGIN
            INSERT INTO entries_fts(entries_fts, rowid, transcript)
            VALUES ('delete', old.id, old.transcript);
        END
        """
    )
    conn.commit()


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    conn = _connect(settings.db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
