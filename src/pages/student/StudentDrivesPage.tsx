import { useState } from "react";
import { CheckCircle2, Info, Send } from "lucide-react";
import { applicationApi, driveApi, resumeApi } from "../../api/studentApi";
import { KeyValue, KeyValueGrid, SectionCard } from "../../components/ui/blocks";
import { Alert, EmptyState, ErrorState, LoadingState, StatusBadge } from "../../components/ui/primitives";
import { useAction, useAsync } from "../../hooks/useAsync";
import { useToast } from "../../context/ToastContext";
import { formatDate } from "../../utils/format";

export function StudentDrivesPage() {
  const toast = useToast();
  const [reloadKey, setReloadKey] = useState("0");
  const drives = useAsync(() => driveApi.list(), reloadKey);
  const eligibility = useAsync(() => driveApi.myEligibility(), reloadKey);
  const resumes = useAsync(() => resumeApi.list(), "resumes");
  const action = useAction();
  const [selectedResume, setSelectedResume] = useState<Record<number, number | undefined>>({});

  const eligibilityById = new Map((eligibility.data ?? []).map((row) => [row.drive_id, row.eligibility]));
  const approvedResumes = (resumes.data ?? []).filter((resume) => resume.status === "approved");

  async function apply(driveId: number) {
    const ok = await action.run(async () => {
      await applicationApi.apply({
        drive_id: driveId,
        resume_id: selectedResume[driveId] ?? approvedResumes[0]?.id ?? null,
      });
      return "applied";
    });
    if (ok) {
      toast.success("Application submitted. Your mentor will review it next.");
      setReloadKey(String(Date.now()));
    }
  }

  if (drives.loading) return <LoadingState label="Loading placement drives…" />;
  if (drives.error) return <ErrorState message={drives.error} onRetry={drives.reload} />;
  const rows = drives.data ?? [];

  return (
    <div className="page-grid">
      <SectionCard eyebrow="Placement drives" title={`${rows.length} open drive(s)`}>
        {action.error && <p className="form-error">{action.error}</p>}
        {approvedResumes.length === 0 && (
          <Alert tone="warning">
            You do not have an approved resume version yet. Create a resume and submit it for mentor review before
            applying.
          </Alert>
        )}
        {rows.length === 0 && (
          <EmptyState
            description="The placement cell has not published an open drive yet. Check back soon."
            title="No open drives"
          />
        )}
      </SectionCard>

      <div className="card-grid">
        {rows.map((drive) => {
          const result = eligibilityById.get(drive.id);
          const eligible = Boolean(result?.eligible);
          const alreadyApplied = Boolean(result?.already_applied);
          return (
            <SectionCard key={drive.id} className="drive-card">
              <div className="drive-head">
                <div>
                  <p className="eyebrow">{drive.company_name}</p>
                  <h3>{drive.job_title ?? drive.name}</h3>
                  <p className="muted small">{drive.name}</p>
                </div>
                <StatusBadge value={drive.status} />
              </div>

              <KeyValueGrid>
                <KeyValue label="Location" value={drive.location} />
                <KeyValue label="Minimum CGPA" value={drive.min_cgpa ?? "No minimum"} />
                <KeyValue label="Deadline" value={formatDate(drive.application_deadline)} />
                <KeyValue label="Drive date" value={formatDate(drive.drive_date)} />
                <KeyValue label="Departments" value={drive.eligible_departments.join(", ") || "All"} />
                <KeyValue label="Graduation years" value={drive.graduation_years.join(", ") || "All"} />
              </KeyValueGrid>

              <div className="chip-row">
                {drive.required_skills.length > 0 ? (
                  drive.required_skills.map((skill) => (
                    <span className="chip" key={skill}>
                      {skill}
                    </span>
                  ))
                ) : (
                  <span className="muted small">No specific skills listed</span>
                )}
              </div>

              <div className="eligibility-box">
                <p className="eyebrow">
                  {eligible ? <CheckCircle2 size={14} /> : <Info size={14} />} Eligibility
                </p>
                <StatusBadge value={result?.status ?? "unknown"} />
                {result?.reasons.length ? (
                  <ul className="list compact-list">
                    {result.reasons.map((reason) => (
                      <li key={reason}>
                        <span className="muted small">{reason}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="muted small">You meet every criterion for this drive.</p>
                )}
              </div>

              <div className="drive-actions">
                {approvedResumes.length > 0 && !alreadyApplied && eligible && (
                  <label className="inline-label">
                    Resume version
                    <select
                      onChange={(event) =>
                        setSelectedResume((current) => ({ ...current, [drive.id]: Number(event.target.value) }))
                      }
                      value={selectedResume[drive.id] ?? approvedResumes[0]?.id}
                    >
                      {approvedResumes.map((resume) => (
                        <option key={resume.id} value={resume.id}>
                          {resume.version_name}
                        </option>
                      ))}
                    </select>
                  </label>
                )}
                <button
                  className="btn btn-primary btn-sm"
                  disabled={!eligible || alreadyApplied || action.pending}
                  onClick={() => void apply(drive.id)}
                  type="button"
                >
                  <Send size={15} />
                  {alreadyApplied ? "Already applied" : eligible ? "Apply to drive" : "Not eligible"}
                </button>
              </div>
            </SectionCard>
          );
        })}
      </div>
    </div>
  );
}
