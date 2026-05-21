import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

export function getTimeOfDay(): { label: string; emoji: string; hour: number } {
  const h = new Date().getHours();
  if (h < 6) return { label: "Night", emoji: "🌙", hour: h };
  if (h < 12) return { label: "Morning", emoji: "🌅", hour: h };
  if (h < 17) return { label: "Afternoon", emoji: "☀️", hour: h };
  if (h < 21) return { label: "Evening", emoji: "🌆", hour: h };
  return { label: "Night", emoji: "🌙", hour: h };
}

export function getDayProgress(): number {
  const h = new Date().getHours();
  const m = new Date().getMinutes();
  return Math.round(((h * 60 + m) / (24 * 60)) * 100);
}

export function debounce<T extends (...args: unknown[]) => unknown>(
  fn: T,
  ms: number
): (...args: Parameters<T>) => void {
  let timer: ReturnType<typeof setTimeout>;
  return (...args: Parameters<T>) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}

export function randomItem<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

export function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}
