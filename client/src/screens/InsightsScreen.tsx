import { useEffect, useState } from "react";
import { api, type Synthesis } from "../api/client";
import { cleanDisplayText, markdownToBlocks } from "../utils/displayText";

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
        <article key={s.id} className="space-y-4 rounded-2xl bg-slate-900/60 p-5 text-sm leading-relaxed">
          {markdownToBlocks(s.markdown).map((block) => (
            <div key={`${s.id}-${block.heading ?? "p"}`}>
              {block.heading && (
                <h3 className="mb-1 font-medium text-slate-200">{cleanDisplayText(block.heading)}</h3>
              )}
              <p className="whitespace-pre-wrap text-slate-300">{cleanDisplayText(block.body)}</p>
            </div>
          ))}
        </article>
      ))}
      {!items.length && <p className="text-slate-500">No syntheses yet.</p>}
    </div>
  );
}
