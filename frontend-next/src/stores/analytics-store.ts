import { create } from "zustand";
import type { AnalyticsInsight, ScoreData, FocusPattern, MoodEntry, ProductivityCorrelation } from "@/lib/types";
import { api } from "@/services/api";

interface AnalyticsState {
  insights: AnalyticsInsight[];
  scores: ScoreData;
  focusPatterns: FocusPattern[];
  moodHistory: MoodEntry[];
  correlations: ProductivityCorrelation[];
  currentMood: string;
  timeBlindnessEnabled: boolean;
  overwhelmMode: boolean;
  startTinyMode: boolean;
  loading: boolean;
  error: string | null;
  setInsights: (insights: AnalyticsInsight[]) => void;
  setScores: (scores: ScoreData) => void;
  addMood: (emoji: string, energy?: number, note?: string) => void;
  setCurrentMood: (emoji: string) => void;
  toggleTimeBlindness: () => void;
  setOverwhelmMode: (val: boolean) => void;
  setStartTinyMode: (val: boolean) => void;
  loadAnalytics: (username: string) => Promise<void>;
}

export const useAnalyticsStore = create<AnalyticsState>((set, get) => ({
  insights: [],
  scores: {},
  focusPatterns: [],
  moodHistory: [],
  correlations: [],
  currentMood: "",
  timeBlindnessEnabled: true,
  overwhelmMode: false,
  startTinyMode: false,
  loading: false,
  error: null,

  setInsights: (insights) => set({ insights }),
  setScores: (scores) => set({ scores }),

  addMood: (emoji, energy, note) => {
    const labelMap: Record<string, string> = {
      "😊": "Happy", "😌": "Calm", "😐": "Okay",
      "😟": "Worried", "😰": "Anxious", "😤": "Frustrated",
    };
    const entry: MoodEntry = {
      emoji, label: labelMap[emoji] || emoji, timestamp: new Date().toISOString(), energy, note,
    };
    set((s) => ({
      currentMood: emoji,
      moodHistory: [...s.moodHistory.slice(-60), entry],
    }));
  },

  setCurrentMood: (emoji) => set({ currentMood: emoji }),
  toggleTimeBlindness: () => set((s) => ({ timeBlindnessEnabled: !s.timeBlindnessEnabled })),
  setOverwhelmMode: (val) => set({ overwhelmMode: val }),
  setStartTinyMode: (val) => set({ startTinyMode: val }),

  loadAnalytics: async (username) => {
    set({ loading: true, error: null });
    try {
      const data = await api.getAnalytics(username);
      set({
        insights: data.insights || [],
        focusPatterns: Object.values(data.focus_patterns || {}).flat() as FocusPattern[],
        correlations: (data.correlations || []) as ProductivityCorrelation[],
        loading: false,
      });
    } catch (err) {
      set({
        loading: false,
        error: err instanceof Error ? err.message : "Failed to load analytics",
      });
    }
  },
}));
