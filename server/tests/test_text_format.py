from app.text_format import parse_llm_json, readable_transcript, sanitize_display_text


def test_parse_llm_json_strips_fence():
    raw = '```json\n{"text": "Hello", "alternates": ["A", "B"]}\n```'
    data = parse_llm_json(raw)
    assert data["text"] == "Hello"


def test_sanitize_display_text():
    assert sanitize_display_text("```json\noops") == "oops"


def test_readable_transcript():
    out = readable_transcript("um i think we should leave uh the job")
    assert "um" not in out.lower()
    assert out.endswith(".")
