"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";
import { Card, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Celebration } from "@/components/shared/celebration";
import { useUserStore } from "@/stores/user-store";
import { useAnalyticsStore } from "@/stores/analytics-store";
import { useChatStore } from "@/stores/chat-store";
import { API_URL } from "@/lib/api";

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
  const { game, settings } = useUserStore();
  const { activeAgentId, setActiveAgentId } = useChatStore();
  const { moodHistory } = useAnalyticsStore();
  const [selectedCardId, setSelectedCardId] = useState<string | null>(null);
  const [showCelebration, setShowCelebration] = useState(false);

  // ==================== VOICE ASSISTANT STATE ====================
  const [voiceSessionActive, setVoiceSessionActive] = useState(false);
  const [voiceAgentId, setVoiceAgentId] = useState<string | null>(null);
  const [voiceIsRecording, setVoiceIsRecording] = useState(false);
  const [voiceIsSpeaking, setVoiceIsSpeaking] = useState(false);
  const [voiceTranscript, setVoiceTranscript] = useState("");
  const [voiceAgentResponse, setVoiceAgentResponse] = useState("");
  const [voiceLanguage, setVoiceLanguage] = useState("en-US");
  const [voiceContinuousMode, setVoiceContinuousMode] = useState(true);
  const [voiceIsThinking, setVoiceIsThinking] = useState(false);
  const [voiceError, setVoiceError] = useState<string | null>(null);
  
  const voiceRecognitionRef = useRef<any>(null);
  const speakTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const activeVoiceAgent = agentsList.find(a => a.id === voiceAgentId);

  // Synchronize initial settings language
  useEffect(() => {
    if (settings.language) {
      if (settings.language === "es") setVoiceLanguage("es-ES");
      else if (settings.language === "fr") setVoiceLanguage("fr-FR");
      else if (settings.language === "de") setVoiceLanguage("de-DE");
      else if (settings.language === "it") setVoiceLanguage("it-IT");
      else if (settings.language === "pt") setVoiceLanguage("pt-PT");
      else if (settings.language === "hi") setVoiceLanguage("hi-IN");
      else if (settings.language === "ja") setVoiceLanguage("ja-JP");
      else if (settings.language === "zh") setVoiceLanguage("zh-CN");
      else setVoiceLanguage("en-US");
    }
  }, [settings.language]);

  // Clean synthesis on unmount
  useEffect(() => {
    return () => {
      if (typeof window !== "undefined" && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const startVoiceSession = (agentId: string) => {
    setVoiceAgentId(agentId);
    setVoiceTranscript("Tap the microphone or speak... 🎙️");
    
    const agentName = agentsList.find(a => a.id === agentId)?.name || "ADHD Assistant";
    let greeting = `Hi there! I am your ${agentName}. Let's chat voice-to-voice!`;
    if (settings.language === "es") greeting = `¡Hola! Soy tu ${agentName}. ¡Hablemos por voz!`;
    else if (settings.language === "fr") greeting = `Bonjour! Je suis ton ${agentName}. Parlons par voix!`;
    else if (settings.language === "de") greeting = `Hallo! Ich bin dein ${agentName}. Lass uns per Sprache chatten!`;
    else if (settings.language === "ja") greeting = `こんにちは！私はあなたの${agentName}です。音声で話しましょう！`;

    setVoiceAgentResponse(greeting);
    setVoiceSessionActive(true);
    setVoiceError(null);
    setVoiceIsSpeaking(false);
    setVoiceIsRecording(false);
    setVoiceIsThinking(false);

    // Automatically speak greeting
    setTimeout(() => {
      speakVoiceText(greeting, settings.language === "es" ? "es-ES" : settings.language === "fr" ? "fr-FR" : settings.language === "de" ? "de-DE" : settings.language === "ja" ? "ja-JP" : "en-US");
    }, 600);
  };

  const closeVoiceSession = () => {
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    if (voiceRecognitionRef.current) {
      voiceRecognitionRef.current.stop();
    }
    if (speakTimeoutRef.current) {
      clearTimeout(speakTimeoutRef.current);
    }
    setVoiceSessionActive(false);
    setVoiceAgentId(null);
  };

  const startSpeechListening = () => {
    if (typeof window === "undefined") return;
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setVoiceError("Speech recognition is not supported in this browser.");
      return;
    }

    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    setVoiceIsSpeaking(false);

    const recognition = new SpeechRecognition();
    voiceRecognitionRef.current = recognition;
    recognition.continuous = false;
    recognition.lang = voiceLanguage;
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      setVoiceIsRecording(true);
      setVoiceTranscript("Listening deeply... 🌱");
      setVoiceError(null);
    };

    recognition.onresult = async (event: any) => {
      const transcript = event.results[0][0].transcript;
      if (transcript) {
        setVoiceTranscript(transcript);
        setVoiceIsRecording(false);
        await sendVoicePrompt(transcript);
      }
    };

    recognition.onerror = (event: any) => {
      console.error("Speech recognition error:", event.error);
      setVoiceIsRecording(false);
      if (event.error !== "no-speech") {
        setVoiceError(`Mic error: ${event.error}`);
      } else {
        setVoiceTranscript("I didn't catch that. Tap 'Speak Now' to try again!");
      }
    };

    recognition.onend = () => {
      setVoiceIsRecording(false);
    };

    try {
      recognition.start();
    } catch (e) {
      console.error(e);
    }
  };

  const stopSpeechListening = () => {
    if (voiceRecognitionRef.current) {
      voiceRecognitionRef.current.stop();
    }
    setVoiceIsRecording(false);
  };

  const sendVoicePrompt = async (promptText: string) => {
    if (!promptText || !voiceAgentId) return;
    setVoiceIsThinking(true);
    setVoiceError(null);
    
    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: promptText,
          history: [],
          user_data: { sleep_hours: 7, stress_level: 5, phone_distractions: 0, energy_level: 5 },
          username: "default",
          agent_id: voiceAgentId,
          language: voiceLanguage.split("-")[0],
        })
      });

      if (!res.ok) {
        throw new Error(`Server returned code ${res.status}`);
      }

      const data = await res.json();
      const replyText = data.reply || "I am here to support you.";
      
      // Filter any custom syntax out
      const cleanReply = replyText.replace(/\*\*Tasks:\*\*/gi, "").split("Tasks:")[0].trim();
      setVoiceAgentResponse(cleanReply);
      setVoiceIsThinking(false);

      speakVoiceText(cleanReply, voiceLanguage);
    } catch (err: any) {
      console.error(err);
      setVoiceIsThinking(false);
      setVoiceError("Connection timed out. Please try speaking again.");
      setVoiceTranscript("Tap mic to retry.");
    }
  };

  const speakVoiceText = (text: string, langCode: string) => {
    if (typeof window === "undefined" || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();

    const cleanText = text
      .replace(/[*#_~`\[\]\(\)]/g, "")
      .replace(/REPLY:\s*/gi, "")
      .replace(/TASKS:\s*/gi, "")
      .trim();

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = settings.voice_speed ?? 1.0;
    utterance.pitch = settings.voice_pitch ?? 1.0;
    utterance.lang = langCode;

    const voices = window.speechSynthesis.getVoices();
    let matchedVoice = null;

    if (settings.voice_accent && settings.voice_accent !== "auto") {
      matchedVoice = voices.find(v => v.lang.startsWith(settings.voice_accent!));
    }

    if (!matchedVoice) {
      matchedVoice = voices.find(v => v.lang.startsWith(langCode.split("-")[0]));
    }

    if (matchedVoice) {
      utterance.voice = matchedVoice;
    }

    utterance.onstart = () => {
      setVoiceIsSpeaking(true);
    };

    utterance.onend = () => {
      setVoiceIsSpeaking(false);
      if (voiceContinuousMode && voiceSessionActive) {
        speakTimeoutRef.current = setTimeout(() => {
          startSpeechListening();
        }, 1200);
      }
    };

    utterance.onerror = () => {
      setVoiceIsSpeaking(false);
    };

    window.speechSynthesis.speak(utterance);
  };

  useEffect(() => {
    return () => {
      if (speakTimeoutRef.current) {
        clearTimeout(speakTimeoutRef.current);
      }
    };
  }, [voiceSessionActive, voiceContinuousMode]);

  // Recommend agent based on current user analytics
  const getRecommendedAgent = () => {
    const latestMood = moodHistory[moodHistory.length - 1];
    if (latestMood && (latestMood.label === "Anxious" || latestMood.label === "Frustrated" || latestMood.label === "Worried")) {
      return "burnout-support";
    }
    if (game.total_focus_minutes < 20) {
      return "focus-coach";
    }
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
          <span className="text-4xl animate-bounce">🤖</span>
          <div>
            <h1 className="text-3xl font-black bg-gradient-to-r from-calm-400 via-focus-400 to-purple-400 bg-clip-text text-transparent">
              AI Chatbot Hub
            </h1>
            <p className="text-muted text-sm max-w-2xl mt-1 font-medium">
              Select one of our 8 ADHD-specialized companions to start chatting verbally or via standard messaging. Enjoy continuous hands-free voice loops.
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
              whileHover={{ y: -6, scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
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
                          <p className="text-[10px] text-muted font-bold uppercase tracking-wider">
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
                    <p className="text-xs text-muted/90 leading-relaxed mb-4 min-h-[48px] font-medium">
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
                            className="text-[10px] px-2 py-1 rounded-md bg-surface/60 border border-border/40 text-muted font-medium"
                          >
                            {act}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Dual Mode Launch Panel */}
                  <div className="flex gap-2.5 w-full mt-auto">
                    <Button
                      variant={isActive ? "primary" : "ghost"}
                      size="sm"
                      className="flex-1 text-xs font-bold rounded-xl border border-border bg-gradient-to-r hover:from-white/10 hover:to-white/5 transition-all"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleLaunchAgent(agent.id);
                      }}
                    >
                      {isActive ? "Chat Active" : "💬 Chat"}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1 text-xs font-bold rounded-xl border-calm-500/20 text-calm-400 hover:bg-calm-500/10 hover:border-calm-500/40 transition-all flex items-center justify-center gap-1"
                      onClick={(e) => {
                        e.stopPropagation();
                        startVoiceSession(agent.id);
                      }}
                    >
                      🎙️ Voice
                    </Button>
                  </div>
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

      {/* Premium Glassmorphic Vocal Assistant Overlay */}
      <AnimatePresence>
        {voiceSessionActive && activeVoiceAgent && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-2xl"
          >
            <motion.div
              initial={{ scale: 0.95, y: 30, opacity: 0 }}
              animate={{ scale: 1, y: 0, opacity: 1 }}
              exit={{ scale: 0.95, y: 30, opacity: 0 }}
              transition={{ type: "spring", stiffness: 300, damping: 25 }}
              className="relative w-full max-w-lg overflow-hidden border border-white/10 bg-surface/80 backdrop-blur-xl shadow-2xl rounded-3xl p-6 md:p-8 space-y-6"
            >
              {/* Background ambient glow matching agent's theme */}
              <div className={`absolute -right-32 -top-32 w-64 h-64 rounded-full bg-gradient-to-br ${activeVoiceAgent.gradient} blur-3xl opacity-30 pointer-events-none`} />
              <div className={`absolute -left-32 -bottom-32 w-64 h-64 rounded-full bg-gradient-to-br ${activeVoiceAgent.gradient} blur-3xl opacity-30 pointer-events-none`} />

              {/* Header */}
              <div className="flex items-center justify-between border-b border-border/40 pb-4 relative z-10">
                <div className="flex items-center gap-3">
                  <span className="text-3xl p-1.5 rounded-xl bg-surface border border-border/60 shadow-sm">{activeVoiceAgent.emoji}</span>
                  <div>
                    <h2 className="text-lg font-black text-foreground">{activeVoiceAgent.name}</h2>
                    <p className="text-[10px] text-muted font-semibold uppercase tracking-widest leading-none">{activeVoiceAgent.specialty}</p>
                  </div>
                </div>
                <button
                  onClick={closeVoiceSession}
                  className="w-8 h-8 rounded-full border border-border bg-surface/50 hover:bg-surface/90 text-sm font-bold flex items-center justify-center text-muted hover:text-foreground transition-all cursor-pointer"
                >
                  ✕
                </button>
              </div>

              {/* Glowing Avatar & Visualizer */}
              <div className="flex flex-col items-center justify-center py-6 space-y-5 relative z-10">
                <motion.div
                  animate={{
                    scale: voiceIsRecording ? [1, 1.12, 1] : voiceIsSpeaking ? [1, 1.05, 1] : 1,
                    boxShadow: voiceIsRecording
                      ? "0 0 30px rgba(16, 185, 129, 0.4)"
                      : voiceIsSpeaking
                      ? "0 0 30px rgba(168, 85, 247, 0.4)"
                      : "0 0 15px rgba(255, 255, 255, 0.05)",
                  }}
                  transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut" }}
                  className={`w-28 h-28 rounded-full border-2 flex items-center justify-center bg-surface relative z-10 transition-all ${
                    voiceIsRecording
                      ? "border-emerald-500"
                      : voiceIsSpeaking
                      ? "border-purple-500"
                      : "border-white/10"
                  }`}
                >
                  <span className="text-5xl">{activeVoiceAgent.emoji}</span>
                </motion.div>

                {/* CSS soundwave visualizer */}
                <div className="flex items-center justify-center gap-1.5 h-10 w-48 overflow-hidden px-4">
                  {[...Array(9)].map((_, i) => {
                    let duration = 0.5 + Math.random() * 0.8;
                    let heightRange = voiceIsRecording ? [4, 32, 4] : voiceIsSpeaking ? [4, 20, 4] : [4, 8, 4];
                    let bgColor = voiceIsRecording
                      ? "bg-gradient-to-t from-emerald-500 to-cyan-400"
                      : voiceIsSpeaking
                      ? "bg-gradient-to-t from-purple-500 to-pink-500"
                      : "bg-border/60";

                    return (
                      <motion.div
                        key={i}
                        animate={{ height: heightRange }}
                        transition={{ duration: duration, repeat: Infinity, ease: "easeInOut", delay: i * 0.08 }}
                        className={`w-1.5 rounded-full ${bgColor}`}
                        style={{ height: "4px" }}
                      />
                    );
                  })}
                </div>
              </div>

              {/* Text Transcripts Panel */}
              <div className="space-y-3.5 bg-surface/50 border border-border/40 rounded-2xl p-4 relative z-10 max-h-[180px] overflow-y-auto">
                <div className="space-y-1.5">
                  <p className="text-[10px] text-muted font-bold uppercase tracking-wider flex items-center gap-1">
                    🎤 You said:
                  </p>
                  <p className="text-xs text-foreground/90 italic leading-relaxed pl-1.5">
                    {voiceTranscript}
                  </p>
                </div>
                <div className="space-y-1.5 border-t border-border/40 pt-3.5">
                  <p className="text-[10px] text-purple-400 font-bold uppercase tracking-wider flex items-center gap-1">
                    💬 {activeVoiceAgent.name} replied:
                  </p>
                  {voiceIsThinking ? (
                    <motion.div
                      animate={{ opacity: [0.4, 1, 0.4] }}
                      transition={{ duration: 1.2, repeat: Infinity }}
                      className="text-xs text-muted font-mono leading-none py-1 pl-1.5"
                    >
                      Thinking...
                    </motion.div>
                  ) : (
                    <p className="text-xs text-foreground leading-relaxed pl-1.5 font-medium">
                      {voiceAgentResponse}
                    </p>
                  )}
                </div>
              </div>

              {/* Status or Errors alerts */}
              {voiceError && (
                <div className="text-[11px] text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-xl p-2.5 text-center relative z-10 font-medium">
                  ⚠️ {voiceError}
                </div>
              )}

              {/* Lang and accent configs inside vocal console */}
              <div className="grid grid-cols-2 gap-3.5 border-t border-border/40 pt-4 relative z-10">
                <div className="space-y-1">
                  <span className="text-[9px] font-bold text-muted uppercase tracking-wider">Language</span>
                  <select
                    value={voiceLanguage}
                    onChange={(e) => setVoiceLanguage(e.target.value)}
                    className="w-full bg-surface/90 border border-border/80 rounded-xl px-2.5 py-1.5 text-xs text-foreground focus:outline-none cursor-pointer hover:border-muted/50 transition-all font-medium"
                  >
                    {[
                      { code: "en-US", name: "English 🇺🇸" },
                      { code: "es-ES", name: "Spanish 🇪🇸" },
                      { code: "fr-FR", name: "French 🇫🇷" },
                      { code: "de-DE", name: "German 🇩🇪" },
                      { code: "it-IT", name: "Italian 🇮🇹" },
                      { code: "pt-PT", name: "Portuguese 🇵🇹" },
                      { code: "hi-IN", name: "Hindi 🇮🇳" },
                      { code: "ja-JP", name: "Japanese 🇯🇵" },
                      { code: "zh-CN", name: "Chinese 🇨🇳" },
                      { code: "ru-RU", name: "Russian 🇷🇺" },
                      { code: "ko-KR", name: "Korean 🇰🇷" },
                    ].map((lang) => (
                      <option key={lang.code} value={lang.code}>
                        {lang.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1">
                  <span className="text-[9px] font-bold text-muted uppercase tracking-wider">Hands-Free Loop</span>
                  <button
                    onClick={() => setVoiceContinuousMode(!voiceContinuousMode)}
                    className={`w-full h-8 rounded-xl border text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${
                      voiceContinuousMode
                        ? "bg-calm-500/10 border-calm-500/50 text-calm-400"
                        : "bg-surface border-border text-muted hover:text-foreground"
                    }`}
                  >
                    {voiceContinuousMode ? "♾️ Continuous On" : "🔘 Continuous Off"}
                  </button>
                </div>
              </div>

              {/* Main Controls Panel */}
              <div className="flex items-center justify-center gap-3 pt-2 relative z-10">
                <Button
                  onClick={voiceIsRecording ? stopSpeechListening : startSpeechListening}
                  disabled={voiceIsThinking || voiceIsSpeaking}
                  className={`rounded-2xl h-12 px-6 text-xs font-bold flex items-center justify-center gap-1.5 shadow-lg transition-all ${
                    voiceIsRecording
                      ? "bg-rose-500 hover:bg-rose-600 text-white animate-pulse"
                      : "bg-gradient-to-r from-calm-500 to-calm-400 text-black border border-white/10"
                  }`}
                >
                  <span className="text-sm">{voiceIsRecording ? "🛑" : "🎤"}</span>
                  {voiceIsRecording ? "Stop Listening" : "Speak Now"}
                </Button>
                
                {voiceIsSpeaking && (
                  <Button
                    onClick={() => {
                      if (typeof window !== "undefined" && window.speechSynthesis) {
                        window.speechSynthesis.cancel();
                        setVoiceIsSpeaking(false);
                      }
                    }}
                    variant="outline"
                    className="rounded-2xl h-12 text-xs font-bold border-red-500/30 text-red-400 hover:bg-red-500/10"
                  >
                    ⏹️ Mute Speech
                  </Button>
                )}
              </div>

              <p className="text-[9px] text-muted/30 text-center font-medium leading-none relative z-10">
                ADHD Vocal Integration · Chrome Recommended for Auto Speech Handoff
              </p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
