import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { UserSettings, GameState } from "@/lib/types";
import { api } from "@/services/api";

interface UserState {
  username: string | null;
  lastUsername: string | null;
  isAuthenticated: boolean;
  contactInfo: string | null;
  settings: Partial<UserSettings>;
  game: GameState;
  role: string | null;
  deviceId: string | null;
  getDeviceId: () => string;
  login: (username: string, role?: string) => void;
  logout: () => void;
  updateSettings: (s: Partial<UserSettings>) => void;
  updateGame: (g: Partial<GameState>) => void;
  addPoints: (points: number) => void;
  checkStreak: () => void;
  addBadge: (badge: string) => void;
  incrementSession: () => void;
  completeTask: () => void;
  loadSettings: (username: string) => Promise<void>;
}

const defaultGame: GameState = {
  points: 0, level: 1, streak: 0, longest_streak: 0,
  badges: [], session_count: 0, total_focus_minutes: 0,
  tasks_completed: 0, progress: [],
};

const generateUUID = () => {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
};

export const useUserStore = create<UserState>()(
  persist(
    (set, get) => ({
      username: null,
      lastUsername: null,
      isAuthenticated: false,
      contactInfo: null,
      settings: {},
      game: defaultGame,
      role: null,
      deviceId: null,

      getDeviceId: () => {
        let id = get().deviceId;
        if (!id) {
          if (typeof window !== "undefined") {
            id = localStorage.getItem("adhd_device_id");
            if (!id) {
              id = generateUUID();
              localStorage.setItem("adhd_device_id", id);
            }
          } else {
            id = generateUUID();
          }
          set({ deviceId: id });
        }
        return id;
      },

      login: (username, role) => set({ username, lastUsername: username, isAuthenticated: true, role: role || "user" }),

      logout: () =>
        set({
          username: null, isAuthenticated: false, contactInfo: null,
          settings: {}, game: defaultGame, role: null,
        }),

      updateSettings: (settings) =>
        set((s) => ({ settings: { ...s.settings, ...settings } })),

      updateGame: (partial) =>
        set((s) => ({ game: { ...s.game, ...partial } })),

      addPoints: (points) => {
        const game = get().game;
        const newPoints = game.points + points;
        const newLevel = Math.floor(newPoints / 100) + 1;
        const progress = [
          ...game.progress,
          { time: new Date().toISOString(), points: newPoints },
        ].slice(-100);
        set({ game: { ...game, points: newPoints, level: newLevel, progress } });
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
        }
      },

      incrementSession: () =>
        set((s) => ({
          game: { ...s.game, session_count: s.game.session_count + 1 },
        })),

      completeTask: () =>
        set((s) => ({
          game: { ...s.game, tasks_completed: s.game.tasks_completed + 1 },
        })),

      loadSettings: async (username) => {
        try {
          const settings = await api.getSettings(username);
          set({ settings });
        } catch {
          // Use defaults
        }
      },
    }),
    { name: "adhd-coach-user" }
  )
);
