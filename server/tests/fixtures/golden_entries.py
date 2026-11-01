"""Golden-set journal snippets for prompt regression (run with real LLM in CI optional)."""

SAMPLES = [
    {
        "transcript": "I said I'd wake up early all week and I didn't once. I'm frustrated with myself but I don't want a lecture.",
        "must_not_contain": ["diagnos", "narciss", " wonderful "],
        "should_contain_tentative": True,
    },
]
