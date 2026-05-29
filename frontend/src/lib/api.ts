/**
 * JobPilot — API Client
 * Type-safe fetch wrapper with JWT auth, token refresh, and error handling.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost/api/v1";

interface FetchOptions extends RequestInit {
  skipAuth?: boolean;
}

// Token management
let accessToken: string | null = null;
let refreshToken: string | null = null;

export function setTokens(access: string, refresh: string) {
  accessToken = access;
  refreshToken = refresh;
  if (typeof window !== "undefined") {
    localStorage.setItem("jobpilot_access_token", access);
    localStorage.setItem("jobpilot_refresh_token", refresh);
  }
}

export function getTokens() {
  if (typeof window !== "undefined" && !accessToken) {
    accessToken = localStorage.getItem("jobpilot_access_token");
    refreshToken = localStorage.getItem("jobpilot_refresh_token");
  }
  return { accessToken, refreshToken };
}

export function clearTokens() {
  accessToken = null;
  refreshToken = null;
  if (typeof window !== "undefined") {
    localStorage.removeItem("jobpilot_access_token");
    localStorage.removeItem("jobpilot_refresh_token");
  }
}

async function attemptTokenRefresh(): Promise<boolean> {
  const { refreshToken: rt } = getTokens();
  if (!rt) return false;

  try {
    const res = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: rt }),
    });

    if (res.ok) {
      const data = await res.json();
      setTokens(data.access_token, data.refresh_token);
      return true;
    }
  } catch {
    // Refresh failed
  }

  clearTokens();
  return false;
}

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
    this.name = "ApiError";
  }
}

export async function api<T = unknown>(
  endpoint: string,
  options: FetchOptions = {}
): Promise<T> {
  const { skipAuth, ...fetchOptions } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(fetchOptions.headers as Record<string, string>),
  };

  if (!skipAuth) {
    const { accessToken: at } = getTokens();
    if (at) {
      headers["Authorization"] = `Bearer ${at}`;
    }
  }

  let res = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...fetchOptions,
    headers,
  });

  // If 401, try refreshing the token
  if (res.status === 401 && !skipAuth) {
    const refreshed = await attemptTokenRefresh();
    if (refreshed) {
      const { accessToken: newAt } = getTokens();
      headers["Authorization"] = `Bearer ${newAt}`;
      res = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...fetchOptions,
        headers,
      });
    }
  }

  if (!res.ok) {
    let detail = "An error occurred";
    try {
      const errorData = await res.json();
      detail = errorData.detail || errorData.message || detail;
    } catch {
      // Response wasn't JSON
    }
    throw new ApiError(res.status, detail);
  }

  // Handle 204 No Content
  if (res.status === 204) {
    return undefined as T;
  }

  return res.json();
}

// -------------------------------------------------------
// Typed API Methods
// -------------------------------------------------------

// Auth
export const authApi = {
  register: (data: { email: string; password: string; full_name: string }) =>
    api("/auth/register", { method: "POST", body: JSON.stringify(data), skipAuth: true }),

  login: (data: { email: string; password: string }) =>
    api("/auth/login", { method: "POST", body: JSON.stringify(data), skipAuth: true }),

  me: () => api("/auth/me"),
  
  updateMe: (data: Record<string, unknown>) =>
    api("/auth/me", { method: "PATCH", body: JSON.stringify(data) }),
};

// Applications
export const applicationsApi = {
  list: (params?: Record<string, string>) => {
    const query = params ? "?" + new URLSearchParams(params).toString() : "";
    return api(`/applications${query}`);
  },

  get: (id: string) => api(`/applications/${id}`),

  create: (data: Record<string, unknown>) =>
    api("/applications", { method: "POST", body: JSON.stringify(data) }),

  update: (id: string, data: Record<string, unknown>) =>
    api(`/applications/${id}`, { method: "PATCH", body: JSON.stringify(data) }),

  updateStatus: (id: string, status: string, notes?: string) =>
    api(`/applications/${id}/status`, { method: "PATCH", body: JSON.stringify({ status, notes }) }),

  delete: (id: string) =>
    api(`/applications/${id}`, { method: "DELETE" }),
};

// Interviews
export const interviewsApi = {
  list: (params?: Record<string, string>) => {
    const query = params ? "?" + new URLSearchParams(params).toString() : "";
    return api(`/interviews${query}`);
  },

  upcoming: (limit = 10) => api(`/interviews/upcoming?limit=${limit}`),

  create: (data: Record<string, unknown>) =>
    api("/interviews", { method: "POST", body: JSON.stringify(data) }),

  update: (id: string, data: Record<string, unknown>) =>
    api(`/interviews/${id}`, { method: "PATCH", body: JSON.stringify(data) }),

  addFeedback: (id: string, feedback: string, status = "completed") =>
    api(`/interviews/${id}/feedback`, { method: "PATCH", body: JSON.stringify({ feedback, status }) }),
};

// Analytics
export const analyticsApi = {
  overview: () => api("/analytics/overview"),
  statusBreakdown: () => api("/analytics/status-breakdown"),
  trends: (days = 30) => api(`/analytics/trends?days=${days}`),
  platformPerformance: () => api("/analytics/platform-performance"),
  heatmap: () => api("/analytics/heatmap"),
};

// Notifications
export const notificationsApi = {
  list: (params?: Record<string, string>) => {
    const query = params ? "?" + new URLSearchParams(params).toString() : "";
    return api(`/notifications${query}`);
  },
  unreadCount: () => api("/notifications/unread-count"),
  markRead: (id: string) => api(`/notifications/${id}/read`, { method: "PATCH" }),
  markAllRead: () => api("/notifications/read-all", { method: "POST" }),
};

// Follow-ups
export const followUpsApi = {
  list: (params?: Record<string, string>) => {
    const query = params ? "?" + new URLSearchParams(params).toString() : "";
    return api(`/follow-ups${query}`);
  },
  due: () => api("/follow-ups/due"),
  create: (data: Record<string, unknown>) =>
    api("/follow-ups", { method: "POST", body: JSON.stringify(data) }),
  complete: (id: string) =>
    api(`/follow-ups/${id}/complete`, { method: "PATCH" }),
};

// Resumes
export const resumesApi = {
  list: () => api("/resumes"),
  update: (id: string, data: Record<string, unknown>) =>
    api(`/resumes/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
};

// AI
export const aiApi = {
  parseJob: (text: string) =>
    api("/ai/parse-job", { method: "POST", body: JSON.stringify({ text }) }),
  classifyEmail: (data: { subject: string; body: string; from_address?: string }) =>
    api("/ai/classify-email", { method: "POST", body: JSON.stringify(data) }),
  generateInsights: (timeRangeDays = 30) =>
    api("/ai/generate-insights", { method: "POST", body: JSON.stringify({ time_range_days: timeRangeDays }) }),
  health: () => api("/ai/health"),
  integrationsStatus: () => api("/ai/integrations-status"),
};

// Email Events
export const emailEventsApi = {
  list: (params?: Record<string, string>) => {
    const query = params ? "?" + new URLSearchParams(params).toString() : "";
    return api(`/email-events${query}`);
  },
};

// Silent background authentication to bypass login form
export async function ensureSilentAuth(): Promise<boolean> {
  const { accessToken } = getTokens();
  if (accessToken) return true;

  const defaultCreds = {
    email: "mohdalipatel8976@gmail.com",
    password: "admin_password_123",
    full_name: "JobPilot Admin",
  };

  try {
    const loginData = (await authApi.login({
      email: defaultCreds.email,
      password: defaultCreds.password,
    })) as { access_token: string; refresh_token: string };
    setTokens(loginData.access_token, loginData.refresh_token);
    return true;
  } catch (err) {
    try {
      const regData = (await authApi.register(defaultCreds)) as {
        access_token: string;
        refresh_token: string;
      };
      setTokens(regData.access_token, regData.refresh_token);
      return true;
    } catch (regErr) {
      console.error("Silent authentication failed:", regErr);
      return false;
    }
  }
}

