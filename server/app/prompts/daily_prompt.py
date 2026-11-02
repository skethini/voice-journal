DAILY_PROMPT_SCHEMA = {
    "type": "object",
    "properties": {
        "text": {"type": "string"},
        "alternates": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["text", "alternates"],
    "additionalProperties": False,
}
