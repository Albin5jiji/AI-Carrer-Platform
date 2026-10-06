// Admin endpoints: users, students, assignments, companies, jobs, drives, monitoring, audit.

import { apiRequest } from "./client";
import type {
  AdminDashboard,
  AdminStudentRow,
  AdminUser,
  Application,
  Assignment,
  AuditLog,
  Company,
  JobPosting,
  Paginated,
  PlacementDrive,
} from "../types";

export const adminApi = {
  dashboard: () => apiRequest<AdminDashboard>("/admin/dashboard"),

  users: (params: { role?: string; search?: string; is_active?: boolean; page?: number; page_size?: number } = {}) =>
    apiRequest<Paginated<AdminUser>>("/admin/users", { query: params }),

  createUser: (payload: {
    full_name: string;
    email: string;
    password: string;
    role: string;
    identifier: string;
    department_or_program: string;
  }) => apiRequest<AdminUser>("/admin/users", { method: "POST", body: payload }),

  updateUser: (id: number, payload: { full_name?: string; is_active?: boolean; department_or_program?: string }) =>
    apiRequest<AdminUser>(`/admin/users/${id}`, { method: "PATCH", body: payload }),

  resetPassword: (id: number, newPassword: string) =>
    apiRequest<{ message: string }>(`/admin/users/${id}/reset-password`, {
      method: "POST",
      query: { new_password: newPassword },
    }),

  students: (params: { search?: string; needs_attention?: boolean; without_mentor?: boolean } = {}) =>
    apiRequest<AdminStudentRow[]>("/admin/students", { query: params }),

  assignments: (params: { mentor_id?: number; student_id?: number } = {}) =>
    apiRequest<Assignment[]>("/admin/assignments", { query: params }),

  assign: (payload: { mentor_id: number; student_id: number; notes?: string }) =>
    apiRequest<Assignment>("/admin/assignments", { method: "POST", body: payload }),

  endAssignment: (id: number) => apiRequest<{ message: string }>(`/admin/assignments/${id}`, { method: "DELETE" }),

  companies: (params: { search?: string; include_inactive?: boolean } = {}) =>
    apiRequest<Company[]>("/companies", { query: params }),

  createCompany: (payload: Record<string, unknown>) =>
    apiRequest<Company>("/companies", { method: "POST", body: payload }),

  updateCompany: (id: number, payload: Record<string, unknown>) =>
    apiRequest<Company>(`/companies/${id}`, { method: "PATCH", body: payload }),

  deleteCompany: (id: number) => apiRequest<{ message: string }>(`/companies/${id}`, { method: "DELETE" }),

  jobs: (params: { search?: string; company_id?: number; status_filter?: string } = {}) =>
    apiRequest<JobPosting[]>("/jobs", { query: params }),

  createJob: (payload: Record<string, unknown>) => apiRequest<JobPosting>("/jobs", { method: "POST", body: payload }),

  updateJob: (id: number, payload: Record<string, unknown>) =>
    apiRequest<JobPosting>(`/jobs/${id}`, { method: "PATCH", body: payload }),

  publishJob: (id: number) => apiRequest<JobPosting>(`/jobs/${id}/publish`, { method: "POST" }),

  closeJob: (id: number) => apiRequest<JobPosting>(`/jobs/${id}/close`, { method: "POST" }),

  deleteJob: (id: number) => apiRequest<{ message: string }>(`/jobs/${id}`, { method: "DELETE" }),

  drives: (params: { search?: string; status_filter?: string; company_id?: number } = {}) =>
    apiRequest<PlacementDrive[]>("/drives", { query: params }),

  createDrive: (payload: Record<string, unknown>) =>
    apiRequest<PlacementDrive>("/drives", { method: "POST", body: payload }),

  updateDrive: (id: number, payload: Record<string, unknown>) =>
    apiRequest<PlacementDrive>(`/drives/${id}`, { method: "PATCH", body: payload }),

  setDriveStatus: (id: number, status: string, note?: string) =>
    apiRequest<PlacementDrive>(`/drives/${id}/status`, { method: "POST", body: { status, note } }),

  eligibleStudents: (id: number) =>
    apiRequest<{
      drive_id: number;
      count: number;
      students: {
        student_id: number;
        full_name: string | null;
        registration_number: string;
        department: string | null;
        cgpa: number | null;
      }[];
    }>(`/drives/${id}/eligible-students`),

  deleteDrive: (id: number) => apiRequest<{ message: string }>(`/drives/${id}`, { method: "DELETE" }),

  applications: (params: {
    status_filter?: string;
    company_id?: number;
    drive_id?: number;
    search?: string;
    page?: number;
    page_size?: number;
  } = {}) => apiRequest<Paginated<Application>>("/admin/applications", { query: params }),

  setApplicationStatus: (id: number, status: string, note?: string) =>
    apiRequest<Application>(`/applications/${id}/status`, { method: "PATCH", body: { status, note } }),

  auditLogs: (params: { action?: string; entity_type?: string; actor_email?: string; page?: number } = {}) =>
    apiRequest<{ items: AuditLog[]; total: number; page: number; page_size: number }>("/admin/audit-logs", {
      query: params,
    }),

  reseed: () =>
    apiRequest<{ message: string; created: Record<string, number> }>("/admin/reference/seed", { method: "POST" }),
};
