import {
  BookOpen,
  BriefcaseBusiness,
  Building2,
  CalendarCheck,
  ClipboardList,
  FileText,
  Gauge,
  LayoutDashboard,
  LineChart,
  MessagesSquare,
  Send,
  ScrollText,
  ShieldCheck,
  Target,
  UserRound,
  Users,
  UsersRound,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { UserRole } from "../types";

export type NavItem = { path: string; label: string; icon: LucideIcon };

export const studentNav: NavItem[] = [
  { path: "/student/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { path: "/student/profile", label: "Profile", icon: UserRound },
  { path: "/student/readiness", label: "Readiness Score", icon: Gauge },
  { path: "/student/skill-gap", label: "Skill Gap", icon: Target },
  { path: "/student/learning", label: "Learning Path", icon: BookOpen },
  { path: "/student/interview", label: "Interview Prep", icon: MessagesSquare },
  { path: "/student/history", label: "Readiness History", icon: LineChart },
  { path: "/student/resumes", label: "Resumes", icon: FileText },
  { path: "/student/drives", label: "Placement Drives", icon: BriefcaseBusiness },
  { path: "/student/applications", label: "Applications", icon: Send },
];

export const mentorNav: NavItem[] = [
  { path: "/mentor/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { path: "/mentor/students", label: "Assigned Students", icon: UsersRound },
  { path: "/mentor/resume-reviews", label: "Resume Reviews", icon: FileText },
  { path: "/mentor/application-reviews", label: "Application Approvals", icon: ClipboardList },
  { path: "/mentor/feedback", label: "Feedback", icon: MessagesSquare },
];

export const adminNav: NavItem[] = [
  { path: "/admin/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { path: "/admin/users", label: "User Management", icon: Users },
  { path: "/admin/students", label: "Student Monitoring", icon: UsersRound },
  { path: "/admin/assignments", label: "Mentor Assignment", icon: ClipboardList },
  { path: "/admin/companies", label: "Companies", icon: Building2 },
  { path: "/admin/jobs", label: "Job Postings", icon: BriefcaseBusiness },
  { path: "/admin/drives", label: "Placement Drives", icon: CalendarCheck },
  { path: "/admin/applications", label: "Application Monitoring", icon: Send },
  { path: "/admin/audit", label: "Audit Log", icon: ScrollText },
];

export function navForRole(role: UserRole | null): NavItem[] {
  if (role === "mentor") return mentorNav;
  if (role === "administrator") return adminNav;
  return studentNav;
}

export function homePathForRole(role: UserRole | null): string {
  if (role === "mentor") return "/mentor/dashboard";
  if (role === "administrator") return "/admin/dashboard";
  return "/student/dashboard";
}

export const portalIcon = ShieldCheck;
