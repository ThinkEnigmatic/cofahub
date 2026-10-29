/** Thin fetch client for the COFAHUB JSON API (HTTP Basic auth). */

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export function getToken(): string | null {
  return localStorage.getItem("cofahub_token");
}

export function setToken(user: string, pass: string): void {
  const token = btoa(`${user}:${pass}`);
  localStorage.setItem("cofahub_token", token);
}

export function clearToken(): void {
  localStorage.removeItem("cofahub_token");
}

export async function api<T>(path: string): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Basic ${token}`;
  const res = await fetch(`${API_BASE}${path}`, { headers });
  if (res.status === 401) {
    clearToken();
    throw new ApiError(401, "unauthorized");
  }
  if (!res.ok) throw new ApiError(res.status, `HTTP ${res.status}`);
  return res.json() as Promise<T>;
}

export async function login(user: string, pass: string): Promise<boolean> {
  const token = btoa(`${user}:${pass}`);
  const res = await fetch(`${API_BASE}/login`, {
    headers: { Authorization: `Basic ${token}` },
  });
  if (res.ok) {
    localStorage.setItem("cofahub_token", token);
    return true;
  }
  return false;
}
