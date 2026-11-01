from __future__ import annotations

import io
import json
import shutil
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from app.config import get_settings
from app.db import get_db


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
        base = settings.entries_export_dir
        if base.is_dir():
            for p in base.rglob("*.md"):
                zf.write(p, p.relative_to(settings.data_dir))
    return buf.getvalue()


def nightly_backup() -> None:
    settings = get_settings()
    if not settings.age_recipient:
        return
    settings.backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    archive = settings.backup_dir / f"journal-{stamp}.tar.gz"
    shutil.make_archive(str(archive.with_suffix("")), "gztar", settings.data_dir)
    enc_path = settings.backup_dir / f"journal-{stamp}.tar.gz.age"
    subprocess.run(
        ["age", "-r", settings.age_recipient, "-o", str(enc_path), str(archive)],
        check=True,
        capture_output=True,
    )
    archive.unlink(missing_ok=True)
