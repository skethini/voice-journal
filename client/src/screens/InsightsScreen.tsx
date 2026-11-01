import { useEffect, useState } from "react";
import { api, type Synthesis } from "../api/client";

export function InsightsScreen() {
  const [period, setPeriod] = useState<"week" | "month">("week");
  const [items, setItems] = useState<Synthesis[]>([]);

  useEffect(() => {
    void api.insights(period).then((r) => setItems(r.items));
  }, [period]);

  return (
    <div className="space-y-4 py-4">
      <div className="flex gap-2">
        {(["week", "month"] as const).map((p) => (
          <button
            key={p}
            type="button"
            onClick={() => setPeriod(p)}
            className={`rounded-lg px-4 py-2 capitalize ${period === p ? "bg-slate-700" : "bg-slate-900"}`}
          >
            {p}
          </button>
        ))}
        <button
          type="button"
          className="ml-auto text-sm text-emerald-400"
          onClick={() => void api.generateInsight(period).then((s) => setItems((i) => [s, ...i]))}
        >
          Generate
        </button>
      </div>
      {items.map((s) => (
        <article key={s.id} className="prose prose-invert max-w-none rounded-2xl bg-slate-900/60 p-5 text-sm">
          <pre className="whitespace-pre-wrap font-sans">{s.markdown}</pre>
        </article>
      ))}
      {!items.length && <p className="text-slate-500">No syntheses yet.</p>}
    </div>
  );
}
