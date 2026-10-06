import { useState } from "react";
import { Ban, Send } from "lucide-react";
import { applicationApi } from "../../api/studentApi";
import { SectionCard } from "../../components/ui/blocks";
import { EmptyState, ErrorState, LoadingState, StatusBadge } from "../../components/ui/primitives";
import { useAction, useAsync } from "../../hooks/useAsync";
import { useToast } from "../../context/ToastContext";
import { navigate } from "../../router/router";
import { formatDateTime } from "../../utils/format";

export function StudentApplicationsPage() {
  const toast = useToast();
  const [reloadKey, setReloadKey] = useState("0");
  const applications = useAsync(() => applicationApi.mine(), reloadKey);
  const action = useAction();

  async function withdraw(id: number) {
    const ok = await action.run(async () => {
      await applicationApi.withdraw(id);
      return "withdrawn";
    });
    if (ok) {
      toast.success("Application withdrawn.");
      setReloadKey(String(Date.now()));
    }
  }

  if (applications.loading) return <LoadingState label="Loading your applications…" />;
  if (applications.error) return <ErrorState message={applications.error} onRetry={applications.reload} />;
  const rows = applications.data ?? [];

  return (
    <div className="page-grid">
      <SectionCard
        actions={
          <button className="btn btn-outline btn-sm" onClick={() => navigate("/student/drives")} type="button">
            <Send size={15} /> Browse drives
          </button>
        }
        eyebrow="Application tracker"
        title={`${rows.length} application(s)`}
      >
        {action.error && <p className="form-error">{action.error}</p>}
        {rows.length === 0 && (
          <EmptyState
            description="Apply to an open placement drive once your resume is approved by a mentor."
            title="No applications yet"
          />
        )}

        {rows.length > 0 && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Application</th>
                  <th>Company / Role</th>
                  <th>Resume</th>
                  <th>Eligibility</th>
                  <th>Status</th>
                  <th>Next action</th>
                  <th>Updated</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {rows.map((application) => {
                  const canWithdraw = !["selected", "rejected", "withdrawn"].includes(application.status);
                  return (
                    <tr key={application.id}>
                      <td>
                        <strong>{application.code}</strong>
                      </td>
                      <td>
                        <strong>{application.company_name}</strong>
                        <span className="muted small block">
                          {application.job_title ?? application.drive_name}
                        </span>
                      </td>
                      <td>{application.resume_version_name ?? "—"}</td>
                      <td>
                        <StatusBadge value={application.eligibility_status} />
                      </td>
                      <td>
                        <StatusBadge value={application.status} />
                      </td>
                      <td className="muted small">{application.next_action}</td>
                      <td className="muted small">{formatDateTime(application.updated_at)}</td>
                      <td>
                        {canWithdraw && (
                          <button
                            className="btn btn-ghost btn-sm"
                            disabled={action.pending}
                            onClick={() => void withdraw(application.id)}
                            type="button"
                          >
                            <Ban size={14} /> Withdraw
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </SectionCard>

      <SectionCard eyebrow="Pipeline" title="Where each application stands">
        <div className="stage-grid">
          {["pending_mentor_approval", "changes_requested", "approved", "submitted", "shortlisted", "interview_scheduled", "selected", "rejected"].map(
            (stage) => {
              const count = rows.filter((row) => row.status === stage).length;
              return (
                <div className={count ? "stage-card active" : "stage-card"} key={stage}>
                  <span>{stage.replaceAll("_", " ")}</span>
                  <strong>{count}</strong>
                </div>
              );
            },
          )}
        </div>
      </SectionCard>

      {rows.some((row) => row.mentor_feedback) && (
        <SectionCard eyebrow="Mentor feedback" title="Notes on your applications">
          <ul className="list">
            {rows
              .filter((row) => row.mentor_feedback)
              .map((row) => (
                <li key={`feedback-${row.id}`}>
                  <div>
                    <strong>
                      {row.company_name} · {row.code}
                    </strong>
                    <span className="muted">{row.mentor_feedback}</span>
                  </div>
                  <StatusBadge value={row.status} />
                </li>
              ))}
          </ul>
        </SectionCard>
      )}
    </div>
  );
}
