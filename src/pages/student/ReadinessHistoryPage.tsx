import { useState } from "react";
import { RefreshCw } from "lucide-react";
import { readinessApi } from "../../api/studentApi";
import { KeyValue, KeyValueGrid, SectionCard } from "../../components/ui/blocks";
import { EmptyState, ErrorState, LoadingState, StatusBadge } from "../../components/ui/primitives";
import { ComponentBarChart, TrendChart } from "../../components/charts/Charts";
import { useAction, useAsync } from "../../hooks/useAsync";
import { useToast } from "../../context/ToastContext";
import { formatDate, formatDateTime } from "../../utils/format";

const COMPONENTS = ["academics", "skills", "projects", "certifications", "resume", "interview"] as const;

export function ReadinessHistoryPage() {
  const toast = useToast();
  const [reloadKey, setReloadKey] = useState("0");
  const history = useAsync(() => readinessApi.history(), reloadKey);
  const action = useAction();

  async function snapshot() {
    const ok = await action.run(async () => {
      await readinessApi.me();
      return "snapshot";
    });
    if (ok) {
      toast.success("New snapshot stored. History updated.");
      setReloadKey(String(Date.now()));
    }
  }

  if (history.loading) return <LoadingState label="Loading readiness history…" />;
  if (history.error) return <ErrorState message={history.error} onRetry={history.reload} />;
  const data = history.data;
  if (!data) return <EmptyState title="Readiness history unavailable" />;

  const latest = data.snapshots[data.snapshots.length - 1];

  return (
    <div className="page-grid">
      <SectionCard
        actions={
          <button className="btn btn-outline btn-sm" disabled={action.pending} onClick={snapshot} type="button">
            <RefreshCw size={15} /> Store new snapshot
          </button>
        }
        eyebrow="Readiness history"
        title={`${data.snapshot_count} snapshot(s) recorded`}
      >
        <KeyValueGrid>
          <KeyValue label="Latest score" value={data.latest_score ?? "—"} />
          <KeyValue label="Previous score" value={data.previous_score ?? "—"} />
          <KeyValue
            label="Change"
            value={data.change === null ? "Not enough history" : `${data.change > 0 ? "+" : ""}${data.change}`}
          />
          <KeyValue label="Target role" value={data.target_role ?? "Not selected"} />
        </KeyValueGrid>
        {action.error && <p className="form-error">{action.error}</p>}
      </SectionCard>

      <SectionCard eyebrow="Trend" title="Overall score over time">
        <TrendChart
          points={data.snapshots.map((item) => ({
            label: formatDate(item.computed_at),
            value: item.overall_score,
          }))}
          title="Overall readiness score per calculation"
        />
      </SectionCard>

      {latest && (
        <SectionCard eyebrow="Latest calculation" title={`Component scores (${formatDate(latest.computed_at)})`}>
          <ComponentBarChart
            items={COMPONENTS.map((key) => ({ label: key, value: latest[key] }))}
          />
        </SectionCard>
      )}

      <div className="two-column">
        <SectionCard eyebrow="Timeline" title="Improvement timeline">
          {data.improvement_timeline.length === 0 && <EmptyState title="No timeline entries yet" />}
          <ul className="list bullet-list">
            {data.improvement_timeline.map((entry) => (
              <li key={entry}>
                <span>{entry}</span>
              </li>
            ))}
          </ul>
        </SectionCard>

        <SectionCard eyebrow="Snapshots" title="Calculation history">
          {data.snapshots.length === 0 && (
            <EmptyState
              description="Each recalculation stores a snapshot so you can track progress."
              title="No history yet"
            />
          )}
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Overall</th>
                  <th>Skills</th>
                  <th>Projects</th>
                  <th>Resume</th>
                  <th>Interview</th>
                </tr>
              </thead>
              <tbody>
                {data.snapshots
                  .slice()
                  .reverse()
                  .map((snapshot) => (
                    <tr key={snapshot.id}>
                      <td>{formatDateTime(snapshot.computed_at)}</td>
                      <td>
                        <StatusBadge
                          tone={snapshot.overall_score >= 70 ? "success" : snapshot.overall_score >= 50 ? "warning" : "danger"}
                          value={String(snapshot.overall_score)}
                        />
                      </td>
                      <td>{snapshot.skills}</td>
                      <td>{snapshot.projects}</td>
                      <td>{snapshot.resume}</td>
                      <td>{snapshot.interview}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </SectionCard>
      </div>
    </div>
  );
}
