"use client";

import Link from "next/link";
import { motion } from "framer-motion";

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-6">
      <div className="text-center max-w-md">
        <motion.div
          className="text-7xl mb-6"
          animate={{ y: [0, -12, 0] }}
          transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
        >
          🧭
        </motion.div>
        <h1 className="text-4xl font-bold text-foreground mb-3">
          You&apos;ve wandered off course
        </h1>
        <p className="text-muted mb-2">
          That&apos;s okay — it happens to the best of us. This page doesn&apos;t exist
          (yet!).
        </p>
        <p className="text-sm text-muted/60 mb-8">
          (404: Page not found)
        </p>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-calm-500/20 text-calm-400 border border-calm-500/30 hover:bg-calm-500/30 transition-all font-medium"
        >
          ← Back to Dashboard
        </Link>
      </div>
    </div>
  );
}
