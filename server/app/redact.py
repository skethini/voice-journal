"""Optional reversible redaction hook (stub v1)."""

from app.config import get_settings


def redact_text(text: str) -> str:
    names = _load_name_list()
    if not names:
        return text
    out = text
    for i, name in enumerate(names):
        if name:
            out = out.replace(name, f"[NAME_{i}]")
    return out


def _load_name_list() -> list[str]:
    path = get_settings().data_dir / "redact_names.txt"
    if not path.is_file():
        return []
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]
