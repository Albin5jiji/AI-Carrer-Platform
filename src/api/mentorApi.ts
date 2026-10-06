// Mentor endpoints: assigned students, reviews, feedback.

import { apiRequest } from "./client";
import type {
  Application,
  Feedback,
  MentorDashboard,
  MentorStudentDetail,
  Resume,
  StudentProfile,
  StudentSummary,
} from "../types";

export const mentorApi = {
  dashboard: () => apiRequest<MentorDashboard>("/mentor/dashboard"),

  students: (params: { search?: string; needs_attention?: boolean } = {}) =>
    apiRequest<StudentSummary[]>("/mentor/students", { query: params }),

  student: (studentId: number) => apiRequest<MentorStudentDetail>(`/mentor/students/${studentId}`),

  studentProfile: (studentId: number) => apiRequest<StudentProfile>(`/students/${studentId}/profile`),

  pendingResumes: () => apiRequest<Resume[]>("/mentor/resumes/pending"),
  resumeDownloadUrl: (resumeId: number) =>
    apiRequest<{ download_url: string; expires_in: number }>(`/mentor/resumes/${resumeId}/download-url`),

  reviewResume: (resumeId: number, payload: { action: "approve" | "request_changes"; feedback?: string }) =>
    apiRequest<Resume>(`/mentor/resumes/${resumeId}/review`, { method: "POST", body: payload }),

  pendingApplications: () => apiRequest<Application[]>("/mentor/applications/pending"),

  decideApplication: (applicationId: number, payload: { action: "approve" | "request_changes"; feedback?: string }) =>
    apiRequest<Application>(`/applications/${applicationId}/decision`, {
      method: "POST",
      query: { action: payload.action, feedback: payload.feedback ?? undefined },
    }),

  feedback: (params: { student_id?: number; status_filter?: string } = {}) =>
    apiRequest<Feedback[]>("/mentor/feedback", { query: params }),

  createFeedback: (payload: {
    student_id: number;
    title: string;
    body: string;
    resume_id?: number | null;
    application_id?: number | null;
    status?: string;
  }) => apiRequest<Feedback>("/mentor/feedback", { method: "POST", body: payload }),

  updateFeedback: (id: number, payload: { title?: string; body?: string; status?: string }) =>
    apiRequest<Feedback>(`/mentor/feedback/${id}`, { method: "PATCH", body: payload }),
};
