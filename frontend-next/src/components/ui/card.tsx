"use client";

import { type HTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/utils";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "stat" | "glass" | "glass-strong" | "gradient" | "elevated";
  hover?: boolean;
}

const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ variant = "default", hover = true, className, children, ...props }, ref) => {
    const variants = {
      default: "bg-surface border border-border rounded-xl",
      stat: "bg-gradient-to-br from-calm-500/10 to-calm-600/10 border border-calm-500/20 rounded-xl",
      glass: "glass rounded-xl",
      "glass-strong": "glass-strong rounded-xl",
      gradient: "gradient-border bg-surface rounded-xl",
      elevated: "bg-surface-elevated border border-border-light rounded-xl shadow-lg",
    };

    return (
      <div
        ref={ref}
        className={cn(
          variants[variant],
          "p-4 md:p-5 transition-all duration-300",
          hover && "hover:shadow-lg hover:shadow-black/20 hover:border-calm-500/20",
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = "Card";

function CardTitle({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3 className={cn("text-lg font-semibold text-foreground", className)} {...props} />
  );
}

function CardValue({ className, ...props }: HTMLAttributes<HTMLSpanElement>) {
  return (
    <span className={cn("text-3xl font-bold text-calm-400", className)} {...props} />
  );
}

function CardLabel({ className, ...props }: HTMLAttributes<HTMLSpanElement>) {
  return (
    <span className={cn("text-xs uppercase tracking-wider text-muted font-semibold", className)} {...props} />
  );
}

function CardDescription({ className, ...props }: HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p className={cn("text-sm text-muted", className)} {...props} />
  );
}

export { Card, CardTitle, CardValue, CardLabel, CardDescription };
