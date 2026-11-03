import { useState } from "react";
import { cleanDisplayText } from "../utils/displayText";
import { Link } from "react-router-dom";
import { api, type Citation } from "../api/client";

export function AskScreen() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [citations, setCitations] = useState<Citation[]>([]);
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;
    setLoading(true);
    try {
      const r = await api.ask(question.trim());
      setAnswer(r.answer);
      setCitations(r.citations);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-4 py-4">
      <form onSubmit={(e) => void submit(e)} className="flex gap-2">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask your journal…"
          className="flex-1 rounded-xl border border-border bg-background px-4 py-3"
        />
        <button type="submit" disabled={loading} className="rounded-xl bg-secondary px-4 py-3">
          Ask
        </button>
      </form>
      {answer && (
        <div className="rounded-2xl bg-card p-5 leading-relaxed">
          <p className="whitespace-pre-wrap text-foreground">{cleanDisplayText(answer)}</p>
          {citations.length > 0 && (
            <ul className="mt-4 space-y-2 border-t border-border pt-4 text-sm">
              {citations.map((c) => (
                <li key={`${c.entry_id}-${c.quote.slice(0, 20)}`}>
                  <Link to={`/entries/${c.entry_id}`} className="text-emerald-700">
                    {c.date}
                  </Link>
                  <span className="text-muted-foreground"> — {c.quote}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
