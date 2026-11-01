import { useEffect, useState } from "react";
import { api, type SettingsResponse } from "../api/client";

export function SettingsScreen() {
  const [settings, setSettings] = useState<SettingsResponse | null>(null);

  useEffect(() => {
    void api.settings().then(setSettings);
  }, []);

  return (
    <div className="space-y-6 py-4 text-sm">
      {settings && (
        <ul className="space-y-2 text-slate-400">
          <li>LLM: {settings.llm_provider} / {settings.llm_model || "(set on server)"}</li>
          <li>Keep audio: {settings.keep_audio ? "yes" : "no (default)"}</li>
          <li>Encrypted backup: {settings.backup_configured ? "configured" : "not configured"}</li>
        </ul>
      )}
      <a
        href="/api/export"
        className="inline-block rounded-xl bg-slate-800 px-4 py-3"
        download
      >
        Download markdown export (zip)
      </a>
      <p className="text-slate-500">
        Server URL, passcode, and Tailscale setup are configured on the host. See README.
      </p>
    </div>
  );
}
