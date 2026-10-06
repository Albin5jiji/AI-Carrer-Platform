import { apiRequest, authRequest } from "./client";
import type { AuthUser, UserRole } from "../types";

export type AuthPayload = {
  full_name: string;
  email: string;
  password: string;
  role: Exclude<UserRole, "administrator"> | UserRole;
  identifier: string;
  department_or_program: string;
};

type TokenResponse = { access_token: string; token_type: string };

export function login(email: string, password: string) {
  return authRequest<TokenResponse>("/auth/login", { email, password });
}

export function register(payload: AuthPayload) {
  return authRequest<TokenResponse>("/auth/register", payload);
}

export function getCurrentUser() {
  return apiRequest<AuthUser>("/auth/me");
}
