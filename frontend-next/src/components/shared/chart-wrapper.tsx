"use client";

import { useEffect, useState, type ReactNode } from "react";

interface ChartWrapperProps {
  children: ReactNode;
  className?: string;
  /** Minimum height for the chart container. Defaults to h-64 (16rem / 256px). */
  height?: string;
}

/**
 * Client-only chart wrapper that defers rendering of Recharts charts
 * until after the component has mounted on the client. This prevents the
 * "width(-1) and height(-1) of chart should be greater than 0" warning
 * from ResponsiveContainer during hydration / initial render.
 *
 * Shows a placeholder skeleton during SSR / initial paint so the container
 * has proper dimensions before the chart tries to measure them.
 */
export function ChartWrapper({
  children,
  className = "",
  height = "h-64",
}: ChartWrapperProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    // Defer one frame to ensure the parent container has been laid out
    const id = requestAnimationFrame(() => setMounted(true));
    return () => cancelAnimationFrame(id);
  }, []);

  return (
    <div className={`relative w-full ${height} ${className}`}>
      {mounted ? (
        children
      ) : (
        <div className="w-full h-full flex items-center justify-center">
          <div className="flex flex-col items-center gap-2">
            <div className="w-6 h-6 border-2 border-calm-500/30 border-t-calm-500 rounded-full animate-spin" />
            <span className="text-xs text-muted">Loading chart...</span>
          </div>
        </div>
      )}
    </div>
  );
}
