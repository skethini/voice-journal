from app.export import build_export_zip, write_automatic_backup


def test_build_export_zip_and_automatic_backup(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("AUTO_BACKUP", "true")
    from app.config import get_settings

    get_settings.cache_clear()
    from app.db import init_db

    init_db()
    with __import__("app.db", fromlist=["get_db"]).get_db() as conn:
        conn.execute(
            "INSERT INTO entries (created_at, transcript, status) VALUES ('2025-01-01T12:00:00+00:00', 'hello', 'analyzed')"
        )

    assert len(build_export_zip()) > 100
    path = write_automatic_backup(create_dated=True)
    assert path is not None
    latest = tmp_path / "backups" / "journal-latest.zip"
    assert latest.is_file()
    assert len(list((tmp_path / "backups").glob("journal-2*.zip"))) >= 2
