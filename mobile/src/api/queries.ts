import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import apiClient, { setAuthToken } from "./client";
import type {
  ChatMessage,
  ChatRequest,
  ChatResponse,
  ScoreData,
  AuthResponse,
  UserSettings,
  AnalyticsInsight,
  FocusPattern,
  ProductivityCorrelation,
} from "./types";

// Cache Keys constants
export const QUERY_KEYS = {
  settings: (username: string) => ["settings", username] as const,
  analytics: (username: string) => ["analytics", username] as const,
  scores: (username: string) => ["scores", username] as const,
  memory: (username: string) => ["memory", username] as const,
};

// ==================== Auth Queries & Mutations ====================
export const useLoginMutation = () => {
  return useMutation({
    mutationFn: async ({ username, password }: Record<string, string>) => {
      const response = await apiClient.post<AuthResponse>("/auth/login", {
        username,
        password,
      });
      if (response.data.success && response.data.token) {
        setAuthToken(response.data.token);
      }
      return response.data;
    },
  });
};

export const useRegisterMutation = () => {
  return useMutation({
    mutationFn: async ({ username, password, email }: Record<string, string>) => {
      const response = await apiClient.post<AuthResponse>("/auth/register", {
        username,
        password,
        email,
      });
      if (response.data.success && response.data.token) {
        setAuthToken(response.data.token);
      }
      return response.data;
    },
  });
};

export const useResetPasswordMutation = () => {
  return useMutation({
    mutationFn: async ({ username, email, newPassword }: Record<string, string>) => {
      const response = await apiClient.post<AuthResponse>("/auth/reset-password", {
        username,
        email,
        new_password: newPassword,
      });
      return response.data;
    },
  });
};

// ==================== Settings Queries & Mutations ====================
export const useSettingsQuery = (username: string, enabled = false) => {
  return useQuery({
    queryKey: QUERY_KEYS.settings(username),
    queryFn: async () => {
      const response = await apiClient.get<UserSettings>(
        `/settings/${encodeURIComponent(username)}`
      );
      return response.data;
    },
    enabled: enabled && !!username,
    staleTime: 5 * 60 * 1000, // 5 mins cache
  });
};

export const useUpdateSettingsMutation = (username: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (settings: Partial<UserSettings>) => {
      const response = await apiClient.put<UserSettings>(
        `/settings/${encodeURIComponent(username)}`,
        settings
      );
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.setQueryData(QUERY_KEYS.settings(username), data);
    },
  });
};

// ==================== Analytics Query ====================
export interface AnalyticsData {
  insights: AnalyticsInsight[];
  insight_summary: string;
  focus_patterns: Record<string, FocusPattern[]>;
  mood_patterns: Record<string, unknown>;
  correlations: ProductivityCorrelation[];
  recommendations: unknown[];
  priority_recommendations: unknown[];
  formatted_recommendations: string;
}

export const useAnalyticsQuery = (username: string, userData: Record<string, unknown> = {}, enabled = false) => {
  return useQuery({
    queryKey: QUERY_KEYS.analytics(username),
    queryFn: async () => {
      const response = await apiClient.post<AnalyticsData>("/analytics", {
        username,
        user_data: userData,
      });
      return response.data;
    },
    enabled: enabled && !!username,
    staleTime: 2 * 60 * 1000, // 2 mins cache
  });
};

// ==================== Score Queries ====================
export const useScoresMutation = () => {
  return useMutation({
    mutationFn: async ({ username, userData }: { username: string; userData: Record<string, unknown> }) => {
      const response = await apiClient.post<{ scores: ScoreData }>("/calculate_scores", {
        username,
        user_data: userData,
      });
      return response.data.scores;
    },
  });
};

// ==================== Task Paralysis (Start Tiny Breakdown) Mutation ====================
export const useAnalyzeTaskMutation = () => {
  return useMutation({
    mutationFn: async ({ taskDescription, userData }: { taskDescription: string; userData: Record<string, unknown> }) => {
      const response = await apiClient.post<Record<string, any>>("/task-paralysis/analyze", {
        task: taskDescription,
        user_data: userData,
      });
      return response.data;
    },
  });
};

// ==================== AI Chat / Streaming fallback ====================
export const useChatMutation = () => {
  return useMutation({
    mutationFn: async (request: ChatRequest) => {
      const response = await apiClient.post<ChatResponse>("/chat", request);
      return response.data;
    },
  });
};

// ==================== AI Agent Orchestration analyze ====================
export const useAgentAnalyzeMutation = () => {
  return useMutation({
    mutationFn: async ({ agentType, context }: { agentType: string; context: Record<string, unknown> }) => {
      const response = await apiClient.post<Record<string, unknown>>("/agents/analyze", {
        agent_type: agentType,
        context,
      });
      return response.data;
    },
  });
};

// ==================== Feedback & Support Mutations ====================
export const useSubmitFeedbackMutation = () => {
  return useMutation({
    mutationFn: async ({
      username,
      rating,
      category,
      feedbackText,
    }: {
      username: string;
      rating: number;
      category: string;
      feedbackText?: string;
    }) => {
      const response = await apiClient.post<{
        success: boolean;
        message: string;
        xp_awarded: number;
        skill_status: { level: number; xp: number; xp_to_next: number; leveled_up: boolean };
        new_achievements: Array<{ id: string; title: string; description: string; xp_reward: number }>;
      }>("/feedback", {
        username,
        rating,
        category,
        feedback_text: feedbackText,
      });
      return response.data;
    },
  });
};
