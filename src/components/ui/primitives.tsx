import type { ReactNode } from "react";
import { Loader2, RefreshCw } from "lucide-react";

/* ------------------------------------------------------------------ badges */

const SUCCESS_STATES = new Set([
  "approved",
  "selected",
  "shortlisted",
  "completed",
  "covered",
  "published",
  "open",
  "active",
  "good",
  "resolved",
  "practiced",
]);

const WARNING_STATES = new Set([
  "pending_review",
  "pending_mentor_approval",
  "in_progress",
  "changes_requested",
  "draft",
  "action_needed",
  "interview_scheduled",
  "partial",
  "medium",
  "open_feedback",
  "submitted",
]);

const DANGER_STATES = new Set([
  "rejected",
  "withdrawn",
  "not_eligible",
  "missing",
  "low",
  "closed",
  "inactive",
  "needs_revision",
]);

export type Tone = "success" | "warning" | "danger" | "neutral" | "info";

export function toneForState(value: string | null | undefined): Tone {
  if (!value) return "neutral";
  const key = value.toLowerCase();
  if (SUCCESS_STATES.has(key)) return "success";
  if (WARNING_STATES.has(key)) return "warning";
  if (DANGER_STATES.has(key)) return "danger";
  return "neutral";
}

export function StatusBadge({ value, tone }: { value: string | null | undefined; tone?: Tone }) {
  const label = (value ?? "unknown").replaceAll("_", " ");
  const resolved = tone ?? toneForState(value);
  return <span className={`badge badge-${resolved}`}>{label}</span>;
}

export function Chip({ children }: { children: ReactNode }) {
  return <span className="chip">{children}</span>;
}

export function ChipList({ values, empty = "None recorded" }: { values: string[]; empty?: string }) {
  if (!values || values.length === 0) return <span className="muted">{empty}</span>;
  return (
    <div className="chip-row">
      {values.map((value) => (
        <Chip key={value}>{value}</Chip>
      ))}
    </div>
  );
}

/* -------------------------------------------------------- states and loaders */

export function LoadingState({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="state-block" role="status">
      <Loader2 className="spin" size={20} />
      <p>{label}</p>
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="state-block state-error" role="alert">
      <p>{message}</p>
      {onRetry && (
        <button className="btn btn-ghost btn-sm" onClick={onRetry} type="button">
          <RefreshCw size={15} /> Try again
        </button>
      )}
    </div>
  );
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="state-block state-empty">
      <p className="state-title">{title}</p>
      {description && <p className="muted">{description}</p>}
      {action}
    </div>
  );
}

export function Alert({ tone = "info", children }: { tone?: "info" | "success" | "warning" | "error"; children: ReactNode }) {
  return <div className={`alert alert-${tone}`}>{children}</div>;
}

/* -------------------------------------------------------------- indicators */

export function ProgressBar({ value, tone = "accent" }: { value: number; tone?: "accent" | "gold" | "danger" }) {
  const clamped = Math.max(0, Math.min(100, value));
  return (
    <div className="progress-track" aria-label={`Progress ${clamped}%`}>
      <div className={`progress-fill progress-${tone}`} style={{ width: `${clamped}%` }} />
    </div>
  );
}

export function ScoreRing({ score, size = 148, caption }: { score: number; size?: number; caption?: string }) {
  const radius = 50;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (circumference * Math.max(0, Math.min(100, score))) / 100;
  const tone = score >= 70 ? "#2c7a54" : score >= 50 ? "#c08b23" : "#c0583d";

  return (
    <div className="score-ring" style={{ width: size, height: size }}>
      <svg viewBox="0 0 120 120" role="img" aria-label={`Score ${score} out of 100`}>
        <circle cx="60" cy="60" r={radius} />
        <circle cx="60" cy="60" r={radius} style={{ stroke: tone, strokeDashoffset: offset }} />
      </svg>
      <div className="score-ring-label">
        <strong>{score}</strong>
        {caption && <span>{caption}</span>}
      </div>
    </div>
  );
}

export function Stat({ label, value, hint }: { label: string; value: ReactNode; hint?: string }) {
  return (
    <div className="stat">
      <p>{label}</p>
      <strong>{value}</strong>
      {hint && <span>{hint}</span>}
    </div>
  );
}
