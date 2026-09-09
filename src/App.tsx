import {
  Bell,
  BriefcaseBusiness,
  CheckCircle2,
  ChevronRight,
  ClipboardCheck,
  FileText,
  GraduationCap,
  LayoutDashboard,
  LineChart,
  Plus,
  RotateCcw,
  Save,
  Send,
  ShieldCheck,
  Sparkles,
  UsersRound,
} from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { getCurrentUser, login, register, type AuthMode, type AuthPayload, type AuthRole, type AuthUser } from "./authApi";
import { initialState, readinessWeights } from "./data";
import type { AppState, PlacementDrive, Role, ScoreKey } from "./types";
import { calculateReadinessScore, getReadinessLevel, getRecommendation, scoreLabels } from "./utils";

const scoreKeys = Object.keys(readinessWeights) as ScoreKey[];
const storageKey = "ai-career-platform-first-review";
const tokenStorageKey = "ai-career-platform-token";

function getTodayLabel() {
  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(new Date());
}

function loadState(): AppState {
  const saved = localStorage.getItem(storageKey);
  if (!saved) return initialState;

  try {
    return { ...initialState, ...JSON.parse(saved) } as AppState;
  } catch {
    return initialState;
  }
}

function App() {
  const [role, setRole] = useState<Role>("Student");
  const [authMode, setAuthMode] = useState<AuthMode>("login");
  const [token, setToken] = useState(() => localStorage.getItem(tokenStorageKey));
  const [user, setUser] = useState<AuthUser | null>(null);
  const [authError, setAuthError] = useState("");
  const [isAuthLoading, setIsAuthLoading] = useState(Boolean(token));
  const [state, setState] = useState<AppState>(loadState);
  const [skillInput, setSkillInput] = useState("");
  const [driveDraft, setDriveDraft] = useState<PlacementDrive>({
    company: "",
    role: "",
    deadline: "",
    eligibleStudents: 0,
    needsMentorApproval: true,
  });
  const [showNotifications, setShowNotifications] = useState(false);
  const [skillGapReport, setSkillGapReport] = useState<string[]>([]);

  useEffect(() => {
    localStorage.setItem(storageKey, JSON.stringify(state));
  }, [state]);

  useEffect(() => {
    if (!token) {
      setIsAuthLoading(false);
      return;
    }

    getCurrentUser(token)
      .then((currentUser) => {
        setUser(currentUser);
        setRole(roleFromAuth(currentUser.role));
        setAuthError("");
      })
      .catch(() => {
        localStorage.removeItem(tokenStorageKey);
        setToken(null);
        setUser(null);
      })
      .finally(() => setIsAuthLoading(false));
  }, [token]);

  const readinessScore = useMemo(() => calculateReadinessScore(state.scores), [state.scores]);
  const readinessLevel = getReadinessLevel(readinessScore);

  function addTimeline(message: string) {
    setState((current) => ({
      ...current,
      timeline: [message, ...current.timeline].slice(0, 8),
    }));
  }

  function addNotification(message: string) {
    setState((current) => ({
      ...current,
      notifications: [message, ...current.notifications].slice(0, 8),
    }));
  }

  function saveProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const targetRole = String(formData.get("targetRole") ?? state.profile.targetRole);
    const cgpa = Number(formData.get("cgpa") ?? state.profile.cgpa);

    setState((current) => ({
      ...current,
      profile: {
        ...current.profile,
        targetRole,
        cgpa,
        resumeStatus: "Pending Review",
      },
      scores: {
        ...current.scores,
        academics: Math.min(100, Math.round(cgpa * 10)),
        resume: Math.max(60, current.scores.resume - 2),
      },
      timeline: [`Profile saved for ${targetRole}`, ...current.timeline].slice(0, 8),
      notifications: ["Profile changes saved and resume marked Pending Review.", ...current.notifications].slice(0, 8),
    }));
  }

  function addSkill() {
    const nextSkill = skillInput.trim();
    if (!nextSkill || state.profile.skills.includes(nextSkill)) return;

    setState((current) => ({
      ...current,
      profile: {
        ...current.profile,
        skills: [...current.profile.skills, nextSkill],
        resumeStatus: "Pending Review",
      },
      scores: {
        ...current.scores,
        skills: Math.min(100, current.scores.skills + 4),
        resume: Math.min(100, current.scores.resume + 2),
      },
      timeline: [`Added skill: ${nextSkill}`, ...current.timeline].slice(0, 8),
      notifications: [`${nextSkill} added. Readiness Score recomputed.`, ...current.notifications].slice(0, 8),
    }));
    setSkillInput("");
  }

  function generateSkillGapReport() {
    const weakAreas = scoreKeys
      .filter((key) => state.scores[key] < 80)
      .sort((first, second) => state.scores[first] - state.scores[second])
      .slice(0, 3);

    const report = weakAreas.map((key) => {
      return `${scoreLabels[key]} is at ${state.scores[key]}/100. Next action: complete one targeted task and request mentor feedback.`;
    });

    setSkillGapReport(report);
    addTimeline("Generated AI-assisted skill-gap report");
    addNotification("Skill-gap report generated from latest readiness data.");
  }

  function applyToJob(applicationId: string) {
    setState((current) => ({
      ...current,
      applications: current.applications.map((application) => {
        if (application.id !== applicationId) return application;
        return {
          ...application,
          status: application.eligibility === "Eligible" ? "Pending Review" : "Not Applied",
          resumeVersion: application.eligibility === "Eligible" ? "Resume v2" : application.resumeVersion,
          updatedAt: getTodayLabel(),
        };
      }),
      timeline: [`Application ${applicationId} submitted for mentor review`, ...current.timeline].slice(0, 8),
      notifications: [`Application ${applicationId} is now pending mentor review.`, ...current.notifications].slice(0, 8),
    }));
  }

  function updateApplicationStatus(applicationId: string, status: "Approved" | "Changes Requested") {
    setState((current) => ({
      ...current,
      applications: current.applications.map((application) =>
        application.id === applicationId ? { ...application, status, updatedAt: getTodayLabel() } : application,
      ),
      mentorNotes: [
        {
          title: `Application ${status}`,
          note:
            status === "Approved"
              ? "Mentor approved the application for placement submission."
              : "Mentor requested changes before application submission.",
          status: status === "Approved" ? "Approved" : "Action Needed",
        },
        ...current.mentorNotes,
      ].slice(0, 6),
      timeline: [`Mentor marked ${applicationId} as ${status}`, ...current.timeline].slice(0, 8),
      notifications: [`Mentor marked ${applicationId} as ${status}.`, ...current.notifications].slice(0, 8),
    }));
  }

  function createDrive(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!driveDraft.company.trim() || !driveDraft.role.trim() || !driveDraft.deadline.trim()) return;

    setState((current) => ({
      ...current,
      drives: [{ ...driveDraft, eligibleStudents: Number(driveDraft.eligibleStudents) }, ...current.drives],
      applications: [
        {
          id: `APP-${Math.floor(2000 + Math.random() * 7000)}`,
          company: driveDraft.company,
          role: driveDraft.role,
          status: "Not Applied",
          eligibility: "Eligible",
          resumeVersion: "-",
          updatedAt: "Open",
        },
        ...current.applications,
      ],
      timeline: [`Admin published ${driveDraft.company} drive`, ...current.timeline].slice(0, 8),
      notifications: [`New drive published: ${driveDraft.company} - ${driveDraft.role}.`, ...current.notifications].slice(0, 8),
    }));

    setDriveDraft({
      company: "",
      role: "",
      deadline: "",
      eligibleStudents: 0,
      needsMentorApproval: true,
    });
  }

  function resetDemo() {
    setState(initialState);
    setSkillGapReport([]);
    localStorage.removeItem(storageKey);
  }

  async function handleAuthSubmit(payload: AuthPayload) {
    setAuthError("");
    setIsAuthLoading(true);

    try {
      const response =
        authMode === "register" ? await register(payload) : await login(payload.email, payload.password);
      localStorage.setItem(tokenStorageKey, response.access_token);
      setToken(response.access_token);
    } catch (error) {
      setAuthError(error instanceof Error ? error.message : "Authentication failed");
    } finally {
      setIsAuthLoading(false);
    }
  }

  function logout() {
    localStorage.removeItem(tokenStorageKey);
    setToken(null);
    setUser(null);
    setAuthMode("login");
  }

  if (!user) {
    return (
      <AuthScreen
        authError={authError}
        authMode={authMode}
        isLoading={isAuthLoading}
        onModeChange={setAuthMode}
        onSubmit={handleAuthSubmit}
      />
    );
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <Sparkles size={24} />
          </div>
          <div>
            <p>AI Career</p>
            <span>Working First Review</span>
          </div>
        </div>

        <nav className="nav-stack" aria-label="Primary navigation">
          {role === "Student" && (
            <>
              <a href="#dashboard" className="nav-item active">
                <LayoutDashboard size={18} />
                Dashboard
              </a>
              <a href="#profile" className="nav-item">
                <FileText size={18} />
                Profile & Resume
              </a>
              <a href="#applications" className="nav-item">
                <BriefcaseBusiness size={18} />
                Applications
              </a>
            </>
          )}
          {role === "Mentor" && (
            <a href="#mentor" className="nav-item active">
              <ClipboardCheck size={18} />
              Mentor Review
            </a>
          )}
          {role === "Admin" && (
            <a href="#admin" className="nav-item active">
              <ShieldCheck size={18} />
              Admin Drives
            </a>
          )}
        </nav>

        <section className="session-card" aria-label="Signed in role">
          <p>Signed in role</p>
          <strong>{role}</strong>
        </section>
      </aside>

      <section className="content">
        <header className="topbar">
          <div>
            <p className="eyebrow">{role} workspace</p>
            <h1>Career Intelligence & Placement Management</h1>
            <p className="session-line">
              Signed in as {user.full_name} · {user.role} · {user.identifier}
            </p>
          </div>
          <div className="topbar-actions">
            <button className="secondary-action" onClick={logout} type="button">
              Logout
            </button>
            <button className="secondary-action" onClick={resetDemo} type="button">
              <RotateCcw size={17} />
              Reset Demo
            </button>
            <button
              className="icon-button notification-button"
              onClick={() => setShowNotifications((current) => !current)}
              type="button"
              aria-label="Notifications"
            >
              <Bell size={20} />
              <span>{state.notifications.length}</span>
            </button>
          </div>
        </header>

        {showNotifications && (
          <section className="notification-panel">
            {state.notifications.map((notification) => (
              <p key={notification}>{notification}</p>
            ))}
          </section>
        )}

        {role === "Student" && (
          <>
            <section className="hero-grid" id="dashboard">
              <article className="readiness-panel">
                <div>
                  <p className="eyebrow">Placement Readiness Score</p>
                  <h2>{readinessScore}</h2>
                  <span>{readinessLevel}</span>
                </div>
                <div className="score-ring" aria-label={`Readiness score ${readinessScore} out of 100`}>
                  <svg viewBox="0 0 120 120" role="img">
                    <circle cx="60" cy="60" r="50" />
                    <circle
                      cx="60"
                      cy="60"
                      r="50"
                      style={{ strokeDashoffset: 314 - (314 * readinessScore) / 100 }}
                    />
                  </svg>
                  <strong>{readinessScore}%</strong>
                </div>
              </article>

              <article className="recommendation-panel">
                <div className="panel-icon">
                  <Sparkles size={20} />
                </div>
                <p className="eyebrow">AI-assisted recommendation</p>
                <h2>{getRecommendation(readinessScore)}</h2>
                <button className="primary-action" onClick={generateSkillGapReport} type="button">
                  Generate Skill-Gap Report
                  <ChevronRight size={17} />
                </button>
                {skillGapReport.length > 0 && (
                  <div className="report-box">
                    {skillGapReport.map((item) => (
                      <p key={item}>{item}</p>
                    ))}
                  </div>
                )}
              </article>
            </section>

            <section className="metric-grid" aria-label="Score breakdown">
              {scoreKeys.map((key) => (
                <article className="metric-card" key={key}>
                  <div>
                    <p>{scoreLabels[key]}</p>
                    <strong>{state.scores[key]}</strong>
                  </div>
                  <span>{readinessWeights[key]}% weight</span>
                  <div className="progress-track">
                    <div style={{ width: `${state.scores[key]}%` }} />
                  </div>
                </article>
              ))}
            </section>

            <section className="two-column">
              <article className="section-panel" id="profile">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Student Profile</p>
                <h2>{state.profile.name}</h2>
              </div>
              <GraduationCap size={24} />
            </div>
            <form className="form-grid" onSubmit={saveProfile}>
              <label>
                Target Role
                <input name="targetRole" defaultValue={state.profile.targetRole} />
              </label>
              <label>
                CGPA
                <input name="cgpa" defaultValue={state.profile.cgpa} max="10" min="0" step="0.1" type="number" />
              </label>
              <button className="primary-action" type="submit">
                <Save size={17} />
                Save Profile
              </button>
            </form>
            <div className="profile-list">
              <Info label="Register No" value={state.profile.regNo} />
              <Info label="Program" value={state.profile.program} />
              <Info label="Email" value={state.profile.email} />
              <Info label="Resume Status" value={state.profile.resumeStatus} />
            </div>
            <div className="inline-form">
              <input
                onChange={(event) => setSkillInput(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    event.preventDefault();
                    addSkill();
                  }
                }}
                placeholder="Add a skill"
                value={skillInput}
              />
              <button className="secondary-action" onClick={addSkill} type="button">
                <Plus size={17} />
                Add Skill
              </button>
            </div>
            <div className="chip-row">
              {state.profile.skills.map((skill) => (
                <span key={skill}>{skill}</span>
              ))}
            </div>
              </article>

              <article className="section-panel">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Career Timeline</p>
                <h2>Recent Activity</h2>
              </div>
              <LineChart size={24} />
            </div>
            <ol className="timeline">
              {state.timeline.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ol>
              </article>
            </section>

            <section className="section-panel" id="applications">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Application Tracking</p>
              <h2>Job Applications</h2>
            </div>
            <Send size={24} />
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Company</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Eligibility</th>
                  <th>Resume</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {state.applications.map((application) => (
                  <tr key={application.id}>
                    <td>{application.company}</td>
                    <td>{application.role}</td>
                    <td>
                      <StatusPill value={application.status} />
                    </td>
                    <td>{application.eligibility}</td>
                    <td>{application.resumeVersion}</td>
                    <td>
                      <button
                        className="table-action"
                        disabled={application.status !== "Not Applied" || application.eligibility !== "Eligible"}
                        onClick={() => applyToJob(application.id)}
                        type="button"
                      >
                        Apply
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
            </section>
          </>
        )}

        {role === "Mentor" && (
          <article className="section-panel" id="mentor">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Mentor Dashboard</p>
                <h2>Review Queue</h2>
              </div>
              <UsersRound size={24} />
            </div>
            <div className="mentor-actions">
              {state.applications
                .filter((application) => application.status === "Pending Review")
                .map((application) => (
                  <div className="approval-card" key={application.id}>
                    <div>
                      <strong>{application.company}</strong>
                      <span>{application.role}</span>
                    </div>
                    <button onClick={() => updateApplicationStatus(application.id, "Approved")} type="button">
                      Approve
                    </button>
                    <button onClick={() => updateApplicationStatus(application.id, "Changes Requested")} type="button">
                      Request Changes
                    </button>
                  </div>
                ))}
            </div>
            <div className="note-list">
              {state.mentorNotes.map((item) => (
                <div className="note-card" key={`${item.title}-${item.note}`}>
                  <span>{item.status}</span>
                  <strong>{item.title}</strong>
                  <p>{item.note}</p>
                </div>
              ))}
            </div>
          </article>
        )}

        {role === "Admin" && (
          <article className="section-panel" id="admin">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Admin Dashboard</p>
                <h2>Placement Drives</h2>
              </div>
              <CheckCircle2 size={24} />
            </div>
            <form className="drive-form" onSubmit={createDrive}>
              <input
                onChange={(event) => setDriveDraft((current) => ({ ...current, company: event.target.value }))}
                placeholder="Company"
                value={driveDraft.company}
              />
              <input
                onChange={(event) => setDriveDraft((current) => ({ ...current, role: event.target.value }))}
                placeholder="Role"
                value={driveDraft.role}
              />
              <input
                onChange={(event) => setDriveDraft((current) => ({ ...current, deadline: event.target.value }))}
                type="date"
                value={driveDraft.deadline}
              />
              <input
                min="0"
                onChange={(event) =>
                  setDriveDraft((current) => ({ ...current, eligibleStudents: Number(event.target.value) }))
                }
                placeholder="Eligible"
                type="number"
                value={driveDraft.eligibleStudents}
              />
              <button className="primary-action" type="submit">
                <Plus size={17} />
                Create Drive
              </button>
            </form>
            <div className="drive-list">
              {state.drives.map((drive) => (
                <div className="drive-row" key={`${drive.company}-${drive.role}-${drive.deadline}`}>
                  <div>
                    <strong>{drive.company}</strong>
                    <span>{drive.role}</span>
                  </div>
                  <p>{drive.deadline}</p>
                  <p>{drive.eligibleStudents} eligible</p>
                  <StatusPill value={drive.needsMentorApproval ? "Mentor Approval" : "Direct Apply"} />
                </div>
              ))}
            </div>
          </article>
        )}
      </section>
    </main>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function roleFromAuth(role: AuthRole): Role {
  if (role === "administrator") return "Admin";
  if (role === "mentor") return "Mentor";
  return "Student";
}

function AuthScreen({
  authError,
  authMode,
  isLoading,
  onModeChange,
  onSubmit,
}: {
  authError: string;
  authMode: AuthMode;
  isLoading: boolean;
  onModeChange: (mode: AuthMode) => void;
  onSubmit: (payload: AuthPayload) => Promise<void>;
}) {
  const [role, setRole] = useState<AuthRole>("student");

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    void onSubmit({
      fullName: String(formData.get("fullName") ?? ""),
      email: String(formData.get("email") ?? ""),
      password: String(formData.get("password") ?? ""),
      role,
      identifier: String(formData.get("identifier") ?? ""),
      departmentOrProgram: String(formData.get("departmentOrProgram") ?? ""),
    });
  }

  return (
    <main className="auth-shell">
      <section className="auth-copy">
        <div className="brand auth-brand">
          <div className="brand-mark">
            <Sparkles size={24} />
          </div>
          <div>
            <p>AI Career</p>
            <span>Review 1 Auth Slice</span>
          </div>
        </div>
        <h1>React, FastAPI, PostgreSQL, and JWT working together.</h1>
        <p>
          Register a Student, Mentor, or Administrator account. After login, the existing prototype unlocks with a
          validated session from the protected API route.
        </p>
      </section>

      <section className="auth-card">
        <div className="auth-tabs">
          <button className={authMode === "login" ? "selected" : ""} onClick={() => onModeChange("login")} type="button">
            Login
          </button>
          <button
            className={authMode === "register" ? "selected" : ""}
            onClick={() => onModeChange("register")}
            type="button"
          >
            Register
          </button>
        </div>

        <form className="auth-form" onSubmit={submit}>
          {authMode === "register" && (
            <>
              <label>
                Full Name
                <input name="fullName" placeholder="Albin Thomas Jiji" required />
              </label>
              <label>
                Role
                <select onChange={(event) => setRole(event.target.value as AuthRole)} value={role}>
                  <option value="student">Student</option>
                  <option value="mentor">Mentor</option>
                  <option value="administrator">Administrator</option>
                </select>
              </label>
            </>
          )}

          <label>
            Email
            <input name="email" placeholder="name@vitstudent.ac.in" required type="email" />
          </label>
          <label>
            Password
            <input minLength={8} name="password" placeholder="Minimum 8 characters" required type="password" />
          </label>

          {authMode === "register" && (
            <>
              <label>
                {role === "student" ? "Registration Number" : role === "mentor" ? "Employee Code" : "Staff Code"}
                <input name="identifier" placeholder={role === "student" ? "24BCE1141" : "EMP001"} required />
              </label>
              <label>
                {role === "student" ? "Program" : role === "mentor" ? "Department" : "Office"}
                <input
                  name="departmentOrProgram"
                  placeholder={role === "student" ? "B.Tech CSE" : "Placement Cell"}
                  required
                />
              </label>
            </>
          )}

          {authError && <p className="form-error">{authError}</p>}

          <button className="primary-action auth-submit" disabled={isLoading} type="submit">
            {isLoading ? "Please wait..." : authMode === "register" ? "Create Account" : "Login"}
          </button>
        </form>
      </section>
    </main>
  );
}

function StatusPill({ value }: { value: string }) {
  return <span className={`status status-${value.toLowerCase().replaceAll(" ", "-")}`}>{value}</span>;
}

export default App;
