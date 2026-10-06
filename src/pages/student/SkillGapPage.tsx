import { ArrowRight, Sparkles, Target } from "lucide-react";
import { useState } from "react";
import { ApiError } from "../../api/client";
import { readinessApi } from "../../api/studentApi";
import { KeyValue, KeyValueGrid, SectionCard } from "../../components/ui/blocks";
import { Alert, ChipList, EmptyState, ErrorState, LoadingState, ProgressBar, StatusBadge } from "../../components/ui/primitives";
import { useAsync } from "../../hooks/useAsync";
import { navigate } from "../../router/router";
import type { AISkillGapAnalysis } from "../../types";

export function SkillGapPage() {
  const [reloadKey, setReloadKey] = useState("0");
  const [aiAnalysis, setAiAnalysis] = useState<AISkillGapAnalysis | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState("");
  const gap = useAsync(() => readinessApi.skillGap(), reloadKey);

  async function generateAiAnalysis() {
    setAiLoading(true);
    setAiError("");
    try {
      setAiAnalysis(await readinessApi.aiSkillGap());
    } catch (caught) {
      setAiAnalysis(null);
      if (caught instanceof ApiError) {
        if (caught.status === 401) setAiError("Your session has expired. Please sign in again.");
        else if (caught.status === 422) setAiError("The AI response could not be validated. Please try again.");
        else if (caught.status === 503) {
          setAiError("AI recommendations are temporarily unavailable. No previous validated recommendation is available.");
        } else setAiError(caught.message);
      } else {
        setAiError("AI recommendations could not be loaded. Please try again.");
      }
    } finally {
      setAiLoading(false);
    }
  }

  if (gap.loading) return <LoadingState label="Analysing your skill gap…" />;
  if (gap.error) return <ErrorState message={gap.error} onRetry={gap.reload} />;
  const data = gap.data;
  if (!data) return <EmptyState title="Skill gap unavailable" />;

  return (
    <div className="page-grid">
      <SectionCard
        actions={
          <button className="btn btn-outline btn-sm" onClick={() => setReloadKey(String(Date.now()))} type="button">
            <Target size={15} /> Recalculate
          </button>
        }
        eyebrow="Skill gap analysis"
        title={`Target role: ${data.target_role}`}
      >
        <KeyValueGrid>
          <KeyValue label="Required skills" value={data.required_skill_count} />
          <KeyValue label="Covered" value={data.covered_skill_count} />
          <KeyValue label="Missing or partial" value={data.missing_skill_count} />
          <KeyValue label="Skills component score" value={`${data.skills_component_score}/100`} />
        </KeyValueGrid>

        <div className="gap-coverage">
          <ProgressBar tone="accent" value={data.coverage_percent} />
          <span className="muted small">{data.coverage_percent}% of required skills are at the target level</span>
        </div>

        {!data.has_role_data && (
          <EmptyState
            action={
              <button className="btn btn-primary btn-sm" onClick={() => navigate("/student/profile")} type="button">
                Select a target role <ArrowRight size={15} />
              </button>
            }
            title="No target role selected"
            description="Choose a target role in your profile to compare your skills with real role requirements."
          />
        )}
      </SectionCard>

      {data.has_role_data && (
        <SectionCard eyebrow="Requirements" title="Required skills for your target role">
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Skill</th>
                  <th>Priority</th>
                  <th>Your level</th>
                  <th>Target level</th>
                  <th>Status</th>
                  <th>Next step</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((item) => (
                  <tr key={item.skill_name}>
                    <td>
                      <strong>{item.skill_name}</strong>
                    </td>
                    <td>
                      <StatusBadge
                        tone={item.priority === "high" ? "danger" : item.priority === "medium" ? "warning" : "neutral"}
                        value={item.priority}
                      />
                    </td>
                    <td>{item.current_proficiency ?? "not recorded"}</td>
                    <td>{item.target_proficiency}</td>
                    <td>
                      <StatusBadge value={item.status} />
                    </td>
                    <td className="muted">{item.action}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </SectionCard>
      )}

      <SectionCard
        actions={
          <button className="btn btn-primary btn-sm" disabled={aiLoading} onClick={generateAiAnalysis} type="button">
            <Sparkles size={15} /> {aiLoading ? "Generating…" : "Generate AI Skill Gap Analysis"}
          </button>
        }
        eyebrow="AI advisory"
        title="AI Skill Gap Analysis"
      >
        <Alert tone="info">
          This is advisory guidance generated from your profile and target-role data. The deterministic skill gap above
          remains authoritative for role requirements, readiness, and eligibility.
        </Alert>
        {aiError && <Alert tone={aiError.includes("temporarily unavailable") ? "warning" : "error"}>{aiError}</Alert>}
        {aiLoading && <LoadingState label="Generating validated AI guidance…" />}
        {aiAnalysis && !aiLoading && (
          <div className="page-grid">
            {aiAnalysis.outdated && (
              <Alert tone="warning">
                Showing the most recent validated recommendation because a new AI generation was unavailable. This result
                is outdated.
              </Alert>
            )}
            <div className="two-column">
              <div>
                <p className="eyebrow">Strengths</p>
                <ChipList empty="No profile-supported strengths returned" values={aiAnalysis.strengths} />
              </div>
              <div>
                <p className="eyebrow">Missing skills</p>
                <ChipList empty="No validated missing skills returned" values={aiAnalysis.missing_skills} />
              </div>
            </div>
            <div>
              <p className="eyebrow">Recommendations</p>
              {aiAnalysis.recommendations.length > 0 ? (
                <ul className="list bullet-list">
                  {aiAnalysis.recommendations.map((recommendation) => <li key={recommendation}>{recommendation}</li>)}
                </ul>
              ) : (
                <p className="muted">No validated recommendations returned.</p>
              )}
            </div>
            <div>
              <p className="eyebrow">Explanation</p>
              <p>{aiAnalysis.explanation}</p>
            </div>
          </div>
        )}
      </SectionCard>

      <div className="two-column">
        <SectionCard eyebrow="Covered" title="Skills at or above the target level">
          {data.items.filter((item) => item.status === "covered").length === 0 && (
            <EmptyState title="Nothing covered yet" description="Add your strongest skills to your profile." />
          )}
          <ul className="list">
            {data.items
              .filter((item) => item.status === "covered")
              .map((item) => (
                <li key={item.skill_name}>
                  <div>
                    <strong>{item.skill_name}</strong>
                    <span className="muted">{item.action}</span>
                  </div>
                  <StatusBadge value="covered" />
                </li>
              ))}
          </ul>
        </SectionCard>

        <SectionCard
          actions={
            <button className="btn btn-ghost btn-sm" onClick={() => navigate("/student/learning")} type="button">
              Learning path
            </button>
          }
          eyebrow="Gaps"
          title="Skills to build next"
        >
          {data.items.filter((item) => item.status !== "covered").length === 0 && (
            <EmptyState title="No open gaps" description="Every required skill is covered for this role." />
          )}
          <ul className="list">
            {data.items
              .filter((item) => item.status !== "covered")
              .map((item) => (
                <li key={item.skill_name}>
                  <div>
                    <strong>{item.skill_name}</strong>
                    <span className="muted">{item.action}</span>
                  </div>
                  <StatusBadge value={item.status} />
                </li>
              ))}
          </ul>
        </SectionCard>
      </div>
    </div>
  );
}
