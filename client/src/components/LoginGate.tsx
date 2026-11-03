import { useEffect, useState } from "react";
import { api } from "../api/client";

export function LoginGate({ children }: { children: React.ReactNode }) {
  const [passcode, setPasscode] = useState("");
  const [authed, setAuthed] = useState(false);
  const [checking, setChecking] = useState(true);
  const [needsPasscode, setNeedsPasscode] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    void api
      .settings()
      .then((s) => {
        if (!s.has_passcode) setAuthed(true);
        setNeedsPasscode(s.has_passcode);
      })
      .catch(() => setAuthed(true))
      .finally(() => setChecking(false));
  }, []);

  if (checking) {
    return <p className="p-8 text-center text-muted-foreground">Loading…</p>;
  }

  if (authed) return <>{children}</>;

  if (!needsPasscode) return <>{children}</>;

  return (
    <div className="flex min-h-dvh flex-col items-center justify-center gap-4 px-6">
      <h1 className="text-xl">Voice Journal</h1>
      <form
        className="flex w-full max-w-sm flex-col gap-3"
        onSubmit={(e) => {
          e.preventDefault();
          void api
            .login(passcode)
            .then(() => setAuthed(true))
            .catch(() => setErr("Invalid passcode"));
        }}
      >
        <input
          type="password"
          inputMode="numeric"
          autoComplete="current-password"
          placeholder="Passcode"
          value={passcode}
          onChange={(e) => setPasscode(e.target.value)}
          className="rounded-xl border border-input bg-background px-4 py-3"
        />
        <button type="submit" className="rounded-xl bg-emerald-800 py-3 font-medium">
          Unlock
        </button>
        {err && <p className="text-sm text-rose-400">{err}</p>}
      </form>
    </div>
  );
}
