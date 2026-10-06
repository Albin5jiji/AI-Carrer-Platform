import { useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import { profileApi } from "../../api/studentApi";
import { useAction } from "../../hooks/useAsync";
import { useToast } from "../../context/ToastContext";
import { Field, SectionCard } from "../ui/blocks";
import { EmptyState } from "../ui/primitives";
import { textToList } from "../../utils/format";
import type { Project } from "../../types";

const EMPTY = { title: "", description: "", tech_stack: "", repo_url: "" };

export function ProjectsPanel({ projects, onChange }: { projects: Project[]; onChange: () => void }) {
  const toast = useToast();
  const action = useAction();
  const [draft, setDraft] = useState(EMPTY);

  async function add() {
    if (!draft.title.trim()) return;
    const ok = await action.run(async () => {
      await profileApi.addProject({
        title: draft.title.trim(),
        description: draft.description || null,
        tech_stack: textToList(draft.tech_stack),
        repo_url: draft.repo_url || null,
        live_url: null,
      });
      return "Project added";
    });
    if (ok) {
      setDraft(EMPTY);
      toast.success("Project added. Projects feed the project relevance component.");
      onChange();
    }
  }

  async function remove(project: Project) {
    const ok = await action.run(async () => {
      await profileApi.deleteProject(project.id);
      return "Project removed";
    });
    if (ok) {
      toast.success(`${project.title} removed`);
      onChange();
    }
  }

  return (
    <SectionCard eyebrow="Projects" title={`${projects.length} project(s)`}>
      <div className="form-grid">
        <Field label="Project title">
          <input onChange={(event) => setDraft((c) => ({ ...c, title: event.target.value }))} value={draft.title} />
        </Field>
        <Field label="Repository URL" hint="Projects with a repository or demo link score higher">
          <input
            onChange={(event) => setDraft((c) => ({ ...c, repo_url: event.target.value }))}
            placeholder="https://github.com/…"
            value={draft.repo_url}
          />
        </Field>
        <Field label="Tech stack" hint="Comma separated">
          <input
            onChange={(event) => setDraft((c) => ({ ...c, tech_stack: event.target.value }))}
            placeholder="React, FastAPI, PostgreSQL"
            value={draft.tech_stack}
          />
        </Field>
        <Field label="Description" span={2}>
          <textarea
            onChange={(event) => setDraft((c) => ({ ...c, description: event.target.value }))}
            rows={2}
            value={draft.description}
          />
        </Field>
        <button className="btn btn-primary" disabled={action.pending} onClick={add} type="button">
          <Plus size={16} /> Add project
        </button>
      </div>

      {action.error && <p className="form-error">{action.error}</p>}
      {projects.length === 0 && (
        <EmptyState title="No projects yet" description="Add at least two role relevant projects with links." />
      )}
      <ul className="list">
        {projects.map((project) => (
          <li key={project.id}>
            <div>
              <strong>{project.title}</strong>
              <span className="muted">{project.tech_stack.join(", ") || "No tech stack listed"}</span>
            </div>
            <button
              aria-label={`Remove ${project.title}`}
              className="icon-btn"
              onClick={() => void remove(project)}
              type="button"
            >
              <Trash2 size={15} />
            </button>
          </li>
        ))}
      </ul>
    </SectionCard>
  );
}
