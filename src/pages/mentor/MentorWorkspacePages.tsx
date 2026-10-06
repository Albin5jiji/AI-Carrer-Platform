import { mentorApi } from "../../api/mentorApi";
import { SectionCard, KeyValue, KeyValueGrid } from "../../components/ui/blocks";
import { EmptyState, ErrorState, LoadingState, StatusBadge } from "../../components/ui/primitives";
import { useAction, useAsync } from "../../hooks/useAsync";
import { formatDate } from "../../utils/format";
import type { MentorStudentDetail, Resume } from "../../types";

export function MentorDashboardPage() { const data = useAsync(mentorApi.dashboard); if (data.loading) return <LoadingState />; if (data.error || !data.data) return <ErrorState message={data.error ?? "Dashboard unavailable"} onRetry={data.reload} />; const d = data.data; return <div className="page-grid"><SectionCard eyebrow="Mentor workspace" title={`Welcome, ${d.mentor_name}`}><KeyValueGrid><KeyValue label="Assigned students" value={d.assigned_student_count} /><KeyValue label="Pending resumes" value={d.pending_resume_reviews} /><KeyValue label="Pending applications" value={d.pending_application_reviews} /><KeyValue label="Average readiness" value={d.average_readiness ?? "—"} /></KeyValueGrid></SectionCard><SectionCard title="Students needing attention">{d.students_needing_attention.length ? d.students_needing_attention.map((s) => <p key={s.student_id}>{s.full_name} — {s.attention_reasons.join(", ")}</p>) : <EmptyState title="No students need attention" />}</SectionCard></div>; }
export function MentorStudentsPage() { const students = useAsync(mentorApi.students); if (students.loading) return <LoadingState />; if (students.error) return <ErrorState message={students.error} onRetry={students.reload} />; return <SectionCard eyebrow="Assigned students" title="Student progress">{students.data?.map((s) => <a className="card" href={`#/mentor/students/${s.student_id}`} key={s.student_id}><strong>{s.full_name}</strong><p className="muted">{s.target_role ?? "No target role"} · Readiness {s.overall_score ?? "—"}</p><StatusBadge value={s.needs_attention ? "action_needed" : "good"} /></a>)}</SectionCard>; }
export function MentorStudentDetailPage({ studentId }: { studentId: number }) { const data = useAsync(() => mentorApi.student(studentId), String(studentId)); return <MentorDetail data={data.data} loading={data.loading} error={data.error} />; }
function ParsedResume({ resume }: { resume: Resume }) {
  const sections = Object.entries(resume.content ?? {}).filter(([, items]) => items?.length);
  return sections.length ? <div className="parsed-preview"><p className="eyebrow">Parsed from submitted PDF</p>{sections.map(([section, items]) => <div key={section}><strong>{section}</strong><span>{items?.slice(0, 3).join(" · ")}</span></div>)}</div> : <p className="muted small">No structured details were extracted from this PDF.</p>;
}
function ResumeFileButton({ resumeId }: { resumeId: number }) {
  const action = useAction();
  const open = async () => {
    // Open synchronously during the click so popup blockers allow the PDF tab.
    const pdfWindow = window.open("about:blank", "_blank");
    if (!pdfWindow) {
      action.setError("Your browser blocked the PDF tab. Allow pop-ups for this site and try again.");
      return;
    }
    pdfWindow.opener = null;
    const result = await action.run(() => mentorApi.resumeDownloadUrl(resumeId));
    if (result && typeof result !== "boolean") {
      pdfWindow.location.href = result.download_url;
    } else {
      pdfWindow.close();
    }
  };
  return <><button className="btn btn-ghost btn-sm" disabled={action.pending} onClick={() => void open()} type="button">View PDF</button>{action.error && <span className="muted small" role="alert">{action.error}</span>}</>;
}
function MentorDetail({ data, loading, error }: { data: MentorStudentDetail | undefined; loading: boolean; error: string | null }) {
  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;
  if (!data) return <EmptyState title="Student unavailable" />;
  return <div className="page-grid">
    <SectionCard title={data.student.full_name} eyebrow={data.student.registration_number}>
      <KeyValueGrid>
        <KeyValue label="Readiness" value={data.student.overall_score ?? "—"} />
        <KeyValue label="Skill coverage" value={`${data.skill_coverage_percent}%`} />
        <KeyValue label="Target role" value={data.student.target_role} />
      </KeyValueGrid>
    </SectionCard>
    <SectionCard title="Skills">
      <p>{data.skills.join(", ") || "No skills recorded"}</p>
      <p className="muted">Missing: {data.missing_skills.join(", ") || "None"}</p>
    </SectionCard>
    <SectionCard title="Resume versions">
      {data.resumes.length ? data.resumes.map((r) => <article className="card" key={r.id}>
        <div className="card-head"><strong>{r.version_name}</strong><StatusBadge value={r.status} /></div>
        <ParsedResume resume={r} />
        {r.file_url?.startsWith("s3://") && <div className="roadmap-actions"><ResumeFileButton resumeId={r.id} /></div>}
      </article>) : <EmptyState title="No resume versions" />}
    </SectionCard>
  </div>;
}
export function MentorResumeReviewsPage() {
  const data = useAsync(mentorApi.pendingResumes);
  const action = useAction();
  if (data.loading) return <LoadingState />;
  if (data.error) return <ErrorState message={data.error} onRetry={data.reload} />;

  const review = async (id: number, actionName: "approve" | "request_changes") => {
    let feedback: string | undefined;
    if (actionName === "request_changes") {
      const entered = window.prompt("What should the student change in this resume?");
      if (entered === null) return;
      feedback = entered.trim();
      if (!feedback) {
        action.setError("Add feedback explaining the requested changes.");
        return;
      }
    }
    const ok = await action.run(() => mentorApi.reviewResume(id, { action: actionName, feedback }));
    if (ok) data.reload();
  };

  return <SectionCard title="Pending resume reviews">
    {data.data?.length === 0 && <EmptyState title="No pending resumes" />}
    {data.data?.map((r) => <div className="card" key={r.id}>
      <div className="card-head"><strong>{r.version_name}</strong><StatusBadge value={r.status} /></div>
      <ParsedResume resume={r} />
      <div className="roadmap-actions">
        {r.file_url?.startsWith("s3://") && <ResumeFileButton resumeId={r.id} />}
        <button className="btn btn-primary btn-sm" disabled={action.pending} onClick={() => void review(r.id, "approve")} type="button">Approve</button>
        <button className="btn btn-outline btn-sm" disabled={action.pending} onClick={() => void review(r.id, "request_changes")} type="button">Request changes</button>
        {action.error && <span className="form-error" role="alert">{action.error}</span>}
      </div>
    </div>)}
  </SectionCard>;
}
export function MentorApplicationReviewsPage() { const data = useAsync(mentorApi.pendingApplications); const action = useAction(); const decide = (id: number, actionName: "approve" | "request_changes") => void action.run(() => mentorApi.decideApplication(id, { action: actionName })); if (data.loading) return <LoadingState />; if (data.error) return <ErrorState message={data.error} />; return <SectionCard title="Pending application reviews">{data.data?.map((a) => <div className="card" key={a.id}><strong>{a.drive_name ?? a.code}</strong><p>{a.student_name ?? "Student"}</p><button className="btn btn-primary btn-sm" onClick={() => decide(a.id, "approve")} type="button">Approve</button></div>) || <EmptyState title="No pending applications" />}</SectionCard>; }
export function MentorFeedbackPage() { const data = useAsync(mentorApi.feedback); if (data.loading) return <LoadingState />; if (data.error) return <ErrorState message={data.error} />; return <SectionCard title="Feedback history">{data.data?.length ? data.data.map((f) => <article className="card" key={f.id}><strong>{f.title}</strong><p>{f.body}</p><p className="muted">{f.student_name} · {formatDate(f.created_at)}</p></article>) : <EmptyState title="No feedback yet" />}</SectionCard>; }
