"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Card, CardTitle, CardValue, CardLabel } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useUserStore } from "@/stores/user-store";
import { useAnalyticsStore } from "@/stores/analytics-store";
import { useTimerStore } from "@/stores/timer-store";
import { api } from "@/lib/api-client";
import Link from "next/link";
import { MomentumRing, StreakFlame, LevelUpBadge } from "@/components/shared/celebration";

const containerVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.08 } },
};

const itemVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4 } },
};

const healthItems = [
  { key: "adhd_risk" as const, label: "ADHD Risk", color: "#6ee7b7", format: (v: number) => `${(v * 100).toFixed(0)}%` },
  { key: "mental_health_score" as const, label: "Mental Health", color: "#667eea", format: (v: number) => `${v.toFixed(0)}%` },
  { key: "productivity_score" as const, label: "Productivity", color: "#fbbf24", format: (v: number) => `${v.toFixed(0)}%` },
  { key: "depression_score" as const, label: "Burnout Resistance", color: "#f87171", format: (v: number) => `${v.toFixed(0)}%` },
];

export default function DashboardPage() {
  const { username, game } = useUserStore();
  const { scores, insights, setScores, setInsights, overwhelmMode, setOverwhelmMode } = useAnalyticsStore();
  const timer = useTimerStore();
  const [loading, setLoading] = useState(true);
  const [showAllMetrics, setShowAllMetrics] = useState(false);
  const [showCelebration, setShowCelebration] = useState(false);

  useEffect(() => {
    if (!username) return;
    Promise.all([
      api.getScores(username, {}).then(setScores).catch(() => {}),
      api.getAnalytics(username).then((data) => setInsights(data.insights || [])).catch(() => {}),
    ]).finally(() => setLoading(false));
  }, [username, setScores, setInsights]);

  // Auto-detect overwhelm: if mental health or burnout resistance is low, suggest overwhelm mode
  const shouldSuggestOverwhelm =
    scores.mental_health_score != null && scores.mental_health_score < 35;
  const isLowEnergy =
    scores.productivity_score != null && scores.productivity_score < 30;

  // In overwhelm mode, show only essential items
  const visibleHealthItems = overwhelmMode ? healthItems.slice(0, 2) : showAllMetrics ? healthItems : healthItems;

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="max-w-5xl mx-auto p-6 space-y-6"
    >
      {/* Header — adaptive greeting */}
      <motion.div variants={itemVariants}>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground">
              {overwhelmMode ? "🌿 Welcome" : "📊 Dashboard"}
            </h1>
            <p className="text-muted mt-1">
              {overwhelmMode
                ? "Let's keep things simple today. Just the essentials."
                : isLowEnergy
                ? "A gentle overview of where you are right now."
                : "Your wellness snapshot at a glance"}
            </p>
          </div>
          {game.streak >= 3 && (
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: "spring", stiffness: 200, damping: 12 }}
            >
              <StreakFlame streak={game.streak} />
            </motion.div>
          )}
        </div>
      </motion.div>

      {/* Overwhelm suggestion banner */}
      <AnimatePresence>
        {shouldSuggestOverwhelm && !overwhelmMode && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <Card variant="glass" className="border-danger-500/30">
              <div className="flex items-center gap-3">
                <span className="text-2xl">🌿</span>
                <div className="flex-1">
                  <p className="text-sm font-medium text-foreground">Things feel heavy?</p>
                  <p className="text-xs text-muted">Switch to Gentle Mode — I&apos;ll simplify things and focus on what matters most right now.</p>
                </div>
                <Button variant="danger" size="sm" onClick={() => setOverwhelmMode(true)}>
                  🌿 Gentle Mode
                </Button>
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Overwhelm mode active banner */}
      <AnimatePresence>
        {overwhelmMode && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            <Card variant="glass" className="border-danger-500/30 text-center">
              <p className="text-sm text-danger-400 font-medium">🌿 Gentle Mode Active</p>
              <p className="text-xs text-muted mt-1">Showing only what matters most right now.</p>
              <Button variant="ghost" size="sm" className="mt-2" onClick={() => setOverwhelmMode(false)}>
                Exit Gentle Mode
              </Button>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Wellness Snapshot — only 2 cards in overwhelm mode */}
      <motion.section variants={itemVariants}>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-foreground">
            {overwhelmMode ? "🌱 Your Focus" : "🧠 Your Wellness Snapshot"}
          </h2>
          {!overwhelmMode && (
            <button
              onClick={() => setShowAllMetrics(!showAllMetrics)}
              className="text-xs text-muted hover:text-foreground transition-colors"
            >
              {showAllMetrics ? "Show less" : "Show all"}
            </button>
          )}
        </div>
        {loading ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="shimmer h-28 rounded-xl" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {visibleHealthItems.map((item) => {
              const val = scores[item.key];
              return (
                <motion.div key={item.key} whileHover={overwhelmMode ? undefined : { y: -4, transition: { duration: 0.2 } }}>
                  <Card variant={overwhelmMode ? "glass" : "stat"} className="text-center h-full">
                    <CardLabel>{item.label}</CardLabel>
                    <CardValue className="mt-1 block" style={{ color: item.color }}>
                      {val != null ? item.format(val as number) : "--"}
                    </CardValue>
                  </Card>
                </motion.div>
              );
            })}
          </div>
        )}
      </motion.section>

      {/* Quick Stats — simplified in overwhelm mode */}
      <motion.section variants={itemVariants}>
        <h2 className="text-lg font-semibold text-foreground mb-3">
          {overwhelmMode ? "🌊 Just today" : "⚡ Quick Stats"}
        </h2>
        <div className="grid grid-cols-3 gap-3">
          {[
            { label: "Streak", value: `${game.streak} days` },
            { label: "Level", value: game.level },
            { label: "Sessions", value: game.session_count },
          ].map((stat) => (
            <motion.div key={stat.label} whileHover={overwhelmMode ? undefined : { scale: 1.02 }}>
              <Card variant={overwhelmMode ? "glass" : "glass"} className="text-center">
                <CardLabel>{stat.label}</CardLabel>
                <CardValue className="block mt-1">{stat.value}</CardValue>
              </Card>
            </motion.div>
          ))}
        </div>
      </motion.section>

      {/* Momentum Ring */}
      {game.points > 0 && !overwhelmMode && (
        <motion.div variants={itemVariants} className="flex justify-center">
          <div className="relative">
            <MomentumRing
              progress={Math.min(100, (game.points % 100))}
              size={120}
              strokeWidth={6}
              color="#667eea"
              label="Points to next level"
            />
          </div>
        </motion.div>
      )}

      {/* Focus Timer Quick Start */}
      <motion.div variants={itemVariants}>
        <Card>
          <CardTitle>⏱️ Focus Session</CardTitle>
          <div className="mt-3 flex items-center gap-4">
            <input
              type="range"
              min={overwhelmMode ? 2 : 5}
              max={overwhelmMode ? 30 : 120}
              step={5}
              value={timer.duration / 60}
              onChange={(e) => timer.setDuration(Number(e.target.value))}
              className="flex-1 accent-calm-500"
            />
            <span className="text-sm text-muted w-12 text-right">{timer.duration / 60} min</span>
            <Button onClick={() => timer.start()}>
              {overwhelmMode ? "🌿 Start gentle" : "▶ Start"}
            </Button>
          </div>
          {overwhelmMode && (
            <p className="text-xs text-muted mt-2">Short sessions recommended right now. Just 2 minutes counts.</p>
          )}
        </Card>
      </motion.div>

      {/* Insights — limited count in overwhelm mode */}
      {insights.length > 0 && (
        <motion.section variants={itemVariants}>
          <h2 className="text-lg font-semibold text-foreground mb-3">
            {overwhelmMode ? "💡 One thing to know" : "💡 Insights"}
          </h2>
          <div className="space-y-2">
            {insights.slice(0, overwhelmMode ? 1 : 5).map((insight, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
              >
                <Card
                  className={`border-l-4 ${
                    insight.priority === "high"
                      ? "border-l-danger-500"
                      : insight.priority === "medium"
                      ? "border-l-warm-500"
                      : "border-l-calm-500"
                  }`}
                >
                  <p className="text-sm text-foreground">{insight.description}</p>
                </Card>
              </motion.div>
            ))}
          </div>
        </motion.section>
      )}

      {/* Quick Actions — reduced in overwhelm mode */}
      <motion.section variants={itemVariants}>
        <h2 className="text-lg font-semibold text-foreground mb-3">
          {overwhelmMode ? "🌱 One thing" : "🚀 Quick Actions"}
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {(overwhelmMode
            ? [
                { href: "/chat", icon: "💬", title: "Chat", desc: "Talk to your AI coach" },
                { href: "/tasks", icon: "📋", title: "Tasks", desc: "Just one tiny task" },
              ]
            : [
                { href: "/chat", icon: "💬", title: "Chat", desc: "Talk to your AI coach" },
                { href: "/focus", icon: "🎯", title: "Focus", desc: "Full-screen focus mode" },
                { href: "/tasks", icon: "📋", title: "Tasks", desc: "Break down tasks" },
                { href: "/mood", icon: "😊", title: "Mood", desc: "Track your feelings" },
              ]
          ).map((action) => (
            <Link key={action.href} href={action.href}>
              <motion.div whileHover={overwhelmMode ? { scale: 1.02 } : { y: -4, scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                <Card className={`h-full cursor-pointer transition-all ${
                  overwhelmMode ? "hover:border-danger-500/40" : "hover:border-calm-500/50"
                }`}>
                  <CardTitle className="text-lg">{action.icon} {action.title}</CardTitle>
                  <p className="text-xs text-muted mt-1">{action.desc}</p>
                </Card>
              </motion.div>
            </Link>
          ))}
        </div>
      </motion.section>
    </motion.div>
  );
}
