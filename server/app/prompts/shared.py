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

ENTRY_USER = """Analyze this journal entry transcript. Return JSON only (no markdown fences).

Writing rules for summary and themes:
- Name what actually happened (specific situation, decision, conversation, or moment)—not vague buckets like "work learning" or "personal growth" alone.
- Include the user's real insight, tension, or open loop in their own framing.
- themes: concrete phrases tied to events (e.g. "debated quitting the project after the standup"), not one-word labels.

Entry date: {date}
Transcript:
{transcript}
"""

DAILY_PROMPT_USER = """Write one primary journaling prompt and two alternates for today ({date}).
Be specific—tie to something concrete from recent entries when possible, not generic self-help.
Return JSON only with keys text and alternates (array of two strings). No markdown code blocks.

Recent summaries (7 days):
{summaries}

Open threads:
{threads}

Recent prompts (avoid repeating):
{recent_prompts}
"""

SYNTHESIS_USER = """Write a {period} synthesis in plain markdown (no JSON, no ``` fences).
Use specific events and quotes—not vague theme names alone.
Sections: What stood out · Recurring themes (dated evidence) · Intentions vs follow-through ·
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
