import { create } from "zustand";

interface TimerState {
  isActive: boolean;
  seconds: number;
  duration: number;
  startTime: number | null;
  sessionsCompleted: number;
  distractions: number;
  setDuration: (minutes: number) => void;
  start: () => void;
  stop: () => void;
  tick: () => boolean; // returns true if timer just completed
  reset: () => void;
  incrementDistractions: () => void;
  syncBackgroundTime: () => boolean; // Call when app resumes from background
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
  distractions: 0,

  setDuration: (minutes) =>
    set({ duration: minutes * 60, seconds: minutes * 60, distractions: 0 }),

  start: () => {
    // Record actual epoch millisecond timestamp for bulletproof background calculations
    set({ isActive: true, startTime: Date.now() });
  },

  stop: () => {
    // Calculate elapsed time before stopping
    const state = get();
    if (state.isActive && state.startTime) {
      const elapsed = Math.floor((Date.now() - state.startTime) / 1000);
      const remaining = Math.max(0, state.seconds - elapsed);
      set({ isActive: false, startTime: null, seconds: remaining });
    } else {
      set({ isActive: false, startTime: null });
    }
  },

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
      return true; // Finished!
    }
    return false;
  },

  reset: () =>
    set((s) => ({
      isActive: false,
      seconds: s.duration,
      startTime: null,
      distractions: 0,
    })),

  incrementDistractions: () =>
    set((s) => ({ distractions: s.distractions + 1 })),

  syncBackgroundTime: () => {
    const state = get();
    if (!state.isActive || !state.startTime) return false;

    const elapsedSeconds = Math.floor((Date.now() - state.startTime) / 1000);
    const remainingSeconds = state.duration - elapsedSeconds;

    if (remainingSeconds <= 0) {
      set((s) => ({
        isActive: false,
        startTime: null,
        seconds: s.duration,
        sessionsCompleted: s.sessionsCompleted + 1,
      }));
      return true; // Completed in background
    } else {
      set({ seconds: remainingSeconds });
      return false;
    }
  },

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
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  },
}));
