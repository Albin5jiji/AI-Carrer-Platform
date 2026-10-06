import { useState } from "react";
import { RefreshCw, Sparkles } from "lucide-react";
import { readinessApi } from "../../api/studentApi";
import { SectionCard, BarRow, KeyValue, KeyValueGrid } from "../../components/ui/blocks";
import { ErrorState, LoadingState, ScoreRing, StatusBadge } from "../../components/ui/primitives";
import { ComponentBarChart, TrendChart } from "../../components/charts/Charts";
import { useAction, useAsync } from "../../hooks/useAsync";
import { useToast } from "../../context/ToastContext";
import { formatDate, formatDateTime, scoreTone } from "../../utils/format";

export function StudentReadinessPage() {
  const toast = useToast();
  const [reloadKey, setReloadKey] = useState("0");
  const readiness = useAsync(() => readinessApi.me(), reloadKey);
  const weights = useAsync(() => readinessApi.weights(), "weights");
  const history = useAsync(() => readinessApi.history(), "history");
  const action = useAction();

  async function recalculate() {
    const ok = await action.run(async () => {
      await readinessApi.me();
      return "Readiness score recalculated";
    });
    if (ok) {
      toast.success("Readiness score recalculated and a history snapshot was stored.");
      setReloadKey(String(Date.now()));
    }
  }

  if (readiness.loading) return <LoadingState label="Calculating your readiness score…" />;
  if (readiness.error) return <ErrorState message={readiness.error} onRetry={readiness.reload} />;
  const data = readiness.data;
  if (!data) return <ErrorState message="Readiness score unavailable" onRetry={readiness.reload} />;

  const snapshots = history.data?.snapshots ?? [];

  return (
    <div className="page-grid">
      <SectionCard className="readiness-hero">
        <div className="readiness-layout">
          <ScoreRing caption="out of 100" score={data.overall_score} size={168} />
          <div className="readiness-side">
            <p className="eyebrow">Personal Readiness Score</p>
            <h3>
              {data.overall_score}/100 · {data.level}
            </h3>
            <KeyValueGrid>
              <KeyValue label="Target role" value={data.target_role ?? "Not selected"} />
              <KeyValue label="Last calculated" value={formatDateTime(data.computed_at)} />
              <KeyValue
                label="Change vs previous"
                value={
                  history.data?.change === null || history.data?.change === undefined
                    ? "No previous snapshot"
                    : `${history.data.change > 0 ? "+" : ""}${history.data.change}`
                }
              />
              <KeyValue label="Snapshots stored" value={history.data?.snapshot_count ?? 0} />
            </KeyValueGrid>
            <button className="btn btn-primary" disabled={action.pending} onClick={recalculate} type="button">
              <RefreshCw size={16} /> {action.pending ? "Recalculating…" : "Recalculate score"}
            </button>
            {action.error && <p className="form-error">{action.error}</p>}
          </div>
        </div>
      </SectionCard>

      <SectionCard eyebrow="Components" title="Six weighted components">
        <ComponentBarChart
          items={data.components.map((component) => ({ label: `${component.label} (${component.weight}%)`, value: component.score }))}
        />
        <div className="component-list">
          {data.components.map((component) => (
            <div className="component-row" key={component.key}>
              <div>
                <strong>{component.label}</strong>
                <p className="muted">{component.explanation}</p>
              </div>
              <div className="component-row-value">
                <StatusBadge tone={scoreTone(component.score)} value={`${component.score}/100`} />
                <span className="muted small">
                  {component.weighted_points} of {component.weight} weighted points
                </span>
              </div>
            </div>
          ))}
        </div>
        <p className="disclaimer">{data.disclaimer}</p>
      </SectionCard>

      <div className="two-column">
        <SectionCard eyebrow="Improvement" title="Suggested next actions">
          <ul className="list bullet-list">
            {data.suggestions.map((suggestion) => (
              <li key={suggestion}>
                <Sparkles size={15} />
                <span>{suggestion}</span>
              </li>
            ))}
          </ul>
        </SectionCard>

        <SectionCard eyebrow="Formula" title="How the score is calculated">
          {(weights.data?.weights ?? data.components.reduce<Record<string, number>>((acc, item) => ({ ...acc, [item.key]: item.weight }), {})) &&
            Object.entries(
              weights.data?.weights ??
                data.components.reduce<Record<string, number>>((acc, item) => ({ ...acc, [item.key]: item.weight }), {}),
            ).map(([key, weight]) => <BarRow key={key} label={key} max={40} suffix="%" value={weight} />)}
          <p className="muted small">
            Each component is normalised to a 0–100 scale, multiplied by its weight and summed. The weights total{" "}
            {weights.data?.total ?? 100}.
          </p>
        </SectionCard>
      </div>

      <SectionCard eyebrow="History" title="Score over time">
        <TrendChart
          max={100}
          points={snapshots.map((snapshot) => ({
            label: formatDate(snapshot.computed_at),
            value: snapshot.overall_score,
          }))}
          title="Overall readiness score by calculation date"
        />
      </SectionCard>
    </div>
  );
}
