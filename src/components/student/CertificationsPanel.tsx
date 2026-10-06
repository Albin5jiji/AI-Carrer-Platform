import { useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import { profileApi } from "../../api/studentApi";
import { useAction } from "../../hooks/useAsync";
import { useToast } from "../../context/ToastContext";
import { Field, SectionCard } from "../ui/blocks";
import { EmptyState } from "../ui/primitives";
import { textToList } from "../../utils/format";
import type { Certification } from "../../types";

const EMPTY = { name: "", issuer: "", issued_year: "", skill_tags: "" };

export function CertificationsPanel({
  certifications,
  onChange,
}: {
  certifications: Certification[];
  onChange: () => void;
}) {
  const toast = useToast();
  const action = useAction();
  const [draft, setDraft] = useState(EMPTY);

  async function add() {
    if (!draft.name.trim()) return;
    const ok = await action.run(async () => {
      await profileApi.addCertification({
        name: draft.name.trim(),
        issuer: draft.issuer || null,
        issued_year: draft.issued_year ? Number(draft.issued_year) : null,
        credential_url: null,
        skill_tags: textToList(draft.skill_tags),
      });
      return "Certification added";
    });
    if (ok) {
      setDraft(EMPTY);
      toast.success("Certification added");
      onChange();
    }
  }

  async function remove(certification: Certification) {
    const ok = await action.run(async () => {
      await profileApi.deleteCertification(certification.id);
      return "Certification removed";
    });
    if (ok) {
      toast.success(`${certification.name} removed`);
      onChange();
    }
  }

  return (
    <SectionCard eyebrow="Certifications" title={`${certifications.length} certification(s)`}>
      <div className="form-grid">
        <Field label="Certification name">
          <input onChange={(event) => setDraft((c) => ({ ...c, name: event.target.value }))} value={draft.name} />
        </Field>
        <Field label="Issuer">
          <input
            onChange={(event) => setDraft((c) => ({ ...c, issuer: event.target.value }))}
            placeholder="freeCodeCamp"
            value={draft.issuer}
          />
        </Field>
        <Field label="Year">
          <input
            max="2100"
            min="1980"
            onChange={(event) => setDraft((c) => ({ ...c, issued_year: event.target.value }))}
            type="number"
            value={draft.issued_year}
          />
        </Field>
        <Field label="Skill tags" hint="Comma separated; tagged skills count as role relevant">
          <input
            onChange={(event) => setDraft((c) => ({ ...c, skill_tags: event.target.value }))}
            value={draft.skill_tags}
          />
        </Field>
        <button className="btn btn-primary" disabled={action.pending} onClick={add} type="button">
          <Plus size={16} /> Add certification
        </button>
      </div>

      {action.error && <p className="form-error">{action.error}</p>}
      {certifications.length === 0 && <EmptyState title="No certifications yet" />}
      <ul className="list">
        {certifications.map((certification) => (
          <li key={certification.id}>
            <div>
              <strong>{certification.name}</strong>
              <span className="muted">
                {certification.issuer ?? "Issuer not set"}
                {certification.issued_year ? ` · ${certification.issued_year}` : ""}
              </span>
            </div>
            <button
              aria-label={`Remove ${certification.name}`}
              className="icon-btn"
              onClick={() => void remove(certification)}
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
