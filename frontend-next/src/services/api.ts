"use client";

import type {
  ChatRequest,
  ChatResponse,
  ScoreData,
  AuthResponse,
  UserSettings,
  AnalyticsInsight,
} from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_TIMEOUT = 30000;

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
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), API_TIMEOUT);

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        signal: controller.signal,
        headers: {
          "Content-Type": "application/json",
          ...options.headers,
        },
      });

      if (!res.ok) {
        const errorBody = await res.text().catch(() => "Unknown error");
        throw new ApiError(
          `API ${res.status}: ${errorBody.slice(0, 200)}`,
          res.status
        );
      }

      return (await res.json()) as T;
    } catch (err) {
      if (attempt === retries || err instanceof ApiError) {
        if (err instanceof ApiError) throw err;
        throw new ApiError(
          err instanceof Error ? err.message : "Network error",
          0
        );
      }
      await new Promise((r) => setTimeout(r, 1000 * (attempt + 1)));
    } finally {
      // Only clear timeout on last attempt or success
      if (attempt === retries) clearTimeout(timeout);
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
    fetchApi<ScoreData>("/calculate_scores", {
      method: "POST",
      body: JSON.stringify({ username, user_data: userData }),
    }),

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
      body: JSON.stringify({ username, password }),
    }),

  register: (username: string, password: string, email?: string) =>
    fetchApi<AuthResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ username, password, email }),
    }),

  resetPassword: (username: string, email: string, newPassword: string) =>
    fetchApi<AuthResponse>("/auth/reset-password", {
      method: "POST",
      body: JSON.stringify({ username, email, new_password: newPassword }),
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
