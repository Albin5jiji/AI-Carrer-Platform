import type { AppState, Application, MentorNote, PlacementDrive, StudentProfile } from "./types";

export const readinessWeights = {
  academics: 15,
  skills: 30,
  projects: 20,
  certifications: 10,
  resume: 15,
  interview: 10,
};

export const studentProfile: StudentProfile = {
  name: "Albin Thomas Jiji",
  regNo: "24BCE1141",
  program: "B.Tech Computer Science and Engineering",
  targetRole: "AI / Full-Stack Developer",
  email: "albin.24bce1141@vitstudent.ac.in",
  cgpa: 8.7,
  skills: ["React", "Python", "FastAPI", "PostgreSQL", "Machine Learning"],
  projects: [
    "AI Career Intelligence Platform",
    "Resume Analyzer",
    "Placement Drive Tracker",
  ],
  certifications: ["Python for Data Science", "Frontend Development"],
  resumeStatus: "Pending Review",
  portfolioUrl: "https://portfolio.example.com/albin",
  githubUrl: "https://github.com/Albin5jiji",
};

export const scoreInputs = {
  academics: 87,
  skills: 78,
  projects: 82,
  certifications: 70,
  resume: 76,
  interview: 68,
};

export const applications: Application[] = [
  {
    id: "APP-1024",
    company: "TCS Digital",
    role: "Software Engineer",
    status: "Shortlisted",
    eligibility: "Eligible",
    resumeVersion: "Resume v2",
    updatedAt: "22 Jul 2026",
  },
  {
    id: "APP-1025",
    company: "Zoho",
    role: "Frontend Developer Intern",
    status: "Pending Review",
    eligibility: "Eligible",
    resumeVersion: "Resume v2",
    updatedAt: "23 Jul 2026",
  },
  {
    id: "APP-1026",
    company: "Infosys",
    role: "Systems Engineer",
    status: "Not Applied",
    eligibility: "Missing certification preference",
    resumeVersion: "-",
    updatedAt: "Open",
  },
];

export const mentorNotes: MentorNote[] = [
  {
    title: "Resume headline",
    note: "Make the AI platform project the first project and add measurable outcomes.",
    status: "Action Needed",
  },
  {
    title: "Interview practice",
    note: "Complete two DSA mock rounds before applying to product companies.",
    status: "Open",
  },
  {
    title: "Profile evidence",
    note: "GitHub and portfolio links are present and verified.",
    status: "Approved",
  },
];

export const drives: PlacementDrive[] = [
  {
    company: "TCS Digital",
    role: "Software Engineer",
    deadline: "28 Jul 2026",
    eligibleStudents: 184,
    needsMentorApproval: true,
  },
  {
    company: "Zoho",
    role: "Frontend Developer Intern",
    deadline: "30 Jul 2026",
    eligibleStudents: 96,
    needsMentorApproval: true,
  },
  {
    company: "Infosys",
    role: "Systems Engineer",
    deadline: "03 Aug 2026",
    eligibleStudents: 242,
    needsMentorApproval: false,
  },
];

export const timeline = [
  "Profile updated with FastAPI and PostgreSQL skills",
  "Resume v2 submitted for mentor review",
  "Readiness Score recomputed after mock interview",
  "Application submitted to TCS Digital",
];

export const initialState: AppState = {
  profile: studentProfile,
  scores: scoreInputs,
  applications,
  mentorNotes,
  drives,
  timeline,
  notifications: [
    "Zoho application is waiting for mentor approval.",
    "Skill-gap report can be regenerated after profile changes.",
  ],
};
