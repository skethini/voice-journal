import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api, type EntryListItem, type PromptToday } from "../api/client";
import { enqueueUpload, flushQueue } from "../api/offlineQueue";
import { cleanDisplayText } from "../utils/displayText";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

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
  const [storageWarning, setStorageWarning] = useState<string | null>(null);
  const [scanPreview, setScanPreview] = useState<string | null>(null);
  const [scanFile, setScanFile] = useState<File | null>(null);
  const recorder = useRef<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]);
  const timer = useRef<number | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);

  useEffect(() => {
    void flushQueue();
    void (async () => {
      try {
        const [p, e, s] = await Promise.all([api.todayPrompt(), api.listEntries(), api.settings()]);
        setPrompt(p);
        setRecent(e.items.slice(0, 5));
        if (s.storage_warning) setStorageWarning(s.storage_warning);
      } catch {
        /* prompt optional offline */
      }
    })();
  }, []);

  useEffect(() => {
    return () => {
      if (scanPreview) URL.revokeObjectURL(scanPreview);
    };
  }, [scanPreview]);

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

  async function refreshRecent() {
    const e = await api.listEntries();
    setRecent(e.items.slice(0, 5));
  }

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
      await refreshRecent();
    } catch {
      await enqueueUpload(blob, seconds);
      setStatus("Queued for upload.");
    }
    recorder.current = null;
    setRecording(false);
    setPaused(false);
    setSeconds(0);
  }

  function onPickPhoto(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    if (scanPreview) URL.revokeObjectURL(scanPreview);
    setScanFile(file);
    setScanPreview(URL.createObjectURL(file));
    setStatus(null);
  }

  function clearScan() {
    if (scanPreview) URL.revokeObjectURL(scanPreview);
    setScanPreview(null);
    setScanFile(null);
  }

  async function uploadScan() {
    if (!scanFile) return;
    setStatus("Reading photo…");
    try {
      await api.createScanEntry(scanFile);
      setStatus("Photo uploaded. Turning handwriting into an entry…");
      clearScan();
      await refreshRecent();
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Upload failed");
    }
  }

  const mm = String(Math.floor(seconds / 60)).padStart(2, "0");
  const ss = String(seconds % 60).padStart(2, "0");
  const promptText = prompt ? cleanDisplayText(prompt.text) : null;

  return (
    <div className="flex flex-col gap-8 py-4">
      {storageWarning && (
        <Alert variant="destructive">
          <AlertTitle>Back up your journal</AlertTitle>
          <AlertDescription>{storageWarning}</AlertDescription>
        </Alert>
      )}
      {prompt && promptText && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-normal uppercase tracking-wide text-muted-foreground">
              Today
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 leading-relaxed">
            <p className="text-lg">{promptText}</p>
            {prompt.alternates_list?.length > 0 && (
              <ul className="space-y-1 text-sm text-muted-foreground">
                {prompt.alternates_list.map((a) => (
                  <li key={a}>{cleanDisplayText(a)}</li>
                ))}
              </ul>
            )}
            <div className="flex gap-3">
              <button
                type="button"
                className="text-xs text-muted-foreground underline"
                onClick={() => void api.promptFeedback(prompt.id, "skip")}
              >
                Skip
              </button>
              <button
                type="button"
                className="text-xs text-muted-foreground underline"
                onClick={() => void api.promptFeedback(prompt.id, "not_helpful")}
              >
                Not helpful
              </button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="flex flex-col items-center gap-6">
        <p className="text-4xl tabular-nums text-muted-foreground">
          {mm}:{ss}
        </p>
        {!recording ? (
          <Button
            type="button"
            size="lg"
            onClick={() => void start()}
            className="h-28 w-28 rounded-full bg-rose-600 text-lg font-medium text-white shadow-lg hover:bg-rose-700"
          >
            Record
          </Button>
        ) : (
          <div className="flex flex-wrap justify-center gap-3">
            <Button type="button" variant="secondary" size="lg" onClick={pauseResume}>
              {paused ? "Resume" : "Pause"}
            </Button>
            <Button type="button" variant="secondary" size="lg" onClick={discard}>
              Discard
            </Button>
            <Button type="button" size="lg" className="bg-emerald-700 hover:bg-emerald-800" onClick={() => void save()}>
              Save
            </Button>
          </div>
        )}
        {status && <p className="max-w-sm text-center text-sm text-muted-foreground">{status}</p>}
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base font-medium">Photo of a written page</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Snap or upload a journal page. We read the handwriting and analyze it like a voice entry.
          </p>
          <input
            ref={fileInput}
            type="file"
            accept="image/jpeg,image/png,image/webp,image/*"
            capture="environment"
            className="hidden"
            onChange={onPickPhoto}
          />
          {!scanPreview ? (
            <Button type="button" variant="outline" className="w-full" onClick={() => fileInput.current?.click()}>
              Choose photo or take picture
            </Button>
          ) : (
            <div className="space-y-3">
              <img src={scanPreview} alt="Journal page preview" className="max-h-64 w-full rounded-lg border object-contain" />
              <div className="flex flex-wrap gap-2">
                <Button type="button" className="flex-1" onClick={() => void uploadScan()}>
                  Add to journal
                </Button>
                <Button type="button" variant="secondary" onClick={clearScan}>
                  Cancel
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {recent.length > 0 && (
        <section>
          <h2 className="mb-3 text-sm uppercase tracking-wide text-muted-foreground">Recent</h2>
          <ul className="space-y-2">
            {recent.map((e) => (
              <li key={e.id}>
                <Link to={`/entries/${e.id}`} className="block rounded-xl border bg-card px-4 py-3 shadow-sm">
                  <span className="text-xs text-muted-foreground">{e.created_at}</span>
                  <p className="text-sm leading-snug">{cleanDisplayText(e.summary) || e.status}</p>
                  {e.status === "uploaded" && (
                    <Badge variant="secondary" className="mt-1">
                      Processing…
                    </Badge>
                  )}
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
