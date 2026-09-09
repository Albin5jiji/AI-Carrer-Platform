export type AuthRole = "student" | "mentor" | "administrator";

export type AuthUser = {
  id: number;
  full_name: string;
  email: string;
  role: AuthRole;
  identifier: string;
  department_or_program: string;
};

export type AuthMode = "login" | "register";

export type AuthPayload = {
  fullName: string;
  email: string;
  password: string;
  role: AuthRole;
  identifier: string;
  departmentOrProgram: string;
};

const apiBaseUrl = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

async function parseResponse<T>(response: Response): Promise<T> {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail ?? "Request failed");
  }

  return data as T;
}

export async function register(payload: AuthPayload) {
  const response = await fetch(`${apiBaseUrl}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      full_name: payload.fullName,
      email: payload.email,
      password: payload.password,
      role: payload.role,
      identifier: payload.identifier,
      department_or_program: payload.departmentOrProgram,
    }),
  });

  return parseResponse<{ access_token: string; token_type: string }>(response);
}

export async function login(email: string, password: string) {
  const response = await fetch(`${apiBaseUrl}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  return parseResponse<{ access_token: string; token_type: string }>(response);
}

export async function getCurrentUser(token: string) {
  const response = await fetch(`${apiBaseUrl}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });

  return parseResponse<AuthUser>(response);
}
