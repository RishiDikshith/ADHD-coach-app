import { create } from "zustand";
import type { ChatMessage, ChatResponse, ScoreData, Intervention } from "@/lib/types";
import { api } from "@/services/api";

interface ChatState {
  messages: ChatMessage[];
  isThinking: boolean;
  isStreaming: boolean;
  scores: ScoreData;
  interventions: Intervention[];
  error: string | null;
  sendMessage: (text: string, username: string, userData?: Record<string, number>) => Promise<void>;
  addMessage: (msg: ChatMessage) => void;
  clearMessages: () => void;
  setThinking: (val: boolean) => void;
  clearError: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  isThinking: false,
  isStreaming: false,
  scores: {},
  interventions: [],
  error: null,

  sendMessage: async (text, username, userData) => {
    const userMsg: ChatMessage = {
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
    };

    set((s) => ({
      messages: [...s.messages, userMsg],
      isThinking: true,
      isStreaming: true,
      error: null,
    }));

    try {
      const history = get()
        .messages.slice(0, -1)
        .map((m) => ({ role: m.role, content: m.content }));

      const data = await api.chat({
        text,
        history,
        user_data: {
          sleep_hours: userData?.sleep_hours ?? 7,
          stress_level: userData?.stress_level ?? 5,
          phone_distractions: userData?.phone_distractions ?? 0,
        },
        session_data: {},
        language: "en",
        language_name: "English",
        username,
      });

      const assistantMsg: ChatMessage = {
        role: "assistant",
        content: data.reply,
        tasks: data.interventions?.slice(0, 3).map((i) => ({
          emoji: i.emoji || "✓",
          text: i.action || i.title,
        })),
        timestamp: new Date().toISOString(),
      };

      set((s) => ({
        messages: [...s.messages, assistantMsg],
        isThinking: false,
        isStreaming: false,
        scores: data.scores || {},
        interventions: data.interventions || [],
      }));
    } catch (err) {
      set({
        isThinking: false,
        isStreaming: false,
        error: err instanceof Error ? err.message : "Failed to get response",
      });
    }
  },

  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  clearMessages: () => set({ messages: [] }),
  setThinking: (val) => set({ isThinking: val }),
  clearError: () => set({ error: null }),
}));
