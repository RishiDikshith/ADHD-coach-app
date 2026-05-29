"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useState, useRef, useEffect, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Card, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Celebration } from "@/components/shared/celebration";
import { useChatStore } from "@/stores/chat-store";
import { useUserStore } from "@/stores/user-store";
import { useAnalyticsStore } from "@/stores/analytics-store";
import { api } from "@/services/api";

// Rich theme registry for all 8 specialized chatbots
const agentThemes: Record<string, {
  name: string;
  emoji: string;
  gradient: string;
  bubbleStyle: string;
  glow: string;
  bgGlow: string;
  tagline: string;
  avatarBg: string;
  quickActions: string[];
}> = {
  "productivity-coach": {
    name: "Productivity Coach",
    emoji: "⚡",
    gradient: "from-emerald-600 via-emerald-500 to-teal-500",
    bubbleStyle: "from-emerald-500/90 to-teal-500/80 text-black",
    glow: "shadow-emerald-500/20",
    bgGlow: "bg-emerald-500/5",
    tagline: "Let's find a realistic, shame-free rhythm together.",
    avatarBg: "bg-emerald-500/10 border-emerald-500/30 text-emerald-400",
    quickActions: [" Smart Plan my day", " Pick top 3 wins", " Give me motivation", " Keep it simple today"],
  },
  "task-breakdown": {
    name: "Task Breakdown",
    emoji: "🔨",
    gradient: "from-indigo-600 via-indigo-500 to-violet-500",
    bubbleStyle: "from-indigo-500/90 to-violet-500/80 text-white",
    glow: "shadow-indigo-500/20",
    bgGlow: "bg-indigo-500/5",
    tagline: "Breaking heavy tasks down into tiny, concrete micro-steps.",
    avatarBg: "bg-indigo-500/10 border-indigo-500/30 text-indigo-400",
    quickActions: [" Break down a task", " Give me a 2-minute starter", " Overwhelm rescue!", " Simplify a complex goal"],
  },
  "focus-coach": {
    name: "Focus Coach",
    emoji: "🎯",
    gradient: "from-amber-600 via-amber-500 to-orange-500",
    bubbleStyle: "from-amber-500/90 to-orange-500/80 text-black",
    glow: "shadow-amber-500/20",
    bgGlow: "bg-amber-500/5",
    tagline: "Shielding focus & building a quiet flow space.",
    avatarBg: "bg-amber-500/10 border-amber-500/30 text-amber-400",
    quickActions: [" Start a Pomodoro timer", " Help! I got distracted", " Get into flow state", " Review focus peaks"],
  },
  "burnout-support": {
    name: "Burnout Support",
    emoji: "🌿",
    gradient: "from-rose-600 via-rose-500 to-pink-500",
    bubbleStyle: "from-rose-500/80 to-pink-500/70 text-white",
    glow: "shadow-rose-500/20",
    bgGlow: "bg-rose-500/5",
    tagline: "A safe, warm space to rest and recover without guilt.",
    avatarBg: "bg-rose-500/10 border-rose-500/30 text-rose-400",
    quickActions: [" Quick breathing grounding", " Relieve resting guilt", " Help me slow down", " Make a recovery plan"],
  },
  "accountability-coach": {
    name: "Accountability Coach",
    emoji: "🤝",
    gradient: "from-purple-600 via-purple-500 to-fuchsia-500",
    bubbleStyle: "from-purple-500/90 to-fuchsia-500/80 text-white",
    glow: "shadow-purple-500/20",
    bgGlow: "bg-purple-500/5",
    tagline: "Zero judgment, positive checks, and momentum building.",
    avatarBg: "bg-purple-500/10 border-purple-500/30 text-purple-400",
    quickActions: [" 5-minute progress check", " Set accountability goal", " Review consistency", " Celebrate a small win"],
  },
  "mood-support": {
    name: "Mood Support",
    emoji: "😌",
    gradient: "from-sky-600 via-sky-500 to-cyan-500",
    bubbleStyle: "from-sky-500/90 to-cyan-500/80 text-black",
    glow: "shadow-sky-500/20",
    bgGlow: "bg-sky-500/5",
    tagline: "Checking in with emotions and stress reflections.",
    avatarBg: "bg-sky-500/10 border-sky-500/30 text-sky-400",
    quickActions: [" Guided emotional journal", " Check my mood trends", " Process high stress", " Journaling prompt"],
  },
  "habit-builder": {
    name: "Habit Builder",
    emoji: "🔄",
    gradient: "from-violet-600 via-violet-500 to-pink-500",
    bubbleStyle: "from-violet-500/90 to-pink-500/80 text-white",
    glow: "shadow-violet-500/20",
    bgGlow: "bg-violet-500/5",
    tagline: "Dopamine-friendly routine building & consistency hacks.",
    avatarBg: "bg-violet-500/10 border-violet-500/30 text-violet-400",
    quickActions: [" Optimize morning routine", " Set routine habit trigger", " Streak milestones", " ADHD routine hacks"],
  },
  "study-assistant": {
    name: "Study Assistant",
    emoji: "🎓",
    gradient: "from-cyan-600 via-cyan-500 to-emerald-500",
    bubbleStyle: "from-cyan-500/90 to-emerald-500/80 text-black",
    glow: "shadow-cyan-500/20",
    bgGlow: "bg-cyan-500/5",
    tagline: "Academic revision scheduling without the burnout.",
    avatarBg: "bg-cyan-500/10 border-cyan-500/30 text-cyan-400",
    quickActions: [" Break down a study topic", " Schedule study blocks", " Spaced repetition triggers", " Feynman method guide"],
  },
  "support-agent": {
    name: "AI Support Agent",
    emoji: "🆘",
    gradient: "from-pink-600 via-pink-500 to-rose-500",
    bubbleStyle: "from-pink-500/90 to-rose-500/80 text-white",
    glow: "shadow-pink-500/20",
    bgGlow: "bg-pink-500/5",
    tagline: "Shame-free tech support, glitches logging, & ADHD FAQs.",
    avatarBg: "bg-pink-500/10 border-pink-500/30 text-pink-400",
    quickActions: ["🐞 Report a glitch", "🎫 Check my tickets", "❓ View ADHD FAQs", "📣 Log app suggestion"],
  },
};

const messageVariants = {
  hidden: { opacity: 0, y: 15, scale: 0.98 },
  visible: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.25 } },
};

export default function ChatPage() {
  const {
    messages,
    isThinking,
    isStreaming,
    error,
    sendMessage,
    clearMessages,
    activeAgentId,
    setActiveAgentId,
    handoffSuggestion,
    setHandoffSuggestion,
  } = useChatStore();

  const { username, game, addPoints, settings } = useUserStore();
  const { overwhelmMode, setOverwhelmMode } = useAnalyticsStore();

  const [input, setInput] = useState("");
  const [showCelebration, setShowCelebration] = useState(false);
  const [celebrationType, setCelebrationType] = useState<"confetti" | "sparkle" | "levelUp">("confetti");
  const [celebrationMessage, setCelebrationMessage] = useState("");

  // Support Agent state
  const [tickets, setTickets] = useState<any[]>([]);
  const [loadingTickets, setLoadingTickets] = useState(false);
  const [ticketType, setTicketType] = useState("glitch");
  const [ticketSubject, setTicketSubject] = useState("");
  const [ticketDescription, setTicketDescription] = useState("");
  const [submittingTicket, setSubmittingTicket] = useState(false);
  const [expandedTicketId, setExpandedTicketId] = useState<number | null>(null);
  const [showSupportWidget, setShowSupportWidget] = useState(true);

  // Voice Assistant & Language states
  const [selectedLanguage, setSelectedLanguage] = useState(settings.language || "auto");
  const [autoSpeak, setAutoSpeak] = useState(settings.voice_autospeak ?? false);
  const [isRecording, setIsRecording] = useState(false);
  const [speakingMessageId, setSpeakingMessageId] = useState<number | null>(null);
  const recognitionRef = useRef<any>(null);

  const supportedLanguages = [
    { code: "auto", name: "Auto-Detect 🔍" },
    { code: "en", name: "English 🇺🇸" },
    { code: "es", name: "Spanish 🇪🇸" },
    { code: "fr", name: "French 🇫🇷" },
    { code: "de", name: "German 🇩🇪" },
    { code: "it", name: "Italian 🇮🇹" },
    { code: "pt", name: "Portuguese 🇵🇹" },
    { code: "hi", name: "Hindi 🇮🇳" },
    { code: "ja", name: "Japanese 🇯🇵" },
    { code: "zh", name: "Chinese 🇨🇳" },
    { code: "ar", name: "Arabic 🇸🇦" },
    { code: "ru", name: "Russian 🇷🇺" },
    { code: "ko", name: "Korean 🇰🇷" },
    { code: "nl", name: "Dutch 🇳🇱" },
    { code: "tr", name: "Turkish 🇹🇷" },
  ];

  const toggleSpeechInput = () => {
    if (typeof window === "undefined") return;
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Speech recognition is not supported in this browser. Please use Chrome or Edge.");
      return;
    }

    if (isRecording) {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      setIsRecording(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognitionRef.current = recognition;
    recognition.continuous = false;
    recognition.lang = selectedLanguage === "auto" ? "en-US" : selectedLanguage;
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      setIsRecording(true);
    };

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      if (transcript) {
        setInput(prev => prev ? `${prev} ${transcript}` : transcript);
      }
    };

    recognition.onerror = (event: any) => {
      console.error("Speech recognition error:", event.error);
      setIsRecording(false);
    };

    recognition.onend = () => {
      setIsRecording(false);
    };

    recognition.start();
  };

  const speakText = (text: string, msgIndex: number) => {
    if (typeof window === "undefined" || !window.speechSynthesis) return;

    if (speakingMessageId === msgIndex) {
      window.speechSynthesis.cancel();
      setSpeakingMessageId(null);
      return;
    }

    window.speechSynthesis.cancel();

    const cleanText = text
      .replace(/[*#_~`\[\]\(\)]/g, "")
      .replace(/REPLY:\s*/gi, "")
      .replace(/TASKS:\s*/gi, "")
      .trim();

    const utterance = new SpeechSynthesisUtterance(cleanText);
    
    // Connect user customization speed & pitch
    utterance.rate = settings.voice_speed ?? 1.0;
    utterance.pitch = settings.voice_pitch ?? 1.0;

    let speechLang = selectedLanguage;
    if (speechLang === "auto") {
      speechLang = settings.language || "en";
    }
    utterance.lang = speechLang;

    const voices = window.speechSynthesis.getVoices();
    let matchedVoice = null;
    
    if (settings.voice_accent && settings.voice_accent !== "auto") {
      matchedVoice = voices.find(v => v.lang.startsWith(settings.voice_accent!));
    }
    
    if (!matchedVoice) {
      matchedVoice = voices.find(v => v.lang.startsWith(speechLang.split("-")[0]));
    }
    
    if (matchedVoice) {
      utterance.voice = matchedVoice;
    }

    utterance.onend = () => {
      setSpeakingMessageId(null);
    };
    utterance.onerror = () => {
      setSpeakingMessageId(null);
    };

    setSpeakingMessageId(msgIndex);
    window.speechSynthesis.speak(utterance);
  };

  useEffect(() => {
    if (autoSpeak && messages.length > 0 && !isStreaming && !isThinking) {
      const lastMsg = messages[messages.length - 1];
      if (lastMsg.role === "assistant" && speakingMessageId === null) {
        speakText(lastMsg.content, messages.length - 1);
      }
    }
  }, [messages, isStreaming, isThinking, autoSpeak]);

  useEffect(() => {
    return () => {
      if (typeof window !== "undefined" && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const fetchTickets = useCallback(async () => {
    if (!username) return;
    setLoadingTickets(true);
    try {
      const res = await api.getUserTickets(username);
      if (res.success) {
        setTickets(res.tickets);
      }
    } catch (err) {
      console.error("Failed to load support tickets:", err);
    } finally {
      setLoadingTickets(false);
    }
  }, [username]);

  useEffect(() => {
    if (activeAgentId === "support-agent") {
      setActiveAgentId("productivity-coach");
    }
  }, [activeAgentId, setActiveAgentId]);

  const handleCreateTicket = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !ticketSubject.trim() || !ticketDescription.trim()) return;
    setSubmittingTicket(true);
    try {
      const res = await api.submitSupportTicket(
        username,
        ticketType,
        ticketSubject.trim(),
        ticketDescription.trim()
      );
      if (res.success) {
        setTicketSubject("");
        setTicketDescription("");
        addPoints(15);
        setCelebrationType("sparkle");
        setCelebrationMessage("🎟️ Support Ticket logged successfully! +15 XP");
        setShowCelebration(true);
        setTimeout(() => setShowCelebration(false), 2500);
        fetchTickets();
      }
    } catch (err) {
      console.error("Failed to submit support ticket:", err);
    } finally {
      setSubmittingTicket(false);
    }
  };

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Active theme mapping
  const currentTheme = agentThemes[activeAgentId] || agentThemes["productivity-coach"];

  // ==================== Breathing Guide State (Burnout Support) ====================
  const [breathingState, setBreathingState] = useState<"idle" | "inhale" | "hold" | "exhale">("idle");
  const [breathingProgress, setBreathingProgress] = useState(0);

  const startBreathingGuide = () => {
    setBreathingState("inhale");
    addPoints(5); // reward showing up
    setCelebrationType("sparkle");
    setCelebrationMessage("Let's drop our shoulders together...");
    setShowCelebration(true);
    setTimeout(() => setShowCelebration(false), 2000);
  };

  useEffect(() => {
    if (breathingState === "idle") return;
    let timer: NodeJS.Timeout;
    const cycleDuration = 4000; // 4s inhale/hold/exhale

    if (breathingState === "inhale") {
      timer = setTimeout(() => setBreathingState("hold"), cycleDuration);
    } else if (breathingState === "hold") {
      timer = setTimeout(() => setBreathingState("exhale"), cycleDuration);
    } else if (breathingState === "exhale") {
      timer = setTimeout(() => setBreathingState("inhale"), cycleDuration);
    }

    return () => clearTimeout(timer);
  }, [breathingState]);

  // ==================== Pomodoro Timer State (Focus Coach) ====================
  const [timerRemaining, setTimerRemaining] = useState(25 * 60);
  const [timerRunning, setTimerRunning] = useState(false);
  const timerIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const toggleTimer = () => {
    setTimerRunning(!timerRunning);
  };

  const resetTimer = () => {
    setTimerRunning(false);
    setTimerRemaining(25 * 60);
  };

  useEffect(() => {
    if (timerRunning) {
      timerIntervalRef.current = setInterval(() => {
        setTimerRemaining((prev) => prev - 1);
      }, 1000);
    } else {
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
    }

    return () => {
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
    };
  }, [timerRunning]);

  useEffect(() => {
    if (timerRemaining <= 0) {
      const timer = setTimeout(() => {
        setTimerRunning(false);
        setTimerRemaining(25 * 60);
        // Award Pomodoro completion XP!
        addPoints(50);
        setCelebrationType("levelUp");
        setCelebrationMessage("🏆 Amazing! Deep Focus Block Complete +50 XP!");
        setShowCelebration(true);
        setTimeout(() => setShowCelebration(false), 4000);
      }, 0);
      return () => clearTimeout(timer);
    }
  }, [timerRemaining, addPoints]);

  const formatTimer = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  // ==================== Checklist State (Task Breakdown) ====================
  const [checkedTasks, setCheckedTasks] = useState<Record<string, boolean>>({});

  const toggleChecklistTask = (taskId: string) => {
    const isChecked = !checkedTasks[taskId];
    setCheckedTasks((prev) => ({ ...prev, [taskId]: isChecked }));

    if (isChecked) {
      addPoints(10); // Reward task checkbox!
      setCelebrationType("sparkle");
      setCelebrationMessage("✨ Momentum starter checked off! +10 XP");
      setShowCelebration(true);
      setTimeout(() => setShowCelebration(false), 1500);
    }
  };

  // Auto-scroll
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTo({
        top: chatContainerRef.current.scrollHeight,
        behavior: "smooth"
      });
    }
  }, [messages, isThinking]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [input]);

  const handleSend = () => {
    if (!input.trim() || isThinking) return;
    const text = input.trim();
    setInput("");

    // Custom reward loops for ADHD completed moments
    const lower = text.toLowerCase();
    if (["i did it", "i finished", "done", "completed"].some((t) => lower.includes(t))) {
      addPoints(20);
      setCelebrationType("confetti");
      setCelebrationMessage("🎉 Epic accomplishment! Leveling up focus! +20 XP");
      setShowCelebration(true);
      setTimeout(() => setShowCelebration(false), 3000);
    }

    sendMessage(text, username || "default", undefined, selectedLanguage);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleQuickActionClick = (actionText: string) => {
    setInput(actionText.trim());
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  };

  return (
    <div className="flex flex-col h-[calc(100dvh-64px)] md:h-[100dvh] relative overflow-hidden bg-background">
      <Celebration type={celebrationType} show={showCelebration} onComplete={() => setShowCelebration(false)} />

      {/* Decorative Radial Ambient Glow for selected agent */}
      <div className={`absolute top-0 left-1/2 -translate-x-1/2 w-[500px] h-[300px] rounded-full ${currentTheme.bgGlow} blur-3xl opacity-60 pointer-events-none`} />

      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border/80 backdrop-blur-md bg-surface/30 relative z-10">
        <div className="flex items-center gap-3">
          <motion.div
            key={activeAgentId}
            initial={{ scale: 0.8, rotate: -8 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ type: "spring", stiffness: 260, damping: 20 }}
            className={`text-2xl w-11 h-11 flex items-center justify-center rounded-2xl border bg-surface/90 shadow-sm ${currentTheme.avatarBg}`}
          >
            {currentTheme.emoji}
          </motion.div>
          <div>
            <h1 className="text-base font-bold text-foreground flex items-center gap-2">
              {currentTheme.name}
            </h1>
            <p className="text-[11px] text-muted leading-none">
              {currentTheme.tagline}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {overwhelmMode && (
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30">
              🌿 Overwhelm Mode
            </span>
          )}
          {activeAgentId === "support-agent" && (
            <Button
              variant="outline"
              size="sm"
              className="text-xs rounded-xl border-pink-500/30 text-pink-400 hover:bg-pink-500/10"
              onClick={() => setShowSupportWidget(!showSupportWidget)}
            >
              {showSupportWidget ? "Hide Tickets 🎫" : "Show Tickets 🎫"}
            </Button>
          )}
          <Button variant="ghost" size="sm" className="text-xs rounded-xl" onClick={clearMessages}>
            Clear History
          </Button>
        </div>
      </div>

      {/* Handoff Suggestion Banner */}
      <AnimatePresence>
        {handoffSuggestion && (
          <motion.div
            initial={{ opacity: 0, y: -20, height: 0 }}
            animate={{ opacity: 1, y: 0, height: "auto" }}
            exit={{ opacity: 0, y: -20, height: 0 }}
            className="relative z-10 border-b border-calm-500/30 bg-calm-500/10 backdrop-blur-md overflow-hidden"
          >
            <div className="p-3.5 max-w-4xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3 text-center sm:text-left">
              <div className="flex items-center gap-2.5">
                <span className="text-xl">💡</span>
                <p className="text-xs text-calm-300 font-medium leading-normal">
                  {handoffSuggestion.message}
                </p>
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  className="text-[11px] h-8 bg-calm-500 hover:bg-calm-600 text-black font-bold rounded-xl"
                  onClick={() => {
                    setActiveAgentId(handoffSuggestion.agent_id);
                    setHandoffSuggestion(null);
                  }}
                >
                  Switch to {agentThemes[handoffSuggestion.agent_id]?.name || "Specialist"}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-[11px] h-8 text-white/80 rounded-xl"
                  onClick={() => setHandoffSuggestion(null)}
                >
                  Stay here
                </Button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Side-by-side main container */}
      <div className="flex-1 flex flex-row overflow-hidden relative z-10">
        {/* Left Side: Chat Container */}
        <div className="flex-1 flex flex-col h-full overflow-hidden">
          {/* Scrollable chat body */}
          <div ref={chatContainerRef} className="flex-1 overflow-y-auto p-4 space-y-5">
            
            {/* Dynamic Embedded Widgets based on active agent */}
            
            {/* 1. Pomodoro Timer Widget for Focus Coach */}
            {activeAgentId === "focus-coach" && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="max-w-md mx-auto"
              >
                <Card className="p-4 bg-surface/50 border-amber-500/30 border backdrop-blur-md shadow-md text-center space-y-3">
                  <CardTitle className="text-xs font-bold tracking-widest text-amber-400 uppercase flex items-center justify-center gap-2">
                    ⏱️ Deep Work Shield Timer
                  </CardTitle>
                  <div className="text-3xl font-black font-mono text-foreground leading-none">
                    {formatTimer(timerRemaining)}
                  </div>
                  <div className="flex justify-center gap-2 pt-1">
                    <Button
                      size="sm"
                      className="bg-amber-500 hover:bg-amber-600 text-black font-bold text-xs rounded-xl"
                      onClick={toggleTimer}
                    >
                      {timerRunning ? "Pause Timer" : "Start Focus Block"}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="border-border hover:bg-surface/85 text-xs rounded-xl"
                      onClick={resetTimer}
                    >
                      Reset
                    </Button>
                  </div>
                </Card>
              </motion.div>
            )}

            {/* 2. Pulsing Breathing Guide Widget for Burnout Support */}
            {activeAgentId === "burnout-support" && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="max-w-md mx-auto"
              >
                <Card className="p-4 bg-surface/50 border-rose-500/30 border backdrop-blur-md shadow-md text-center space-y-3">
                  <CardTitle className="text-xs font-bold tracking-widest text-rose-400 uppercase">
                    🧘 Compassionate Grounding Ring
                  </CardTitle>
                  
                  {breathingState === "idle" ? (
                    <div className="space-y-2">
                      <p className="text-xs text-muted leading-relaxed">
                        {"Feeling anxious, exhausted, or stuck? Let's take three deep breaths together."}
                      </p>
                      <Button
                        size="sm"
                        className="bg-rose-500 hover:bg-rose-600 text-white font-semibold text-xs rounded-xl"
                        onClick={startBreathingGuide}
                      >
                        Breathe with Me 🌬️
                      </Button>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center space-y-3 py-2">
                      <motion.div
                        animate={{
                          scale: breathingState === "inhale" ? 1.5 : breathingState === "hold" ? 1.5 : 0.9,
                        }}
                        transition={{ duration: 4, ease: "easeInOut" }}
                        className={`w-14 h-14 rounded-full flex items-center justify-center border-2 border-rose-400 bg-rose-500/20`}
                      >
                        <span className="text-lg">🌿</span>
                      </motion.div>
                      <p className="text-sm font-bold text-rose-300 capitalize tracking-wider">
                        {breathingState === "inhale" && "🌬️ Inhale deeply..."}
                        {breathingState === "hold" && "🛑 Hold and soften..."}
                        {breathingState === "exhale" && "💨 Gently exhale..."}
                      </p>
                      <Button
                        variant="ghost"
                        size="xs"
                        className="text-[10px] text-muted/60"
                        onClick={() => setBreathingState("idle")}
                      >
                        Stop Exercise
                      </Button>
                    </div>
                  )}
                </Card>
              </motion.div>
            )}

            {/* Empty state greeting */}
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center h-[60%] text-center space-y-4">
                <motion.div
                  animate={{ y: [0, -6, 0] }}
                  transition={{ duration: 3.5, repeat: Infinity, ease: "easeInOut" }}
                  className="text-6xl p-4 bg-surface/50 rounded-full border border-border/80 shadow-md"
                >
                  {currentTheme.emoji}
                </motion.div>
                <div className="space-y-1">
                  <h2 className="text-lg font-black text-foreground">
                    Chat with {currentTheme.name}
                  </h2>
                  <p className="text-xs text-muted max-w-sm mx-auto leading-relaxed">
                    {currentTheme.tagline} What productivity hurdle or emotional state shall we conquer today?
                  </p>
                </div>
              </div>
            )}

            {/* Messages List */}
            <AnimatePresence>
              {messages.map((msg, i) => {
                const isUser = msg.role === "user";
                
                return (
                  <motion.div
                    key={i}
                    variants={messageVariants}
                    initial="hidden"
                    animate="visible"
                    className={`flex ${isUser ? "justify-end" : "justify-start"}`}
                  >
                    <div className={`max-w-[85%] ${isUser ? "" : "flex items-end gap-2.5"}`}>
                      {!isUser && (
                        <div className={`text-xl w-8 h-8 rounded-xl flex items-center justify-center border bg-surface/90 shrink-0 ${currentTheme.avatarBg}`}>
                          {currentTheme.emoji}
                        </div>
                      )}
                      
                      <div
                        className={`p-3.5 rounded-2xl relative group ${
                          isUser
                            ? "bg-gradient-to-r from-calm-500 to-calm-400 text-black rounded-br-md shadow-sm"
                            : "bg-surface border border-border/60 rounded-bl-md"
                        }`}
                      >
                        {!isUser && (
                          <button
                            onClick={() => speakText(msg.content, i)}
                            className="absolute -top-2.5 -right-2.5 w-7 h-7 rounded-xl bg-surface border border-border flex items-center justify-center text-xs hover:text-calm-400 opacity-0 group-hover:opacity-100 transition-opacity focus:opacity-100 shadow-sm z-20"
                            title="Speak message aloud"
                          >
                            {speakingMessageId === i ? "🛑" : "🔊"}
                          </button>
                        )}
                        {/* Render message markdown content */}
                        <div className="prose prose-invert prose-xs max-w-none
                          prose-headings:text-foreground prose-headings:font-bold prose-headings:mt-2.5 prose-headings:mb-1.5
                          prose-p:text-foreground/90 prose-p:leading-relaxed prose-p:mb-2 prose-p:last:mb-0
                          prose-strong:text-foreground prose-strong:font-bold
                          prose-code:px-1 prose-code:py-0.5 prose-code:rounded-md prose-code:bg-white/10 prose-code:text-calm-300 prose-code:text-xs prose-code:font-mono
                          prose-pre:bg-white/5 prose-pre:border prose-pre:border-white/10 prose-pre:rounded-xl prose-pre:p-2.5
                          prose-li:text-foreground/90 prose-li:my-0.5
                          prose-ul:my-1.5 prose-ol:my-1.5
                          [&_ul]:!list-disc [&_ol]:!list-decimal [&_li]:!text-xs
                        ">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {msg.content}
                          </ReactMarkdown>
                        </div>

                        {/* Inline microtask checklists for Task Breakdown / general turns */}
                        {msg.tasks && msg.tasks.length > 0 && (
                          <div className="mt-3.5 pt-3 border-t border-border/40 space-y-2">
                            <p className="text-[9px] text-muted/60 uppercase tracking-widest font-bold">
                              🧠 Microtask Action Checklist (Earn +10 XP)
                            </p>
                            <div className="space-y-1.5">
                              {msg.tasks.map((task, j) => {
                                const taskId = `${i}-${j}`;
                                const isChecked = checkedTasks[taskId] || false;
                                
                                return (
                                  <div
                                    key={j}
                                    className="flex items-center gap-2.5 text-xs p-1 rounded-lg hover:bg-surface/50 transition-colors"
                                  >
                                    <input
                                      type="checkbox"
                                      checked={isChecked}
                                      onChange={() => toggleChecklistTask(taskId)}
                                      className="w-4 h-4 rounded-md border-border bg-surface text-calm-500 focus:ring-0 focus:ring-offset-0 cursor-pointer"
                                    />
                                    <span className={`${isChecked ? "line-through text-muted/50" : "text-foreground/80 font-medium"}`}>
                                      {task.emoji} {task.text}
                                    </span>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>

            {/* AI is thinking indicator */}
            {isThinking && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex justify-start items-end gap-2.5"
              >
                <div className={`text-xl w-8 h-8 rounded-xl flex items-center justify-center border bg-surface/90 shrink-0 ${currentTheme.avatarBg}`}>
                  {currentTheme.emoji}
                </div>
                <div className="bg-surface border border-border/60 rounded-2xl rounded-bl-md p-3.5">
                  <motion.div
                    className="flex items-center gap-2"
                    animate={{ opacity: [1, 0.4, 1] }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                  >
                    {[0, 150, 300].map((delay) => (
                      <motion.div
                        key={delay}
                        className="w-2.5 h-2.5 rounded-full bg-calm-400"
                        animate={{ y: [0, -5, 0] }}
                        transition={{ duration: 0.6, repeat: Infinity, delay: delay / 1000 }}
                      />
                    ))}
                  </motion.div>
                </div>
              </motion.div>
            )}

            {/* Stream progress or final error logs */}
            {error && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center py-2">
                <p className="text-xs text-rose-500 bg-rose-500/10 border border-rose-500/20 rounded-xl p-3 inline-block">
                  ⚠️ {error}
                </p>
              </motion.div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input container at the bottom */}
          <div className="border-t border-border/80 p-4 bg-surface/30 backdrop-blur-md relative z-10 space-y-3">
            
            {/* Quick Action Dopamine Suggesters */}
            <div className="flex gap-1.5 overflow-x-auto pb-1 scrollbar-none">
              {currentTheme.quickActions.map((act) => (
                <motion.button
                  key={act}
                  whileHover={{ scale: 1.02, y: -1 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => handleQuickActionClick(act)}
                  className="shrink-0 text-[10px] font-bold px-3 py-1.5 rounded-full bg-surface border border-border/60 text-muted hover:text-foreground hover:border-muted/50 transition-all shadow-sm"
                >
                  {act}
                </motion.button>
              ))}
            </div>

            {/* Message Input Box */}
            <div className="flex items-end gap-2.5">
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={
                  overwhelmMode
                    ? "Start with something tiny... even one word 🌱"
                    : `Message ${currentTheme.name}...`
                }
                rows={1}
                className="flex-1 resize-none px-4 py-3 rounded-2xl bg-surface border border-border/60 text-foreground placeholder:text-muted/40 focus:outline-none focus:ring-1 focus:ring-calm-500 focus:border-calm-500 transition-all text-xs max-h-[120px]"
              />

              {/* Mic Speech-to-Text Button */}
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={toggleSpeechInput}
                className={`w-10 h-10 rounded-2xl flex items-center justify-center shrink-0 border transition-all relative ${
                  isRecording
                    ? "bg-rose-500 border-rose-500 shadow-md shadow-rose-500/30 text-white animate-pulse"
                    : "bg-surface border-border/60 text-muted hover:text-foreground hover:border-muted/50"
                }`}
                title="Speak to type (Voice Input)"
              >
                <span className="text-sm">{isRecording ? "🛑" : "🎤"}</span>
              </motion.button>

              <Button
                onClick={handleSend}
                disabled={!input.trim() || isThinking}
                className={`rounded-2xl h-10 px-5 text-xs font-bold transition-all bg-gradient-to-r ${currentTheme.gradient} text-black border border-white/10`}
              >
                Send
              </Button>
            </div>

            {/* Premium Controls Tray for Voice and Language settings */}
            <div className="flex flex-wrap items-center justify-between gap-2.5 pt-2.5 border-t border-border/40">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold text-muted uppercase tracking-wider">🌐 Voice Language</span>
                <select
                  value={selectedLanguage}
                  onChange={(e) => setSelectedLanguage(e.target.value)}
                  className="bg-surface border border-border/60 rounded-xl px-2.5 py-1 text-xs text-foreground focus:outline-none cursor-pointer hover:border-muted/50 transition-all font-medium"
                >
                  {supportedLanguages.map((lang) => (
                    <option key={lang.code} value={lang.code}>
                      {lang.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => setAutoSpeak(!autoSpeak)}
                  className={`px-3 py-1 rounded-xl text-xs border transition-all flex items-center gap-1.5 font-bold ${
                    autoSpeak
                      ? "bg-calm-500/10 border-calm-500/50 text-calm-400"
                      : "bg-surface border-border text-muted hover:text-foreground"
                  }`}
                  title="Auto-speak AI responses"
                >
                  <span>{autoSpeak ? "🔊 Auto-Speak: On" : "🔇 Auto-Speak: Off"}</span>
                </button>
              </div>
            </div>

            <p className="text-[10px] text-muted/40 mt-1 text-center font-medium leading-none">
              Ecosystem session checkin · Streak {game.streak} days · Gamer Rank {Math.min(5, Math.floor(game.total_focus_minutes / 30) + 1)}
            </p>
          </div>
        </div>

        {/* Right Side: Interactive Support Ticket Widget */}
        {activeAgentId === "support-agent" && showSupportWidget && (
          <div className="w-80 md:w-96 border-l border-border bg-[#070b16]/90 backdrop-blur-xl flex flex-col h-full shrink-0 z-10 animate-in slide-in-from-right duration-300">
            {/* Widget Header */}
            <div className="p-4 border-b border-border flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-lg">🎫</span>
                <span className="font-bold text-xs uppercase tracking-wider text-pink-400">My Support Tickets</span>
              </div>
              <button
                onClick={fetchTickets}
                className="text-xs text-muted hover:text-foreground p-1 transition-colors flex items-center gap-1"
                disabled={loadingTickets}
              >
                {loadingTickets ? "🔄" : "🔁 Refresh"}
              </button>
            </div>

            {/* Scrollable list & form container */}
            <div className="flex-1 overflow-y-auto p-4 space-y-6">
              {/* Ticket List */}
              <div className="space-y-3">
                {loadingTickets && tickets.length === 0 ? (
                  <div className="space-y-2 py-3">
                    {[1, 2].map((i) => (
                      <div key={i} className="h-16 rounded-xl bg-surface animate-pulse" />
                    ))}
                  </div>
                ) : tickets.length === 0 ? (
                  <div className="text-center py-6 px-4 border border-dashed border-border rounded-2xl bg-surface/30">
                    <span className="text-2xl block mb-2">🌸</span>
                    <p className="text-xs text-muted font-medium">No tickets created yet.</p>
                    <p className="text-[10px] text-muted/60 mt-1">If you have a glitch or general question, raise one shame-free below!</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {tickets.map((t) => {
                      const isOpen = expandedTicketId === t.id;
                      const statusColors: Record<string, string> = {
                        open: "bg-amber-500/10 text-amber-400 border border-amber-500/20",
                        in_progress: "bg-indigo-500/10 text-indigo-400 border border-indigo-500/20",
                        resolved: "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20",
                      };

                      return (
                        <div
                          key={t.id}
                          onClick={() => setExpandedTicketId(isOpen ? null : t.id)}
                          className="p-3 rounded-xl border border-border/80 bg-surface/50 hover:bg-surface transition-all cursor-pointer space-y-2 shadow-sm"
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div>
                              <div className="flex items-center gap-1.5 flex-wrap">
                                <span className="text-[9px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider bg-white/5 border border-white/10 text-muted">
                                  {t.type}
                                </span>
                                <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider ${statusColors[t.status] || "bg-border text-muted"}`}>
                                  {t.status.replace("_", " ")}
                                </span>
                              </div>
                              <h4 className="font-bold text-xs mt-1 text-foreground/95 line-clamp-1">
                                {t.subject}
                              </h4>
                            </div>
                            <span className="text-xs text-muted/60 transition-transform">
                              {isOpen ? "▲" : "▼"}
                            </span>
                          </div>

                          <AnimatePresence>
                            {isOpen && (
                              <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: "auto" }}
                                exit={{ opacity: 0, height: 0 }}
                                className="text-[11px] text-muted/90 pt-1 border-t border-border/40 space-y-2 cursor-default"
                                onClick={(e) => e.stopPropagation()}
                              >
                                <p className="leading-relaxed whitespace-pre-wrap">{t.description}</p>
                                <p className="text-[9px] text-muted/40 font-mono">
                                  Logged: {new Date(t.created_at).toLocaleString()}
                                </p>
                              </motion.div>
                            )}
                          </AnimatePresence>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Ticket Creation Form */}
              <div className="border-t border-border pt-6 space-y-4">
                <div className="space-y-1">
                  <h3 className="text-xs font-bold text-foreground/90 uppercase tracking-wide">Raise Support Ticket</h3>
                  <p className="text-[10px] text-muted">Submit bugs, questions, or ideas. Shame-free.</p>
                </div>

                <form onSubmit={handleCreateTicket} className="space-y-3">
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-muted uppercase tracking-wider">Ticket Type</label>
                    <select
                      value={ticketType}
                      onChange={(e) => setTicketType(e.target.value)}
                      className="w-full bg-surface border border-border/60 rounded-xl px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-pink-500 text-foreground transition-all cursor-pointer font-medium"
                    >
                      <option value="glitch">Glitch / Bug 🐞</option>
                      <option value="question">Question / Coping FAQ ❓</option>
                      <option value="suggestion">App Suggestion 💡</option>
                    </select>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-muted uppercase tracking-wider">Subject</label>
                    <input
                      type="text"
                      required
                      value={ticketSubject}
                      onChange={(e) => setTicketSubject(e.target.value)}
                      placeholder="What is the issue?"
                      className="w-full bg-surface border border-border/60 rounded-xl px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-pink-500 text-foreground placeholder:text-muted/40 transition-all font-medium"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-muted uppercase tracking-wider">Description</label>
                    <textarea
                      required
                      rows={3}
                      value={ticketDescription}
                      onChange={(e) => setTicketDescription(e.target.value)}
                      placeholder="Give us a quick description of what you need or what happened..."
                      className="w-full bg-surface border border-border/60 rounded-xl px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-pink-500 text-foreground placeholder:text-muted/40 transition-all resize-none font-medium"
                    />
                  </div>

                  <Button
                    type="submit"
                    disabled={submittingTicket || !ticketSubject.trim() || !ticketDescription.trim()}
                    className="w-full rounded-xl py-2.5 text-xs font-bold transition-all bg-gradient-to-r from-pink-500 to-rose-500 hover:from-pink-600 hover:to-rose-600 text-white shadow-md border border-white/10"
                  >
                    {submittingTicket ? "Logging..." : "Submit Ticket 🚀"}
                  </Button>
                </form>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
