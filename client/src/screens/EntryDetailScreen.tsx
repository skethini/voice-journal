import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api, type EntryDetail } from "../api/client";

export function EntryDetailScreen() {
  const { id } = useParams();
  const [entry, setEntry] = useState<EntryDetail | null>(null);
  const [transcript, setTranscript] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!id) return;
    void api.getEntry(Number(id)).then((e) => {
      setEntry(e);
      setTranscript(e.transcript || "");
    });
  }, [id]);

  if (!entry) return <p className="py-8 text-slate-500">Loading…</p>;

  const parsed = entry.analysis?.parsed;

  return (
    <div className="space-y-6 py-4">
      <p className="text-xs text-slate-500">
        {entry.created_at} · {entry.status}
      </p>
      {entry.analysis?.summary && (
        <section>
          <h2 className="mb-2 text-sm uppercase text-slate-500">Summary</h2>
          <p className="leading-relaxed">{entry.analysis.summary}</p>
        </section>
      )}
      {parsed?.themes?.length ? (
        <p className="text-sm text-slate-400">Themes: {parsed.themes.join(", ")}</p>
      ) : null}
      {parsed?.proposed_guidance?.length ? (
        <section>
          <h2 className="mb-2 text-sm uppercase text-slate-500">Suggested standing notes</h2>
          <div className="flex flex-wrap gap-2">
            {parsed.proposed_guidance.map((g) => (
              <button
                key={g}
                type="button"
                className="rounded-full bg-slate-800 px-3 py-2 text-sm"
                onClick={() => void api.createGuidance(g)}
              >
                Save: {g}
              </button>
            ))}
          </div>
        </section>
      ) : null}
      <section>
        <div className="mb-2 flex items-center justify-between">
          <h2 className="text-sm uppercase text-slate-500">Transcript</h2>
          <button
            type="button"
            disabled={saving}
            className="text-sm text-emerald-400"
            onClick={() => {
              setSaving(true);
              void api.patchEntry(entry.id, transcript).finally(() => setSaving(false));
            }}
          >
            Save edits
          </button>
        </div>
        <textarea
          value={transcript}
          onChange={(e) => setTranscript(e.target.value)}
          rows={12}
          className="w-full rounded-xl border border-slate-800 bg-slate-900 p-4 text-sm leading-relaxed"
        />
      </section>
      <button
        type="button"
        className="text-sm text-slate-500 underline"
        onClick={() => void api.feedback("entry_analysis", entry.id, "doesn't feel right")}
      >
        Doesn&apos;t feel right
      </button>
    </div>
  );
}
