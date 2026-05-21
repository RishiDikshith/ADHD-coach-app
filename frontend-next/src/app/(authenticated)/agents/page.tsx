"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";
import { Card, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Celebration } from "@/components/shared/celebration";
import { useUserStore } from "@/stores/user-store";
import { useAnalyticsStore } from "@/stores/analytics-store";

const agents = [
  { id: "productivity-coach", name: "Productivity Coach", emoji: "⚡", role: "Focus & motivation guidance", description: "Helps you find motivation, overcome procrastination, and maintain focus on your priorities.", color: "#6ee7b7", promptExamples: ["I can't focus today", "Help me get motivated", "What should I prioritize?"] },
  { id: "task-breakdown", name: "Task Breakdown", emoji: "🔨", role: "Microtask generation & overwhelm reduction", description: "Takes overwhelming tasks and breaks them into tiny, concrete micro-steps.", color: "#667eea", promptExamples: ["I'm overwhelmed by this project", "Break this task down for me", "This feels impossible"] },
  { id: "focus-optimization", name: "Focus Optimization", emoji: "🎯", role: "Focus session analysis & timing", description: "Analyzes your focus patterns and optimizes your Pomodoro timing.", color: "#fbbf24", promptExamples: ["I keep getting distracted", "Help me find my focus hours", "When should I take breaks?"] },
  { id: "mood-burnout", name: "Mood & Burnout", emoji: "😌", role: "Emotional exhaustion detection & recovery", description: "Detects burnout patterns and provides compassionate recovery recommendations.", color: "#f87171", promptExamples: ["I feel burned out", "My mood is low today", "I need emotional support"] },
  { id: "habit-builder", name: "Habit Builder", emoji: "🔄", role: "Streak reinforcement & consistency", description: "Reinforces positive habits and builds routines that stick with an ADHD brain.", color: "#c084fc", promptExamples: ["I can't stick to habits", "Help me build a routine", "How do I stay consistent?"] },
  { id: "intervention", name: "Intervention Agent", emoji: "🆘", role: "ADHD rescue interventions", description: "Detects overwhelm and triggers rescue modes with grounding exercises.", color: "#34d399", promptExamples: ["I'm having a panic moment", "I can't stop hyperfocusing", "I need a grounding exercise"] },
  { id: "accountability", name: "Accountability", emoji: "🤝", role: "Gentle reminders & check-ins", description: "Non-judgmental accountability through reminders and check-ins.", color: "#f472b6", promptExamples: ["Check in on my progress", "Help me stay accountable", "Remind me of my goals"] },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.06 } },
};
const itemVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0 },
};

export default function AgentsPage() {
  const router = useRouter();
  const { game } = useUserStore();
  const { moodHistory } = useAnalyticsStore();
  const [activeAgent, setActiveAgent] = useState<string | null>(null);
  const [showCelebration, setShowCelebration] = useState(false);

  const handleTryAgent = (id: string) => {
    setActiveAgent(id);
    setShowCelebration(true);
    setTimeout(() => setShowCelebration(false), 2000);
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="max-w-5xl mx-auto p-6 space-y-6"
    >
      <Celebration type="sparkle" show={showCelebration} onComplete={() => setShowCelebration(false)} />

      {/* Header */}
      <motion.div variants={itemVariants}>
        <h1 className="text-3xl font-bold text-foreground">🤖 AI Agents</h1>
        <p className="text-muted mt-1">
          Seven specialized ADHD agents working together as your personal executive function team
        </p>
      </motion.div>

      {/* Agent Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {agents.map((agent) => (
          <motion.div
            key={agent.id}
            variants={itemVariants}
            whileHover={{ y: -4, scale: 1.01 }}
            whileTap={{ scale: 0.99 }}
          >
            <Card
              className={`relative overflow-hidden cursor-pointer h-full ${
                activeAgent === agent.id ? "ring-2 ring-offset-2 ring-offset-black" : ""
              }`}
              style={{ borderColor: activeAgent === agent.id ? agent.color : undefined }}
              onClick={() => handleTryAgent(agent.id)}
            >
              <div className="absolute top-0 left-0 right-0 h-1" style={{ backgroundColor: agent.color }} />
              <div className="pt-2">
                <div className="flex items-center gap-3 mb-2">
                  <span className="text-3xl">{agent.emoji}</span>
                  <div>
                    <h3 className="font-semibold text-foreground">{agent.name}</h3>
                    <p className="text-[10px] text-muted">{agent.role}</p>
                  </div>
                </div>
                <p className="text-xs text-muted leading-relaxed mb-3">{agent.description}</p>
                <div className="space-y-1 mb-3">
                  <p className="text-[10px] text-muted/60 uppercase tracking-wider font-semibold">Try saying:</p>
                  {agent.promptExamples.map((example, i) => (
                    <p key={i} className="text-xs text-muted italic">💬 &ldquo;{example}&rdquo;</p>
                  ))}
                </div>
                <Button variant="ghost" size="sm" className="w-full" onClick={(e) => { e.stopPropagation(); handleTryAgent(agent.id); }}>
                  Ask {agent.name.split(" ")[0]} →
                </Button>
              </div>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* How it works */}
      <motion.div variants={itemVariants}>
        <Card variant="glass">
          <CardTitle>🧠 How the Agent System Works</CardTitle>
          <div className="mt-3 space-y-3 text-sm text-muted">
            <p>Each agent is a specialized AI persona that focuses on one aspect of your executive function.</p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-3">
              {[
                { step: "1", text: "You chat naturally" },
                { step: "2", text: "Agents analyze in real-time" },
                { step: "3", text: "Memory stores patterns" },
                { step: "4", text: "Personalized responses" },
              ].map((s) => (
                <div key={s.step} className="text-center p-3 rounded-xl bg-white/5">
                  <span className="text-xl font-bold text-calm-400 block">{s.step}</span>
                  <span className="text-xs text-muted">{s.text}</span>
                </div>
              ))}
            </div>
          </div>
        </Card>
      </motion.div>

      {/* Active agent detail */}
      <AnimatePresence>
        {activeAgent && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <Card
              variant="stat"
              style={{ borderColor: `${agents.find((a) => a.id === activeAgent)?.color}40` }}
            >
              <CardTitle>
                {agents.find((a) => a.id === activeAgent)?.emoji}{" "}
                {agents.find((a) => a.id === activeAgent)?.name}
              </CardTitle>
              <p className="text-sm text-muted mt-2">
                Head over to the Chat page to talk with this agent! Just mention what you need help with
                and the system will route your request to the right specialist.
              </p>
              <Button className="mt-3" onClick={() => router.push("/chat")}>
                Go to Chat →
              </Button>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Skill Trees */}
      <motion.div variants={itemVariants}>
        <Card>
          <CardTitle>🌳 Skill Trees — Level Up Your Executive Functions</CardTitle>
          <p className="text-xs text-muted mt-1">
            Each skill improves as you use the related features. Your progress determines your growth.
          </p>
          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3">
            {[
              {
                skill: "Focus", emoji: "🎯", color: "#6ee7b7",
                desc: "Improved by completing focus sessions",
                level: Math.min(5, Math.floor(game.total_focus_minutes / 30)),
                xp: game.total_focus_minutes % 30,
                maxXp: 30,
              },
              {
                skill: "Consistency", emoji: "📅", color: "#667eea",
                desc: "Improved by maintaining daily streaks",
                level: Math.min(5, game.streak),
                xp: game.streak % 5,
                maxXp: 5,
              },
              {
                skill: "Emotional Resilience", emoji: "😌", color: "#c084fc",
                desc: "Improved by mood tracking and recovery",
                level: Math.min(5, Math.floor(game.badges.length / 2)),
                xp: game.badges.length % 2,
                maxXp: 2,
              },
            ].map((tree) => (
              <div key={tree.skill} className="p-4 rounded-xl bg-surface border border-border">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-2xl">{tree.emoji}</span>
                  <div>
                    <p className="text-sm font-semibold text-foreground">{tree.skill}</p>
                    <p className="text-[10px] text-muted">Level {tree.level}/5</p>
                  </div>
                </div>
                <p className="text-xs text-muted mb-3">{tree.desc}</p>
                {/* XP bar */}
                <div className="h-2 bg-border rounded-full overflow-hidden">
                  <motion.div
                    className="h-full rounded-full"
                    style={{ backgroundColor: tree.color }}
                    initial={{ width: 0 }}
                    animate={{ width: `${(tree.xp / tree.maxXp) * 100}%` }}
                    transition={{ duration: 1, ease: "easeOut" }}
                  />
                </div>
                <div className="flex justify-between text-[10px] text-muted mt-1">
                  <span>{tree.xp}/{tree.maxXp} XP</span>
                  <span>Next: Lv.{Math.min(5, tree.level + 1)}</span>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-3">
            {[
              {
                skill: "Task Management", emoji: "📋", color: "#fbbf24",
                desc: "Improved by completing and breaking down tasks",
                level: Math.min(5, Math.floor(game.tasks_completed / 3)),
                xp: game.tasks_completed % 3,
                maxXp: 3,
              },
              {
                skill: "Self-Awareness", emoji: "💡", color: "#f87171",
                desc: "Improved by mood check-ins and journaling",
                level: Math.min(5, Math.floor(moodHistory.length / 5)),
                xp: moodHistory.length % 5,
                maxXp: 5,
              },
              {
                skill: "Mindfulness", emoji: "🧘", color: "#34d399",
                desc: "Improved by breathing exercises and breaks",
                level: Math.min(5, Math.floor(game.session_count / 5)),
                xp: game.session_count % 5,
                maxXp: 5,
              },
            ].map((tree) => (
              <div key={tree.skill} className="p-4 rounded-xl bg-surface border border-border">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-2xl">{tree.emoji}</span>
                  <div>
                    <p className="text-sm font-semibold text-foreground">{tree.skill}</p>
                    <p className="text-[10px] text-muted">Level {tree.level}/5</p>
                  </div>
                </div>
                <p className="text-xs text-muted mb-3">{tree.desc}</p>
                <div className="h-2 bg-border rounded-full overflow-hidden">
                  <motion.div
                    className="h-full rounded-full"
                    style={{ backgroundColor: tree.color }}
                    initial={{ width: 0 }}
                    animate={{ width: `${(tree.xp / tree.maxXp) * 100}%` }}
                    transition={{ duration: 1, ease: "easeOut" }}
                  />
                </div>
                <div className="flex justify-between text-[10px] text-muted mt-1">
                  <span>{tree.xp}/{tree.maxXp} XP</span>
                  <span>Next: Lv.{Math.min(5, tree.level + 1)}</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </motion.div>
    </motion.div>
  );
}
