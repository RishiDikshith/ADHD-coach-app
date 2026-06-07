"use client";

import type {
  ChatRequest,
  ChatResponse,
  ScoreData,
  AuthResponse,
  UserSettings,
  AnalyticsInsight,
} from "@/lib/types";

import { API_URL } from "@/lib/api";
const API_BASE = API_URL;
const API_TIMEOUT = 60000; // Increased to 60 seconds to support Render free tier cold starts

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {},
  retries = 2
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;

  for (let attempt = 0; attempt <= retries; attempt++) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
      console.warn(`[API REQUEST TIMEOUT] Request to ${url} timed out after ${API_TIMEOUT}ms. Aborting.`);
      controller.abort();
    }, API_TIMEOUT);

    console.log(`[API REQUEST START] ${options.method || "GET"} ${url} (Attempt ${attempt + 1}/${retries + 1})`);

    try {
      const res = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          "Content-Type": "application/json",
          ...options.headers,
        },
      });

      console.log(`[API REQUEST COMPLETE] ${options.method || "GET"} ${url} - Status: ${res.status}`);

      if (!res.ok) {
        const errorBody = await res.text().catch(() => "");
        console.error(`[API RESPONSE ERROR] ${options.method || "GET"} ${url} - Status: ${res.status}, Body:`, errorBody);

        let errorMessage = `API Error ${res.status}`;
        if (errorBody) {
          try {
            const parsed = JSON.parse(errorBody);
            if (parsed && typeof parsed === "object") {
              if (typeof parsed.detail === "string") {
                errorMessage = parsed.detail;
              } else if (Array.isArray(parsed.detail)) {
                errorMessage = parsed.detail.map((err: any) => err.msg || JSON.stringify(err)).join(", ");
              } else if (parsed.message) {
                errorMessage = parsed.message;
              } else if (parsed.error) {
                errorMessage = parsed.error;
              } else {
                errorMessage = errorBody.slice(0, 200);
              }
            }
          } catch {
            errorMessage = errorBody.slice(0, 200);
          }
        }
        throw new ApiError(errorMessage, res.status);
      }

      const responseText = await res.text();
      console.log(`[API RESPONSE SUCCESS] ${options.method || "GET"} ${url} - Body:`, responseText);

      try {
        return JSON.parse(responseText) as T;
      } catch (parseErr) {
        console.error(`[API PARSE ERROR] Failed to parse JSON response from ${url}:`, parseErr);
        throw new ApiError("Failed to parse JSON response", res.status);
      }
    } catch (err: any) {
      console.error(`[API FETCH FAILURE] ${options.method || "GET"} ${url} - Error:`, err);

      if (err.name === "AbortError" || controller.signal.aborted) {
        console.warn(`[API REQUEST TIMEOUT/ABORTED] Request to ${url} was aborted/timed out.`);
      }

      if (attempt === retries || err instanceof ApiError) {
        if (err instanceof ApiError) throw err;
        throw new ApiError(
          err instanceof Error ? err.message : "Network error",
          0
        );
      }
      
      const retryDelay = 1000 * (attempt + 1);
      console.log(`[API RETRY] Retrying request to ${url} in ${retryDelay}ms...`);
      await new Promise((r) => setTimeout(r, retryDelay));
    } finally {
      clearTimeout(timeoutId);
    }
  }

  throw new ApiError("Max retries exceeded", 0);
}

export const api = {
  // ==================== Chat ====================
  chat: (request: ChatRequest) =>
    fetchApi<ChatResponse>("/chat", {
      method: "POST",
      body: JSON.stringify(request),
    }),

  // ==================== Scores ====================
  getScores: (username: string, userData: Record<string, unknown> = {}) =>
    fetchApi<{ scores: ScoreData }>("/calculate_scores", {
      method: "POST",
      body: JSON.stringify({ username, user_data: userData }),
    }).then((res) => res.scores),

  // ==================== Analytics ====================
  getAnalytics: (username: string, userData: Record<string, unknown> = {}) =>
    fetchApi<{
      insights: AnalyticsInsight[];
      insight_summary: string;
      focus_patterns: Record<string, unknown>;
      mood_patterns: Record<string, unknown>;
      correlations: unknown[];
      recommendations: unknown[];
      priority_recommendations: unknown[];
      formatted_recommendations: string;
    }>("/analytics", {
      method: "POST",
      body: JSON.stringify({ username, user_data: userData }),
    }),

  // ==================== Interventions ====================
  getInterventions: (
    userData: Record<string, unknown>,
    scores: Record<string, unknown>
  ) =>
    fetchApi<{ interventions: unknown[] }>("/get_interventions", {
      method: "POST",
      body: JSON.stringify({ user_data: userData, scores }),
    }),

  // ==================== Auth ====================
  login: (username: string, password: string) =>
    fetchApi<AuthResponse>("/auth/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username, password }),
    }),

  register: (username: string, password: string) =>
    fetchApi<AuthResponse>("/auth/register", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username, password }),
    }),

  resetPassword: (username: string, email: string, newPassword: string) =>
    fetchApi<AuthResponse>("/auth/reset-password", {
      method: "POST",
      body: JSON.stringify({ username, email, new_password: newPassword }),
    }),

  loginPin: (username: string, pin: string) =>
    fetchApi<AuthResponse>("/auth/login-pin", {
      method: "POST",
      body: JSON.stringify({ username, pin }),
    }),

  hasPin: (username: string) =>
    fetchApi<{ has_pin: boolean }>(`/auth/has-pin/${encodeURIComponent(username)}`),

  setPin: (pin: string) =>
    fetchApi<{ success: boolean; message?: string }>("/auth/set-pin", {
      method: "POST",
      body: JSON.stringify({ pin }),
    }),

  removePin: () =>
    fetchApi<{ success: boolean; message?: string }>("/auth/remove-pin", {
      method: "POST",
    }),

  // ==================== Settings ====================
  getSettings: (username: string) =>
    fetchApi<UserSettings>(`/settings/${encodeURIComponent(username)}`),

  updateSettings: (username: string, settings: Partial<UserSettings>) =>
    fetchApi<UserSettings>(`/settings/${encodeURIComponent(username)}`, {
      method: "PUT",
      body: JSON.stringify(settings),
    }),

  // ==================== Memory ====================
  getMemoryContext: (username: string) =>
    fetchApi<Record<string, unknown>>(
      `/memory/${encodeURIComponent(username)}`
    ),

  // ==================== Agents ====================
  triggerAgent: (
    agentType: string,
    context: Record<string, unknown>
  ) =>
    fetchApi<Record<string, unknown>>("/agents/analyze", {
      method: "POST",
      body: JSON.stringify({ agent_type: agentType, context }),
    }),

  // ==================== Task Paralysis ====================
  analyzeTask: (
    taskDescription: string,
    userData: Record<string, unknown>
  ) =>
    fetchApi<Record<string, unknown>>("/task-paralysis/analyze", {
      method: "POST",
      body: JSON.stringify({ task: taskDescription, user_data: userData }),
    }),

  // ==================== Feedback & Support ====================
  submitFeedback: (
    username: string,
    rating: number,
    category: string,
    feedbackText?: string
  ) =>
    fetchApi<{
      success: boolean;
      message: string;
      xp_awarded: number;
      skill_status: { level: number; xp: number; xp_to_next: number; leveled_up: boolean };
      new_achievements: Array<{ id: string; title: string; description: string; xp_reward: number }>;
    }>("/feedback", {
      method: "POST",
      body: JSON.stringify({
        username,
        rating,
        category,
        feedback_text: feedbackText,
      }),
    }),

  submitSupportTicket: (
    username: string,
    type: string,
    subject: string,
    description: string
  ) =>
    fetchApi<{
      success: boolean;
      message: string;
      ticket: {
        id: number;
        type: string;
        subject: string;
        description: string;
        status: string;
        created_at: string;
      };
    }>("/support/ticket", {
      method: "POST",
      body: JSON.stringify({ username, type, subject, description }),
    }),

  getFaqs: () =>
    fetchApi<
      Array<{ id: string; question: string; answer: string }>
    >("/support/faqs"),

  getUserTickets: (username: string) =>
    fetchApi<{ success: boolean; tickets: any[] }>(`/support/tickets/${encodeURIComponent(username)}`),

  getAdminFeedbacks: () =>
    fetchApi<{ success: boolean; feedbacks: any[] }>("/admin/feedbacks"),

  getAdminTickets: () =>
    fetchApi<{ success: boolean; tickets: any[] }>("/admin/tickets"),

  updateTicketStatus: (id: number, status: string) =>
    fetchApi<{
      success: boolean;
      message: string;
      ticket: { id: number; status: string };
    }>(`/admin/tickets/${id}/status`, {
      method: "PUT",
      body: JSON.stringify({ status }),
    }),
};
