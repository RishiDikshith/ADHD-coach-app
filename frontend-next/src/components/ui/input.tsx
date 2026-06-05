"use client";

import { forwardRef, useState, type InputHTMLAttributes } from "react";
import { cn } from "@/lib/utils";
import { Eye, EyeOff } from "lucide-react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className, id, type, ...props }, ref) => {
    const [showPassword, setShowPassword] = useState(false);
    
    const isPasswordType = type === "password";
    const resolvedType = isPasswordType ? (showPassword ? "text" : "password") : type;

    return (
      <div className="space-y-1.5 w-full">
        {label && (
          <label htmlFor={id} className="block text-sm font-medium text-muted">
            {label}
          </label>
        )}
        <div className="relative w-full">
          <input
            ref={ref}
            id={id}
            type={resolvedType}
            className={cn(
              "w-full px-4 py-2.5 rounded-xl bg-surface border text-foreground placeholder:text-muted/40",
              "focus:outline-none focus:ring-2 focus:ring-calm-500/50 focus:border-calm-500/50",
              "transition-all duration-200 text-sm",
              isPasswordType && "pr-11", // Add right padding to prevent overlapping with the toggle icon
              error ? "border-danger-500" : "border-border",
              className
            )}
            {...props}
          />
          {isPasswordType && (
            <button
              type="button"
              onClick={() => setShowPassword((prev) => !prev)}
              className="absolute right-3.5 top-1/2 -translate-y-1/2 text-muted hover:text-foreground transition-colors p-1 rounded-lg hover:bg-white/5 cursor-pointer"
            >
              {showPassword ? (
                <EyeOff className="w-4 h-4" />
              ) : (
                <Eye className="w-4 h-4" />
              )}
            </button>
          )}
        </div>
        {error && (
          <p className="text-xs text-danger-500 mt-1">{error}</p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";

export { Input };
