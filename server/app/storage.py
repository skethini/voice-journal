"""Detect ephemeral storage (e.g. Render free without a disk)."""
from __future__ import annotations

import os

from app.config import get_settings
from app.db import get_db


def storage_status() -> dict:
    settings = get_settings()
    on_render = bool(os.environ.get("RENDER"))
    persistent_flag = os.environ.get("PERSISTENT_DISK", "").lower() in ("1", "true", "yes")
    db_path = settings.db_path
    db_exists = db_path.is_file()
    entry_count = 0
    if db_exists:
        with get_db() as conn:
            entry_count = conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]

    ephemeral = on_render and not persistent_flag
    warning = None
    if ephemeral:
        warning = (
            "This server uses ephemeral disk. Entries can be lost on redeploy unless you attach "
            "a Render persistent disk (paid) or download backups regularly from Settings."
        )
    elif not db_exists and entry_count == 0:
        warning = "Database is empty. If entries are missing after a deploy, restore from a backup zip."

    return {
        "data_dir": str(settings.data_dir),
        "entry_count": entry_count,
        "ephemeral_storage": ephemeral,
        "storage_warning": warning,
    }
