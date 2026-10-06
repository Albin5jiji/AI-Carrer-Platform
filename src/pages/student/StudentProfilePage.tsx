import { useState } from "react";
import type { FormEvent } from "react";
import { Save } from "lucide-react";
import { profileApi } from "../../api/studentApi";
import { Field, SectionCard } from "../../components/ui/blocks";
import { EmptyState, ErrorState, LoadingState, ProgressBar, StatusBadge } from "../../components/ui/primitives";
import { SkillsPanel } from "../../components/student/SkillsPanel";
import { ProjectsPanel } from "../../components/student/ProjectsPanel";
import { CertificationsPanel } from "../../components/student/CertificationsPanel";
import { useAction, useAsync } from "../../hooks/useAsync";
import { useToast } from "../../context/ToastContext";
import { listToText, textToList } from "../../utils/format";

export function StudentProfilePage() {
  const toast = useToast();
  const [reloadKey, setReloadKey] = useState("0");
  const profile = useAsync(() => profileApi.me(), reloadKey);
  const roles = useAsync(() => profileApi.roles(), "roles");
  const action = useAction();
  const refresh = () => setReloadKey(String(Date.now()));

  async function saveProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const text = (key: string) => String(form.get(key) ?? "").trim() || null;
    const number = (key: string) => (text(key) === null ? null : Number(text(key)));

    const ok = await action.run(async () => {
      await profileApi.update({
        program: text("program"),
        degree: text("degree"),
        department: text("department"),
        graduation_year: number("graduation_year"),
        cgpa: number("cgpa"),
        phone: text("phone"),
        location: text("location"),
        bio: text("bio"),
        target_role: text("target_role"),
        career_interests: textToList(String(form.get("career_interests") ?? "")),
        preferred_locations: textToList(String(form.get("preferred_locations") ?? "")),
        github_url: text("github_url"),
        linkedin_url: text("linkedin_url"),
        portfolio_url: text("portfolio_url"),
      });
      return "Profile updated";
    });

    if (ok) {
      toast.success("Profile saved. Readiness, skill gap and learning path were recomputed.");
      refresh();
    }
  }

  if (profile.loading) return <LoadingState label="Loading your profile…" />;
  if (profile.error) return <ErrorState message={profile.error} onRetry={profile.reload} />;
  const student = profile.data;
  if (!student) return <EmptyState title="Profile unavailable" />;

  return (
    <div className="page-grid">
      <SectionCard className="profile-head">
        <div>
          <p className="eyebrow">Student profile</p>
          <h3>{student.full_name}</h3>
          <p className="muted">
            {student.registration_number} · {student.program} · {student.email}
          </p>
          <div className="chip-row">
            <StatusBadge tone="info" value={`${student.profile_completion}% complete`} />
            <StatusBadge
              tone={student.target_role ? "success" : "warning"}
              value={student.target_role ?? "no target role"}
            />
          </div>
        </div>
        <div className="profile-completion">
          <ProgressBar tone="gold" value={student.profile_completion} />
          <span className="muted small">Completion drives mentor visibility and scoring accuracy.</span>
        </div>
      </SectionCard>

      <SectionCard eyebrow="Academic, links and targets" title="Edit your profile">
        {action.error && <p className="form-error">{action.error}</p>}
        <form className="form-grid" onSubmit={saveProfile}>
          <Field label="Program">
            <input defaultValue={student.program} name="program" />
          </Field>
          <Field label="Degree">
            <input defaultValue={student.degree ?? ""} name="degree" placeholder="B.Tech" />
          </Field>
          <Field label="Department">
            <input defaultValue={student.department ?? ""} name="department" placeholder="CSE" />
          </Field>
          <Field label="Graduation year">
            <input
              defaultValue={student.graduation_year ?? ""}
              max="2100"
              min="2000"
              name="graduation_year"
              type="number"
            />
          </Field>
          <Field label="CGPA" hint="Ten point scale, used by the academics component">
            <input defaultValue={student.cgpa ?? ""} max="10" min="0" name="cgpa" step="0.01" type="number" />
          </Field>
          <Field label="Phone">
            <input defaultValue={student.phone ?? ""} name="phone" />
          </Field>
          <Field label="Location">
            <input defaultValue={student.location ?? ""} name="location" />
          </Field>
          <Field label="Target role" hint="Drives the readiness score and skill gap">
            <select defaultValue={student.target_role ?? ""} name="target_role">
              <option value="">Select a target role</option>
              {(roles.data ?? []).map((role) => (
                <option key={role.id} value={role.name}>
                  {role.name}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Career interests" hint="Comma separated">
            <input defaultValue={listToText(student.career_interests)} name="career_interests" />
          </Field>
          <Field label="Preferred locations" hint="Comma separated">
            <input defaultValue={listToText(student.preferred_locations)} name="preferred_locations" />
          </Field>
          <Field label="GitHub URL">
            <input defaultValue={student.github_url ?? ""} name="github_url" />
          </Field>
          <Field label="LinkedIn URL">
            <input defaultValue={student.linkedin_url ?? ""} name="linkedin_url" />
          </Field>
          <Field label="Portfolio URL">
            <input defaultValue={student.portfolio_url ?? ""} name="portfolio_url" />
          </Field>
          <Field label="Short bio" span={2}>
            <textarea defaultValue={student.bio ?? ""} name="bio" rows={3} />
          </Field>
          <button className="btn btn-primary" disabled={action.pending} type="submit">
            <Save size={16} /> {action.pending ? "Saving…" : "Save profile"}
          </button>
        </form>
      </SectionCard>

      <div className="two-column">
        <SkillsPanel onChange={refresh} skills={student.skills} />
        <CertificationsPanel certifications={student.certifications} onChange={refresh} />
      </div>

      <ProjectsPanel onChange={refresh} projects={student.projects} />
    </div>
  );
}
