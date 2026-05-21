"use client";

import { useEffect } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("App error:", error);
  }, [error]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-6">
      <div className="text-center max-w-md">
        <motion.div
          className="text-7xl mb-6"
          animate={{ rotate: [0, -10, 10, -10, 0] }}
          transition={{ duration: 0.8, ease: "easeInOut" }}
        >
          🌿
        </motion.div>
        <h1 className="text-3xl font-bold text-foreground mb-3">
          Something went off track
        </h1>
        <p className="text-muted mb-2">
          Don&apos;t worry — it&apos;s not you, it&apos;s us. Let&apos;s try that again.
        </p>
        <p className="text-xs text-muted/40 mb-8">
          {error.message || "An unexpected error occurred"}
        </p>
        <div className="flex items-center justify-center gap-3">
          <Button onClick={reset} variant="calm">
            🔄 Try again
          </Button>
          <Button
            onClick={() => (window.location.href = "/dashboard")}
            variant="ghost"
          >
            ← Go to Dashboard
          </Button>
        </div>
      </div>
    </div>
  );
}
