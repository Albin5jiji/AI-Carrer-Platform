import { useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import { profileApi } from "../../api/studentApi";
import { useAction } from "../../hooks/useAsync";
import { useToast } from "../../context/ToastContext";
import { SectionCard } from "../ui/blocks";
import { EmptyState } from "../ui/primitives";
import type { Skill } from "../../types";

const LEVELS = ["beginner", "intermediate", "advanced"];

export function SkillsPanel({ skills, onChange }: { skills: Skill[]; onChange: () => void }) {
  const toast = useToast();
  const action = useAction();
  const [draft, setDraft] = useState({ name: "", proficiency: "intermediate" });

  async function add() {
    if (!draft.name.trim()) return;
    const ok = await action.run(async () => {
      await profileApi.addSkill({ name: draft.name.trim(), proficiency: draft.proficiency });
      return "Skill added";
    });
    if (ok) {
      setDraft({ name: "", proficiency: "intermediate" });
      toast.success("Skill added to your profile");
      onChange();
    }
  }

  async function remove(skill: Skill) {
    const ok = await action.run(async () => {
      await profileApi.deleteSkill(skill.id);
      return "Skill removed";
    });
    if (ok) {
      toast.success(`${skill.name} removed`);
      onChange();
    }
  }

  return (
    <SectionCard eyebrow="Skills" title={`${skills.length} skill(s) recorded`}>
      <div className="inline-form">
        <input
          onChange={(event) => setDraft((current) => ({ ...current, name: event.target.value }))}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              void add();
            }
          }}
          placeholder="Add a skill, e.g. React"
          value={draft.name}
        />
        <select
          onChange={(event) => setDraft((current) => ({ ...current, proficiency: event.target.value }))}
          value={draft.proficiency}
        >
          {LEVELS.map((level) => (
            <option key={level} value={level}>
              {level}
            </option>
          ))}
        </select>
        <button className="btn btn-outline" disabled={action.pending} onClick={add} type="button">
          <Plus size={16} /> Add
        </button>
      </div>

      {action.error && <p className="form-error">{action.error}</p>}
      {skills.length === 0 && (
        <EmptyState title="No skills yet" description="Skills are matched against your target role requirements." />
      )}
      <ul className="list">
        {skills.map((skill) => (
          <li key={skill.id}>
            <div>
              <strong>{skill.name}</strong>
              <span className="muted">{skill.proficiency}</span>
            </div>
            <button
              aria-label={`Remove ${skill.name}`}
              className="icon-btn"
              onClick={() => void remove(skill)}
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
