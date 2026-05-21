"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Card, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { useUserStore } from "@/stores/user-store";
import { useAnalyticsStore } from "@/stores/analytics-store";

const containerVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.08 } },
};
const itemVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0 },
};

export default function SettingsPage() {
  const { settings, updateSettings } = useUserStore();
  const { timeBlindnessEnabled, toggleTimeBlindness, startTinyMode, setStartTinyMode } = useAnalyticsStore();

  const [coachTone, setCoachTone] = useState(settings.coach_tone || "encouraging");
  const [focusArea, setFocusArea] = useState(settings.focus_area || "general");
  const [timerDuration, setTimerDuration] = useState(settings.timer_duration || 25);
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    updateSettings({ coach_tone: coachTone as "encouraging" | "direct" | "gentle" | "humorous", focus_area: focusArea, timer_duration: timerDuration });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="max-w-3xl mx-auto p-6 space-y-6"
    >
      {/* Header */}
      <motion.div variants={itemVariants}>
        <h1 className="text-3xl font-bold text-foreground">⚙️ Settings</h1>
        <p className="text-muted mt-1">Personalize your ADHD Coach experience</p>
      </motion.div>

      {/* Coach Preferences */}
      <motion.div variants={itemVariants}>
        <Card>
          <CardTitle>🧠 ADHD Coach Preferences</CardTitle>
          <div className="mt-4 space-y-5">
            {/* Coach Tone */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Coach Tone</label>
              <p className="text-xs text-muted mb-3">How would you like your AI coach to speak to you?</p>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { id: "encouraging", emoji: "🌟", label: "Encouraging", desc: "Warm, supportive, celebratory" },
                  { id: "direct", emoji: "🎯", label: "Direct", desc: "Clear, concise, no fluff" },
                  { id: "gentle", emoji: "🌿", label: "Gentle", desc: "Soft, calming, patient" },
                  { id: "humorous", emoji: "😄", label: "Humorous", desc: "Light, funny, playful" },
                ].map((tone) => (
                  <motion.button
                    key={tone.id}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => setCoachTone(tone.id as "encouraging" | "direct" | "gentle" | "humorous")}
                    className={`p-3 rounded-xl text-left transition-all duration-200 border ${
                      coachTone === tone.id
                        ? "bg-calm-500/10 border-calm-500/50 text-calm-400"
                        : "bg-surface border-border text-muted hover:border-calm-500/30"
                    }`}
                  >
                    <span className="text-lg block mb-1">{tone.emoji}</span>
                    <span className="text-sm font-medium block">{tone.label}</span>
                    <span className="text-[10px]">{tone.desc}</span>
                  </motion.button>
                ))}
              </div>
            </div>

            {/* Focus Area */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Primary Focus Area</label>
              <p className="text-xs text-muted mb-3">What would you like to work on most?</p>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { id: "general", emoji: "🧠", label: "General" },
                  { id: "productivity", emoji: "⚡", label: "Productivity" },
                  { id: "focus", emoji: "🎯", label: "Focus" },
                  { id: "emotional", emoji: "😌", label: "Emotional Health" },
                  { id: "habits", emoji: "🔄", label: "Habit Building" },
                  { id: "organization", emoji: "📋", label: "Organization" },
                ].map((area) => (
                  <motion.button
                    key={area.id}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => setFocusArea(area.id)}
                    className={`p-2.5 rounded-xl text-sm text-left transition-all duration-200 border ${
                      focusArea === area.id
                        ? "bg-focus-500/10 border-focus-500/50 text-focus-400"
                        : "bg-surface border-border text-muted hover:border-focus-500/30"
                    }`}
                  >
                    <span className="mr-1.5">{area.emoji}</span>
                    {area.label}
                  </motion.button>
                ))}
              </div>
            </div>
          </div>
          <div className="mt-6 flex items-center gap-3">
            <Button onClick={handleSave}>{saved ? "✅ Saved!" : "Save Preferences"}</Button>
          </div>
        </Card>
      </motion.div>

      {/* Focus Timer */}
      <motion.div variants={itemVariants}>
        <Card>
          <CardTitle>⏱️ Focus Timer</CardTitle>
          <div className="mt-4">
            <Slider label="Default session duration (minutes)" value={timerDuration} onChange={setTimerDuration} min={5} max={120} step={5} />
            <motion.div whileTap={{ scale: 0.98 }}>
              <Button className="mt-3" size="sm" onClick={() => { updateSettings({ timer_duration: timerDuration }); setSaved(true); setTimeout(() => setSaved(false), 2000); }}>
                Update Timer Duration
              </Button>
            </motion.div>
          </div>
        </Card>
      </motion.div>

      {/* ADHD UX Features */}
      <motion.div variants={itemVariants}>
        <Card>
          <CardTitle>🎨 ADHD UX Features</CardTitle>
          <div className="mt-4 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-foreground">🌙 Time Blindness Helper</p>
                <p className="text-xs text-muted">Shows a visual day progress bar in the sidebar</p>
              </div>
              <button onClick={toggleTimeBlindness} className={`w-11 h-6 rounded-full transition-all duration-300 relative ${timeBlindnessEnabled ? "bg-calm-500" : "bg-border"}`}>
                <motion.div className="absolute top-0.5 w-5 h-5 rounded-full bg-white shadow" animate={{ left: timeBlindnessEnabled ? 22 : 2 }} transition={{ type: "spring", stiffness: 500, damping: 30 }} />
              </button>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-foreground">🐣 Start Tiny Mode</p>
                <p className="text-xs text-muted">Default to micro-tasks and small wins</p>
              </div>
              <button onClick={() => setStartTinyMode(!startTinyMode)} className={`w-11 h-6 rounded-full transition-all duration-300 relative ${startTinyMode ? "bg-calm-500" : "bg-border"}`}>
                <motion.div className="absolute top-0.5 w-5 h-5 rounded-full bg-white shadow" animate={{ left: startTinyMode ? 22 : 2 }} transition={{ type: "spring", stiffness: 500, damping: 30 }} />
              </button>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-foreground">🎉 Celebration Effects</p>
                <p className="text-xs text-muted">Dopamine-friendly confetti on achievements</p>
              </div>
              <span className="text-xs text-muted">✨ Enabled</span>
            </div>
          </div>
        </Card>
      </motion.div>

      {/* About */}
      <motion.div variants={itemVariants}>
        <Card variant="glass">
          <CardTitle>🧠 About ADHD AI Coach</CardTitle>
          <div className="mt-3 text-sm text-muted space-y-2">
            <p>Version 2.0 — ADHD Executive Function Ecosystem</p>
            <p>Free & Open Source · Built with Next.js + FastAPI</p>
            <p>Designed specifically for ADHD brains — reducing cognitive load, providing dopamine-friendly feedback, and offering emotionally intelligent support.</p>
          </div>
        </Card>
      </motion.div>
    </motion.div>
  );
}
