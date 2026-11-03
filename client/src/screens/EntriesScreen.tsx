import { useEffect, useState } from "react";
import { cleanDisplayText } from "../utils/displayText";
import { Link } from "react-router-dom";
import { api, type EntryListItem } from "../api/client";

export function EntriesScreen() {
  const [query, setQuery] = useState("");
  const [items, setItems] = useState<EntryListItem[]>([]);

  useEffect(() => {
    const t = setTimeout(() => {
      void api.listEntries(query).then((r) => setItems(r.items));
    }, 200);
    return () => clearTimeout(t);
  }, [query]);

  return (
    <div className="space-y-4 py-4">
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search entries"
        className="w-full rounded-xl border border-input bg-background px-4 py-3"
      />
      <ul className="space-y-2">
        {items.map((e) => (
          <li key={e.id}>
            <Link to={`/entries/${e.id}`} className="block rounded-xl border bg-card px-4 py-3 shadow-sm">
              <span className="text-xs text-muted-foreground">{e.created_at}</span>
              <p className="leading-snug">{cleanDisplayText(e.summary) || e.status}</p>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
