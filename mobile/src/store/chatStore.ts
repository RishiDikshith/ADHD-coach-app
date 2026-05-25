import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { ChatMessage, ScoreData, Intervention } from "../api/types";
import { hybridStorage } from "./mmkvStorage";
import apiClient, { API_BASE } from "../api/client";

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
  sendMessage: (
    text: string,
    username: string,
    userData?: Record<string, any>,
    language?: string
  ) => Promise<void>;
  addMessage: (msg: ChatMessage) => void;
  clearMessages: () => void;
  setThinking: (val: boolean) => void;
  clearError: () => void;
  setActiveAgentId: (agentId: string) => void;
  setHandoffSuggestion: (val: { agent_id: string; message: string } | null) => void;
}

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
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
            handoffSuggestion: null,
            error: null,
          };
        });

        try {
          const agentHistory = get().messagesByAgent[currentAgent] || [];
          const history = agentHistory
            .slice(0, -1) // Exclude the user message we just added
            .map((m) => ({ role: m.role, content: m.content }));

          // API POST call for Chat. Since RN fetch readable streams require polyfills,
          // we use standard HTTP POST with highly responsive token simulation for ADHD UX!
          const chatPayload = {
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
          };

          const response = await apiClient.post("/chat", chatPayload);
          const data = response.data;

          set({ isThinking: false });

          // Simulate streaming/typing effect token-by-token for high engagement ADHD UX
          const fullReply = data.reply || "";
          const tokens = fullReply.split(/(\s+)/); // Splitting by words and spaces
          let currentReply = "";
          let tokenIndex = 0;

          const typingInterval = setInterval(() => {
            if (tokenIndex < tokens.length) {
              currentReply += tokens[tokenIndex];
              tokenIndex++;

              set((s) => {
                const history = s.messagesByAgent[currentAgent] || [];
                const lastMsgIndex = history.length - 1;
                const updatedHistory = [...history];

                if (lastMsgIndex >= 0 && updatedHistory[lastMsgIndex].role === "assistant") {
                  updatedHistory[lastMsgIndex] = {
                    ...updatedHistory[lastMsgIndex],
                    content: currentReply,
                  };
                } else {
                  updatedHistory.push({
                    role: "assistant",
                    content: currentReply,
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
            } else {
              clearInterval(typingInterval);
              // Complete streaming transition and set metadata
              set((s) => {
                const history = s.messagesByAgent[currentAgent] || [];
                const lastMsgIndex = history.length - 1;
                const updatedHistory = [...history];

                if (lastMsgIndex >= 0 && updatedHistory[lastMsgIndex].role === "assistant") {
                  updatedHistory[lastMsgIndex] = {
                    ...updatedHistory[lastMsgIndex],
                    tasks: data.interventions?.slice(0, 3).map((i: any) => ({
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
                  scores: data.scores || {},
                  interventions: data.interventions || [],
                  handoffSuggestion: data.handoff_suggestion || null,
                  isStreaming: false,
                };
              });
            }
          }, 30); // 30ms per token - fast but visual and satisfying
        } catch (err: any) {
          set({
            isThinking: false,
            isStreaming: false,
            error: err?.message || "Failed to get response",
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
    }),
    {
      name: "adhd-coach-chat-store",
      storage: createJSONStorage(() => hybridStorage),
      partialize: (state) => ({
        messagesByAgent: state.messagesByAgent,
        scores: state.scores,
        interventions: state.interventions,
      }),
    }
  )
);
