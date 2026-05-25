import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { UserSettings, GameState } from "../api/types";
import { hybridStorage } from "./mmkvStorage";
import { setAuthToken } from "../api/client";

interface UserState {
  username: string | null;
  token: string | null;
  isAuthenticated: boolean;
  contactInfo: string | null;
  settings: Partial<UserSettings>;
  game: GameState;
  role: string | null;
  login: (username: string, token: string, role?: string) => void;
  logout: () => void;
  updateSettings: (s: Partial<UserSettings>) => void;
  updateGame: (g: Partial<GameState>) => void;
  addPoints: (points: number) => { leveledUp: boolean; newLevel: number };
  checkStreak: () => void;
  addBadge: (badge: string) => boolean;
  incrementSession: (minutes: number) => void;
  completeTask: () => void;
}

const defaultGame: GameState = {
  points: 0,
  level: 1,
  streak: 0,
  longest_streak: 0,
  badges: [],
  session_count: 0,
  total_focus_minutes: 0,
  tasks_completed: 0,
  progress: [],
};

const defaultSettings: UserSettings = {
  theme: "dark",
  language: "auto",
  notifications_enabled: true,
  notification_frequency: "daily",
  timer_duration: 25,
  auto_check_in: true,
  sound_enabled: true,
  use_12h_format: true,
  coach_tone: "gentle",
  focus_area: "motivation",
  overwhelm_mode_enabled: true,
  start_tiny_default: false,
  time_blindness_enabled: true,
  celebration_effects: true,
};

export const useUserStore = create<UserState>()(
  persist(
    (set, get) => ({
      username: null,
      token: null,
      isAuthenticated: false,
      contactInfo: null,
      settings: defaultSettings,
      game: defaultGame,
      role: null,

      login: (username, token, role) => {
        setAuthToken(token);
        set({
          username,
          token,
          isAuthenticated: true,
          role: role || "user",
        });
      },

      logout: () => {
        setAuthToken(null);
        set({
          username: null,
          token: null,
          isAuthenticated: false,
          contactInfo: null,
          settings: defaultSettings,
          game: defaultGame,
          role: null,
        });
      },

      updateSettings: (newSettings) =>
        set((s) => ({ settings: { ...s.settings, ...newSettings } })),

      updateGame: (partial) =>
        set((s) => ({ game: { ...s.game, ...partial } })),

      addPoints: (points) => {
        const game = get().game;
        const currentLevel = game.level;
        const newPoints = game.points + points;
        // Level up formula: each level takes (Level * 100) XP
        const newLevel = Math.floor(newPoints / 100) + 1;
        const progress = [
          ...game.progress,
          { time: new Date().toISOString(), points: newPoints },
        ].slice(-100);

        set({ game: { ...game, points: newPoints, level: newLevel, progress } });
        return {
          leveledUp: newLevel > currentLevel,
          newLevel,
        };
      },

      checkStreak: () => {
        const today = new Date().toISOString().split("T")[0];
        const game = get().game;
        const lastDate =
          game.progress.length > 0
            ? game.progress[game.progress.length - 1].time.split("T")[0]
            : null;
        if (lastDate === today) return;
        const yesterday = new Date(Date.now() - 86400000).toISOString().split("T")[0];
        const newStreak = lastDate === yesterday ? game.streak + 1 : 1;
        set({
          game: {
            ...game,
            streak: newStreak,
            longest_streak: Math.max(newStreak, game.longest_streak),
          },
        });
      },

      addBadge: (badge) => {
        const game = get().game;
        if (!game.badges.includes(badge)) {
          set({ game: { ...game, badges: [...game.badges, badge] } });
          return true;
        }
        return false;
      },

      incrementSession: (minutes) =>
        set((s) => ({
          game: {
            ...s.game,
            session_count: s.game.session_count + 1,
            total_focus_minutes: s.game.total_focus_minutes + minutes,
          },
        })),

      completeTask: () =>
        set((s) => ({
          game: { ...s.game, tasks_completed: s.game.tasks_completed + 1 },
        })),
    }),
    {
      name: "adhd-coach-user-store",
      storage: createJSONStorage(() => hybridStorage),
      // Automatically re-apply Authorization token on store hydration
      onRehydrateStorage: () => (state) => {
        if (state?.token) {
          setAuthToken(state.token);
        }
      },
    }
  )
);
