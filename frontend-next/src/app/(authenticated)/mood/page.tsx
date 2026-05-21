"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Card, CardTitle, CardValue, CardLabel, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Celebration } from "@/components/shared/celebration";
import { useUserStore } from "@/stores/user-store";
import { useAnalyticsStore } from "@/stores/analytics-store";
import { MOODS } from "@/lib/types";

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.06 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0 },
};

const habits = [
  { id: "water", emoji: "💧", label: "Drank water", category: "Health" },
  { id: "exercise", emoji: "🏃", label: "Moved my body", category: "Health" },
  { id: "meditate", emoji: "🧘", label: "Meditated", category: "Mindfulness" },
  { id: "outside", emoji: "☀️", label: "Went outside", category: "Wellness" },
  { id: "social", emoji: "💬", label: "Connected with someone", category: "Social" },
  { id: "read", emoji: "📖", label: "Read something", category: "Learning" },
  { id: "focus", emoji: "🎯", label: "Focused session", category: "Productivity" },
  { id: "grateful", emoji: "🙏", label: "Practiced gratitude", category: "Mindfulness" },
  { id: "sleep", emoji: "😴", label: "Slept 7+ hours", category: "Health" },
  { id: "creative", emoji: "🎨", label: "Did something creative", category: "Learning" },
];

export default function MoodPage() {
  const { game, addPoints, addBadge } = useUserStore();
  const { currentMood, setCurrentMood, moodHistory, addMood, loading } = useAnalyticsStore();
  const [showCelebration, setShowCelebration] = useState(false);
  const [celebrationType, setCelebrationType] = useState<"confetti" | "sparkle" | "levelUp">("confetti");
  const [completedHabits, setCompletedHabits] = useState<string[]>([]);
  const [journalEntry, setJournalEntry] = useState("");
  const [energy, setEnergy] = useState(5);

  const handleMoodSelect = (emoji: string) => {
    const wasAlreadySet = currentMood === emoji;
    addMood(emoji, energy, journalEntry || undefined);
    if (!wasAlreadySet) {
      addPoints(5);
      setCelebrationType("sparkle");
      setShowCelebration(true);
      setTimeout(() => setShowCelebration(false), 2000);
    }
  };

  const toggleHabit = (id: string) => {
    setCompletedHabits((prev) => {
      const next = prev.includes(id) ? prev.filter((h) => h !== id) : [...prev, id];
      if (!prev.includes(id)) {
        addPoints(3);
        if (next.length === 5) {
          setCelebrationType("confetti");
          setShowCelebration(true);
          setTimeout(() => setShowCelebration(false), 2500);
        }
      }
      return next;
    });
  };

  const handleJournalSave = () => {
    if (!journalEntry.trim()) return;
    addPoints(10);
    setCelebrationType("sparkle");
    setShowCelebration(true);
    setTimeout(() => setShowCelebration(false), 2000);
    setJournalEntry("");
  };

  // Calculate mood stats
  const recentMoods = moodHistory.slice(-30);
  const moodCounts: Record<string, number> = {};
  recentMoods.forEach((m) => {
    moodCounts[m.emoji] = (moodCounts[m.emoji] || 0) + 1;
  });
  const topMood = Object.entries(moodCounts).sort((a, b) => b[1] - a[1])[0];
  const todayStr = new Date().toISOString().split("T")[0];
  const todayEntries = moodHistory.filter(
    (m) => m.timestamp.startsWith(todayStr)
  );

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="max-w-4xl mx-auto p-6 space-y-6"
    >
      <Celebration type={celebrationType} show={showCelebration} onComplete={() => setShowCelebration(false)} />

      {/* Header */}
      <motion.div variants={itemVariants}>
        <h1 className="text-3xl font-bold text-foreground">😊 Mood & Habits</h1>
        <p className="text-muted mt-1">Track how you feel, build habits that stick</p>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Quick stats */}
        <motion.div variants={itemVariants} className="md:col-span-1 space-y-3">
          <Card variant="stat" className="text-center">
            <CardLabel>Current Streak</CardLabel>
            <CardValue className="block mt-1">{game.streak} days</CardValue>
          </Card>
          <Card variant="glass" className="text-center">
            <CardLabel>Moods Tracked</CardLabel>
            <CardValue className="block mt-1">{moodHistory.length}</CardValue>
          </Card>
          {topMood && (
            <Card variant="glass" className="text-center">
              <CardLabel>Most Common Mood</CardLabel>
              <div className="text-3xl mt-1">{topMood[0]}</div>
              <p className="text-xs text-muted mt-1">
                {MOODS.find((m) => m.emoji === topMood[0])?.label || topMood[0]}
              </p>
            </Card>
          )}
          <Card variant="glass" className="text-center">
            <CardLabel>Today&apos;s Moods</CardLabel>
            <CardValue className="block mt-1">{todayEntries.length}</CardValue>
          </Card>
        </motion.div>

        {/* Mood Check-in / Journal */}
        <motion.div variants={itemVariants} className="md:col-span-2 space-y-4">
          {/* Emotional Check-in */}
          <Card>
            <CardTitle>💭 How are you feeling right now?</CardTitle>
            <CardDescription className="mt-1">Track your emotion and energy level</CardDescription>
            <div className="mt-4">
              <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
                {MOODS.map((mood) => (
                  <motion.button
                    key={mood.emoji}
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => handleMoodSelect(mood.emoji)}
                    className={`p-3 rounded-xl text-center transition-all ${
                      currentMood === mood.emoji
                        ? "bg-calm-500/20 ring-2 ring-calm-500"
                        : "bg-surface border border-border hover:border-calm-500/30"
                    }`}
                  >
                    <span className="text-2xl block">{mood.emoji}</span>
                    <span className="text-[10px] text-muted mt-1 block">{mood.label}</span>
                  </motion.button>
                ))}
              </div>

              {/* Energy Slider */}
              <div className="mt-4">
                <label className="text-sm text-muted font-medium block mb-2">
                  Energy Level: {energy}/10
                </label>
                <input
                  type="range"
                  min={1}
                  max={10}
                  value={energy}
                  onChange={(e) => setEnergy(Number(e.target.value))}
                  className="w-full accent-calm-500"
                />
                <div className="flex justify-between text-[10px] text-muted mt-1">
                  <span>😴 Low</span>
                  <span>⚡ High</span>
                </div>
              </div>
            </div>

            {currentMood && (
              <motion.p
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-xs text-calm-400 mt-2"
              >
                {MOODS.find((m) => m.emoji === currentMood)?.label} — Energy {energy}/10
              </motion.p>
            )}
          </Card>

          {/* Journal */}
          <Card>
            <CardTitle>📝 Quick Journal</CardTitle>
            <CardDescription className="mt-1">Write a short note about how you&apos;re doing</CardDescription>
            <div className="mt-3">
              <textarea
                value={journalEntry}
                onChange={(e) => setJournalEntry(e.target.value)}
                placeholder="What's on your mind? (optional)..."
                rows={3}
                className="w-full px-4 py-3 rounded-xl bg-surface border border-border text-foreground placeholder:text-muted/40 focus:outline-none focus:ring-2 focus:ring-calm-500/50 text-sm resize-none"
              />
              <Button
                size="sm"
                className="mt-2"
                onClick={handleJournalSave}
                disabled={!journalEntry.trim()}
              >
                💾 Save Entry (+10 pts)
              </Button>
            </div>
          </Card>

          {/* Recent Mood Timeline */}
          {moodHistory.length > 0 && (
            <Card>
              <CardTitle>📊 Recent Mood Timeline</CardTitle>
              <div className="mt-3 space-y-1.5 max-h-48 overflow-y-auto">
                {[...moodHistory].reverse().slice(0, 30).map((entry, i) => (
                  <div key={i} className="flex items-center gap-3 text-sm py-1">
                    <span className="text-lg">{entry.emoji}</span>
                    <span className="text-xs text-muted">
                      {new Date(entry.timestamp).toLocaleDateString([], {
                        weekday: "short",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                    {entry.energy && (
                      <div className="flex gap-0.5">
                        {Array.from({ length: entry.energy }).map((_, j) => (
                          <div key={j} className="w-1.5 h-1.5 rounded-full bg-warm-400" />
                        ))}
                      </div>
                    )}
                    {entry.note && (
                      <span className="text-xs text-muted truncate max-w-[200px]">{entry.note}</span>
                    )}
                  </div>
                ))}
              </div>
            </Card>
          )}
        </motion.div>
      </div>

      {/* Habits */}
      <motion.div variants={itemVariants}>
        <Card>
          <CardTitle>🔄 Daily Habits</CardTitle>
          <CardDescription className="mt-1">
            {completedHabits.length > 0
              ? `${completedHabits.length}/10 habits completed today`
              : "Check off what you've done today"}
          </CardDescription>

          {/* Progress bar */}
          <div className="mt-3 h-2 bg-border rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-calm-500 to-calm-400 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${(completedHabits.length / 10) * 100}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>

          <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-2">
            {habits.map((habit) => (
              <motion.button
                key={habit.id}
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => toggleHabit(habit.id)}
                className={`flex items-center gap-3 p-3 rounded-xl text-left transition-all border ${
                  completedHabits.includes(habit.id)
                    ? "bg-calm-500/10 border-calm-500/30"
                    : "bg-surface border-border hover:border-calm-500/20"
                }`}
              >
                <div
                  className={`w-5 h-5 rounded-md border-2 flex items-center justify-center transition-all ${
                    completedHabits.includes(habit.id)
                      ? "bg-calm-500 border-calm-500"
                      : "border-border"
                  }`}
                >
                  {completedHabits.includes(habit.id) && (
                    <motion.span
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      className="text-black text-xs font-bold"
                    >
                      ✓
                    </motion.span>
                  )}
                </div>
                <span className="text-lg">{habit.emoji}</span>
                <span
                  className={`text-sm ${
                    completedHabits.includes(habit.id)
                      ? "text-calm-400 line-through"
                      : "text-foreground"
                  }`}
                >
                  {habit.label}
                </span>
                <Badge variant="glass" className="ml-auto text-[10px]">
                  {habit.category}
                </Badge>
              </motion.button>
            ))}
          </div>
        </Card>
      </motion.div>

      {/* Badges */}
      {game.badges.length > 0 && (
        <motion.div variants={itemVariants}>
          <Card variant="glass">
            <CardTitle>🏅 Earned Badges</CardTitle>
            <div className="mt-3 flex flex-wrap gap-2">
              {game.badges.map((badge) => (
                <Badge key={badge} variant="purple" className="text-sm py-1 px-3">
                  {badge}
                </Badge>
              ))}
            </div>
          </Card>
        </motion.div>
      )}
    </motion.div>
  );
}
