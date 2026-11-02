const BASE = import.meta.env.VITE_API_BASE ?? "/api";

export const apiBase = BASE;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...init?.headers,
    },
  });
  if (res.status === 401) {
    throw new Error("unauthorized");
  }
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  if (res.headers.get("content-type")?.includes("application/json")) {
    return res.json() as Promise<T>;
  }
  return res as unknown as T;
}

export const api = {
  login: (passcode: string) =>
    request<{ ok: boolean }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ passcode }),
    }),

  createEntry: (blob: Blob, duration_s: number) => {
    const fd = new FormData();
    const ext = blob.type.includes("mp4") ? "mp4" : "webm";
    fd.append("audio", blob, `recording.${ext}`);
    fd.append("duration_s", String(duration_s));
    return request<{ id: number }>("/entries", { method: "POST", body: fd });
  },

  listEntries: (query = "") =>
    request<{ items: EntryListItem[]; next_cursor: number | null }>(
      `/entries?limit=30${query ? `&query=${encodeURIComponent(query)}` : ""}`,
    ),

  getEntry: (id: number) => request<EntryDetail>(`/entries/${id}`),

  patchEntry: (id: number, transcript: string) =>
    request<{ ok: boolean }>(`/entries/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ transcript }),
    }),

  todayPrompt: () => request<PromptToday>("/prompts/today"),

  promptFeedback: (id: number, feedback: string) =>
    request<{ ok: boolean }>(`/prompts/${id}/feedback`, {
      method: "POST",
      body: JSON.stringify({ feedback }),
    }),

  ask: (question: string) =>
    request<{ answer: string; citations: Citation[] }>("/ask", {
      method: "POST",
      body: JSON.stringify({ question }),
    }),

  listGuidance: () => request<{ items: GuidanceItem[] }>("/guidance"),

  createGuidance: (text: string) =>
    request<{ id: number }>("/guidance", {
      method: "POST",
      body: JSON.stringify({ text }),
    }),

  patchGuidance: (id: number, patch: { text?: string; active?: boolean }) =>
    request<{ ok: boolean }>(`/guidance/${id}`, {
      method: "PATCH",
      body: JSON.stringify(patch),
    }),

  deleteGuidance: (id: number) =>
    request<{ ok: boolean }>(`/guidance/${id}`, { method: "DELETE" }),

  insights: (period: "week" | "month") =>
    request<{ items: Synthesis[] }>(`/insights?period=${period}`),

  generateInsight: (period: "week" | "month") =>
    request<Synthesis>("/insights/generate", {
      method: "POST",
      body: JSON.stringify({ period }),
    }),

  feedback: (target_type: string, target_id: number, note?: string) =>
    request<{ id: number }>("/feedback", {
      method: "POST",
      body: JSON.stringify({ target_type, target_id, note }),
    }),

  settings: () => request<SettingsResponse>("/settings"),
};

export type EntryListItem = {
  id: number;
  created_at: string;
  status: string;
  summary: string | null;
};

export type EntryDetail = EntryListItem & {
  transcript: string;
  transcript_display?: string;
  analysis: {
    summary: string;
    parsed: AnalysisJson;
  } | null;
};

export type AnalysisJson = {
  summary: string;
  themes: string[];
  goals: { text: string; quote: string }[];
  frustrations: { text: string; quote: string }[];
  intentions: { text: string; quote: string }[];
  open_questions: string[];
  proposed_guidance: string[];
};

export type PromptToday = {
  id: number;
  date: string;
  text: string;
  alternates_list: string[];
};

export type Citation = { entry_id: number; date: string; quote: string };

export type GuidanceItem = {
  id: number;
  text: string;
  active: number;
  created_at: string;
};

export type Synthesis = {
  id: number;
  period: string;
  markdown: string;
  start: string;
  end: string;
};

export type SettingsResponse = {
  keep_audio: boolean;
  llm_provider: string;
  llm_model: string;
  has_passcode: boolean;
  backup_configured: boolean;
};
