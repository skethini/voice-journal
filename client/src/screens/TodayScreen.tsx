import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type EntryListItem, type PromptToday } from "../api/client";

export function TodayScreen() {
  const [prompt, setPrompt] = useState<PromptToday | null>(null);
  const [entries, setEntries] = useState<EntryListItem[]>([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const [p, e] = await Promise.all([api.todayPrompt(), api.listEntries()]);
        setPrompt(p);
        setEntries(e.items.slice(0, 5));
      } catch (e) {
        setErr(String(e));
      }
    })();
  }, []);

  return (
    <div className="space-y-8 py-4">
      <section>
        <h2 className="mb-3 text-sm uppercase tracking-wide text-slate-500">Today</h2>
        {err && <p className="text-sm text-amber-400">{err}</p>}
        {prompt && (
          <div className="rounded-2xl bg-slate-900/80 p-5 leading-relaxed">
            <p className="text-lg">{prompt.text}</p>
            {prompt.alternates_list?.length > 0 && (
              <ul className="mt-4 space-y-2 text-sm text-slate-400">
                {prompt.alternates_list.map((a) => (
                  <li key={a}>· {a}</li>
                ))}
              </ul>
            )}
            <div className="mt-4 flex gap-3">
              <button
                type="button"
                className="text-sm text-slate-500 underline"
                onClick={() => void api.promptFeedback(prompt.id, "skip")}
              >
                Skip
              </button>
              <button
                type="button"
                className="text-sm text-slate-500 underline"
                onClick={() => void api.promptFeedback(prompt.id, "not_helpful")}
              >
                Not helpful
              </button>
            </div>
          </div>
        )}
      </section>
      <section>
        <h2 className="mb-3 text-sm uppercase tracking-wide text-slate-500">Recent</h2>
        <ul className="space-y-2">
          {entries.map((e) => (
            <li key={e.id}>
              <Link to={`/entries/${e.id}`} className="block rounded-xl bg-slate-900/60 px-4 py-3">
                <span className="text-xs text-slate-500">{e.created_at}</span>
                <p className="text-sm">{e.summary || e.status}</p>
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
