from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root .env (when uvicorn cwd is server/) and server/.env
_ENV_FILES = (
    Path(__file__).resolve().parent.parent / ".env",
    Path(__file__).resolve().parent.parent.parent / ".env",
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[str(p) for p in _ENV_FILES if p.is_file()] or ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_provider: str = "openai"
    llm_model: str = ""
    llm_api_key: str = ""
    whisper_provider: str = "local"  # local | openai
    whisper_model: str = "small"  # local: faster-whisper size; openai: whisper-1
    embed_provider: str = "local"  # local | openai
    data_dir: Path = Path("./data")
    keep_audio: bool = False
    passcode_hash: str = ""
    timezone: str = "America/Los_Angeles"
    backup_dir: Path = Path("./backups")
    age_recipient: str = ""
    session_secret: str = "dev-insecure-change-me"
    host: str = "127.0.0.1"
    port: int = 8000
    cookie_secure: bool = True
    public_url: str = ""  # if set, warn when passcode missing

    @property
    def entries_export_dir(self) -> Path:
        return self.data_dir / "entries"

    @property
    def audio_dir(self) -> Path:
        return self.data_dir / "audio"

    @property
    def db_path(self) -> Path:
        return self.data_dir / "journal.db"


@lru_cache
def get_settings() -> Settings:
    return Settings()
