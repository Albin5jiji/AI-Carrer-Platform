from __future__ import annotations

from typing import Any


def build_skill_gap_prompt(student: Any, gap_data: dict[str, Any], role_requirements: list[str]) -> str:
    skills = ", ".join(skill.name for skill in getattr(student, "skills", []) or []) or "No skills recorded"
    projects = ", ".join(project.title for project in getattr(student, "projects", []) or []) or "No projects recorded"
    certifications = ", ".join(cert.name for cert in getattr(student, "certifications", []) or []) or "No certifications recorded"
    target_role = student.target_role or "No target role selected"

    missing = ", ".join(gap_data.get("missing_skills", [])) or "No major gaps"
    strengths = ", ".join(gap_data.get("strengths", [])) or "No obvious strengths"

    return f"""
You are an advisory career coach. Provide only a JSON object following the required schema.

Student profile:
- target_role: {target_role}
- current_skills: {skills}
- projects: {projects}
- certifications: {certifications}
- DB_role_requirements: {', '.join(role_requirements) if role_requirements else 'No role requirements available'}
- deterministic_gap_summary: {{
    "strengths": {strengths},
    "missing_skills": {missing}
  }}

Rules:
- Do not calculate PRS or eligibility.
- Do not modify profile data or application status.
- This is advisory only.
- Return JSON with exactly these fields: strengths, missing_skills, recommendations, explanation.
- strengths: array of short skill or evidence strings.
- missing_skills: array of missing or weak skills relevant to the target role.
- recommendations: array of 2-5 short actionable recommendations.
- explanation: short plain-language explanation summarizing the student's position.
"""
