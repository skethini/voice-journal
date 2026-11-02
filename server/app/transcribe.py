import re
import subprocess
from pathlib import Path

import httpx

from app.config import get_settings

FILLER = re.compile(r"\b(uh+|um+|like,?\s|you know)\b", re.IGNORECASE)

_model = None


def light_cleanup(transcript: str) -> str:
    text = FILLER.sub("", transcript)
    text = re.sub(r"\s+", " ", text).strip()
    if text and text[-1] not in ".?!":
        text += "."
    return text


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


def _transcribe_local_wav(wav_path: Path) -> tuple[str, str]:
    global _model
    from faster_whisper import WhisperModel

    settings = get_settings()
    if _model is None:
        _model = WhisperModel(settings.whisper_model, device="cpu", compute_type="int8")
    segments, _ = _model.transcribe(str(wav_path), beam_size=5)
    raw = " ".join(s.text.strip() for s in segments).strip()
    return raw, light_cleanup(raw)


async def transcribe_openai(audio_path: Path) -> tuple[str, str]:
    settings = get_settings()
    if not settings.llm_api_key:
        raise RuntimeError("LLM_API_KEY required for OpenAI transcription")
    model = settings.whisper_model if settings.whisper_model.startswith("whisper") else "whisper-1"
    async with httpx.AsyncClient(timeout=180.0) as client:
        with audio_path.open("rb") as f:
            resp = await client.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {settings.llm_api_key}"},
                files={"file": (audio_path.name, f, "application/octet-stream")},
                data={"model": model, "response_format": "json"},
            )
        resp.raise_for_status()
    raw = resp.json().get("text", "").strip()
    return raw, light_cleanup(raw)


async def transcribe_uploaded_audio(source_path: Path) -> tuple[str, str]:
    """Local Whisper (private, CPU-heavy) or OpenAI Whisper API (cloud-friendly)."""
    settings = get_settings()
    if settings.whisper_provider == "openai":
        return await transcribe_openai(source_path)

    wav_path = settings.data_dir / "tmp" / f"{source_path.stem}.wav"
    normalize_audio(source_path, wav_path)
    try:
        return _transcribe_local_wav(wav_path)
    finally:
        wav_path.unlink(missing_ok=True)


def transcribe_file(wav_path: Path) -> tuple[str, str]:
    """Sync local path used by tests; prefer transcribe_uploaded_audio in pipeline."""
    return _transcribe_local_wav(wav_path)
