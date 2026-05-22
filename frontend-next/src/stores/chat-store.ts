import { create } from "zustand";
import type { ChatMessage, ScoreData, Intervention } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ChatState {
  messages: ChatMessage[];
  messagesByAgent: Record<string, ChatMessage[]>;
  activeAgentId: string;
  isThinking: boolean;
  isStreaming: boolean;
  scores: ScoreData;
  interventions: Intervention[];
  handoffSuggestion: { agent_id: string; message: string } | null;
  error: string | null;
  sendMessage: (text: string, username: string, userData?: Record<string, number>, language?: string) => Promise<void>;
  addMessage: (msg: ChatMessage) => void;
  clearMessages: () => void;
  setThinking: (val: boolean) => void;
  clearError: () => void;
  setActiveAgentId: (agentId: string) => void;
  setHandoffSuggestion: (val: { agent_id: string; message: string } | null) => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  messagesByAgent: {},
  activeAgentId: "productivity-coach",
  isThinking: false,
  isStreaming: false,
  scores: {},
  interventions: [],
  handoffSuggestion: null,
  error: null,

  setActiveAgentId: (agentId) => {
    set((s) => ({
      activeAgentId: agentId,
      messages: s.messagesByAgent[agentId] || [],
      handoffSuggestion: null, // Clear handoffs when switching agents
    }));
  },

  setHandoffSuggestion: (val) => set({ handoffSuggestion: val }),

  sendMessage: async (text, username, userData, language = "auto") => {
    const currentAgent = get().activeAgentId;
    const userMsg: ChatMessage = {
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
    };

    set((s) => {
      const agentHistory = s.messagesByAgent[currentAgent] || [];
      const updatedHistory = [...agentHistory, userMsg];
      return {
        messagesByAgent: {
          ...s.messagesByAgent,
          [currentAgent]: updatedHistory,
        },
        messages: updatedHistory,
        isThinking: true,
        isStreaming: true,
        handoffSuggestion: null, // Clear on new message
        error: null,
      };
    });

    try {
      const agentHistory = get().messagesByAgent[currentAgent] || [];
      const history = agentHistory
        .slice(0, -1) // Exclude the user message we just added
        .map((m) => ({ role: m.role, content: m.content }));

      const response = await fetch(`${API_BASE}/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          text,
          history,
          user_data: {
            sleep_hours: userData?.sleep_hours ?? 7,
            stress_level: userData?.stress_level ?? 5,
            phone_distractions: userData?.phone_distractions ?? 0,
            energy_level: userData?.energy_level ?? 5,
          },
          session_data: {},
          language,
          language_name: language === "auto" ? "Auto-Detect" : language,
          username,
          agent_id: currentAgent,
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API Error ${response.status}: ${errorText}`);
      }

      set({ isThinking: false });

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) throw new Error("Response body is not readable");

      let accumulatedContent = "";
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        // Keep the last incomplete line in the buffer
        buffer = lines.pop() || "";

        for (const line of lines) {
          const cleanLine = line.trim();
          if (!cleanLine.startsWith("data: ")) continue;

          try {
            const rawJson = cleanLine.substring(6);
            const parsed = JSON.parse(rawJson);

            if (parsed.token) {
              accumulatedContent += parsed.token;
              set((s) => {
                const history = s.messagesByAgent[currentAgent] || [];
                const lastMsgIndex = history.length - 1;
                const updatedHistory = [...history];

                if (lastMsgIndex >= 0 && updatedHistory[lastMsgIndex].role === "assistant") {
                  updatedHistory[lastMsgIndex] = {
                    ...updatedHistory[lastMsgIndex],
                    content: accumulatedContent,
                  };
                } else {
                  updatedHistory.push({
                    role: "assistant",
                    content: accumulatedContent,
                    timestamp: new Date().toISOString(),
                  });
                }

                return {
                  messagesByAgent: {
                    ...s.messagesByAgent,
                    [currentAgent]: updatedHistory,
                  },
                  messages: updatedHistory,
                };
              });
            } else if (parsed.metadata) {
              const meta = parsed.metadata;
              set((s) => {
                const history = s.messagesByAgent[currentAgent] || [];
                const lastMsgIndex = history.length - 1;
                const updatedHistory = [...history];

                if (lastMsgIndex >= 0 && updatedHistory[lastMsgIndex].role === "assistant") {
                  updatedHistory[lastMsgIndex] = {
                    ...updatedHistory[lastMsgIndex],
                    content: meta.reply || accumulatedContent,
                    tasks: meta.interventions?.slice(0, 3).map((i: { emoji?: string; action?: string; title?: string }) => ({
                      emoji: i.emoji || "✓",
                      text: i.action || i.title,
                    })),
                  };
                }

                return {
                  messagesByAgent: {
                    ...s.messagesByAgent,
                    [currentAgent]: updatedHistory,
                  },
                  messages: updatedHistory,
                  scores: meta.scores || {},
                  interventions: meta.interventions || [],
                  handoffSuggestion: meta.handoff_suggestion || null,
                  isStreaming: false,
                };
              });
            }
          } catch (e) {
            console.error("Error parsing stream line:", e, cleanLine);
          }
        }
      }

      set({ isStreaming: false });
    } catch (err) {
      set({
        isThinking: false,
        isStreaming: false,
        error: err instanceof Error ? err.message : "Failed to get response",
      });
    }
  },

  addMessage: (msg) => {
    const currentAgent = get().activeAgentId;
    set((s) => {
      const history = s.messagesByAgent[currentAgent] || [];
      const updatedHistory = [...history, msg];
      return {
        messagesByAgent: {
          ...s.messagesByAgent,
          [currentAgent]: updatedHistory,
        },
        messages: updatedHistory,
      };
    });
  },

  clearMessages: () => {
    const currentAgent = get().activeAgentId;
    set((s) => ({
      messagesByAgent: {
        ...s.messagesByAgent,
        [currentAgent]: [],
      },
      messages: [],
      handoffSuggestion: null,
    }));
  },

  setThinking: (val) => set({ isThinking: val }),
  clearError: () => set({ error: null }),
}));

