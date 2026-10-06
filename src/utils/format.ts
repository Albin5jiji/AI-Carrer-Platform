// Small formatting helpers shared by every page.

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "—";
  return new Intl.DateTimeFormat("en-IN", { day: "2-digit", month: "short", year: "numeric" }).format(parsed);
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "—";
  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(parsed);
}

/** "pending_mentor_approval" -> "Pending mentor approval" */
export function humanize(value: string | null | undefined): string {
  if (!value) return "—";
  const spaced = value.replaceAll("_", " ");
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}

export function initials(name: string): string {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}

export function formatHours(hours: number): string {
  if (!hours) return "0h";
  return Number.isInteger(hours) ? `${hours}h` : `${hours.toFixed(1)}h`;
}

export function formatScore(value: number | null | undefined): string {
  return value === null || value === undefined ? "—" : `${value}`;
}

export function listToText(values: string[] | null | undefined): string {
  return (values ?? []).join(", ");
}

export function textToList(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

export function linesToText(values: string[] | null | undefined): string {
  return (values ?? []).join("\n");
}

export function textToLines(value: string): string[] {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
}

/** Score band used for colour coding (0-49 low, 50-69 medium, 70+ good). */
export function scoreTone(score: number | null | undefined): "low" | "medium" | "good" {
  if (score === null || score === undefined) return "medium";
  if (score >= 70) return "good";
  if (score >= 50) return "medium";
  return "low";
}
