import { useEffect } from "react";
import type { ReactNode } from "react";
import { AuthPage } from "./pages/auth/AuthPage";
import { AppShell } from "./components/layout/AppShell";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { ToastProvider } from "./context/ToastContext";
import { navigate, useRoute } from "./router/router";
import { homePathForRole } from "./components/layout/navConfig";
import { EmptyState, LoadingState } from "./components/ui/primitives";
import { StudentDashboard } from "./pages/student/StudentDashboard";
import { StudentProfilePage } from "./pages/student/StudentProfilePage";
import { StudentReadinessPage } from "./pages/student/StudentReadinessPage";
import { SkillGapPage } from "./pages/student/SkillGapPage";
import { LearningPathPage } from "./pages/student/LearningPathPage";
import { InterviewPrepPage } from "./pages/student/InterviewPrepPage";
import { ReadinessHistoryPage } from "./pages/student/ReadinessHistoryPage";
import { StudentDrivesPage } from "./pages/student/StudentDrivesPage";
import { StudentApplicationsPage } from "./pages/student/StudentApplicationsPage";
import { StudentResumesPage } from "./pages/student/StudentResumesPage";
import { NotificationsPage } from "./pages/NotificationsPage";
import { MentorApplicationReviewsPage, MentorDashboardPage, MentorFeedbackPage, MentorResumeReviewsPage, MentorStudentDetailPage, MentorStudentsPage } from "./pages/mentor/MentorWorkspacePages";
import { AdminApplicationsPage, AdminAssignmentsPage, AdminAuditPage, AdminCompaniesPage, AdminDashboardPage, AdminDrivesPage, AdminJobsPage, AdminStudentsPage, AdminUsersPage } from "./pages/admin/AdminWorkspacePages";

function AppContent() {
  const { status, role } = useAuth();
  const { path } = useRoute();

  useEffect(() => {
    if (status === "authenticated" && (path === "/" || path === "/login")) {
      navigate(homePathForRole(role));
    }
  }, [path, role, status]);

  if (status === "loading") return <LoadingState label="Restoring your session…" />;
  if (status === "anonymous") return <AuthPage />;

  return (
    <AppShell>
      <RouteContent path={path} role={role} />
    </AppShell>
  );
}

function RouteContent({ path, role }: { path: string; role: "student" | "mentor" | "administrator" | null }) {
  if (role === "student") {
    switch (path) {
      case "/student/profile":
        return <StudentProfilePage />;
      case "/student/readiness":
        return <StudentReadinessPage />;
      case "/student/skill-gap":
        return <SkillGapPage />;
      case "/student/learning":
        return <LearningPathPage />;
      case "/student/interview":
        return <InterviewPrepPage />;
      case "/student/resumes":
        return <StudentResumesPage />;
      case "/student/history":
        return <ReadinessHistoryPage />;
      case "/student/drives":
        return <StudentDrivesPage />;
      case "/student/applications":
        return <StudentApplicationsPage />;
      case "/student/dashboard":
      case "/notifications":
        return <NotificationsPage />;
      case "/":
        return <StudentDashboard />;
      default:
        return <EmptyState title="Page not found" description="Choose a page from the navigation." />;
    }
  }

  if (role === "mentor") {
    if (path === "/mentor/dashboard") return <MentorDashboardPage />;
    if (path === "/mentor/students") return <MentorStudentsPage />;
    if (path.startsWith("/mentor/students/")) { const id = Number(path.split("/").at(-1)); return Number.isFinite(id) ? <MentorStudentDetailPage studentId={id} /> : <EmptyState title="Student not found" />; }
    if (path === "/mentor/resume-reviews") return <MentorResumeReviewsPage />;
    if (path === "/mentor/application-reviews") return <MentorApplicationReviewsPage />;
    if (path === "/mentor/feedback") return <MentorFeedbackPage />;
    if (path === "/notifications") return <NotificationsPage />;
  }
  if (role === "administrator") {
    const pages: Record<string, ReactNode> = { "/admin/dashboard": <AdminDashboardPage />, "/admin/users": <AdminUsersPage />, "/admin/students": <AdminStudentsPage />, "/admin/assignments": <AdminAssignmentsPage />, "/admin/companies": <AdminCompaniesPage />, "/admin/jobs": <AdminJobsPage />, "/admin/drives": <AdminDrivesPage />, "/admin/applications": <AdminApplicationsPage />, "/admin/audit": <AdminAuditPage />, "/notifications": <NotificationsPage /> };
    if (pages[path]) return pages[path];
  }

  return (
    <EmptyState
      title="Workspace unavailable"
      description="This workspace is authenticated, but its backend-backed pages are not part of this frontend slice yet."
    />
  );
}

export default function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ToastProvider>
  );
}
