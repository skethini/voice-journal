import re
import subprocess
from pathlib import Path

from app.config import get_settings

FILLER = re.compile(r"\b(uh+|um+|like,?\s|you know)\b", re.IGNORECASE)


def normalize_audio(input_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-ar",
        "16000",
        "-ac",
        "1",
        "-c:a",
        "pcm_s16le",
        str(output_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def light_cleanup(transcript: str) -> str:
    text = FILLER.sub("", transcript)
    text = re.sub(r"\s+", " ", text).strip()
    if text and text[-1] not in ".?!":
        text += "."
    return text


_model = None


def transcribe_file(wav_path: Path) -> tuple[str, str]:
    global _model
    from faster_whisper import WhisperModel

    settings = get_settings()
    if _model is None:
        _model = WhisperModel(settings.whisper_model, device="cpu", compute_type="int8")
    segments, _ = _model.transcribe(str(wav_path), beam_size=5)
    raw = " ".join(s.text.strip() for s in segments).strip()
    cleaned = light_cleanup(raw)
    return raw, cleaned
