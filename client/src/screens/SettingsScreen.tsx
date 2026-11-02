import { useEffect, useState } from "react";
import { api, apiBase, type SettingsResponse } from "../api/client";

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
        href={`${apiBase}/export`}
        className="inline-block rounded-xl bg-slate-800 px-4 py-3"
        download="journal-export.zip"
      >
        Download full backup (zip)
      </a>
      <p className="text-slate-500">
        Includes <code className="text-slate-400">journal.db</code> (everything) plus markdown
        files under <code className="text-slate-400">entries/</code>. Save copies to iCloud Drive,
        Google Drive, or an external drive regularly — especially if you host on Render free tier.
      </p>
    </div>
  );
}
