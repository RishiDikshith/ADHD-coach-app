"use client";

import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";
import { Card, CardTitle, CardValue, CardLabel } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Celebration } from "@/components/shared/celebration";
import { useTimerStore } from "@/stores/timer-store";
import { useUserStore } from "@/stores/user-store";
import { formatTime } from "@/lib/utils";

// ADHD Focus Modes
const focusModes = [
  {
    id: "deep", name: "Deep Focus", emoji: "🎯",
    description: "Distraction-free deep work. Full screen, no interruptions.",
    defaultDuration: 25, durations: [15, 25, 30, 45, 60],
    color: "#6ee7b7",
    tips: ["Put phone in another room", "Close all unrelated tabs", "Use noise-canceling headphones"],
  },
  {
    id: "gentle", name: "Gentle Start", emoji: "🌱",
    description: "Anti-overwhelm mode. Short, low-pressure sessions.",
    defaultDuration: 8, durations: [3, 5, 8, 10, 15],
    color: "#667eea",
    tips: ["No pressure — just start", "Even 3 minutes counts", "You can stop anytime"],
  },
  {
    id: "recovery", name: "Recovery", emoji: "😌",
    description: "Burnout recovery. Gentle rest with breathing guide.",
    defaultDuration: 10, durations: [5, 10, 15, 20],
    color: "#c084fc",
    tips: ["Rest is productive", "Let your brain wander", "Hydrate and breathe"],
  },
  {
    id: "sprint", name: "Sprint Mode", emoji: "⚡",
    description: "High-energy dopamine bursts. Short, intense sessions.",
    defaultDuration: 15, durations: [5, 10, 15, 20, 25],
    color: "#fbbf24",
    tips: ["Go all in for the sprint", "Reward yourself after", "Channel hyperfocus productively"],
  },
];

const focusQuotes = [
  "You're exactly where you need to be.",
  "One breath at a time. One moment at a time.",
  "Starting is the hardest part — and you've already done it.",
  "Your focus is a muscle. Every session makes it stronger.",
  "Be gentle with yourself. Progress > perfection.",
  "This is your time. Protect it.",
  "Small steps lead to big changes.",
  "You've got this. One minute at a time.",
  "The only person you need to be better than is who you were yesterday.",
  "Rest is productive too. Your brain needs recovery.",
  "You don't need to be perfect. You just need to begin.",
  "Every session counts, no matter how short.",
];

const ambientThemes = [
  { name: "Ocean", gradient: "from-blue-900/30 via-cyan-800/20 to-blue-950/30", accent: "#06b6d4", glow: "rgba(6,182,212,0.15)" },
  { name: "Forest", gradient: "from-emerald-900/30 via-green-800/20 to-emerald-950/30", accent: "#10b981", glow: "rgba(16,185,129,0.15)" },
  { name: "Sunset", gradient: "from-orange-900/30 via-rose-800/20 to-purple-950/30", accent: "#f97316", glow: "rgba(249,115,22,0.15)" },
  { name: "Night", gradient: "from-indigo-950/30 via-purple-900/20 to-slate-950/30", accent: "#8b5cf6", glow: "rgba(139,92,246,0.15)" },
  { name: "Aurora", gradient: "from-teal-900/30 via-cyan-800/20 to-indigo-950/30", accent: "#2dd4bf", glow: "rgba(45,212,191,0.15)" },
  { name: "Warmth", gradient: "from-amber-900/30 via-yellow-800/20 to-orange-950/30", accent: "#f59e0b", glow: "rgba(245,158,11,0.15)" },
];

function BreathingGuide({ isActive, theme }: { isActive: boolean; theme: typeof ambientThemes[0] }) {
  const [phase, setPhase] = useState<"inhale" | "hold" | "exhale" | "rest">("inhale");
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (!isActive) return;
    const cycle = async () => {
      // Inhale 4s
      setPhase("inhale");
      const start1 = Date.now();
      const int1 = setInterval(() => {
        const p = (Date.now() - start1) / 4000;
        setProgress(Math.min(1, p));
        if (p >= 1) { clearInterval(int1); }
      }, 50);
      await new Promise(r => setTimeout(r, 4000));
      clearInterval(int1);

      // Hold 4s
      setPhase("hold");
      setProgress(1);
      await new Promise(r => setTimeout(r, 4000));

      // Exhale 6s
      setPhase("exhale");
      const start2 = Date.now();
      const int2 = setInterval(() => {
        const p = (Date.now() - start2) / 6000;
        setProgress(Math.max(0, 1 - p));
        if (p >= 1) { clearInterval(int2); }
      }, 50);
      await new Promise(r => setTimeout(r, 6000));
      clearInterval(int2);

      // Rest 2s
      setPhase("rest");
      setProgress(0);
      await new Promise(r => setTimeout(r, 2000));
    };
    cycle();
  }, [isActive]);

  if (!isActive) return null;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      className="fixed bottom-8 right-8 z-20"
    >
      <div className="relative flex items-center gap-3 bg-black/30 backdrop-blur-xl rounded-2xl p-4 border border-white/10">
        {/* Breathing circle */}
        <motion.div
          className="w-12 h-12 rounded-full"
          style={{
            backgroundColor: theme.accent,
            boxShadow: `0 0 20px ${theme.glow}`,
          }}
          animate={{
            scale: phase === "inhale" ? [1, 1.4] : phase === "exhale" ? [1.4, 1] : phase === "hold" ? 1.4 : 1,
            opacity: phase === "rest" ? 0.5 : 1,
          }}
          transition={{ duration: 0.3 }}
        />
        <div>
          <p className="text-xs font-medium text-foreground" style={{ color: theme.accent }}>
            {phase === "inhale" ? "Breathe In" : phase === "hold" ? "Hold" : phase === "exhale" ? "Breathe Out" : "Rest"}
          </p>
          <p className="text-[10px] text-muted">
            {phase === "inhale" ? "4 seconds" : phase === "hold" ? "4 seconds" : phase === "exhale" ? "6 seconds" : "2 seconds"}
          </p>
        </div>
      </div>
    </motion.div>
  );
}

export default function FocusPage() {
  const router = useRouter();
  const timer = useTimerStore();
  const { game, addPoints, incrementSession } = useUserStore();
  const [isActive, setIsActive] = useState(false);
  const [duration, setDuration] = useState(25);
  const [remaining, setRemaining] = useState(25 * 60);
  const [themeIndex, setThemeIndex] = useState(0);
  const [quoteIndex, setQuoteIndex] = useState(0);
  const [showQuote, setShowQuote] = useState(true);
  const [showCelebration, setShowCelebration] = useState(false);
  const [celebrationType, setCelebrationType] = useState<"confetti" | "levelUp" | "sparkle">("confetti");
  const [sessionsToday, setSessionsToday] = useState(0);
  const [isBreak, setIsBreak] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showBreathingGuide, setShowBreathingGuide] = useState(false);
  const [showMotivation, setShowMotivation] = useState(true);
  const [focusMode, setFocusMode] = useState(focusModes[0]);
  const [showModePicker, setShowModePicker] = useState(false);
  const [showDistractionLog, setShowDistractionLog] = useState(false);
  const [distractionLog, setDistractionLog] = useState<{id: string; label: string; time: number}[]>([]);
  const [recentDistractionsCount, setRecentDistractionsCount] = useState(0);
  const [sessionQuality, setSessionQuality] = useState<number | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const startTimeRef = useRef<number | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const [particles, setParticles] = useState<{ id: number; x: number; y: number; yOffset: number; duration: number; delay: number }[]>([]);

  // Asynchronously generate random positions in useEffect to keep render phase 100% pure
  useEffect(() => {
    if (!isActive) return;
    const width = typeof window !== "undefined" ? window.innerWidth : 1000;
    const height = typeof window !== "undefined" ? window.innerHeight : 800;
    const items = Array.from({ length: 20 }).map((_, i) => ({
      id: i,
      x: Math.random() * width,
      y: Math.random() * height,
      yOffset: -Math.random() * 100 - 50,
      duration: 3 + Math.random() * 4,
      delay: Math.random() * 5,
    }));
    const timer = setTimeout(() => {
      setParticles(items);
    }, 0);
    return () => clearTimeout(timer);
  }, [isActive]);

  useEffect(() => {
    const quoteInterval = setInterval(() => {
      setQuoteIndex((i) => (i + 1) % focusQuotes.length);
    }, 12000);
    return () => clearInterval(quoteInterval);
  }, []);

  const startFocus = useCallback(() => {
    startTimeRef.current = Date.now();
    setRemaining(duration * 60);
    setIsActive(true);
    setIsBreak(false);
    setShowQuote(true);
    setShowBreathingGuide(true);
    setShowMotivation(true);

    intervalRef.current = setInterval(() => {
      const elapsed = Math.floor((Date.now() - (startTimeRef.current || Date.now())) / 1000);
      const newRemaining = Math.max(0, duration * 60 - elapsed);
      setRemaining(newRemaining);

      if (newRemaining <= 0) {
        clearInterval(intervalRef.current!);
        setIsActive(false);
        setIsBreak(true);
        setShowBreathingGuide(false);
        setSessionsToday((s) => s + 1);
        incrementSession();
        addPoints(25);
        setCelebrationType("levelUp");
        setShowCelebration(true);
        setTimeout(() => setShowCelebration(false), 3500);
      }
    }, 100);
  }, [duration, incrementSession, addPoints]);

  const stopFocus = useCallback(() => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    setIsActive(false);
    setShowBreathingGuide(false);
    setRemaining(duration * 60);
  }, [duration]);

  const startBreak = useCallback(() => {
    const breakDuration = 5 * 60;
    startTimeRef.current = Date.now();
    setRemaining(breakDuration);
    setIsActive(true);
    setShowBreathingGuide(false);

    intervalRef.current = setInterval(() => {
      const elapsed = Math.floor((Date.now() - (startTimeRef.current || Date.now())) / 1000);
      const newRemaining = Math.max(0, breakDuration - elapsed);
      setRemaining(newRemaining);

      if (newRemaining <= 0) {
        clearInterval(intervalRef.current!);
        setIsActive(false);
        setIsBreak(false);
        setShowBreathingGuide(false);
        setCelebrationType("sparkle");
        setShowCelebration(true);
        setTimeout(() => setShowCelebration(false), 2500);
      }
    }, 100);
  }, []);

  const toggleFullscreen = useCallback(() => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().then(() => setIsFullscreen(true)).catch(() => {});
    } else {
      document.exitFullscreen().then(() => setIsFullscreen(false)).catch(() => {});
    }
  }, []);

  useEffect(() => {
    const handleFsChange = () => setIsFullscreen(!!document.fullscreenElement);
    document.addEventListener("fullscreenchange", handleFsChange);
    return () => {
      document.removeEventListener("fullscreenchange", handleFsChange);
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  const theme = ambientThemes[themeIndex];
  const progress = 1 - remaining / (isActive ? (isBreak ? 5 * 60 : duration * 60) : duration * 60);
  const circumference = 2 * Math.PI * 120;
  const strokeDashoffset = circumference * (1 - progress);

  return (
    <motion.div
      ref={containerRef}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className={`min-h-screen flex flex-col relative overflow-hidden ${isFullscreen ? "fixed inset-0 z-50" : ""}`}
    >
      <Celebration type={celebrationType} show={showCelebration} onComplete={() => setShowCelebration(false)} />

      {/* Animated ambient background with particles */}
      <div className={`absolute inset-0 bg-gradient-to-b ${theme.gradient} transition-all duration-1000`}>
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(255,255,255,0.03)_0%,transparent_70%)]" />
        
        {/* Floating gradient orbs */}
        <motion.div
          className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full blur-3xl"
          style={{ backgroundColor: theme.accent, opacity: 0.12 }}
          animate={{ x: [0, 40, -30, 0], y: [0, -40, 30, 0], scale: [1, 1.1, 0.95, 1] }}
          transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
        />
        <motion.div
          className="absolute bottom-1/4 right-1/4 w-80 h-80 rounded-full blur-3xl"
          style={{ backgroundColor: theme.accent, opacity: 0.08 }}
          animate={{ x: [0, -30, 40, 0], y: [0, 30, -40, 0], scale: [1, 0.95, 1.1, 1] }}
          transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }}
        />
        <motion.div
          className="absolute top-1/2 right-1/3 w-64 h-64 rounded-full blur-3xl"
          style={{ backgroundColor: theme.accent, opacity: 0.06 }}
          animate={{ x: [0, 20, -20, 0], y: [0, -20, 20, 0] }}
          transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
        />

        {/* Ambient particle dots */}
        {isActive && particles.map((p) => (
          <motion.div
            key={p.id}
            className="absolute w-1 h-1 rounded-full"
            style={{ backgroundColor: theme.accent, opacity: 0.2 }}
            initial={{
              x: p.x,
              y: p.y,
            }}
            animate={{
              y: [0, p.yOffset],
              opacity: [0.1, 0.3, 0.1],
            }}
            transition={{
              duration: p.duration,
              repeat: Infinity,
              delay: p.delay,
              ease: "easeInOut",
            }}
          />
        ))}
      </div>

      {/* Breathing Guide */}
      <BreathingGuide isActive={showBreathingGuide && isActive} theme={theme} />

      {/* Content */}
      <div className="relative z-10 flex flex-col h-screen">
        {/* Top bar */}
        <div className="flex items-center justify-between p-4 md:p-6">
          <button
            onClick={() => isFullscreen ? toggleFullscreen() : router.push("/dashboard")}
            className="px-3 py-1.5 rounded-xl glass text-sm text-muted hover:text-foreground transition-all"
          >
            {isFullscreen ? "⛶ Exit Fullscreen" : "← Back"}
          </button>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowMotivation(!showMotivation)}
              className="px-3 py-1.5 rounded-xl glass text-sm text-muted hover:text-foreground transition-all"
            >
              {showMotivation ? "💬 Quotes" : "💬 Hide"}
            </button>
            <Button
              variant="ghost"
              size="xs"
              onClick={() => setThemeIndex((i) => (i + 1) % ambientThemes.length)}
              className="text-xs text-muted"
            >
              🎨 {theme.name}
            </Button>
            <button
              onClick={toggleFullscreen}
              className="px-3 py-1.5 rounded-xl glass text-sm text-muted hover:text-foreground transition-all"
              title="Toggle fullscreen"
            >
              {isFullscreen ? "⛶" : "⛶"}
            </button>
          </div>
        </div>

        {/* Main timer area */}
        <div className="flex-1 flex flex-col items-center justify-center px-4">
          {/* Timer ring with glow effect */}
          <motion.div
            className="relative mb-8"
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.6, ease: "easeOut" }}
          >
            {/* Outer glow ring */}
            {isActive && (
              <motion.div
                className="absolute -inset-8 rounded-full blur-2xl"
                style={{ backgroundColor: theme.glow }}
                animate={{ opacity: [0.3, 0.6, 0.3] }}
                transition={{ duration: 3, repeat: Infinity }}
              />
            )}
            
            <svg width="300" height="300" className="transform -rotate-90 relative z-10">
              {/* Background ring */}
              <circle
                cx="150" cy="150" r="130"
                fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="4"
              />
              {/* Progress ring */}
              <motion.circle
                cx="150" cy="150" r="130"
                fill="none"
                stroke={theme.accent}
                strokeWidth="6"
                strokeLinecap="round"
                strokeDasharray={circumference}
                strokeDashoffset={isActive ? strokeDashoffset : circumference}
                className="transition-all duration-300"
                style={{ filter: `drop-shadow(0 0 12px ${theme.accent}60)` }}
              />
              {/* Inner decorative dots */}
              {isActive && Array.from({ length: 12 }).map((_, i) => (
                <circle
                  key={i}
                  cx={150 + 115 * Math.cos((i * 30 * Math.PI) / 180)}
                  cy={150 + 115 * Math.sin((i * 30 * Math.PI) / 180)}
                  r="2"
                  fill={theme.accent}
                  opacity={0.3}
                />
              ))}
            </svg>

            {/* Center content */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <motion.p
                  className="text-6xl md:text-7xl font-bold font-mono tracking-widest"
                  style={{ color: theme.accent }}
                  animate={isActive ? { scale: [1, 1.02, 1] } : {}}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  {formatTime(remaining)}
                </motion.p>
                <p className="text-sm text-muted mt-2">
                  {isActive ? (isBreak ? "☕ Break Time — Rest & Recharge" : "🎯 Focus Mode — You've Got This")
                  : isBreak ? "☕ Break over? Ready for another round?"
                  : isActive ? "🎯 Stay in the flow" : "⏸️ Ready when you are"}
                </p>
              </div>
            </div>
          </motion.div>

          {/* Motivational Quote */}
          <AnimatePresence mode="wait">
            {showMotivation && (
              <motion.div
                key={quoteIndex}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.5 }}
                className="text-center max-w-lg"
              >
                <p className="text-sm md:text-base text-muted/80 italic leading-relaxed">
                  &ldquo;{focusQuotes[quoteIndex]}&rdquo;
                </p>
                {/* Quote progress dots */}
                <div className="flex items-center justify-center gap-1.5 mt-3">
                  {focusQuotes.slice(0, 8).map((_, i) => (
                    <div
                      key={i}
                      className={`w-1.5 h-1.5 rounded-full transition-all duration-300 ${
                        i === quoteIndex ? "bg-calm-500" : "bg-white/10"
                      }`}
                    />
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Controls */}
          <div className="mt-8 flex items-center gap-4">
            {!isActive ? (
              <>
                {isBreak ? (
                  <>
                    <Button variant="calm" size="lg" onClick={startBreak} className="text-lg px-10">
                      ☕ Start Break
                    </Button>
                    <Button variant="primary" size="lg" onClick={() => { setIsBreak(false); startFocus(); }} className="text-lg px-10">
                      🎯 Next Session
                    </Button>
                  </>
                ) : (
                  <motion.div whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}>
                    <Button variant="primary" size="lg" onClick={startFocus} className="text-lg px-12 py-4 text-xl">
                      ▶ Start Focus Session
                    </Button>
                  </motion.div>
                )}
              </>
            ) : (
              <Button variant="danger" size="lg" onClick={stopFocus} className="text-lg px-10">
                ⏹ Stop
              </Button>
            )}
          </div>

          {/* Focus Mode Selector */}
          {!isActive && !isBreak && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-4"
            >
              <div className="flex items-center gap-2 justify-center mb-3">
                {!showModePicker ? (
                  <button
                    onClick={() => setShowModePicker(true)}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl glass text-sm"
                  >
                    <span>{focusMode.emoji}</span>
                    <span>{focusMode.name}</span>
                    <span className="text-muted text-xs">Change</span>
                  </button>
                ) : (
                  <div className="flex gap-2">
                    {focusModes.map((mode) => (
                      <motion.button
                        key={mode.id}
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => {
                          setFocusMode(mode);
                          setDuration(mode.defaultDuration);
                          setShowModePicker(false);
                        }}
                        className={`px-3 py-2 rounded-xl text-xs font-medium transition-all ${
                          focusMode.id === mode.id
                            ? "bg-calm-500/20 text-calm-400 border border-calm-500/30"
                            : "glass text-muted hover:text-foreground"
                        }`}
                      >
                        <span className="mr-1">{mode.emoji}</span>
                        {mode.name}
                      </motion.button>
                    ))}
                  </div>
                )}
              </div>

              {showModePicker && (
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="text-[10px] text-muted text-center mb-3"
                >
                  {focusModes.find(m => m.id === focusMode.id)?.description}
                </motion.p>
              )}

              {/* Duration selector */}
              <div className="flex items-center gap-2 glass rounded-2xl p-3 justify-center">
                {focusMode.durations.map((mins) => (
                  <button
                    key={mins}
                    onClick={() => setDuration(mins)}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                      duration === mins
                        ? "bg-calm-500/20 text-calm-400 border border-calm-500/30"
                        : "text-muted hover:text-foreground hover:bg-white/5"
                    }`}
                  >
                    {mins < 60 ? `${mins}m` : `${mins / 60}h`}
                  </button>
                ))}
              </div>

              {/* Mode tips */}
              {showModePicker && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="mt-2 flex gap-1.5 justify-center"
                >
                  {focusMode.tips.map((tip, i) => (
                    <span key={i} className="px-2 py-1 rounded-md bg-white/5 text-[10px] text-muted">{tip}</span>
                  ))}
                </motion.div>
              )}
            </motion.div>
          )}
        </div>

        {/* Stats bar */}
        <div className="p-4 md:p-6">
          <div className="flex items-center justify-center gap-6 md:gap-8 text-sm text-muted">
            <div className="text-center">
              <p className="font-bold text-foreground text-lg">{sessionsToday}</p>
              <p className="text-xs">Today</p>
            </div>
            <div className="w-px h-8 bg-border" />
            <div className="text-center">
              <p className="font-bold text-foreground text-lg">{game.streak}</p>
              <p className="text-xs">Streak</p>
            </div>
            <div className="w-px h-8 bg-border" />
            <div className="text-center">
              <p className="font-bold text-foreground text-lg">Lv.{game.level}</p>
              <p className="text-xs">Level</p>
            </div>
            <div className="w-px h-8 bg-border" />
            <div className="text-center">
              <p className="font-bold text-foreground text-lg">{Math.floor(game.total_focus_minutes / 60)}h {game.total_focus_minutes % 60}m</p>
              <p className="text-xs">Total</p>
            </div>
            <div className="w-px h-8 bg-border" />
            <button
              onClick={() => setShowDistractionLog(!showDistractionLog)}
              className="text-center hover:text-foreground transition-colors"
            >
              <p className="font-bold text-foreground text-lg">{distractionLog.length}</p>
              <p className="text-xs">Distractions</p>
            </button>
          </div>
        </div>
      </div>

      {/* Distraction Tracking Modal */}
      <AnimatePresence>
        {showDistractionLog && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-30 flex items-center justify-center bg-black/60 backdrop-blur-sm"
            onClick={() => setShowDistractionLog(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="glass-strong rounded-2xl p-6 w-full max-w-sm mx-4"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-bold text-foreground mb-1">🤔 Distraction Log</h3>
              <p className="text-xs text-muted mb-4">Track what pulled your focus to help you improve.</p>

              {isActive && (
                <div className="mb-4">
                  <p className="text-xs text-muted mb-2">What just distracted you?</p>
                  <div className="flex flex-wrap gap-1.5 mb-2">
                    {[
                      { id: "phone", label: "📱 Phone" },
                      { id: "social", label: "📲 Social media" },
                      { id: "noise", label: "🔊 Noise" },
                      { id: "thoughts", label: "💭 Wandering mind" },
                      { id: "notifications", label: "🔔 Notifications" },
                      { id: "people", label: "👥 People" },
                      { id: "hunger", label: "🍕 Hunger/thirst" },
                      { id: "other", label: "📌 Other" },
                    ].map((d) => (
                      <motion.button
                        key={d.id}
                        whileHover={{ scale: 1.03 }}
                        whileTap={{ scale: 0.97 }}
                        onClick={() => {
                          const now = Date.now();
                          setDistractionLog((prev) => [...prev, { id: d.id, label: d.label, time: now }]);
                          setRecentDistractionsCount((prev) => prev + 1);
                          setTimeout(() => {
                            setRecentDistractionsCount((prev) => Math.max(0, prev - 1));
                          }, 60000);
                        }}
                        className="px-2.5 py-1.5 rounded-xl text-xs bg-surface border border-border hover:border-calm-500/40 transition-all"
                      >
                        {d.label}
                      </motion.button>
                    ))}
                  </div>
                  {recentDistractionsCount > 0 && (
                    <motion.p
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="text-[10px] text-calm-400"
                    >
                      Logged {recentDistractionsCount} distraction{recentDistractionsCount > 1 ? "s" : ""} this session
                    </motion.p>
                  )}
                </div>
              )}

              {/* Distraction History */}
              {distractionLog.length > 0 && (
                <div className="max-h-40 overflow-y-auto space-y-1 mb-3">
                  <p className="text-xs text-muted mb-1">Recent distractions:</p>
                  {[...distractionLog].reverse().slice(0, 10).map((d, i) => (
                    <div key={i} className="flex items-center justify-between text-xs">
                      <span className="text-foreground">{d.label}</span>
                      <span className="text-muted">
                        {new Date(d.time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {distractionLog.length === 0 && (
                <p className="text-xs text-muted/50 text-center py-3">No distractions logged yet. That&apos;s great!</p>
              )}

              {/* Session Quality Rating */}
              {!isActive && sessionsToday > 0 && (
                <div className="mb-4">
                  <p className="text-xs text-muted mb-2">Rate your last session quality:</p>
                  <div className="flex gap-1.5 justify-center">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <motion.button
                        key={star}
                        whileHover={{ scale: 1.2 }}
                        whileTap={{ scale: 0.9 }}
                        onClick={() => setSessionQuality(star)}
                        className={`text-xl transition-all ${
                          sessionQuality && star <= sessionQuality ? "opacity-100" : "opacity-30"
                        }`}
                      >
                        {star <= 2 ? "😟" : star <= 3 ? "😐" : star <= 4 ? "😊" : "🤩"}
                      </motion.button>
                    ))}
                  </div>
                </div>
              )}

              <button
                onClick={() => setShowDistractionLog(false)}
                className="w-full py-2 rounded-xl glass text-sm text-muted hover:text-foreground transition-all"
              >
                Close
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
