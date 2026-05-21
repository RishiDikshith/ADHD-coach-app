"use client";

import { cn } from "@/lib/utils";

type BadgeVariant = "default" | "calm" | "focus" | "warm" | "danger" | "purple" | "pink" | "glass";

interface BadgeProps {
  variant?: BadgeVariant;
  className?: string;
  children: React.ReactNode;
}

const variants: Record<BadgeVariant, string> = {
  default: "bg-white/10 text-foreground border border-white/20",
  calm: "bg-calm-500/15 text-calm-400 border border-calm-500/30",
  focus: "bg-focus-500/15 text-focus-400 border border-focus-500/30",
  warm: "bg-warm-500/15 text-warm-400 border border-warm-500/30",
  danger: "bg-danger-500/15 text-danger-400 border border-danger-500/30",
  purple: "bg-purple-500/15 text-purple-400 border border-purple-500/30",
  pink: "bg-pink-500/15 text-pink-400 border border-pink-500/30",
  glass: "glass text-foreground text-xs",
};

export function Badge({ variant = "default", className, children }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium transition-all",
        variants[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
