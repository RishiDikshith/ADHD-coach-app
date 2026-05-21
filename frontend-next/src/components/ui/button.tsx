"use client";

import { forwardRef, type ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type Variant = "primary" | "secondary" | "ghost" | "danger" | "calm" | "outline" | "glass";
type Size = "xs" | "sm" | "md" | "lg" | "xl";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
}

const variants: Record<Variant, string> = {
  primary:
    "bg-gradient-to-r from-calm-500 to-calm-400 text-black font-semibold hover:from-calm-400 hover:to-calm-300 active:scale-[0.98] shadow-lg shadow-calm-500/20",
  secondary:
    "bg-surface text-foreground border border-border hover:bg-border/50 active:bg-border",
  ghost:
    "text-muted hover:text-foreground hover:bg-white/5 active:bg-white/10",
  danger:
    "bg-danger-500 text-white hover:bg-danger-400 active:bg-danger-600",
  calm:
    "bg-calm-900/30 text-calm-300 border border-calm-700/50 hover:bg-calm-800/40 hover:border-calm-500/50",
  outline:
    "border border-border-light text-foreground hover:bg-surface hover:border-calm-500/50 active:bg-white/5",
  glass:
    "glass text-foreground hover:bg-white/10 active:bg-white/15",
};

const sizes: Record<Size, string> = {
  xs: "px-2.5 py-1 text-xs rounded-lg",
  sm: "px-3 py-1.5 text-sm rounded-xl",
  md: "px-4 py-2 text-sm rounded-xl",
  lg: "px-6 py-3 text-base rounded-xl",
  xl: "px-8 py-4 text-lg rounded-2xl",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", size = "md", loading, className, children, disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={cn(
          "inline-flex items-center justify-center gap-2 font-medium transition-all duration-200",
          "disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus-visible:ring-2 focus-visible:ring-calm-500/50",
          variants[variant],
          sizes[size],
          className
        )}
        {...props}
      >
        {loading && (
          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        )}
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";
