import { ArrowRight, Gauge, Sparkles, Target } from "lucide-react";
import { applicationApi, driveApi, learningApi, notificationApi, profileApi, readinessApi } from "../../api/studentApi";
import { KeyValue, KeyValueGrid, SectionCard } from "../../components/ui/blocks";
import { EmptyState, ErrorState, LoadingState, ScoreRing, Stat, StatusBadge } from "../../components/ui/primitives";
import { ComponentBarChart } from "../../components/charts/Charts";
import { useAsync } from "../../hooks/useAsync";
import { navigate } from "../../router/router";
import { formatDate } from "../../utils/format";

export function StudentDashboard() {
  const profile = useAsync(() => profileApi.me(), "dash-profile");
  const readiness = useAsync(() => readinessApi.me(), "dash-readiness");
  const gap = useAsync(() => readinessApi.skillGap(), "dash-gap");
  const path = useAsync(() => learningApi.path(), "dash-path");
  const applications = useAsync(() => applicationApi.mine(), "dash-applications");
  const drives = useAsync(() => driveApi.list(), "dash-drives");
  const eligibility = useAsync(() => driveApi.myEligibility(), "dash-eligibility");
  const notifications = useAsync(() => notificationApi.list({}), "dash-notifications");

  if (readiness.loading && profile.loading) return <LoadingState label="Loading your dashboard…" />;
  if (readiness.error) return <ErrorState message={readiness.error} onRetry={readiness.reload} />;

  const student = profile.data;
  const score = readiness.data;
  const applicationsList = applications.data ?? [];
  const openDrives = drives.data ?? [];
  const eligibilityById = new Map((eligibility.data ?? []).map((row) => [row.drive_id, row.eligibility]));
  const eligibleDrives = openDrives.filter((drive) => eligibilityById.get(drive.id)?.eligible);
  const activeApplications = applicationsList.filter((item) => item.status !== "withdrawn");

  return (
    <div className="page-grid">
      <SectionCard className="welcome-card">
        <div>
          <p className="eyebrow">Welcome back</p>
          <h3>{student?.full_name ?? "Student"}</h3>
          <p className="muted">
            {student?.program || "Program not set"} · Target role:{" "}
            <strong>{student?.target_role ?? "not selected"}</strong>
          </p>
          <div className="chip-row">
            <StatusBadge tone="info" value={`${student?.profile_completion ?? 0}% profile complete`} />
            {student?.cgpa != null && <StatusBadge tone="neutral" value={`CGPA ${student.cgpa}`} />}
            <StatusBadge
              tone={eligibleDrives.length ? "success" : "warning"}
              value={`${eligibleDrives.length} drive(s) eligible`}
            />
          </div>
        </div>
        <button className="btn btn-primary" onClick={() => navigate("/student/profile")} type="button">
          Update profile <ArrowRight size={16} />
        </button>
      </SectionCard>

      {score && (
        <SectionCard
          actions={
            <button className="btn btn-outline btn-sm" onClick={() => navigate("/student/readiness")} type="button">
              <Gauge size={15} /> Breakdown
            </button>
          }
          eyebrow="Personal Readiness Score"
          title={`${score.overall_score}/100 · ${score.level}`}
        >
          <div className="readiness-layout">
            <ScoreRing caption="out of 100" score={score.overall_score} />
            <div className="readiness-side">
              <KeyValueGrid>
                <KeyValue label="Target role" value={score.target_role ?? "Not selected"} />
                <KeyValue label="Last calculated" value={formatDate(score.computed_at)} />
                <KeyValue label="Skill coverage" value={`${gap.data?.coverage_percent ?? 0}%`} />
                <KeyValue label="Learning path" value={`${path.data?.completion_percent ?? 0}% complete`} />
              </KeyValueGrid>
              <div className="suggestion-box">
                <p className="eyebrow">
                  <Sparkles size={14} /> Recommended next action
                </p>
                <p>{score.suggestions[0] ?? "Keep your evidence current and apply to open drives."}</p>
              </div>
            </div>
          </div>

          <p className="disclaimer">{score.disclaimer}</p>
        </SectionCard>
      )}

      {score && (
        <div className="two-column">
          <SectionCard eyebrow="Score components" title="Six readiness components">
            <ComponentBarChart
              items={score.components.map((component) => ({ label: component.label, value: component.score }))}
            />
          </SectionCard>

          <SectionCard
            actions={
              <button className="btn btn-ghost btn-sm" onClick={() => navigate("/student/skill-gap")} type="button">
                <Target size={15} /> Details
              </button>
            }
            eyebrow="Skill gap"
            title={`${gap.data?.covered_skill_count ?? 0}/${gap.data?.required_skill_count ?? 0} target skills covered`}
          >
            {gap.loading && <LoadingState />}
            {gap.data && gap.data.items.filter((item) => item.status !== "covered").length === 0 && (
              <EmptyState title="No open skill gaps" description="Add a target role in your profile to analyse gaps." />
            )}
            <ul className="list">
              {gap.data?.items
                .filter((item) => item.status !== "covered")
                .slice(0, 6)
                .map((item) => (
                  <li key={item.skill_name}>
                    <div>
                      <strong>{item.skill_name}</strong>
                      <span className="muted">{item.action}</span>
                    </div>
                    <StatusBadge tone={item.priority === "high" ? "danger" : "warning"} value={item.priority} />
                  </li>
                ))}
            </ul>
          </SectionCard>
        </div>
      )}

      <div className="two-column">
        <SectionCard
          actions={
            <button className="btn btn-ghost btn-sm" onClick={() => navigate("/student/applications")} type="button">
              Tracker
            </button>
          }
          eyebrow="Applications"
          title={`${activeApplications.length} active application(s)`}
        >
          {applications.loading && <LoadingState />}
          {applicationsList.length === 0 && !applications.loading && (
            <EmptyState
              action={
                <button className="btn btn-primary btn-sm" onClick={() => navigate("/student/drives")} type="button">
                  Browse drives
                </button>
              }
              description="Apply to an open drive once your resume is approved."
              title="No applications yet"
            />
          )}
          <ul className="list">
            {applicationsList.slice(0, 5).map((application) => (
              <li key={application.id}>
                <div>
                  <strong>{application.company_name}</strong>
                  <span className="muted">{application.job_title ?? application.drive_name}</span>
                </div>
                <StatusBadge value={application.status} />
              </li>
            ))}
          </ul>
        </SectionCard>

        <SectionCard eyebrow="Deadlines" title="Open placement drives">
          {drives.loading && <LoadingState />}
          {openDrives.length === 0 && !drives.loading && <EmptyState title="No open drives right now" />}
          <ul className="list">
            {openDrives.slice(0, 5).map((drive) => (
              <li key={drive.id}>
                <div>
                  <strong>{drive.company_name}</strong>
                  <span className="muted">
                    {drive.name} · deadline {formatDate(drive.application_deadline)}
                  </span>
                </div>
                <StatusBadge
                  tone={eligibilityById.get(drive.id)?.eligible ? "success" : "warning"}
                  value={eligibilityById.get(drive.id)?.eligible ? "eligible" : "not eligible"}
                />
              </li>
            ))}
          </ul>
        </SectionCard>
      </div>

      <div className="two-column">
        <SectionCard eyebrow="Activity" title="Recent updates">
          {notifications.loading && <LoadingState />}
          {(notifications.data?.items.length ?? 0) === 0 && !notifications.loading && (
            <EmptyState title="Nothing new yet" description="Mentor feedback and updates appear here." />
          )}
          <ul className="list">
            {notifications.data?.items.slice(0, 5).map((item) => (
              <li key={item.id}>
                <div>
                  <strong>{item.title}</strong>
                  <span className="muted">{item.message}</span>
                </div>
                <span className="muted small">{formatDate(item.created_at)}</span>
              </li>
            ))}
          </ul>
        </SectionCard>

        <SectionCard eyebrow="Summary" title="At a glance">
          <div className="stat-grid">
            <Stat label="Skills" value={student?.skills.length ?? 0} />
            <Stat label="Projects" value={student?.projects.length ?? 0} />
            <Stat label="Certifications" value={student?.certifications.length ?? 0} />
            <Stat label="Open drives" value={openDrives.length} hint={`${eligibleDrives.length} eligible`} />
            <Stat label="Learning path" value={`${path.data?.completion_percent ?? 0}%`} />
            <Stat label="Applications" value={activeApplications.length} />
          </div>
        </SectionCard>
      </div>
    </div>
  );
}

