import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api, type EntryDetail } from "../api/client";
import { cleanDisplayText } from "../utils/displayText";

export function EntryDetailScreen() {
  const { id } = useParams();
  const [entry, setEntry] = useState<EntryDetail | null>(null);
  const [transcript, setTranscript] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!id) return;
    void api.getEntry(Number(id)).then((e) => {
      setEntry(e);
      const display =
        (e as EntryDetail & { transcript_display?: string }).transcript_display ||
        e.transcript ||
        "";
      setTranscript(display);
    });
  }, [id]);

  if (!entry) return <p className="py-8 text-muted-foreground">Loading…</p>;

  const parsed = entry.analysis?.parsed;
  const summary = cleanDisplayText(entry.analysis?.summary || parsed?.summary);

  return (
    <div className="space-y-6 py-4">
      <p className="text-xs text-muted-foreground">
        {entry.created_at} · {entry.status}
      </p>
      {summary && (
        <section>
          <h2 className="mb-2 text-sm uppercase text-muted-foreground">Summary</h2>
          <p className="leading-relaxed text-foreground">{summary}</p>
        </section>
      )}
      {parsed?.themes?.length ? (
        <section>
          <h2 className="mb-2 text-sm uppercase text-muted-foreground">Themes</h2>
          <ul className="list-disc space-y-1 pl-5 text-sm text-foreground/80">
            {parsed.themes.map((t) => (
              <li key={t}>{cleanDisplayText(t)}</li>
            ))}
          </ul>
        </section>
      ) : null}
      {parsed?.proposed_guidance?.length ? (
        <section>
          <h2 className="mb-2 text-sm uppercase text-muted-foreground">Suggested standing notes</h2>
          <div className="flex flex-wrap gap-2">
            {parsed.proposed_guidance.map((g) => (
              <button
                key={g}
                type="button"
                className="rounded-full bg-secondary px-3 py-2 text-sm"
                onClick={() => void api.createGuidance(g)}
              >
                Save: {cleanDisplayText(g)}
              </button>
            ))}
          </div>
        </section>
      ) : null}
      <section>
        <div className="mb-2 flex items-center justify-between">
          <h2 className="text-sm uppercase text-muted-foreground">Transcript</h2>
          <button
            type="button"
            disabled={saving}
            className="text-sm text-emerald-700"
            onClick={() => {
              setSaving(true);
              void api.patchEntry(entry.id, transcript).finally(() => setSaving(false));
            }}
          >
            Save edits
          </button>
        </div>
        <p className="mb-2 text-xs text-muted-foreground">Cleaned for reading — filler removed, sentences punctuated.</p>
        <textarea
          value={transcript}
          onChange={(e) => setTranscript(e.target.value)}
          rows={12}
          className="w-full rounded-xl border border-border bg-background p-4 text-sm leading-relaxed text-foreground"
        />
      </section>
      <button
        type="button"
        className="text-sm text-muted-foreground underline"
        onClick={() => void api.feedback("entry_analysis", entry.id, "doesn't feel right")}
      >
        Doesn&apos;t feel right
      </button>
    </div>
  );
}
