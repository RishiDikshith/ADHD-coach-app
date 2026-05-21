import { create } from "zustand";
import { formatTime } from "@/lib/utils";

interface TimerState {
  isActive: boolean;
  seconds: number;
  duration: number;
  startTime: number | null;
  sessionsCompleted: number;
  setDuration: (minutes: number) => void;
  start: () => void;
  stop: () => void;
  tick: () => boolean;
  reset: () => void;
  getRemaining: () => { mins: number; secs: number };
  getProgress: () => number;
  getFormattedTime: () => string;
}

export const useTimerStore = create<TimerState>((set, get) => ({
  isActive: false,
  seconds: 25 * 60,
  duration: 25 * 60,
  startTime: null,
  sessionsCompleted: 0,

  setDuration: (minutes) =>
    set({ duration: minutes * 60, seconds: minutes * 60 }),

  start: () =>
    set({ isActive: true, startTime: Date.now() }),

  stop: () => set({ isActive: false, startTime: null }),

  tick: () => {
    const state = get();
    if (!state.isActive || !state.startTime) return false;
    const elapsed = Math.floor((Date.now() - state.startTime) / 1000);
    const remaining = Math.max(0, state.duration - elapsed);
    set({ seconds: remaining });
    if (remaining <= 0) {
      set((s) => ({
        isActive: false,
        startTime: null,
        seconds: s.duration,
        sessionsCompleted: s.sessionsCompleted + 1,
      }));
      return true;
    }
    return false;
  },

  reset: () => set((s) => ({ isActive: false, seconds: s.duration, startTime: null })),

  getRemaining: () => {
    const { seconds } = get();
    return { mins: Math.floor(seconds / 60), secs: seconds % 60 };
  },

  getProgress: () => {
    const { seconds, duration } = get();
    return duration > 0 ? 1 - seconds / duration : 0;
  },

  getFormattedTime: () => {
    const { seconds } = get();
    return formatTime(seconds);
  },
}));
