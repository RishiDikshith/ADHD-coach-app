"use client";

import { forwardRef, type InputHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className, id, ...props }, ref) => {
    return (
      <div className="space-y-1.5">
        {label && (
          <label htmlFor={id} className="block text-sm font-medium text-muted">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={id}
          className={cn(
            "w-full px-4 py-2.5 rounded-xl bg-surface border text-foreground placeholder:text-muted/40",
            "focus:outline-none focus:ring-2 focus:ring-calm-500/50 focus:border-calm-500/50",
            "transition-all duration-200 text-sm",
            error ? "border-danger-500" : "border-border",
            className
          )}
          {...props}
        />
        {error && (
          <p className="text-xs text-danger-500 mt-1">{error}</p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";

export { Input };
