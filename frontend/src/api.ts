import {
  GenerationResponse,
  GenerationEvent,
  FileNode,
  FileContentResponse,
  TokenResponse,
  AuthUserDetails,
} from "./types";

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "/api").replace(/\/$/, "");

const ACCESS_TOKEN_KEY = "buildbuddy_access_token";
const CSRF_TOKEN_KEY = "buildbuddy_csrf_token";
const USER_DETAILS_KEY = "buildbuddy_user_details";

// Token storage helpers
export function getStoredAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function setStoredAccessToken(token: string | null): void {
  if (token) {
    localStorage.setItem(ACCESS_TOKEN_KEY, token);
  } else {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
  }
}

export function getStoredCsrfToken(): string | null {
  return localStorage.getItem(CSRF_TOKEN_KEY);
}

export function setStoredCsrfToken(token: string | null): void {
  if (token) {
    localStorage.setItem(CSRF_TOKEN_KEY, token);
  } else {
    localStorage.removeItem(CSRF_TOKEN_KEY);
  }
}

export function getStoredUserDetails(): AuthUserDetails | null {
  const raw = localStorage.getItem(USER_DETAILS_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function setStoredUserDetails(details: AuthUserDetails | null): void {
  if (details) {
    localStorage.setItem(USER_DETAILS_KEY, JSON.stringify(details));
  } else {
    localStorage.removeItem(USER_DETAILS_KEY);
  }
}

export function clearAuthStorage(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(CSRF_TOKEN_KEY);
  localStorage.removeItem(USER_DETAILS_KEY);
}

// Request header helper
function getAuthHeaders(includeContentType: boolean = true): Record<string, string> {
  const headers: Record<string, string> = {};
  if (includeContentType) {
    headers["Content-Type"] = "application/json";
  }
  const token = getStoredAccessToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  const csrfToken = getStoredCsrfToken();
  if (csrfToken) {
    headers["X-CSRF-Token"] = csrfToken;
  }
  return headers;
}

// ================= Authentication APIs =================

export async function loginUser(email: string, password: string): Promise<TokenResponse> {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Invalid email or password");
  }

  const data: TokenResponse = await response.json();
  setStoredAccessToken(data.access_token);
  setStoredCsrfToken(data.csrf_token);
  return data;
}

export async function registerUser(
  email: string,
  password: string,
  orgName?: string
): Promise<TokenResponse> {
  const response = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ email, password, org_name: orgName }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to create account");
  }

  const data: TokenResponse = await response.json();
  setStoredAccessToken(data.access_token);
  setStoredCsrfToken(data.csrf_token);
  return data;
}

export async function getCurrentUser(): Promise<TokenResponse> {
  const response = await fetch(`${API_BASE}/auth/me`, {
    method: "GET",
    headers: getAuthHeaders(false),
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error("Not authenticated");
  }

  const data: TokenResponse = await response.json();
  if (data.access_token) {
    setStoredAccessToken(data.access_token);
  }
  if (data.csrf_token) {
    setStoredCsrfToken(data.csrf_token);
  }
  return data;
}

export async function logoutUser(): Promise<void> {
  try {
    await fetch(`${API_BASE}/auth/logout`, {
      method: "POST",
      headers: getAuthHeaders(true),
      credentials: "include",
    });
  } catch (err) {
    console.warn("Logout request failed, clearing local tokens:", err);
  } finally {
    clearAuthStorage();
  }
}

export async function forgotPassword(email: string): Promise<{ message: string }> {
  const response = await fetch(`${API_BASE}/auth/forgot-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ email }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to request password reset");
  }

  return response.json();
}

// ================= Generation APIs =================

export async function createGeneration(
  prompt: string,
  model?: string
): Promise<GenerationResponse> {
  const response = await fetch(`${API_BASE}/generations`, {
    method: "POST",
    headers: getAuthHeaders(true),
    credentials: "include",
    body: JSON.stringify({ prompt, model }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to start generation run");
  }

  return response.json();
}

export async function refineGeneration(
  id: string,
  prompt: string
): Promise<GenerationResponse> {
  const response = await fetch(`${API_BASE}/generations/${id}/refine`, {
    method: "POST",
    headers: getAuthHeaders(true),
    credentials: "include",
    body: JSON.stringify({ prompt }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to submit refinement edit request");
  }

  return response.json();
}

export async function getGeneration(id: string): Promise<GenerationResponse> {
  const response = await fetch(`${API_BASE}/generations/${id}`, {
    method: "GET",
    headers: getAuthHeaders(false),
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error("Failed to fetch generation status");
  }
  return response.json();
}

export async function getFileTree(id: string): Promise<FileNode[]> {
  const response = await fetch(`${API_BASE}/generations/${id}/files`, {
    method: "GET",
    headers: getAuthHeaders(false),
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error("Failed to fetch project files");
  }
  return response.json();
}

export async function getFileContent(
  id: string,
  path: string
): Promise<FileContentResponse> {
  const encodedPath = path
    .split("/")
    .map((segment) => encodeURIComponent(segment))
    .join("/");
  const response = await fetch(`${API_BASE}/generations/${id}/files/${encodedPath}`, {
    method: "GET",
    headers: getAuthHeaders(false),
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(`Failed to read file: ${path}`);
  }
  return response.json();
}

export async function cancelGeneration(id: string): Promise<boolean> {
  const response = await fetch(`${API_BASE}/generations/${id}/cancel`, {
    method: "POST",
    headers: getAuthHeaders(true),
    credentials: "include",
  });
  if (!response.ok) {
    return false;
  }
  const data = await response.json();
  return data.cancelled;
}

export function getDownloadUrl(id: string): string {
  return `${API_BASE}/generations/${id}/download`;
}

export function subscribeToEvents(
  id: string,
  onEvent: (event: GenerationEvent) => void,
  onError?: (error: any) => void
): () => void {
  const eventSource = new EventSource(`${API_BASE}/generations/${id}/events`);

  eventSource.onmessage = (e) => {
    try {
      const parsed: GenerationEvent = JSON.parse(e.data);
      onEvent(parsed);
    } catch (err) {
      console.error("Failed to parse SSE event payload:", err);
    }
  };

  eventSource.onerror = (err) => {
    if (onError) onError(err);
    eventSource.close();
  };

  return () => {
    eventSource.close();
  };
}
