from __future__ import annotations

import io
import json
import logging
import shutil
import subprocess
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.config import get_settings
from app.db import get_db

logger = logging.getLogger("voice_journal.export")

LATEST_BACKUP_NAME = "journal-latest.zip"


def export_entry_markdown(entry_id: int) -> Path | None:
    settings = get_settings()
    with get_db() as conn:
        row = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
        if not row or not row["transcript"]:
            return None
        analysis = conn.execute(
            "SELECT summary, json FROM entry_analysis WHERE entry_id = ?", (entry_id,)
        ).fetchone()

    created = datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
    year = created.strftime("%Y")
    fname = created.strftime("%Y-%m-%d_%H%M") + ".md"
    out_dir = settings.entries_export_dir / year
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / fname

    lines = [
        f"# Journal entry — {row['created_at']}",
        "",
        "## Transcript",
        "",
        row["transcript"],
        "",
    ]
    if analysis:
        lines.extend(["## Summary", "", analysis["summary"] or "", ""])
        try:
            data = json.loads(analysis["json"])
            if data.get("themes"):
                lines.extend(["## Themes", "", ", ".join(data["themes"]), ""])
        except json.JSONDecodeError:
            pass

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def build_export_zip() -> bytes:
    settings = get_settings()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        db = settings.db_path
        if db.is_file():
            zf.write(db, "journal.db")
        base = settings.entries_export_dir
        if base.is_dir():
            for p in base.rglob("*.md"):
                zf.write(p, p.relative_to(settings.data_dir))
    return buf.getvalue()


def _prune_old_backups() -> None:
    settings = get_settings()
    if settings.backup_retain_days <= 0:
        return
    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.backup_retain_days)
    backup_dir = settings.effective_backup_dir
    for pattern in ("journal-2*.zip", "journal-2*.tar.gz", "journal-2*.tar.gz.age"):
        for path in backup_dir.glob(pattern):
            if path.name == LATEST_BACKUP_NAME:
                continue
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            if mtime < cutoff:
                path.unlink(missing_ok=True)


def write_automatic_backup(*, create_dated: bool = False) -> Path | None:
    """Write journal-latest.zip; optionally add a timestamped copy."""
    settings = get_settings()
    if not settings.auto_backup:
        return None
    backup_dir = settings.effective_backup_dir
    backup_dir.mkdir(parents=True, exist_ok=True)
    data = build_export_zip()
    latest = backup_dir / LATEST_BACKUP_NAME
    latest.write_bytes(data)
    dated: Path | None = None
    if create_dated:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        dated = backup_dir / f"journal-{stamp}.zip"
        dated.write_bytes(data)
        _prune_old_backups()
    logger.info("backup written path=%s dated=%s", latest, dated)
    return dated or latest


def backup_status() -> dict:
    settings = get_settings()
    backup_dir = settings.effective_backup_dir
    latest = backup_dir / LATEST_BACKUP_NAME
    latest_at: str | None = None
    if latest.is_file():
        latest_at = datetime.fromtimestamp(latest.stat().st_mtime, tz=timezone.utc).isoformat()
    dated_count = len(
        [p for p in backup_dir.glob("journal-2*.zip") if p.name != LATEST_BACKUP_NAME]
    )
    return {
        "auto_backup": settings.auto_backup,
        "backup_dir": str(backup_dir),
        "latest_backup_at": latest_at,
        "dated_backup_count": dated_count,
        "backup_retain_days": settings.backup_retain_days,
        "age_encryption": bool(settings.age_recipient),
    }


def nightly_backup() -> None:
    settings = get_settings()
    if not settings.auto_backup and not settings.age_recipient:
        return

    dated_zip: Path | None = None
    if settings.auto_backup:
        dated_zip = write_automatic_backup(create_dated=True)

    if not settings.age_recipient:
        return

    backup_dir = settings.effective_backup_dir
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    archive = backup_dir / f"journal-{stamp}.tar.gz"
    shutil.make_archive(str(archive.with_suffix("")), "gztar", settings.data_dir)
    enc_path = backup_dir / f"journal-{stamp}.tar.gz.age"
    subprocess.run(
        ["age", "-r", settings.age_recipient, "-o", str(enc_path), str(archive)],
        check=True,
        capture_output=True,
    )
    archive.unlink(missing_ok=True)
    _prune_old_backups()
    if dated_zip:
        enc_zip = dated_zip.with_suffix(".zip.age")
        subprocess.run(
            ["age", "-r", settings.age_recipient, "-o", str(enc_zip), str(dated_zip)],
            check=True,
            capture_output=True,
        )
