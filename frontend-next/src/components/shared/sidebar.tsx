"use client";

import { usePathname, useRouter } from "next/navigation";
import Link from "next/link";
import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn, getTimeOfDay, getDayProgress, randomItem } from "@/lib/utils";
import { useUserStore } from "@/stores/user-store";
import { useAnalyticsStore } from "@/stores/analytics-store";
import { useTimerStore } from "@/stores/timer-store";
import { Button } from "@/components/ui/button";
import { Card, CardValue, CardLabel } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: "📊" },
  { href: "/chat", label: "Chat", icon: "💬" },
  { href: "/focus", label: "Focus", icon: "🎯" },
  { href: "/analytics", label: "Analytics", icon: "📈" },
  { href: "/tasks", label: "Tasks", icon: "📋" },
  { href: "/mood", label: "Mood", icon: "😊" },
  { href: "/agents", label: "Agents", icon: "🤖" },
  { href: "/feedback", label: "Feedback", icon: "📣" },
  { href: "/support", label: "Support", icon: "🆘" },
  { href: "/settings", label: "Settings", icon: "⚙️" },
];

const tinyTasks = [
  "💧 Drink a glass of water", "🌬️ Take 3 deep breaths", "🧘 Stand up and stretch",
  "📝 Write one sentence", "🔖 Open the one tab you need", "🧹 Put one thing away",
  "😌 Close your eyes for 30s", "☀️ Step outside for 1 minute",
  "🎵 Play one calming song", "✍️ Write one thing you're grateful for",
];

const moods = [
  { emoji: "😊", label: "Happy" }, { emoji: "😌", label: "Calm" },
  { emoji: "😐", label: "Okay" }, { emoji: "😟", label: "Worried" },
  { emoji: "😰", label: "Anxious" }, { emoji: "😤", label: "Frustrated" },
];

const sidebarVariants = {
  hidden: { x: -280 },
  visible: { x: 0, transition: { type: "spring" as const, stiffness: 300, damping: 30 } },
};

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { username, game, logout, role } = useUserStore();
  const { currentMood, setCurrentMood, timeBlindnessEnabled, startTinyMode, setStartTinyMode } = useAnalyticsStore();
  const timer = useTimerStore();
  const [mounted, setMounted] = useState(false);
  const [microTask, setMicroTask] = useState("");

  useEffect(() => {
    const timer = setTimeout(() => {
      setMounted(true);
    }, 0);
    return () => clearTimeout(timer);
  }, []);

  if (!mounted) return null;

  const tod = getTimeOfDay();
  const dayPct = getDayProgress();

  const itemsToRender = role === "admin"
    ? [
        ...navItems.slice(0, 1),
        { href: "/admin", label: "Admin Dashboard", icon: "🛡️" },
        ...navItems.slice(1)
      ]
    : navItems;

  return (
    <motion.aside
      initial="hidden"
      animate="visible"
      variants={sidebarVariants}
      className="w-72 h-screen bg-gradient-to-b from-[#0a0f1e] to-[#050a18] border-r border-border flex flex-col overflow-y-auto shrink-0"
    >
      {/* Header */}
      <div className="glass-strong m-3 rounded-2xl p-4 text-center">
        <h2 className="text-lg font-bold gradient-text">🧠 ADHD Coach</h2>
        {username && (
          <p className="text-xs text-muted mt-1">Welcome, {username}</p>
        )}
      </div>

      {/* Time Blindness */}
      <AnimatePresence>
        {timeBlindnessEnabled && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="px-4 pb-2"
          >
            <div className="flex items-center gap-2 text-xs text-muted mb-1.5">
              <span>{tod.emoji} {tod.label}</span>
              <span className="text-muted-foreground">— Day {dayPct}% complete</span>
            </div>
            <div className="h-1.5 bg-border rounded-full overflow-hidden">
              <motion.div
                className="h-full rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${dayPct}%` }}
                transition={{ duration: 1, ease: "easeOut" }}
                style={{
                  background: "linear-gradient(90deg, #6ee7b7, #667eea, #c084fc)",
                }}
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-2 space-y-0.5">
        {itemsToRender.map((item, i) => {
          const isActive = pathname === item.href;
          return (
            <motion.div
              key={item.href}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.05 * i, duration: 0.3 }}
            >
              <Link href={item.href}>
                <div
                  className={cn(
                    "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200",
                    isActive
                      ? "glass text-calm-400 border border-calm-500/20"
                      : "text-muted hover:text-foreground hover:bg-white/5"
                  )}
                >
                  <span className="text-lg">{item.icon}</span>
                  {item.label}
                  {isActive && (
                    <motion.div
                      layoutId="nav-indicator"
                      className="ml-auto w-1.5 h-1.5 rounded-full bg-calm-500"
                    />
                  )}
                </div>
              </Link>
            </motion.div>
          );
        })}
      </nav>

      {/* Quick Stats */}
      <div className="px-3 pb-2 space-y-2">
        <div className="grid grid-cols-2 gap-2">
          <Card variant="glass" className="p-3 text-center">
            <CardValue className="text-xl">{game.streak}</CardValue>
            <CardLabel>Streak</CardLabel>
          </Card>
          <Card variant="glass" className="p-3 text-center">
            <CardValue className="text-xl">Lv.{game.level}</CardValue>
            <CardLabel>Level</CardLabel>
          </Card>
        </div>
        <Card variant="glass" className="p-3 text-center">
          <CardValue className="text-xl">{game.points}</CardValue>
          <CardLabel>Points</CardLabel>
        </Card>
      </div>

      {/* Streak Achievement */}
      {game.streak >= 3 && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="px-3 pb-2"
        >
          <div className="streak-achievement">
            <span className="text-lg">{game.streak >= 7 ? "🔥" : "⭐"}</span>
            <p className="text-sm text-warm-500 font-medium">
              {game.streak >= 7
                ? `${game.streak} day streak! Incredible!`
                : `${game.streak} day streak! Keep going!`}
            </p>
          </div>
        </motion.div>
      )}

      {/* Emotional Check-in */}
      <div className="px-3 pb-2">
        <details className="group">
          <summary className="text-xs text-muted font-semibold uppercase tracking-wider cursor-pointer hover:text-foreground transition-colors list-none flex items-center gap-1">
            💭 How are you feeling?
          </summary>
          <div className="mt-2 grid grid-cols-6 gap-1">
            {moods.map((m) => (
              <button
                key={m.emoji}
                onClick={() => setCurrentMood(m.emoji)}
                className={cn(
                  "p-1.5 rounded-lg text-lg transition-all duration-200",
                  currentMood === m.emoji
                    ? "bg-calm-500/20 ring-2 ring-calm-500 scale-110"
                    : "hover:bg-white/10"
                )}
                title={m.label}
              >
                {m.emoji}
              </button>
            ))}
          </div>
          {currentMood && (
            <p className="text-xs text-muted mt-1 text-center">
              {moods.find((m) => m.emoji === currentMood)?.label || currentMood}
            </p>
          )}
        </details>
      </div>

      {/* Start Tiny Mode */}
      <div className="px-3 pb-2">
        <div className="flex items-center justify-between">
          <span className="text-xs text-muted font-semibold">🐣 Start Tiny</span>
          <button
            onClick={() => setStartTinyMode(!startTinyMode)}
            className={cn(
              "w-10 h-5 rounded-full transition-all duration-300 relative",
              startTinyMode ? "bg-calm-500" : "bg-border"
            )}
          >
            <motion.div
              className="absolute top-0.5 w-4 h-4 rounded-full bg-white shadow"
              animate={{ left: startTinyMode ? 22 : 2 }}
              transition={{ type: "spring", stiffness: 500, damping: 30 }}
            />
          </button>
        </div>
        <AnimatePresence>
          {startTinyMode && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-2 overflow-hidden"
            >
              <p className="text-xs text-calm-400 mb-2">Everything in 2 minutes or less!</p>
              <Button
                variant="calm" size="sm" className="w-full"
                onClick={() => setMicroTask(randomItem(tinyTasks))}
              >
                🌱 2-minute task
              </Button>
              {microTask && (
                <motion.p
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="text-xs text-muted mt-2 text-center"
                >
                  {microTask}
                </motion.p>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Focus Timer */}
      <div className="px-3 pb-2">
        <p className="text-xs text-muted font-semibold uppercase tracking-wider mb-2">⏱️ Focus</p>
        <Card variant="glass" className="p-3 text-center">
          {!timer.isActive ? (
            <>
              <input
                type="range" min={5} max={120} step={5}
                value={timer.duration / 60}
                onChange={(e) => timer.setDuration(Number(e.target.value))}
                className="w-full accent-calm-500"
              />
              <p className="text-xs text-muted mt-1">{timer.duration / 60} min</p>
              <Button size="sm" className="w-full mt-2" onClick={() => timer.start()}>
                ▶ Start Focus
              </Button>
            </>
          ) : (
            <>
              <motion.p
                className="text-2xl font-bold text-calm-400 font-mono tracking-wider"
                animate={{ scale: [1, 1.03, 1] }}
                transition={{ duration: 1, repeat: Infinity }}
              >
                {timer.getFormattedTime()}
              </motion.p>
              <Button size="sm" variant="danger" className="w-full mt-2" onClick={() => timer.stop()}>
                ⏹ Stop
              </Button>
            </>
          )}
        </Card>
      </div>

      {/* Badges */}
      {game.badges.length > 0 && (
        <div className="px-3 pb-3">
          <p className="text-xs text-muted font-semibold uppercase tracking-wider mb-2">🏅 Badges</p>
          <div className="flex flex-wrap gap-1.5">
            {game.badges.map((badge) => (
              <Badge key={badge} variant="purple">{badge}</Badge>
            ))}
          </div>
        </div>
      )}

      {/* Logout */}
      <div className="p-3 border-t border-border mt-auto">
        <Button
          variant="ghost"
          size="sm"
          className="w-full text-muted"
          onClick={() => {
            logout();
            router.push("/login");
          }}
        >
          Logout
        </Button>
      </div>
    </motion.aside>
  );
}
