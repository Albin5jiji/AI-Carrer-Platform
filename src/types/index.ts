// Shared types. These mirror the FastAPI Pydantic response schemas exactly.

export type UserRole = "student" | "mentor" | "administrator";

export type AuthUser = {
  id: number;
  full_name: string;
  email: string;
  role: UserRole;
  identifier: string;
  department_or_program: string;
  profile_id: number | null;
  is_active: boolean;
};

export type ProficiencyLevel = "beginner" | "intermediate" | "advanced";
export type Priority = "high" | "medium" | "low";
export type Difficulty = "beginner" | "intermediate" | "advanced";
export type ResumeStatus = "draft" | "pending_review" | "approved" | "changes_requested";
export type LearningStatus = "not_started" | "in_progress" | "completed";
export type InterviewCategory = "technical" | "behavioral" | "role_specific";
export type PracticeStatus = "not_started" | "practiced" | "needs_revision";
export type CompanyStatus = "active" | "inactive";
export type JobPostingStatus = "draft" | "published" | "closed";
export type DriveStatus = "draft" | "open" | "closed" | "completed";
export type FeedbackStatus = "open" | "action_needed" | "resolved";
export type NotificationType =
  | "application_status"
  | "mentor_feedback"
  | "resume_review"
  | "deadline_reminder"
  | "drive_announcement"
  | "eligibility_update"
  | "readiness_update"
  | "general";

export type ApplicationStatus =
  | "pending_mentor_approval"
  | "changes_requested"
  | "approved"
  | "submitted"
  | "shortlisted"
  | "interview_scheduled"
  | "selected"
  | "rejected"
  | "withdrawn";

export type Skill = {
  id: number;
  name: string;
  proficiency: ProficiencyLevel;
  years_experience: number | null;
};

export type Project = {
  id: number;
  title: string;
  description: string | null;
  tech_stack: string[];
  repo_url: string | null;
  live_url: string | null;
};

export type Certification = {
  id: number;
  name: string;
  issuer: string | null;
  issued_year: number | null;
  credential_url: string | null;
  skill_tags: string[];
};

export type StudentProfile = {
  id: number;
  account_id: number;
  full_name: string;
  email: string;
  registration_number: string;
  program: string;
  phone: string | null;
  degree: string | null;
  department: string | null;
  graduation_year: number | null;
  cgpa: number | null;
  location: string | null;
  bio: string | null;
  target_role: string | null;
  target_roles: string[];
  career_interests: string[];
  preferred_locations: string[];
  github_url: string | null;
  linkedin_url: string | null;
  portfolio_url: string | null;
  profile_completion: number;
  skills: Skill[];
  projects: Project[];
  certifications: Certification[];
};

export type RoleProfile = {
  id: number;
  name: string;
  category: string | null;
  description: string | null;
};

export type ResumeContent = {
  education: string[];
  experience: string[];
  projects: string[];
  skills: string[];
  achievements: string[];
  links: string[];
};

export type Resume = {
  id: number;
  student_id: number;
  version_number: number;
  version_name: string;
  title: string;
  target_role: string;
  summary: string | null;
  content: Partial<ResumeContent>;
  file_url: string | null;
  status: ResumeStatus;
  mentor_feedback: string | null;
  reviewer_name: string | null;
  submitted_at: string | null;
  reviewed_at: string | null;
  created_at: string;
  updated_at: string;
  completeness: number;
};

export type ReadinessComponent = {
  key: string;
  label: string;
  score: number;
  weight: number;
  weighted_points: number;
  explanation: string;
};

export type Readiness = {
  student_id: number;
  overall_score: number;
  level: string;
  target_role: string | null;
  components: ReadinessComponent[];
  suggestions: string[];
  explanation: string[];
  disclaimer: string;
  computed_at: string;
};

export type ReadinessSnapshot = {
  id: number;
  overall_score: number;
  academics: number;
  skills: number;
  projects: number;
  certifications: number;
  resume: number;
  interview: number;
  target_role: string | null;
  computed_at: string;
};

export type ReadinessHistory = {
  student_id: number;
  target_role: string | null;
  latest_score: number | null;
  previous_score: number | null;
  change: number | null;
  snapshot_count: number;
  snapshots: ReadinessSnapshot[];
  improvement_timeline: string[];
};

export type SkillGapItem = {
  skill_name: string;
  priority: Priority;
  target_proficiency: ProficiencyLevel;
  current_proficiency: ProficiencyLevel | null;
  status: "covered" | "partial" | "missing";
  score: number;
  action: string;
};

export type SkillGap = {
  target_role: string;
  has_role_data: boolean;
  required_skill_count: number;
  covered_skill_count: number;
  missing_skill_count: number;
  coverage_percent: number;
  skills_component_score: number;
  items: SkillGapItem[];
};

export type AISkillGapAnalysis = {
  strengths: string[];
  missing_skills: string[];
  recommendations: string[];
  explanation: string;
  outdated: boolean;
};

export type LearningPathItem = {
  id: number;
  skill_name: string;
  priority: Priority;
  status: LearningStatus;
  progress_percent: number;
  target_date: string | null;
  title: string;
  provider: string | null;
  url: string | null;
  resource_type: string;
  difficulty: Difficulty;
  estimated_hours: number;
  description: string | null;
};

export type LearningPath = {
  student_id: number;
  target_role: string | null;
  total_items: number;
  not_started: number;
  in_progress: number;
  completed: number;
  completion_percent: number;
  total_estimated_hours: number;
  remaining_estimated_hours: number;
  next_action: string | null;
  items: LearningPathItem[];
};

export type InterviewQuestion = {
  id: number;
  category: InterviewCategory;
  target_role: string | null;
  difficulty: Difficulty;
  question: string;
  guidance: string | null;
  skill_tags: string[];
  practice_status: PracticeStatus;
  self_rating: number | null;
  practiced_at: string | null;
};

export type MockInterview = {
  id: number;
  target_role: string | null;
  mode: string;
  scheduled_for: string | null;
  completed: boolean;
  score: number | null;
  strengths: string | null;
  improvements: string | null;
  feedback: string | null;
  created_at: string;
};

export type InterviewOverview = {
  student_id: number;
  target_role: string | null;
  total_questions: number;
  practiced_count: number;
  needs_revision_count: number;
  progress_percent: number;
  interview_component_score: number;
  categories: {
    category: InterviewCategory;
    total: number;
    practiced: number;
    needs_revision: number;
    progress_percent: number;
  }[];
  mock_interviews: MockInterview[];
  completed_mock_interviews: number;
  average_mock_score: number | null;
  suggestions: string[];
};

export type Company = {
  id: number;
  name: string;
  description: string | null;
  industry: string | null;
  website: string | null;
  location: string | null;
  contact_person: string | null;
  contact_email: string | null;
  contact_phone: string | null;
  status: CompanyStatus;
  created_at: string;
  job_count: number;
  drive_count: number;
};

export type JobPosting = {
  id: number;
  company_id: number;
  company_name: string | null;
  title: string;
  description: string | null;
  required_skills: string[];
  min_cgpa: number | null;
  eligible_departments: string[];
  graduation_years: number[];
  job_type: string;
  location: string | null;
  salary_range: string | null;
  application_deadline: string | null;
  status: JobPostingStatus;
  created_at: string;
  drive_count: number;
};

export type PlacementDrive = {
  id: number;
  company_id: number;
  company_name: string | null;
  job_posting_id: number | null;
  job_title: string | null;
  name: string;
  description: string | null;
  drive_date: string | null;
  application_deadline: string | null;
  min_cgpa: number | null;
  eligible_departments: string[];
  graduation_years: number[];
  required_skills: string[];
  location: string | null;
  requires_mentor_approval: boolean;
  status: DriveStatus;
  created_at: string;
  application_count: number;
  eligible_student_count: number;
  days_to_deadline: number | null;
};

export type Eligibility = {
  eligible: boolean;
  status: string;
  reasons: string[];
  missing_skills: string[];
  matched_skills: string[];
  cgpa_ok: boolean;
  department_ok: boolean;
  graduation_year_ok: boolean;
  deadline_open: boolean;
  already_applied: boolean;
  has_approved_resume: boolean;
};

export type DriveEligibilityRow = { drive_id: number; eligibility: Eligibility };

export type Application = {
  id: number;
  code: string;
  student_id: number;
  student_name: string | null;
  registration_number: string | null;
  department: string | null;
  cgpa: number | null;
  target_role: string | null;
  drive_id: number;
  drive_name: string | null;
  company_id: number;
  company_name: string | null;
  job_title: string | null;
  resume_id: number | null;
  resume_version_name: string | null;
  eligibility_status: string;
  eligibility_reasons: string[];
  missing_skills: string[];
  status: ApplicationStatus;
  mentor_feedback: string | null;
  mentor_name: string | null;
  note_to_mentor: string | null;
  admin_note: string | null;
  created_at: string;
  updated_at: string;
  decided_at: string | null;
  next_action: string | null;
};

export type Notification = {
  id: number;
  title: string;
  message: string;
  type: NotificationType;
  entity_type: string | null;
  entity_id: number | null;
  is_read: boolean;
  created_at: string;
};

export type NotificationList = { unread_count: number; items: Notification[] };

export type Paginated<T> = { items: T[]; total: number; page: number; page_size: number };

export type StudentSummary = {
  student_id: number;
  account_id: number;
  full_name: string;
  email: string;
  registration_number: string;
  program: string;
  department: string | null;
  graduation_year: number | null;
  cgpa: number | null;
  target_role: string | null;
  profile_completion: number;
  overall_score: number | null;
  resume_status: ResumeStatus | null;
  pending_resume_reviews: number;
  pending_application_reviews: number;
  open_applications: number;
  needs_attention: boolean;
  attention_reasons: string[];
};

export type AdminStudentRow = StudentSummary & {
  mentor_names: string[];
  applications_count: number;
};

export type Feedback = {
  id: number;
  student_id: number;
  student_name: string | null;
  mentor_id: number;
  mentor_name: string | null;
  resume_id: number | null;
  application_id: number | null;
  title: string;
  body: string;
  status: FeedbackStatus;
  created_at: string;
};

export type MentorStudentDetail = {
  student: StudentSummary;
  skills: string[];
  missing_skills: string[];
  skill_coverage_percent: number;
  readiness_components: {
    overall_score?: number;
    level?: string;
    last_calculated?: string | null;
    components?: ReadinessComponent[];
  };
  readiness_history: ReadinessSnapshot[];
  resumes: Resume[];
  applications: Application[];
  feedback: Feedback[];
};

export type MentorDashboard = {
  mentor_name: string;
  assigned_student_count: number;
  pending_resume_reviews: number;
  pending_application_reviews: number;
  students_needing_attention: StudentSummary[];
  recent_feedback: Feedback[];
  recent_notifications: Notification[];
  average_readiness: number | null;
  unassigned_student_count: number;
};

export type Assignment = {
  id: number;
  mentor_id: number;
  mentor_name: string | null;
  student_id: number;
  student_name: string | null;
  registration_number: string | null;
  is_active: boolean;
  notes: string | null;
  created_at: string;
};

export type AdminUser = {
  id: number;
  full_name: string;
  email: string;
  role: UserRole;
  identifier: string;
  department_or_program: string;
  is_active: boolean;
  created_at: string;
};

export type AuditLog = {
  id: number;
  actor_account_id: number | null;
  actor_email: string | null;
  actor_role: string | null;
  action: string;
  entity_type: string;
  entity_id: number | null;
  summary: string | null;
  meta: Record<string, unknown>;
  created_at: string;
};

export type AdminDashboard = {
  counts: {
    students: number;
    mentors: number;
    administrators: number;
    companies: number;
    active_companies: number;
    job_postings: number;
    published_job_postings: number;
    placement_drives: number;
    open_drives: number;
    applications: number;
    applications_by_status: Record<string, number>;
    pending_mentor_reviews: number;
    pending_resume_reviews: number;
    students_without_mentor: number;
    notifications_unread: number;
  };
  upcoming_deadlines: {
    drive_id: number;
    drive_name: string;
    company_name: string | null;
    application_deadline: string | null;
    status: string;
    applications: number;
  }[];
  recent_applications: Application[];
  recent_audit_logs: AuditLog[];
  top_companies_by_drives: { company_id: number; company_name: string; drives: number }[];
};
