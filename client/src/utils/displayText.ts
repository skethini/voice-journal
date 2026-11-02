/** Strip accidental markdown/code fences from LLM text shown in the UI. */
export function cleanDisplayText(text: string | null | undefined): string {
  if (!text) return "";
  let t = text.trim();
  const fence = /^```(?:json|markdown)?\s*\n?([\s\S]*?)\n?```\s*$/i.exec(t);
  if (fence) t = fence[1].trim();
  t = t.replace(/^```json\s*/i, "").replace(/```/g, "");
  return t.trim();
}

/** Lightweight markdown → readable blocks (no raw ``` in UI). */
export function markdownToBlocks(md: string): { heading?: string; body: string }[] {
  const cleaned = cleanDisplayText(md);
  const sections: { heading?: string; body: string }[] = [];
  let current: { heading?: string; lines: string[] } = { lines: [] };

  for (const line of cleaned.split("\n")) {
    const h = /^(#{1,3})\s+(.+)$/.exec(line.trim());
    if (h) {
      if (current.lines.length || current.heading) {
        sections.push({
          heading: current.heading,
          body: current.lines.join("\n").trim(),
        });
      }
      current = { heading: h[2].trim(), lines: [] };
    } else {
      current.lines.push(line);
    }
  }
  if (current.lines.length || current.heading) {
    sections.push({
      heading: current.heading,
      body: current.lines.join("\n").trim(),
    });
  }
  if (!sections.length && cleaned) {
    sections.push({ body: cleaned });
  }
  return sections.filter((s) => s.body || s.heading);
}
