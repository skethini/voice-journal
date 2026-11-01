import { useEffect, useState } from "react";
import { api, type GuidanceItem } from "../api/client";

export function GuidanceScreen() {
  const [items, setItems] = useState<GuidanceItem[]>([]);
  const [text, setText] = useState("");

  function reload() {
    void api.listGuidance().then((r) => setItems(r.items));
  }

  useEffect(() => {
    reload();
  }, []);

  return (
    <div className="space-y-4 py-4">
      <p className="text-sm text-slate-400">
        Plain notes for your journal — e.g. &quot;help me stay accountable&quot;. They quietly shape future prompts and
        analyses.
      </p>
      <form
        className="flex flex-col gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          if (!text.trim()) return;
          void api.createGuidance(text.trim()).then(() => {
            setText("");
            reload();
          });
        }}
      >
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={3}
          placeholder="Tell your journal…"
          className="rounded-xl border border-slate-800 bg-slate-900 p-4"
        />
        <button type="submit" className="self-start rounded-xl bg-emerald-800 px-4 py-2">
          Add note
        </button>
      </form>
      <ul className="space-y-2">
        {items.map((g) => (
          <li key={g.id} className="flex items-start gap-3 rounded-xl bg-slate-900/60 p-4">
            <input
              type="checkbox"
              checked={!!g.active}
              onChange={() => void api.patchGuidance(g.id, { active: !g.active }).then(reload)}
            />
            <div className="flex-1">
              <p className={g.active ? "" : "text-slate-500 line-through"}>{g.text}</p>
              <button
                type="button"
                className="mt-2 text-xs text-rose-400"
                onClick={() => void api.deleteGuidance(g.id).then(reload)}
              >
                Delete
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
