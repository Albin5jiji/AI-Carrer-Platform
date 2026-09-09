export type Role = "Student" | "Mentor" | "Admin";

export type ScoreKey =
  | "academics"
  | "skills"
  | "projects"
  | "certifications"
  | "resume"
  | "interview";

export type StudentProfile = {
  name: string;
  regNo: string;
  program: string;
  targetRole: string;
  email: string;
  cgpa: number;
  skills: string[];
  projects: string[];
  certifications: string[];
  resumeStatus: "Draft" | "Pending Review" | "Approved" | "Changes Requested";
  portfolioUrl: string;
  githubUrl: string;
};

export type Application = {
  id: string;
  company: string;
  role: string;
  status:
    | "Not Applied"
    | "Pending Review"
    | "Applied"
    | "Shortlisted"
    | "Interview Scheduled"
    | "Approved"
    | "Changes Requested";
  eligibility: string;
  resumeVersion: string;
  updatedAt: string;
};

export type MentorNote = {
  title: string;
  note: string;
  status: "Open" | "Action Needed" | "Approved";
};

export type PlacementDrive = {
  company: string;
  role: string;
  deadline: string;
  eligibleStudents: number;
  needsMentorApproval: boolean;
};

export type AppState = {
  profile: StudentProfile;
  scores: Record<ScoreKey, number>;
  applications: Application[];
  mentorNotes: MentorNote[];
  drives: PlacementDrive[];
  timeline: string[];
  notifications: string[];
};
