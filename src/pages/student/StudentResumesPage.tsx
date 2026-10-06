import { useState } from "react";
import { FileUp, Sparkles } from "lucide-react";
import { resumeApi } from "../../api/studentApi";
import { EmptyState, ErrorState, LoadingState, StatusBadge } from "../../components/ui/primitives";
import { SectionCard } from "../../components/ui/blocks";
import { useAction, useAsync } from "../../hooks/useAsync";
import { useToast } from "../../context/ToastContext";
import type { ResumeContent } from "../../types";

const emptyContent: ResumeContent = { education: [], experience: [], projects: [], skills: [], achievements: [], links: [] };
const list = (value: string) => value.split(",").map((item) => item.trim()).filter(Boolean);

export function StudentResumesPage() {
  const toast = useToast();
  const [key, setKey] = useState("0");
  const [form, setForm] = useState({ version_name: "", title: "", target_role: "", summary: "", skills: "", education: "", projects: "" });
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  const resumes = useAsync(() => resumeApi.list(), key);
  const action = useAction();
  const refresh = () => setKey(String(Date.now()));

  async function create(event: React.FormEvent) {
    event.preventDefault();
    if (!selectedFile) { action.setError("Choose a PDF resume to upload and parse."); return; }
    const content = { ...emptyContent, skills: list(form.skills), education: list(form.education), projects: list(form.projects) };
    const derivedName = selectedFile.name.replace(/\.pdf$/i, "").replace(/[_-]+/g, " ").trim();
    let createdId: number | null = null;
    const ok = await action.run(async () => {
      const resume = await resumeApi.create({
        version_name: form.version_name.trim() || derivedName,
        title: form.title.trim() || derivedName,
        target_role: form.target_role.trim() || undefined,
        summary: form.summary.trim() || null,
        content,
      });
      createdId = resume.id;
      return "created";
    });
    if (!ok) return;
    if (createdId !== null) await upload(createdId, selectedFile);
    setForm({ version_name: "", title: "", target_role: "", summary: "", skills: "", education: "", projects: "" });
    setSelectedFile(null);
    refresh();
  }
  async function submit(id: number) { const ok = await action.run(() => resumeApi.submit(id)); if (ok) { toast.success("Resume submitted for review."); refresh(); } }
  async function remove(id: number) {
    if (!window.confirm("Delete this resume version and its uploaded PDF? This cannot be undone.")) return;
    const ok = await action.run(() => resumeApi.remove(id));
    if (ok) { toast.success("Resume removed."); refresh(); }
  }
  async function upload(id: number, file: File | undefined) {
    if (!file) return;
    const ok = await action.run(async () => {
      const signed = await resumeApi.uploadUrl(id, { filename: file.name, content_type: file.type, size: file.size });
      const response = await fetch(signed.upload_url, { method: "PUT", headers: { "Content-Type": file.type }, body: file });
      if (!response.ok) throw new Error("Resume upload failed");
      await resumeApi.parse(id);
      return "uploaded";
    });
    if (ok) { toast.success("Resume uploaded privately and parsed into this version."); refresh(); }
  }
  async function download(id: number) { const ok = await action.run(() => resumeApi.downloadUrl(id)); if (ok?.download_url) window.open(ok.download_url, "_blank", "noopener,noreferrer"); }

  if (resumes.loading) return <LoadingState label="Loading resume versions…" />;
  if (resumes.error) return <ErrorState message={resumes.error} onRetry={resumes.reload} />;
  return <div className="page-grid">
    <SectionCard eyebrow="Resume intelligence" title="Upload a PDF — we’ll parse the details">
      <form className="form-grid" onSubmit={(event) => void create(event)}>
        <label className="field field-span-3 resume-file-field upload-dropzone"><span className="field-label"><FileUp size={17} /> Resume PDF</span><input accept="application/pdf" disabled={action.pending} onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)} type="file" /><span className="field-hint">Choose a PDF. It is stored privately, parsed automatically, and never made public.</span></label>
        <div className="upload-summary field-span-3"><Sparkles size={18} /><span>{selectedFile ? `${selectedFile.name} is ready to parse` : "We’ll extract skills, education, projects, experience, achievements and links."}</span></div>
        <button className="btn btn-primary" disabled={action.pending || !selectedFile} type="submit"><Sparkles size={16} /> Upload & parse resume</button>
        <button className="btn btn-ghost" onClick={() => setShowDetails((value) => !value)} type="button">{showDetails ? "Hide optional details" : "Add optional details"}</button>
        {showDetails && <div className="form-grid field-span-3 manual-details">
          <label className="field"><span className="field-label">Version name</span><input placeholder="Optional label" value={form.version_name} onChange={(e) => setForm({ ...form, version_name: e.target.value })} /></label>
          <label className="field"><span className="field-label">Title</span><input placeholder="Optional title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} /></label>
          <label className="field"><span className="field-label">Target role</span><input placeholder="Defaults to your profile role" value={form.target_role} onChange={(e) => setForm({ ...form, target_role: e.target.value })} /></label>
          <label className="field"><span className="field-label">Skills</span><input placeholder="Optional comma-separated skills" value={form.skills} onChange={(e) => setForm({ ...form, skills: e.target.value })} /></label>
          <label className="field"><span className="field-label">Education</span><input placeholder="Optional education" value={form.education} onChange={(e) => setForm({ ...form, education: e.target.value })} /></label>
          <label className="field"><span className="field-label">Projects</span><input placeholder="Optional projects" value={form.projects} onChange={(e) => setForm({ ...form, projects: e.target.value })} /></label>
          <label className="field field-span-3"><span className="field-label">Summary</span><textarea placeholder="Optional summary" value={form.summary} onChange={(e) => setForm({ ...form, summary: e.target.value })} /></label>
        </div>}
      </form>
      {action.error && <p className="form-error">{action.error}</p>}
    </SectionCard>
    <SectionCard eyebrow="Your versions" title="Resume status and reviews">
      {resumes.data?.length === 0 && <EmptyState title="No resume versions yet" description="Create a structured resume version to include it in readiness." />}
      <div className="page-grid">{resumes.data?.map((resume) => {
        const hasPdf = resume.file_url?.startsWith("s3://") ?? false;
        const hasParsedDetails = Object.values(resume.content).some((items) => items?.length);
        const canSubmit = hasPdf && hasParsedDetails && resume.completeness >= 40;
        return <article className="card" key={resume.id}>
        <div className="card-head"><div><p className="eyebrow">Version {resume.version_number} · {resume.target_role}</p><h4>{resume.version_name}</h4></div><StatusBadge value={resume.status} /></div>
        <p className="muted small">{resume.completeness}% complete · {resume.summary || "No summary added"}</p>
        {Object.values(resume.content).some((items) => items?.length) && <div className="parsed-preview"><p className="eyebrow">Parsed from your PDF</p>{Object.entries(resume.content).filter(([, items]) => items?.length).map(([section, items]) => <div key={section}><strong>{section}</strong><span>{items?.slice(0, 3).join(" · ")}</span></div>)}</div>}
        {resume.mentor_feedback && <p className="suggestion-box">Reviewer: {resume.reviewer_name ?? "Mentor"}<br />{resume.mentor_feedback}</p>}
        <div className="roadmap-actions">{(resume.status === "draft" || resume.status === "changes_requested") && <><label className="btn btn-outline btn-sm">{hasPdf ? "Replace PDF" : "Upload PDF"}<input accept="application/pdf" disabled={action.pending} hidden onChange={(event) => void upload(resume.id, event.target.files?.[0])} type="file" /></label><button className="btn btn-primary btn-sm" disabled={action.pending || !canSubmit} onClick={() => void submit(resume.id)} title={!canSubmit ? "Upload and parse a complete PDF before submitting" : undefined} type="button">Submit for review</button>{!canSubmit && <span className="muted small">{!hasPdf ? "Upload and parse a PDF to enable review." : !hasParsedDetails ? "Parse the PDF to enable review." : "Parsed resume needs a little more detail before review."}</span>}</>}
          {resume.file_url?.startsWith("s3://") && <button className="btn btn-ghost btn-sm" disabled={action.pending} onClick={() => void download(resume.id)} type="button">View file</button>}
          <button className="btn btn-ghost btn-sm" disabled={action.pending} onClick={() => void remove(resume.id)} type="button">Delete</button>
          {action.error && <span className="form-error" role="alert">{action.error}</span>}</div>
      </article>})}</div>
    </SectionCard>
  </div>;
}
