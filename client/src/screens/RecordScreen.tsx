import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api, type EntryListItem, type PromptToday } from "../api/client";
import { enqueueUpload, flushQueue } from "../api/offlineQueue";
import { cleanDisplayText } from "../utils/displayText";

function pickMime(): string | undefined {
  if (MediaRecorder.isTypeSupported("audio/webm;codecs=opus")) {
    return "audio/webm;codecs=opus";
  }
  if (MediaRecorder.isTypeSupported("audio/mp4")) {
    return "audio/mp4";
  }
  return undefined;
}

export function RecordScreen() {
  const [prompt, setPrompt] = useState<PromptToday | null>(null);
  const [recent, setRecent] = useState<EntryListItem[]>([]);
  const [recording, setRecording] = useState(false);
  const [paused, setPaused] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const [status, setStatus] = useState<string | null>(null);
  const recorder = useRef<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]);
  const timer = useRef<number | null>(null);

  useEffect(() => {
    void flushQueue();
    void (async () => {
      try {
        const [p, e] = await Promise.all([api.todayPrompt(), api.listEntries()]);
        setPrompt(p);
        setRecent(e.items.slice(0, 5));
      } catch {
        /* prompt optional offline */
      }
    })();
  }, []);

  useEffect(() => {
    if (recording && !paused) {
      timer.current = window.setInterval(() => setSeconds((s) => s + 1), 1000);
    } else if (timer.current) {
      clearInterval(timer.current);
    }
    return () => {
      if (timer.current) clearInterval(timer.current);
    };
  }, [recording, paused]);

  async function start() {
    setStatus(null);
    chunks.current = [];
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mime = pickMime();
    const mr = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);
    mr.ondataavailable = (e) => {
      if (e.data.size) chunks.current.push(e.data);
    };
    mr.start(1000);
    recorder.current = mr;
    setSeconds(0);
    setRecording(true);
    setPaused(false);
  }

  function pauseResume() {
    const mr = recorder.current;
    if (!mr) return;
    if (paused) {
      mr.resume();
      setPaused(false);
    } else {
      mr.pause();
      setPaused(true);
    }
  }

  function discard() {
    recorder.current?.stream.getTracks().forEach((t) => t.stop());
    recorder.current = null;
    chunks.current = [];
    setRecording(false);
    setPaused(false);
    setSeconds(0);
  }

  async function save() {
    const mr = recorder.current;
    if (!mr) return;
    setStatus("Saving…");
    await new Promise<void>((resolve) => {
      mr.onstop = () => resolve();
      mr.stop();
      mr.stream.getTracks().forEach((t) => t.stop());
    });
    const blob = new Blob(chunks.current, { type: chunks.current[0]?.type || "audio/webm" });
    try {
      if (navigator.onLine) {
        await api.createEntry(blob, seconds);
      } else {
        await enqueueUpload(blob, seconds);
        setStatus("Saved offline — will upload when connected.");
      }
      setStatus("Uploaded. Processing on server.");
      const e = await api.listEntries();
      setRecent(e.items.slice(0, 5));
    } catch {
      await enqueueUpload(blob, seconds);
      setStatus("Queued for upload.");
    }
    recorder.current = null;
    setRecording(false);
    setPaused(false);
    setSeconds(0);
  }

  const mm = String(Math.floor(seconds / 60)).padStart(2, "0");
  const ss = String(seconds % 60).padStart(2, "0");
  const promptText = prompt ? cleanDisplayText(prompt.text) : null;

  return (
    <div className="flex flex-col gap-8 py-4">
      {prompt && promptText && (
        <section className="rounded-2xl bg-slate-900/80 p-5 leading-relaxed">
          <p className="mb-2 text-xs uppercase tracking-wide text-slate-500">Today</p>
          <p className="text-lg text-slate-100">{promptText}</p>
          {prompt.alternates_list?.length > 0 && (
            <ul className="mt-3 space-y-1 text-sm text-slate-400">
              {prompt.alternates_list.map((a) => (
                <li key={a}>{cleanDisplayText(a)}</li>
              ))}
            </ul>
          )}
          <div className="mt-3 flex gap-3">
            <button
              type="button"
              className="text-xs text-slate-500 underline"
              onClick={() => void api.promptFeedback(prompt.id, "skip")}
            >
              Skip
            </button>
            <button
              type="button"
              className="text-xs text-slate-500 underline"
              onClick={() => void api.promptFeedback(prompt.id, "not_helpful")}
            >
              Not helpful
            </button>
          </div>
        </section>
      )}

      <div className="flex flex-col items-center gap-8">
        <p className="text-4xl tabular-nums text-slate-300">
          {mm}:{ss}
        </p>
        {!recording ? (
          <button
            type="button"
            onClick={() => void start()}
            className="h-28 w-28 rounded-full bg-rose-600 text-lg font-medium shadow-lg active:scale-95"
          >
            Record
          </button>
        ) : (
          <div className="flex flex-wrap justify-center gap-4">
            <button
              type="button"
              onClick={pauseResume}
              className="min-h-12 rounded-xl bg-slate-800 px-6 py-3"
            >
              {paused ? "Resume" : "Pause"}
            </button>
            <button type="button" onClick={discard} className="min-h-12 rounded-xl bg-slate-800 px-6 py-3">
              Discard
            </button>
            <button
              type="button"
              onClick={() => void save()}
              className="min-h-12 rounded-xl bg-emerald-700 px-6 py-3 font-medium"
            >
              Save
            </button>
          </div>
        )}
        {status && <p className="max-w-sm text-center text-sm text-slate-400">{status}</p>}
      </div>

      {recent.length > 0 && (
        <section>
          <h2 className="mb-3 text-sm uppercase tracking-wide text-slate-500">Recent</h2>
          <ul className="space-y-2">
            {recent.map((e) => (
              <li key={e.id}>
                <Link to={`/entries/${e.id}`} className="block rounded-xl bg-slate-900/60 px-4 py-3">
                  <span className="text-xs text-slate-500">{e.created_at}</span>
                  <p className="text-sm leading-snug">{cleanDisplayText(e.summary) || e.status}</p>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
