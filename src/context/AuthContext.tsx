import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { clearToken, getToken, setToken } from "../api/client";
import { getCurrentUser, login as loginRequest, register as registerRequest } from "../api/authApi";
import type { AuthPayload } from "../api/authApi";
import type { AuthUser, UserRole } from "../types";

export type SessionStatus = "loading" | "authenticated" | "anonymous";

type AuthContextValue = {
  status: SessionStatus;
  user: AuthUser | null;
  role: UserRole | null;
  sessionMessage: string;
  login: (email: string, password: string) => Promise<void>;
  register: (payload: AuthPayload) => Promise<void>;
  logout: (message?: string) => void;
  refresh: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [status, setStatus] = useState<SessionStatus>(() => (getToken() ? "loading" : "anonymous"));
  const [sessionMessage, setSessionMessage] = useState("");

  const loadUser = useCallback(async () => {
    if (!getToken()) {
      setUser(null);
      setStatus("anonymous");
      return;
    }

    setStatus("loading");
    try {
      const current = await getCurrentUser();
      setUser(current);
      setStatus("authenticated");
    } catch {
      clearToken();
      setUser(null);
      setStatus("anonymous");
      setSessionMessage("Your session could not be restored. Please sign in again.");
    }
  }, []);

  useEffect(() => {
    void loadUser();
  }, [loadUser]);

  useEffect(() => {
    function handleExpired() {
      setUser(null);
      setStatus("anonymous");
      setSessionMessage("Your session expired. Please sign in again.");
    }
    window.addEventListener("career:session-expired", handleExpired);
    return () => window.removeEventListener("career:session-expired", handleExpired);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const response = await loginRequest(email, password);
    setToken(response.access_token);
    setSessionMessage("");
    const current = await getCurrentUser();
    setUser(current);
    setStatus("authenticated");
  }, []);

  const register = useCallback(async (payload: AuthPayload) => {
    const response = await registerRequest(payload);
    setToken(response.access_token);
    setSessionMessage("");
    const current = await getCurrentUser();
    setUser(current);
    setStatus("authenticated");
  }, []);

  const logout = useCallback((message = "") => {
    clearToken();
    setUser(null);
    setStatus("anonymous");
    setSessionMessage(message);
    window.location.hash = "#/login";
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      status,
      user,
      role: user?.role ?? null,
      sessionMessage,
      login,
      register,
      logout,
      refresh: loadUser,
    }),
    [status, user, sessionMessage, login, register, logout, loadUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside an AuthProvider");
  }
  return context;
}

export function roleLabel(role: UserRole | null): "Student" | "Mentor" | "Admin" {
  if (role === "administrator") return "Admin";
  if (role === "mentor") return "Mentor";
  return "Student";
}
