import pytest

pytest_plugins = ("pytest_asyncio",)


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("EMBED_MOCK", "1")
    monkeypatch.setenv("PASSCODE_HASH", "")
    from app.config import get_settings

    get_settings.cache_clear()
    from app.db import init_db

    db = tmp_path / "journal.db"
    if db.exists():
        db.unlink()
    init_db(db)
    yield
