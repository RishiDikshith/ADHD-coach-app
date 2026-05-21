"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Card, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs } from "@/components/ui/tabs";
import { useUserStore } from "@/stores/user-store";
import { useAnalyticsStore } from "@/stores/analytics-store";
import { Celebration } from "@/components/shared/celebration";
import { randomItem } from "@/lib/utils";

// ==================== Energy-Aware Task Data ====================

const energyLevels = [
  { level: "low", emoji: "🪫", label: "Low Energy", desc: "Brain fog, tired, can't focus" },
  { level: "medium", emoji: "🔋", label: "Medium Energy", desc: "Some focus, can do light work" },
  { level: "high", emoji: "⚡", label: "High Energy", desc: "Ready to tackle complex tasks" },
];

const lowEnergyTasks = [
  { emoji: "💧", text: "Drink a glass of water (just one sip counts)", time: "1 min" },
  { emoji: "🌬️", text: "Take 3 deep breaths — in for 4, out for 6", time: "1 min" },
  { emoji: "🧘", text: "Stand up and stretch your arms overhead", time: "1 min" },
  { emoji: "😌", text: "Close your eyes for 30 seconds", time: "30 sec" },
  { emoji: "✍️", text: "Write down ONE thing you're grateful for", time: "1 min" },
  { emoji: "🧹", text: "Put one single item back where it belongs", time: "1 min" },
  { emoji: "☀️", text: "Step outside or look out a window for 1 minute", time: "1 min" },
  { emoji: "💬", text: "Send one text you've been putting off", time: "2 min" },
  { emoji: "📝", text: "Open a blank page and write the date", time: "1 min" },
  { emoji: "🎵", text: "Put on one song — no more, just one", time: "1 min" },
];

const mediumEnergyTasks = [
  { emoji: "📧", text: "Reply to one email", time: "5 min" },
  { emoji: "📋", text: "Check one item off your to-do list", time: "3 min" },
  { emoji: "📖", text: "Read one page of something", time: "5 min" },
  { emoji: "🧹", text: "Tidy one small area (desk corner, one drawer)", time: "5 min" },
  { emoji: "💡", text: "Write down three ideas", time: "3 min" },
  { emoji: "📅", text: "Plan just the next 2 hours", time: "4 min" },
  { emoji: "🎯", text: "Set one intention for today", time: "2 min" },
  { emoji: "📊", text: "Organize one folder on your computer", time: "5 min" },
];

const highEnergyTasks = [
  { emoji: "🚀", text: "Start the hardest task for just 10 minutes", time: "10 min" },
  { emoji: "🧠", text: "Deep work session — block 25 minutes", time: "25 min" },
  { emoji: "📝", text: "Brain dump everything on your mind", time: "10 min" },
  { emoji: "🎨", text: "Work on a creative project", time: "20 min" },
  { emoji: "📚", text: "Study or read one chapter", time: "20 min" },
  { emoji: "📊", text: "Review and organize your week", time: "15 min" },
  { emoji: "💪", text: "Exercise or go for a walk", time: "15 min" },
];

const rescueWorkflows = [
  {
    trigger: "can't start", icon: "🐣",
    steps: [
      "Close all tabs except one",
      "Put phone face-down or in another room",
      "Set a timer for just 2 minutes",
      "Open the file/app you need",
      "Type/write ONE sentence",
    ],
  },
  {
    trigger: "stuck", icon: "🔄",
    steps: [
      "Stand up and walk away for 60 seconds",
      "Take 5 deep breaths (in for 4, hold for 4, out for 6)",
      "Ask yourself: what's the NEXT tiny action?",
      "Do that one action. Nothing else.",
    ],
  },
  {
    trigger: "scattered", icon: "🌀",
    steps: [
      "Write down everything in your head right now",
      "Circle the ONE thing that matters most",
      "Delete/close everything else",
      "Focus ONLY on the circled item for 5 minutes",
    ],
  },
];

const breakIdeas = [
  { emoji: "🚶", text: "Walk around the room", time: "2 min" },
  { emoji: "💪", text: "Do 5 jumping jacks or stretches", time: "1 min" },
  { emoji: "🧘", text: "Stretch your neck and shoulders", time: "2 min" },
  { emoji: "👀", text: "Look at something 20 feet away for 20 seconds", time: "1 min" },
  { emoji: "💧", text: "Refill your water bottle", time: "1 min" },
  { emoji: "📖", text: "Read one page of something fun", time: "3 min" },
  { emoji: "🎵", text: "Listen to one song", time: "3 min" },
  { emoji: "🧹", text: "Do one small chore while standing", time: "2 min" },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.06 } },
};
const itemVariants = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0 },
};

export default function TasksPage() {
  const { game, addPoints } = useUserStore();
  const { startTinyMode, setStartTinyMode } = useAnalyticsStore();
  const [currentTask, setCurrentTask] = useState("");
  const [taskInput, setTaskInput] = useState("");
  const [showCelebration, setShowCelebration] = useState(false);
  const [showTaskCelebration, setShowTaskCelebration] = useState(false);
  const [energyLevel, setEnergyLevel] = useState<string | null>(null);
  const [showEnergyPicker, setShowEnergyPicker] = useState(true);
  const [completedCount, setCompletedCount] = useState(0);

  // Show energy picker periodically
  useEffect(() => {
    if (completedCount > 0 && completedCount % 5 === 0) {
      setShowEnergyPicker(true);
    }
  }, [completedCount]);

  const handleCompleteTask = (taskText: string, points: number = 3) => {
    setCurrentTask(`✅ Done! ${taskText}`);
    addPoints(points);
    setCompletedCount((c) => c + 1);
    setShowCelebration(true);
    setTimeout(() => {
      setShowCelebration(false);
      setCurrentTask("");
    }, 2000);
  };

  const handleEnergyBasedTask = (level: string) => {
    setEnergyLevel(level);
    setShowEnergyPicker(false);
    let task;
    if (level === "low") task = randomItem(lowEnergyTasks);
    else if (level === "medium") task = randomItem(mediumEnergyTasks);
    else task = randomItem(highEnergyTasks);
    setCurrentTask(`⚡ ${task.emoji} ${task.text}${task.time ? ` (${task.time})` : ""}`);
    addPoints(2);
    setShowCelebration(true);
    setTimeout(() => setShowCelebration(false), 2000);
  };

  const handleBreakDown = () => {
    if (!taskInput.trim()) return;
    const words = taskInput.trim().split(" ");
    const isComplex = words.length > 5 || taskInput.length > 30;
    const steps = isComplex
      ? [
          { emoji: "1️⃣", text: `Open what you need for: "${taskInput.trim().substring(0, 30)}..."`, time: "2 min" },
          { emoji: "2️⃣", text: "Do just the first small part", time: "5 min" },
          { emoji: "3️⃣", text: "Take a 2-minute break (set a timer!)", time: "2 min" },
          { emoji: "4️⃣", text: "Do the next small part", time: "5 min" },
          { emoji: "5️⃣", text: "Decide if you want to continue", time: "1 min" },
          { emoji: "🎉", text: "Whatever you did — it counts as progress!", time: "Celebrate!" },
        ]
      : [
          { emoji: "1️⃣", text: `Open what you need for "${taskInput.trim()}"`, time: "2 min" },
          { emoji: "2️⃣", text: "Work on it for just 5 minutes", time: "5 min" },
          { emoji: "3️⃣", text: "Take a 2-minute break", time: "2 min" },
          { emoji: "4️⃣", text: "Decide if you'd like to continue", time: "1 min" },
        ];
    setCurrentTask(
      `🌱 Tiny start for "${taskInput.trim()}":\n\n${steps.map((s) => `${s.emoji} ${s.text} (${s.time})`).join("\n")}\n\n✨ You've got this. Just the first step.`
    );
    addPoints(5);
    setShowTaskCelebration(true);
    setTimeout(() => setShowTaskCelebration(false), 2000);
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="max-w-4xl mx-auto p-6 space-y-6"
    >
      <Celebration type="confetti" show={showCelebration} onComplete={() => setShowCelebration(false)} />
      <Celebration type="sparkle" show={showTaskCelebration} onComplete={() => setShowTaskCelebration(false)} />

      {/* Header */}
      <motion.div variants={itemVariants}>
        <h1 className="text-3xl font-bold text-foreground">🎯 Tasks</h1>
        <p className="text-muted mt-1">Energy-aware tasking. Break down overwhelm. Start tiny.</p>
      </motion.div>

      {/* Energy Check-in */}
      <AnimatePresence>
        {showEnergyPicker && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            <Card variant="glass" className="border-calm-500/30">
              <CardTitle>⚡ How&apos;s your energy right now?</CardTitle>
              <p className="text-sm text-muted mt-1">I&apos;ll suggest tasks that match your current state.</p>
              <div className="grid grid-cols-3 gap-2 mt-4">
                {energyLevels.map((e) => (
                  <motion.button
                    key={e.level}
                    whileHover={{ scale: 1.03 }}
                    whileTap={{ scale: 0.97 }}
                    onClick={() => handleEnergyBasedTask(e.level)}
                    className={`p-3 rounded-xl text-center transition-all duration-200 border ${
                      energyLevel === e.level
                        ? "bg-calm-500/10 border-calm-500/50"
                        : "bg-surface border-border hover:border-calm-500/30"
                    }`}
                  >
                    <span className="text-2xl block mb-1">{e.emoji}</span>
                    <span className="text-xs font-medium text-foreground block">{e.label}</span>
                    <span className="text-[10px] text-muted mt-0.5 block">{e.desc}</span>
                  </motion.button>
                ))}
              </div>
              <motion.button
                whileTap={{ scale: 0.98 }}
                onClick={() => setShowEnergyPicker(false)}
                className="text-xs text-muted hover:text-foreground mt-3 block text-center w-full transition-colors"
              >
                I know what I need — hide this
              </motion.button>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Tabs */}
      <Tabs
        tabs={[
          { id: "just-begin", label: "Just Begin", icon: "🐣" },
          { id: "energy-aware", label: "Energy Tasks", icon: "⚡" },
          { id: "break-down", label: "Break Down", icon: "🔨" },
          { id: "rescue", label: "Rescue", icon: "🆘" },
          { id: "breaks", label: "Breaks", icon: "☕" },
        ]}
      >
        {(activeTab) => (
          <motion.div key={activeTab} initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            {/* ===== JUST BEGIN TAB ===== */}
            {activeTab === "just-begin" && (
              <div className="space-y-4">
                <Card variant="glass" className="text-center border-calm-500/30 p-8">
                  <motion.div
                    className="text-5xl mb-3"
                    animate={{ y: [0, -6, 0] }}
                    transition={{ duration: 3, repeat: Infinity }}
                  >
                    🐣
                  </motion.div>
                  <CardTitle>Just Begin Mode</CardTitle>
                  <p className="text-sm text-muted mt-2 max-w-md mx-auto">
                    When you&apos;re stuck, just start with one tiny thing. Momentum builds from the smallest step.
                  </p>
                  <div className="flex gap-2 justify-center mt-4">
                    <motion.div whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}>
                      <Button variant="calm" size="lg" onClick={() => {
                        const task = randomItem(lowEnergyTasks);
                        handleCompleteTask(`${task.emoji} ${task.text}`, 3);
                      }}>
                        🌱 2-minute task
                      </Button>
                    </motion.div>
                    <motion.div whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}>
                      <Button variant="ghost" size="lg" onClick={() => setShowEnergyPicker(true)}>
                        ⚡ Pick by energy
                      </Button>
                    </motion.div>
                  </div>
                </Card>

                <div className="flex items-center justify-between px-2">
                  <span className="text-sm text-muted">🐣 Start Tiny Mode (always show micro-tasks)</span>
                  <button
                    onClick={() => setStartTinyMode(!startTinyMode)}
                    className={`w-11 h-6 rounded-full transition-all duration-300 relative ${
                      startTinyMode ? "bg-calm-500" : "bg-border"
                    }`}
                  >
                    <motion.div
                      className="absolute top-0.5 w-5 h-5 rounded-full bg-white shadow"
                      animate={{ left: startTinyMode ? 22 : 2 }}
                      transition={{ type: "spring", stiffness: 500, damping: 30 }}
                    />
                  </button>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {lowEnergyTasks.map((task, i) => (
                    <motion.button
                      key={i}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => handleCompleteTask(`${task.emoji} ${task.text}`, 2)}
                      className="p-3 rounded-xl bg-surface border border-border text-left hover:border-calm-500/40 transition-all text-sm"
                    >
                      <span className="text-lg mr-1.5">{task.emoji}</span>
                      <span className="text-muted text-xs">{task.text}</span>
                    </motion.button>
                  ))}
                </div>

                <AnimatePresence>
                  {currentTask && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                    >
                      <Card variant="stat">
                        <p className="text-sm text-foreground whitespace-pre-wrap">{currentTask}</p>
                      </Card>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            )}

            {/* ===== ENERGY-AWARE TAB ===== */}
            {activeTab === "energy-aware" && (
              <div className="space-y-4">
                <div className="grid grid-cols-3 gap-2">
                  {energyLevels.map((e) => (
                    <motion.button
                      key={e.level}
                      whileHover={{ scale: 1.03 }}
                      whileTap={{ scale: 0.97 }}
                      onClick={() => handleEnergyBasedTask(e.level)}
                      className={`p-4 rounded-xl text-center transition-all duration-200 border ${
                        energyLevel === e.level
                          ? "bg-calm-500/10 border-calm-500/50"
                          : "bg-surface border-border hover:border-calm-500/30"
                      }`}
                    >
                      <span className="text-3xl block mb-1">{e.emoji}</span>
                      <span className="text-sm font-medium text-foreground block">{e.label}</span>
                    </motion.button>
                  ))}
                </div>

                <AnimatePresence mode="wait">
                  {energyLevel === "low" && (
                    <motion.div key="low" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="grid grid-cols-2 gap-2">
                      {lowEnergyTasks.map((task, i) => (
                        <motion.button
                          key={i} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                          onClick={() => handleCompleteTask(`${task.emoji} ${task.text}`, 3)}
                          className="p-3 rounded-xl bg-surface border border-border text-left hover:border-calm-500/40 transition-all"
                        >
                          <span className="text-lg mr-1.5">{task.emoji}</span>
                          <span className="text-xs text-muted">{task.text}</span>
                        </motion.button>
                      ))}
                    </motion.div>
                  )}
                  {energyLevel === "medium" && (
                    <motion.div key="medium" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="grid grid-cols-2 gap-2">
                      {mediumEnergyTasks.map((task, i) => (
                        <motion.button
                          key={i} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                          onClick={() => handleCompleteTask(`${task.emoji} ${task.text} (${task.time})`, 4)}
                          className="p-3 rounded-xl bg-surface border border-border text-left hover:border-calm-500/40 transition-all"
                        >
                          <span className="text-lg mr-1.5">{task.emoji}</span>
                          <span className="text-xs text-muted">{task.text}</span>
                          <span className="text-[10px] text-calm-400 block mt-0.5">{task.time}</span>
                        </motion.button>
                      ))}
                    </motion.div>
                  )}
                  {energyLevel === "high" && (
                    <motion.div key="high" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="grid grid-cols-2 gap-2">
                      {highEnergyTasks.map((task, i) => (
                        <motion.button
                          key={i} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                          onClick={() => handleCompleteTask(`${task.emoji} ${task.text} (${task.time})`, 5)}
                          className="p-3 rounded-xl bg-surface border border-border text-left hover:border-calm-500/40 transition-all"
                        >
                          <span className="text-lg mr-1.5">{task.emoji}</span>
                          <span className="text-xs text-muted">{task.text}</span>
                          <span className="text-[10px] text-warm-400 block mt-0.5">{task.time}</span>
                        </motion.button>
                      ))}
                    </motion.div>
                  )}
                </AnimatePresence>

                <Card variant="stat">
                  <CardTitle>⚡ What is energy-aware tasking?</CardTitle>
                  <p className="text-sm text-muted mt-2">
                    Instead of fighting your brain, work WITH your current energy level. Low energy? Do micro-tasks.
                    High energy? Tackle deep work. This is how ADHD brains actually thrive.
                  </p>
                </Card>
              </div>
            )}

            {/* ===== BREAK DOWN TAB ===== */}
            {activeTab === "break-down" && (
              <div className="space-y-4">
                <Card>
                  <CardTitle>🔨 Break Down a Task</CardTitle>
                  <p className="text-sm text-muted mt-1">Tell me what feels overwhelming and I&apos;ll break it into micro-steps.</p>
                  <div className="mt-3 flex gap-2">
                    <input
                      type="text"
                      value={taskInput}
                      onChange={(e) => setTaskInput(e.target.value)}
                      placeholder='e.g. "Write an essay" or "Clean my room"'
                      className="flex-1 px-4 py-2.5 rounded-xl bg-surface border border-border text-foreground placeholder:text-muted/50 focus:outline-none focus:ring-2 focus:ring-calm-500/50 text-sm"
                      onKeyDown={(e) => e.key === "Enter" && handleBreakDown()}
                    />
                    <Button onClick={handleBreakDown}>Break Down</Button>
                  </div>
                </Card>

                <AnimatePresence>
                  {currentTask && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                    >
                      <Card variant="stat">
                        <p className="text-sm text-foreground whitespace-pre-wrap">{currentTask}</p>
                      </Card>
                    </motion.div>
                  )}
                </AnimatePresence>

                <Card variant="glass">
                  <CardTitle>💡 Why this works for ADHD</CardTitle>
                  <ul className="mt-3 space-y-2 text-sm text-muted">
                    <li>🧠 <strong>Reduces overwhelm</strong> by making tasks concrete and countable</li>
                    <li>🎯 <strong>Eliminates choice paralysis</strong> — you only need to do step 1</li>
                    <li>⚡ <strong>Builds momentum</strong> — starting is the hardest part</li>
                    <li>✨ <strong>Dopamine hits</strong> — each tiny step completed feels good</li>
                  </ul>
                </Card>
              </div>
            )}

            {/* ===== RESCUE TAB ===== */}
            {activeTab === "rescue" && (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {rescueWorkflows.map((wf, i) => (
                    <motion.div
                      key={i}
                      whileHover={{ y: -3 }}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.08 }}
                    >
                      <Card variant="glass" className="h-full border-danger-500/20">
                        <CardTitle>
                          <span className="text-2xl mr-2">{wf.icon}</span>
                          {wf.trigger.charAt(0).toUpperCase() + wf.trigger.slice(1)}
                        </CardTitle>
                        <ol className="mt-3 space-y-1.5">
                          {wf.steps.map((step, j) => (
                            <li key={j} className="flex items-start gap-2 text-xs text-muted">
                              <span className="text-calm-400 font-mono mt-0.5">{j + 1}.</span>
                              <span>{step}</span>
                            </li>
                          ))}
                        </ol>
                        <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.97 }}>
                          <Button
                            variant="danger"
                            size="sm"
                            className="w-full mt-3"
                            onClick={() => {
                              setCurrentTask(`🆘 Rescue: I can't start — \n\n${wf.steps.map((s, j) => `${j + 1}. ${s}`).join("\n")}`);
                              addPoints(5);
                              setShowTaskCelebration(true);
                              setTimeout(() => setShowTaskCelebration(false), 2000);
                            }}
                          >
                            🆘 Rescue me
                          </Button>
                        </motion.div>
                      </Card>
                    </motion.div>
                  ))}
                </div>

                <Card variant="stat">
                  <CardTitle>🌿 When to use Rescue Mode</CardTitle>
                  <div className="mt-3 text-sm text-muted space-y-2">
                    <p>🌀 <strong>Can&apos;t start?</strong> Use the &quot;Can&apos;t Start&quot; rescue — it reduces friction to almost zero.</p>
                    <p>🔄 <strong>Feeling stuck?</strong> The &quot;Stuck&quot; rescue resets your brain with a physical + mental shift.</p>
                    <p>🌪️ <strong>Feeling scattered?</strong> The &quot;Scattered&quot; rescue gives you one clear focus point.</p>
                  </div>
                </Card>
              </div>
            )}

            {/* ===== BREAKS TAB ===== */}
            {activeTab === "breaks" && (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {breakIdeas.map((task, i) => (
                    <motion.div
                      key={i}
                      whileHover={{ y: -2 }}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.05 }}
                    >
                      <Card variant="glass">
                        <div className="flex items-center gap-3">
                          <span className="text-2xl">{task.emoji}</span>
                          <div>
                            <p className="text-sm text-foreground font-medium">{task.text}</p>
                            <span className="text-[10px] text-calm-400">{task.time}</span>
                          </div>
                        </div>
                      </Card>
                    </motion.div>
                  ))}
                </div>

                <Card>
                  <CardTitle>☕ Pomodoro Break Guide</CardTitle>
                  <div className="mt-3 text-sm text-muted space-y-2">
                    <p>🎯 <strong>25 min focus</strong> → 5 min active break</p>
                    <p>🎯 After 4 cycles → take a 15-30 min real break</p>
                    <p>🎯 During breaks: move your body, hydrate, rest your eyes</p>
                    <p>🎯 Use the Focus Timer to track sessions</p>
                  </div>
                </Card>
              </div>
            )}
          </motion.div>
        )}
      </Tabs>

      {/* Completed count */}
      {completedCount > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center text-xs text-muted pb-4"
        >
          {completedCount} {completedCount === 1 ? "task" : "tasks"} completed this session
          {completedCount >= 5 && " 🎉 You're on fire!"}
          {completedCount >= 10 && " 🔥 Incredible momentum!"}
        </motion.div>
      )}
    </motion.div>
  );
}
