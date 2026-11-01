ENTRY_ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "themes": {"type": "array", "items": {"type": "string"}},
        "goals": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"text": {"type": "string"}, "quote": {"type": "string"}},
                "required": ["text", "quote"],
                "additionalProperties": False,
            },
        },
        "frustrations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"text": {"type": "string"}, "quote": {"type": "string"}},
                "required": ["text", "quote"],
                "additionalProperties": False,
            },
        },
        "intentions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"text": {"type": "string"}, "quote": {"type": "string"}},
                "required": ["text", "quote"],
                "additionalProperties": False,
            },
        },
        "open_questions": {"type": "array", "items": {"type": "string"}},
        "proposed_guidance": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "summary",
        "themes",
        "goals",
        "frustrations",
        "intentions",
        "open_questions",
        "proposed_guidance",
    ],
    "additionalProperties": False,
}
