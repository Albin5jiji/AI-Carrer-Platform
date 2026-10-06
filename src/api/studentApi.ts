// Student facing endpoints: profile, resumes, readiness, learning, interview, applications.

import { apiRequest } from "./client";
import type {
  Application,
  AISkillGapAnalysis,
  Certification,
  DriveEligibilityRow,
  InterviewOverview,
  InterviewQuestion,
  LearningPath,
  NotificationList,
  PlacementDrive,
  Project,
  Readiness,
  ReadinessHistory,
  Resume,
  RoleProfile,
  Skill,
  SkillGap,
  StudentProfile,
} from "../types";

export const profileApi = {
  roles: () => apiRequest<RoleProfile[]>("/students/roles"),
  me: () => apiRequest<StudentProfile>("/students/me/profile"),
  update: (patch: Partial<StudentProfile>) =>
    apiRequest<StudentProfile>("/students/me/profile", { method: "PATCH", body: patch }),
  addSkill: (payload: { name: string; proficiency: string; years_experience?: number | null }) =>
    apiRequest<Skill>("/students/me/skills", { method: "POST", body: payload }),
  updateSkill: (id: number, payload: { name: string; proficiency: string; years_experience?: number | null }) =>
    apiRequest<Skill>(`/students/me/skills/${id}`, { method: "PATCH", body: payload }),
  deleteSkill: (id: number) => apiRequest<{ message: string }>(`/students/me/skills/${id}`, { method: "DELETE" }),
  addProject: (payload: Omit<Project, "id">) =>
    apiRequest<Project>("/students/me/projects", { method: "POST", body: payload }),
  updateProject: (id: number, payload: Omit<Project, "id">) =>
    apiRequest<Project>(`/students/me/projects/${id}`, { method: "PATCH", body: payload }),
  deleteProject: (id: number) =>
    apiRequest<{ message: string }>(`/students/me/projects/${id}`, { method: "DELETE" }),
  addCertification: (payload: Omit<Certification, "id">) =>
    apiRequest<Certification>("/students/me/certifications", { method: "POST", body: payload }),
  updateCertification: (id: number, payload: Omit<Certification, "id">) =>
    apiRequest<Certification>(`/students/me/certifications/${id}`, { method: "PATCH", body: payload }),
  deleteCertification: (id: number) =>
    apiRequest<{ message: string }>(`/students/me/certifications/${id}`, { method: "DELETE" }),
};

export const resumeApi = {
  list: () => apiRequest<Resume[]>("/resumes/me"),
  create: (payload: {
    version_name?: string | null;
    title?: string | null;
    target_role?: string | null;
    summary?: string | null;
    content?: Record<string, string[]>;
    file_url?: string | null;
  }) => apiRequest<Resume>("/resumes/me", { method: "POST", body: payload }),
  update: (id: number, payload: Record<string, unknown>) =>
    apiRequest<Resume>(`/resumes/me/${id}`, { method: "PATCH", body: payload }),
  submit: (id: number) => apiRequest<Resume>(`/resumes/me/${id}/submit`, { method: "POST" }),
  remove: (id: number) => apiRequest<{ message: string }>(`/resumes/me/${id}`, { method: "DELETE" }),
  uploadUrl: (id: number, payload: { filename: string; content_type: string; size: number }) =>
    apiRequest<{ storage_key: string; upload_url: string; expires_in: number }>(`/resumes/me/${id}/upload-url`, { method: "POST", body: payload }),
  downloadUrl: (id: number) => apiRequest<{ download_url: string; expires_in: number }>(`/resumes/me/${id}/download-url`),
  parse: (id: number) => apiRequest<Resume>(`/resumes/me/${id}/parse`, { method: "POST" }),
};

export const readinessApi = {
  weights: () => apiRequest<{ weights: Record<string, number>; total: number }>("/readiness/weights"),
  me: () => apiRequest<Readiness>("/readiness/me"),
  skillGap: () => apiRequest<SkillGap>("/readiness/me/skill-gap"),
  aiSkillGap: () => apiRequest<AISkillGapAnalysis>("/readiness/me/ai-skill-gap", { method: "POST" }),
  history: () => apiRequest<ReadinessHistory>("/readiness/me/history"),
};

export const learningApi = {
  path: () => apiRequest<LearningPath>("/learning/me/path"),
  refresh: () => apiRequest<LearningPath>("/learning/me/refresh", { method: "POST" }),
  updateItem: (
    id: number,
    payload: { status?: string; progress_percent?: number; notes?: string; target_date?: string },
  ) => apiRequest<LearningPath>(`/learning/me/items/${id}`, { method: "PATCH", body: payload }),
};

export const interviewApi = {
  overview: () => apiRequest<InterviewOverview>("/interview/me/overview"),
  questions: (params: { category?: string; only_unpractised?: boolean } = {}) =>
    apiRequest<InterviewQuestion[]>("/interview/me/questions", { query: params }),
  recordPractice: (
    questionId: number,
    payload: { status: string; self_rating?: number | null; notes?: string | null },
  ) => apiRequest<InterviewOverview>(`/interview/me/practice/${questionId}`, { method: "POST", body: payload }),
  addMock: (payload: {
    target_role?: string | null;
    mode: string;
    completed: boolean;
    score?: number | null;
    strengths?: string | null;
    improvements?: string | null;
  }) => apiRequest<InterviewOverview["mock_interviews"]>("/interview/me/mock", { method: "POST", body: payload }),
};

export const driveApi = {
  list: (params: { search?: string; status_filter?: string } = {}) =>
    apiRequest<PlacementDrive[]>("/drives", { query: params }),
  myEligibility: () => apiRequest<DriveEligibilityRow[]>("/drives/me/eligibility"),
};

export const applicationApi = {
  mine: () => apiRequest<Application[]>("/applications/me"),
  apply: (payload: { drive_id: number; resume_id?: number | null; note_to_mentor?: string | null }) =>
    apiRequest<Application>("/applications/me", { method: "POST", body: payload }),
  withdraw: (id: number) => apiRequest<Application>(`/applications/${id}/withdraw`, { method: "POST" }),
};

export const notificationApi = {
  list: (params: { unread_only?: boolean; type_filter?: string } = {}) =>
    apiRequest<NotificationList>("/notifications", { query: params }),
  markRead: (id: number) => apiRequest<unknown>(`/notifications/${id}/read`, { method: "POST" }),
  markAllRead: () => apiRequest<{ message: string }>("/notifications/read-all", { method: "POST" }),
};
