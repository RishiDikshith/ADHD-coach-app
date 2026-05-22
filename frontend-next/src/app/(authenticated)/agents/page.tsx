"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";
import { Card, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Celebration } from "@/components/shared/celebration";
import { useUserStore } from "@/stores/user-store";
import { useAnalyticsStore } from "@/stores/analytics-store";
import { useChatStore } from "@/stores/chat-store";

// Clean, curated list of the 8 dedicated chatbots matching the backend registry
const agentsList = [
  {
    id: "productivity-coach",
    name: "Productivity Coach",
    emoji: "⚡",
    specialty: "Executive function & motivation",
    description: "Helps you break down your day, set priorities, and find natural momentum without the shame.",
    color: "#10b981", // Emerald
    gradient: "from-emerald-500/20 to-teal-500/20",
    border_color: "border-emerald-500/30",
    text_color: "text-emerald-400",
    quick_actions: [" Smart Plan my day", " Pick top 3 wins", " Give me motivation"],
    memory_label: "Dopamine levels & focus spikes monitored",
  },
  {
    id: "task-breakdown",
    name: "Task Breakdown",
    emoji: "🔨",
    specialty: "Microtasking & paralysis rescue",
    description: "Transforms huge, intimidating projects into tiny, bite-sized 2-minute steps to beat paralysis.",
    color: "#6366f1", // Indigo
    gradient: "from-indigo-500/20 to-violet-500/20",
    border_color: "border-indigo-500/30",
    text_color: "text-indigo-400",
    quick_actions: [" Break down a task", " Give me a 2-minute starter", " Overwhelm rescue!"],
    memory_label: "Overwhelm triggers & task blocks logged",
  },
  {
    id: "focus-coach",
    name: "Focus Coach",
    emoji: "🎯",
    specialty: "Timers & distraction recovery",
    description: "Guides you through deep-work blocks, monitors distractions, and helps you recover focus.",
    color: "#f59e0b", // Amber
    gradient: "from-amber-500/20 to-orange-500/20",
    border_color: "border-amber-500/30",
    text_color: "text-amber-400",
    quick_actions: [" Start a Pomodoro timer", " Help! I got distracted", " Review focus peaks"],
    memory_label: "Distraction sources & flow hours mapped",
  },
  {
    id: "burnout-support",
    name: "Burnout Support",
    emoji: "🌿",
    specialty: "Exhaustion recovery & self-compassion",
    description: "Provides a safe, shame-free space when you are exhausted, stressed, or feeling guilty for resting.",
    color: "#ec4899", // Rose
    gradient: "from-rose-500/20 to-pink-500/20",
    border_color: "border-rose-500/30",
    text_color: "text-rose-400",
    quick_actions: [" Quick breathing grounding", " Relieve resting guilt", " Make a recovery plan"],
    memory_label: "Exhaustion cycles & rest history synced",
  },
  {
    id: "accountability-coach",
    name: "Accountability Coach",
    emoji: "🤝",
    specialty: "Gentle checks & zero shaming",
    description: "Your friendly, zero-judgment accountability partner to keep you moving consistently.",
    color: "#a855f7", // Purple
    gradient: "from-purple-500/20 to-fuchsia-500/20",
    border_color: "border-purple-500/30",
    text_color: "text-purple-400",
    quick_actions: [" 5-minute progress check", " Set an accountability goal", " Celebrate a small win"],
    memory_label: "Daily commitments & wins celebrated",
  },
  {
    id: "mood-support",
    name: "Mood Support",
    emoji: "😌",
    specialty: "Emotional processing & journaling",
    description: "Helps you check in with your emotions, reflect on stress levels, and understand your mood patterns.",
    color: "#0ea5e9", // Sky
    gradient: "from-sky-500/20 to-cyan-500/20",
    border_color: "border-sky-500/30",
    text_color: "text-sky-400",
    quick_actions: [" Guided emotional journal", " Check my mood trends", " Process high stress"],
    memory_label: "Mood logs & stress correlations mapped",
  },
  {
    id: "habit-builder",
    name: "Habit Builder",
    emoji: "🔄",
    specialty: "Low-friction routines",
    description: "Designs low-friction routines and rewards consistency with ADHD-friendly dopamine loops.",
    color: "#d8b4fe", // Light violet
    gradient: "from-violet-500/20 to-pink-500/20",
    border_color: "border-violet-500/30",
    text_color: "text-violet-400",
    quick_actions: [" Optimize my morning routine", " Set a routine trigger", " ADHD routine hacks"],
    memory_label: "Streak milestones & triggers recorded",
  },
  {
    id: "study-assistant",
    name: "Study Assistant",
    emoji: "🎓",
    specialty: "Academic scheduling & topics",
    description: "Helps you schedule study sessions, break down heavy subjects, and prepare for exams calmly.",
    color: "#06b6d4", // Cyan
    gradient: "from-cyan-500/20 to-emerald-500/20",
    border_color: "border-cyan-500/30",
    text_color: "text-cyan-400",
    quick_actions: [" Break down a study topic", " Schedule study blocks", " Spaced repetition triggers"],
    memory_label: "Academic topics & revision blocks tracked",
  },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.05 } },
};
const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
};

export default function AgentsPage() {
  const router = useRouter();
  const { game } = useUserStore();
  const { activeAgentId, setActiveAgentId } = useChatStore();
  const { moodHistory } = useAnalyticsStore();
  const [selectedCardId, setSelectedCardId] = useState<string | null>(null);
  const [showCelebration, setShowCelebration] = useState(false);

  // Recommend agent based on current user analytics
  const getRecommendedAgent = () => {
    // If user stress in moodHistory is high, suggest Burnout Support
    const latestMood = moodHistory[moodHistory.length - 1];
    if (latestMood && (latestMood.label === "Anxious" || latestMood.label === "Frustrated" || latestMood.label === "Worried")) {
      return "burnout-support";
    }
    // If focus sessions are low, suggest Focus Coach
    if (game.total_focus_minutes < 20) {
      return "focus-coach";
    }
    // Default suggestion
    return "productivity-coach";
  };

  const recommendedId = getRecommendedAgent();

  const handleLaunchAgent = (id: string) => {
    setActiveAgentId(id);
    setSelectedCardId(id);
    setShowCelebration(true);
    setTimeout(() => {
      setShowCelebration(false);
      router.push("/chat");
    }, 1200);
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="max-w-6xl mx-auto p-6 space-y-8"
    >
      <Celebration type="sparkle" show={showCelebration} onComplete={() => setShowCelebration(false)} />

      {/* Header */}
      <motion.div variants={itemVariants} className="space-y-2">
        <div className="flex items-center gap-3">
          <span className="text-4xl">🤖</span>
          <div>
            <h1 className="text-3xl font-black bg-gradient-to-r from-calm-400 via-focus-400 to-purple-400 bg-clip-text text-transparent">
              AI Chatbot Hub
            </h1>
            <p className="text-muted text-sm max-w-2xl mt-1">
              Choose from 8 dedicated ADHD chatbots with unique personalities, specialized memories, emotional styling, and expert tools.
            </p>
          </div>
        </div>
      </motion.div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {agentsList.map((agent) => {
          const isRecommended = agent.id === recommendedId;
          const isActive = agent.id === activeAgentId;
          
          return (
            <motion.div
              key={agent.id}
              variants={itemVariants}
              whileHover={{ y: -6, scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="relative"
            >
              <Card
                className={`relative overflow-hidden cursor-pointer h-full border bg-surface/40 backdrop-blur-md transition-all duration-300 hover:shadow-lg ${
                  isRecommended ? "ring-2 ring-calm-500/40 border-calm-500/40" : "border-border/60"
                } ${isActive ? "ring-2 ring-offset-2 ring-offset-black ring-focus-500/50" : ""}`}
                onClick={() => handleLaunchAgent(agent.id)}
              >
                {/* Background Ambient Glow */}
                <div className={`absolute -right-16 -bottom-16 w-36 h-36 rounded-full bg-gradient-to-br ${agent.gradient} blur-2xl opacity-40`} />

                {/* Top Border Accent */}
                <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-current to-transparent" style={{ color: agent.color }} />

                <div className="p-5 flex flex-col h-full justify-between relative z-10">
                  <div>
                    {/* Header */}
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <span className="text-4xl p-2 rounded-xl bg-surface border border-border/80 shadow-sm">
                          {agent.emoji}
                        </span>
                        <div>
                          <h3 className="font-bold text-foreground text-base flex items-center gap-1.5">
                            {agent.name}
                          </h3>
                          <p className="text-[10px] text-muted font-medium uppercase tracking-wider">
                            {agent.specialty}
                          </p>
                        </div>
                      </div>
                      
                      {isRecommended && (
                        <span className="text-[9px] px-2 py-0.5 rounded-full font-bold bg-calm-500/20 text-calm-400 border border-calm-500/30 uppercase tracking-widest animate-pulse">
                          🌟 Suggested
                        </span>
                      )}
                    </div>

                    {/* Description */}
                    <p className="text-xs text-muted/90 leading-relaxed mb-4 min-h-[48px]">
                      {agent.description}
                    </p>

                    {/* Memory Count status indicator */}
                    <div className="flex items-center gap-2 mb-4 p-2 rounded-lg bg-surface/50 border border-border/40">
                      <span className="text-xs">🧠</span>
                      <span className="text-[10px] text-muted/80 italic font-mono leading-none">
                        {agent.memory_label}
                      </span>
                    </div>

                    {/* Quick Actions */}
                    <div className="space-y-1.5 mb-5">
                      <p className="text-[9px] text-muted/60 uppercase tracking-widest font-bold">Expert Actions</p>
                      <div className="flex flex-wrap gap-1">
                        {agent.quick_actions.map((act) => (
                          <span
                            key={act}
                            className="text-[10px] px-2 py-1 rounded-md bg-surface/60 border border-border/40 text-muted"
                          >
                            {act}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  <Button
                    variant={isActive ? "primary" : "ghost"}
                    size="sm"
                    className="w-full mt-auto text-xs font-semibold rounded-xl border border-border bg-gradient-to-r hover:from-white/10 hover:to-white/5 transition-all"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleLaunchAgent(agent.id);
                    }}
                  >
                    {isActive ? "Currently Active ⚡" : `Chat with ${agent.name.split(" ")[0]} →`}
                  </Button>
                </div>
              </Card>
            </motion.div>
          );
        })}
      </div>

      {/* Skill Trees */}
      <motion.div variants={itemVariants}>
        <Card variant="glass">
          <CardTitle className="text-lg flex items-center gap-2">
            🌳 Level Up Your Executive Functions
          </CardTitle>
          <p className="text-xs text-muted mt-1">
            Each skill level improves as you chat with specialized agents, build routines, and conquer task paralysis.
          </p>
          <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              {
                skill: "Focus Capacity",
                emoji: "🎯",
                color: "#f59e0b",
                desc: "Boosted by Focus Coach sessions",
                level: Math.min(5, Math.floor(game.total_focus_minutes / 30) + 1),
                xp: game.total_focus_minutes % 30,
                maxXp: 30,
              },
              {
                skill: "Rhythm Consistency",
                emoji: "🔄",
                color: "#a855f7",
                desc: "Reinforced by Habit Builder routines",
                level: Math.min(5, game.streak + 1),
                xp: game.streak % 5,
                maxXp: 5,
              },
              {
                skill: "Emotional Resilience",
                emoji: "🌿",
                color: "#ec4899",
                desc: "Supported by Burnout recovery modes",
                level: Math.min(5, Math.floor(game.badges.length / 2) + 1),
                xp: game.badges.length % 2,
                maxXp: 2,
              },
            ].map((tree) => (
              <div key={tree.skill} className="p-4 rounded-xl bg-surface/50 border border-border/40 shadow-sm relative overflow-hidden group">
                <div className="flex items-center gap-3 mb-2.5">
                  <span className="text-2xl p-1.5 rounded-lg bg-surface/75 border border-border/50 group-hover:scale-110 transition-transform">{tree.emoji}</span>
                  <div>
                    <p className="text-sm font-bold text-foreground">{tree.skill}</p>
                    <p className="text-[10px] text-muted font-medium">Rank {tree.level}/5</p>
                  </div>
                </div>
                <p className="text-[11px] text-muted leading-normal mb-3">{tree.desc}</p>
                {/* XP Bar */}
                <div className="h-2 bg-border/50 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full rounded-full"
                    style={{ backgroundColor: tree.color }}
                    initial={{ width: 0 }}
                    animate={{ width: `${(tree.xp / tree.maxXp) * 100}%` }}
                    transition={{ duration: 1.2, ease: "easeOut" }}
                  />
                </div>
                <div className="flex justify-between text-[9px] text-muted font-semibold mt-1">
                  <span>{tree.xp}/{tree.maxXp} XP</span>
                  <span>Lv.{Math.min(5, tree.level + 1)}</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </motion.div>
    </motion.div>
  );
}
