import { useState } from "react";
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
          className="flex-1 rounded-xl border border-slate-800 bg-slate-900 px-4 py-3"
        />
        <button type="submit" disabled={loading} className="rounded-xl bg-slate-700 px-4 py-3">
          Ask
        </button>
      </form>
      {answer && (
        <div className="rounded-2xl bg-slate-900/80 p-5 leading-relaxed">
          <p className="whitespace-pre-wrap">{answer}</p>
          {citations.length > 0 && (
            <ul className="mt-4 space-y-2 border-t border-slate-800 pt-4 text-sm">
              {citations.map((c) => (
                <li key={`${c.entry_id}-${c.quote.slice(0, 20)}`}>
                  <Link to={`/entries/${c.entry_id}`} className="text-emerald-400">
                    {c.date}
                  </Link>
                  <span className="text-slate-500"> — {c.quote}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
