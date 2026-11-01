import { useEffect, useState } from "react";
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
        className="w-full rounded-xl border border-slate-800 bg-slate-900 px-4 py-3"
      />
      <ul className="space-y-2">
        {items.map((e) => (
          <li key={e.id}>
            <Link to={`/entries/${e.id}`} className="block rounded-xl bg-slate-900/60 px-4 py-3">
              <span className="text-xs text-slate-500">{e.created_at}</span>
              <p>{e.summary || e.status}</p>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
