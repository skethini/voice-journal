import { useEffect, useState } from "react";
import { api, apiBase, type SettingsResponse } from "../api/client";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

export function SettingsScreen() {
  const [settings, setSettings] = useState<SettingsResponse | null>(null);

  useEffect(() => {
    void api.settings().then(setSettings);
  }, []);

  return (
    <div className="space-y-6 py-4 text-sm">
      {settings?.storage_warning && (
        <Alert variant="destructive">
          <AlertTitle>Your entries can disappear on redeploy</AlertTitle>
          <AlertDescription>{settings.storage_warning}</AlertDescription>
        </Alert>
      )}
      {settings && (
        <ul className="space-y-2 text-muted-foreground">
          <li>LLM: {settings.llm_provider} / {settings.llm_model || "(set on server)"}</li>
          <li>Keep audio: {settings.keep_audio ? "yes" : "no (default)"}</li>
          <li>Encrypted backup (age): {settings.backup_configured ? "configured" : "not configured"}</li>
          {settings.auto_backup && (
            <li>
              Automatic backups: on —{" "}
              <code className="text-foreground">{settings.backup_dir || "data/backups"}</code>
              {settings.latest_backup_at
                ? ` · latest ${new Date(settings.latest_backup_at).toLocaleString()}`
                : " · none yet"}
              {typeof settings.dated_backup_count === "number" && settings.dated_backup_count > 0
                ? ` · ${settings.dated_backup_count} dated copies (keep ${settings.backup_retain_days ?? 14} days)`
                : ""}
            </li>
          )}
          {typeof settings.entry_count === "number" && (
            <li>Entries stored on server: {settings.entry_count}</li>
          )}
        </ul>
      )}
      <Button asChild variant="secondary">
        <a href={`${apiBase}/export`} download="journal-export.zip">
          Download full backup (zip)
        </a>
      </Button>
      <p className="text-muted-foreground">
        The server keeps <strong className="font-medium text-foreground">journal-latest.zip</strong> updated after
        each analyzed entry, plus a new dated zip every night (retention configurable via{" "}
        <code className="text-foreground">BACKUP_RETAIN_DAYS</code>). Default folder:{" "}
        <code className="text-foreground">DATA_DIR/backups</code> (on Render, use a persistent disk at{" "}
        <code className="text-foreground">/data</code> so backups survive redeploys). Download the zip below for an
        off-server copy — that is the only recovery if the host wipes its disk.
      </p>
    </div>
  );
}
