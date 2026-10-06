import { useState } from "react";
import type { FormEvent } from "react";
import { GraduationCap, Sparkles, UsersRound } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import type { AuthPayload } from "../../api/authApi";
import { Alert } from "../../components/ui/primitives";

type Mode = "login" | "register";
type RegisterRole = "student" | "mentor";

export function AuthPage() {
  const { login, register, sessionMessage } = useAuth();
  const [mode, setMode] = useState<Mode>("login");
  const [role, setRole] = useState<RegisterRole>("student");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    setError("");
    setPending(true);
    try {
      if (mode === "login") {
        await login(String(formData.get("email") ?? ""), String(formData.get("password") ?? ""));
      } else {
        const payload: AuthPayload = {
          full_name: String(formData.get("full_name") ?? "").trim(),
          email: String(formData.get("email") ?? "").trim(),
          password: String(formData.get("password") ?? ""),
          role,
          identifier: String(formData.get("identifier") ?? "").trim(),
          department_or_program: String(formData.get("department_or_program") ?? "").trim(),
        };
        await register(payload);
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Authentication failed");
    } finally {
      setPending(false);
    }
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
            <span>Career Intelligence Platform</span>
          </div>
        </div>
        <h1>Student career readiness and placement management, end to end.</h1>
        <p>
          Track a Personal Readiness Score built from six measurable components, close skill gaps, follow a learning
          path, prepare for interviews and manage placement applications with mentor review.
        </p>
        <ul className="auth-points">
          <li>
            <GraduationCap size={18} /> Students: profile, resumes, readiness score, skill gaps, interview prep
          </li>
          <li>
            <UsersRound size={18} /> Mentors: assigned students, resume approval, application approval, feedback
          </li>
        </ul>
      </section>

      <section className="card auth-card">
        <div className="auth-tabs">
          <button className={mode === "login" ? "selected" : ""} onClick={() => setMode("login")} type="button">
            Sign in
          </button>
          <button className={mode === "register" ? "selected" : ""} onClick={() => setMode("register")} type="button">
            Create account
          </button>
        </div>

        {sessionMessage && !error && <Alert tone="warning">{sessionMessage}</Alert>}

        <form className="form-grid form-single" onSubmit={submit}>
          {mode === "register" && (
            <>
              <label className="field">
                <span className="field-label">Full name</span>
                <input name="full_name" minLength={2} placeholder="Albin Thomas Jiji" required />
              </label>
              <div className="field">
                <span className="field-label">Registering as</span>
                <div className="role-toggle">
                  <button
                    className={role === "student" ? "role-option active" : "role-option"}
                    onClick={() => setRole("student")}
                    type="button"
                  >
                    <GraduationCap size={16} /> Student
                  </button>
                  <button
                    className={role === "mentor" ? "role-option active" : "role-option"}
                    onClick={() => setRole("mentor")}
                    type="button"
                  >
                    <UsersRound size={16} /> Mentor
                  </button>
                </div>
                <span className="field-hint">Administrator accounts are created by the placement cell.</span>
              </div>
            </>
          )}

          <label className="field">
            <span className="field-label">Email</span>
            <input name="email" placeholder="name@vitstudent.ac.in" required type="email" />
          </label>
          <label className="field">
            <span className="field-label">Password</span>
            <input name="password" minLength={8} placeholder="Minimum 8 characters" required type="password" />
          </label>

          {mode === "register" && (
            <>
              <label className="field">
                <span className="field-label">{role === "student" ? "Registration number" : "Employee code"}</span>
                <input name="identifier" placeholder={role === "student" ? "24BCE1141" : "EMP001"} required />
              </label>
              <label className="field">
                <span className="field-label">{role === "student" ? "Program" : "Department"}</span>
                <input
                  name="department_or_program"
                  placeholder={role === "student" ? "B.Tech CSE" : "Placement Cell"}
                  required
                />
              </label>
            </>
          )}

          {error && <p className="form-error">{error}</p>}

          <button className="btn btn-primary btn-block" disabled={pending} type="submit">
            {pending ? "Please wait…" : mode === "register" ? "Create account" : "Sign in"}
          </button>
        </form>

        <p className="auth-foot">
          Demo accounts after running the demo seed: <code>albin@vitstudent.ac.in</code> / <code>Student@12345</code> ·{" "}
          <code>mentor@campus.edu</code> / <code>Mentor@12345</code> · <code>admin@campus.edu</code> /{" "}
          <code>Admin@12345</code>
        </p>
      </section>
    </main>
  );
}
