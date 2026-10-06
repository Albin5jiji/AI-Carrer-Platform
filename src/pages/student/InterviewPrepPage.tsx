import { useState } from "react";
import { interviewApi } from "../../api/studentApi";
import { SectionCard, Tabs } from "../../components/ui/blocks";
import { ChipList, EmptyState, ErrorState, LoadingState, ProgressBar, StatusBadge } from "../../components/ui/primitives";
import { BarRow } from "../../components/ui/blocks";
import { useAction, useAsync } from "../../hooks/useAsync";
import { useToast } from "../../context/ToastContext";
import { formatDate, humanize } from "../../utils/format";
import type { InterviewCategory, PracticeStatus } from "../../types";

const PRACTICE_OPTIONS: PracticeStatus[] = ["not_started", "practiced", "needs_revision"];
const CATEGORY_TABS: { key: InterviewCategory | "all"; label: string }[] = [
  { key: "all", label: "All questions" },
  { key: "technical", label: "Technical" },
  { key: "behavioral", label: "Behavioural" },
  { key: "role_specific", label: "Role specific" },
];

export function InterviewPrepPage() {
  const toast = useToast();
  const [reloadKey, setReloadKey] = useState("0");
  const [tab, setTab] = useState<InterviewCategory | "all">("all");
  const overview = useAsync(() => interviewApi.overview(), reloadKey);
  const questions = useAsync(
    () => interviewApi.questions(tab === "all" ? {} : { category: tab }),
    `${reloadKey}-${tab}`,
  );
  const action = useAction();
  const [mock, setMock] = useState({ mode: "technical", score: "", strengths: "", improvements: "" });

  async function record(questionId: number, status: PracticeStatus, rating?: number) {
    const ok = await action.run(async () => {
      await interviewApi.recordPractice(questionId, { status, self_rating: rating ?? null });
      return "recorded";
    });
    if (ok) {
      toast.success("Practice recorded. Interview preparation is part of your readiness score.");
      setReloadKey(String(Date.now()));
    }
  }

  async function addMock() {
    const ok = await action.run(async () => {
      await interviewApi.addMock({
        mode: mock.mode,
        completed: mock.score !== "",
        score: mock.score === "" ? null : Number(mock.score),
        strengths: mock.strengths || null,
        improvements: mock.improvements || null,
      });
      return "recorded";
    });
    if (ok) {
      toast.success("Mock interview recorded.");
      setMock({ mode: "technical", score: "", strengths: "", improvements: "" });
      setReloadKey(String(Date.now()));
    }
  }

  if (overview.loading) return <LoadingState label="Loading interview preparation…" />;
  if (overview.error) return <ErrorState message={overview.error} onRetry={overview.reload} />;
  const data = overview.data;
  if (!data) return <EmptyState title="Interview preparation unavailable" />;

  return (
    <div className="page-grid">
      <SectionCard eyebrow="Interview preparation" title={`${data.progress_percent}% of relevant questions practised`}>
        <BarRow label="Interview readiness component" max={100} value={data.interview_component_score} />
        <div className="stat-grid">
          <div className="stat">
            <p>Questions available</p>
            <strong>{data.total_questions}</strong>
          </div>
          <div className="stat">
            <p>Practised</p>
            <strong>{data.practiced_count}</strong>
          </div>
          <div className="stat">
            <p>Needs revision</p>
            <strong>{data.needs_revision_count}</strong>
          </div>
          <div className="stat">
            <p>Average mock score</p>
            <strong>{data.average_mock_score ?? "—"}</strong>
          </div>
        </div>
        {action.error && <p className="form-error">{action.error}</p>}
      </SectionCard>

      <SectionCard eyebrow="Coverage" title="Progress by category">
        <div className="category-grid">
          {data.categories.map((category) => (
            <div className="category-card" key={category.category}>
              <div className="category-head">
                <span>{humanize(category.category)}</span>
                <StatusBadge value={`${category.progress_percent}%`} />
              </div>
              <ProgressBar tone="accent" value={category.progress_percent} />
              <p className="muted small">
                {category.practiced} practised · {category.needs_revision} need revision · {category.total} total
              </p>
            </div>
          ))}
        </div>
      </SectionCard>

      <SectionCard eyebrow="Practice questions" title="Build confidence one question at a time">
        <Tabs active={tab} onChange={setTab} tabs={CATEGORY_TABS} />
        {questions.loading && <LoadingState label="Loading questions…" />}
        {questions.error && <ErrorState message={questions.error} onRetry={questions.reload} />}
        {questions.data?.length === 0 && <EmptyState title="No questions available for this category" />}
        <div className="page-grid">
          {questions.data?.map((question) => (
            <article className="card" key={question.id}>
              <div className="card-head">
                <div>
                  <p className="eyebrow">{humanize(question.category)} · {humanize(question.difficulty)}</p>
                  <h4>{question.question}</h4>
                </div>
                <StatusBadge value={question.practice_status} />
              </div>
              {question.guidance && <p className="muted small">{question.guidance}</p>}
              <ChipList values={question.skill_tags} />
              <div className="roadmap-actions">
                <label className="inline-label">
                  Practice status
                  <select
                    disabled={action.pending}
                    onChange={(event) => void record(question.id, event.target.value as PracticeStatus, question.self_rating ?? undefined)}
                    value={question.practice_status}
                  >
                    {PRACTICE_OPTIONS.map((option) => <option key={option} value={option}>{humanize(option)}</option>)}
                  </select>
                </label>
              </div>
            </article>
          ))}
        </div>
      </SectionCard>

      <SectionCard eyebrow="Mock interview" title="Record a mock interview">
        <div className="form-grid">
          <label className="field"><span className="field-label">Mode</span><input onChange={(event) => setMock({ ...mock, mode: event.target.value })} value={mock.mode} /></label>
          <label className="field"><span className="field-label">Score (optional)</span><input max={100} min={0} onChange={(event) => setMock({ ...mock, score: event.target.value })} type="number" value={mock.score} /></label>
          <label className="field"><span className="field-label">Strengths</span><input onChange={(event) => setMock({ ...mock, strengths: event.target.value })} value={mock.strengths} /></label>
          <label className="field"><span className="field-label">Areas to improve</span><input onChange={(event) => setMock({ ...mock, improvements: event.target.value })} value={mock.improvements} /></label>
        </div>
        <div className="roadmap-actions"><button className="btn btn-primary btn-sm" disabled={action.pending} onClick={() => void addMock()} type="button">Save mock interview</button></div>
        {data.mock_interviews.length > 0 && (
          <div className="table-wrap"><table><thead><tr><th>Mode</th><th>Status</th><th>Score</th><th>Recorded</th></tr></thead><tbody>
            {data.mock_interviews.map((item) => <tr key={item.id}><td>{humanize(item.mode)}</td><td><StatusBadge value={item.completed ? "completed" : "scheduled"} /></td><td>{item.score ?? "—"}</td><td>{formatDate(item.created_at)}</td></tr>)}
          </tbody></table></div>
        )}
      </SectionCard>
    </div>
  );
}
