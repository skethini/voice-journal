SHARED_SYSTEM = """Role: a reflective journaling companion. Not a therapist.
Separate "what you said" from "what I notice". Every observation cites entries by date and short quotes.
Phrase patterns tentatively ("I notice… does that fit?"). End with an open question, not a verdict or advice dump.
No diagnoses, no labels, no flattery. Gently challenge, including gaps between stated intentions and follow-through.
If the user's words suggest serious distress or risk to themselves, respond with care, avoid analysis-speak, and encourage reaching out to a trusted person or professional support.

<standing_guidance>
{guidance}
</standing_guidance>

<rejected_framings>
{rejected}
</rejected_framings>
"""

ENTRY_USER = """Analyze this journal entry transcript. Return JSON matching the schema.

Entry date: {date}
Transcript:
{transcript}
"""

DAILY_PROMPT_USER = """Write one primary journaling prompt and two alternates for today ({date}).
Recent summaries (7 days):
{summaries}

Open threads:
{threads}

Recent prompts (avoid repeating):
{recent_prompts}

Return JSON: {{"text": "...", "alternates": ["...", "..."]}}
"""

SYNTHESIS_USER = """Write a {period} synthesis in markdown with sections:
What stood out · Recurring themes (dated evidence) · Intentions vs follow-through ·
Anything relevant to standing guidance (only if real signal) · 2-3 open questions.

Period: {start} to {end}
Entry summaries:
{summaries}
Threads:
{threads}
"""

ASK_USER = """Answer the question using only the evidence below. Cite entries by date and short quotes.
If evidence is thin, say so rather than guessing.

Question: {question}

Retrieved excerpts:
{excerpts}

Threads:
{threads}
"""

THREAD_MATCH_USER = """Decide if this item matches an existing thread or should be new.
Item type: {type}
Item: {text}
Quote: {quote}

Candidate threads:
{candidates}

Return JSON: {{"action": "match"|"new", "thread_id": null or id, "label": "..."}}
"""
