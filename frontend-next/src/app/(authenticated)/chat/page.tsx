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

const suggestions = [
  "I'm feeling overwhelmed",
  "Help me start this task",
  "I need focus tips",
  "Give me a microtask",
  "I feel burned out",
  "Help me build a habit",
  "I'm proud of what I did today",
  "I can't stop scrolling",
];

// Emotional reaction map for the coach's avatar
const emotionalExpressions = {
  happy: "🌟",
  calm: "😌",
  supportive: "💪",
  concerned: "🤔",
  celebrating: "🎉",
  gentle: "🌿",
  default: "🧠",
} as const;

// Styles for different emotional tones
const toneStyles: Record<string, { gradient: string; emoji: string }> = {
  encouraging: { gradient: "from-calm-500/90 to-calm-400/80", emoji: "🌟" },
  gentle: { gradient: "from-focus-500/90 to-purple-500/70", emoji: "🌿" },
  direct: { gradient: "from-warm-500/90 to-warm-400/80", emoji: "🎯" },
  humorous: { gradient: "from-purple-500/90 to-pink-500/70", emoji: "😄" },
};

// Micro-celebration messages
const microCelebrations = [
  "One step at a time — you're doing it!",
  "That's the spirit! Momentum is building.",
  "Proud of you for showing up today.",
  "Small steps lead to big changes.",
  "You've got this. I believe in you.",
  "Opening up is the first win.",
];

const messageVariants = {
  hidden: { opacity: 0, y: 20, scale: 0.95 },
  visible: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.3 } },
};

export default function ChatPage() {
  const { messages, isThinking, error, sendMessage, clearMessages } = useChatStore();
  const { username, game, addPoints } = useUserStore();
  const { overwhelmMode, setOverwhelmMode } = useAnalyticsStore();
  const [input, setInput] = useState("");
  const [showCelebration, setShowCelebration] = useState(false);
  const [celebrationType, setCelebrationType] = useState<"confetti" | "sparkle" | "levelUp">("confetti");
  const [celebrationMessage, setCelebrationMessage] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(true);
  const [currentExpression, setCurrentExpression] = useState<keyof typeof emotionalExpressions>("default");
  const [quickActions, setQuickActions] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 150)}px`;
    }
  }, [input]);

  // Detect emotional tone from input and adjust expression
  const detectEmotion = useCallback((text: string) => {
    const lower = text.toLowerCase();
    if (["i did it", "i finished", "i completed", "i accomplished", "done!", "heck yes", "lets go", "proud"].some((t) => lower.includes(t))) {
      setCurrentExpression("celebrating");
      return "celebrating";
    }
    if (["happy", "great", "amazing", "wonderful", "awesome", "good day"].some((t) => lower.includes(t))) {
      setCurrentExpression("happy");
      return "happy";
    }
    if (["calm", "peaceful", "relaxed", "okay", "fine"].some((t) => lower.includes(t))) {
      setCurrentExpression("calm");
      return "calm";
    }
    if (["overwhelm", "stressed", "anxious", "scared", "worried", "panic"].some((t) => lower.includes(t))) {
      setCurrentExpression("concerned");
      setOverwhelmMode?.(true);
      return "concerned";
    }
    if (["need help", "struggling", "support", "please", "don't know"].some((t) => lower.includes(t))) {
      setCurrentExpression("supportive");
      return "supportive";
    }
    if (["gentle", "soft", "kind", "slow"].some((t) => lower.includes(t))) {
      setCurrentExpression("gentle");
      return "gentle";
    }
    setCurrentExpression("default");
    return "default";
  }, [setOverwhelmMode]);

  const handleSend = () => {
    if (!input.trim() || isThinking) return;
    const text = input.trim();
    setInput("");
    setShowSuggestions(false);

    // Emotional detection
    const emotion = detectEmotion(text);

    // Celebration trigger check
    const lower = text.toLowerCase();
    if (["i did it", "i finished", "i completed", "i accomplished", "done!", "heck yes", "lets go", "i did", "proud of"].some((t) => lower.includes(t))) {
      addPoints(10);
      setCelebrationType("levelUp");
      setCelebrationMessage("🌟 Amazing! That's a real win!");
      setShowCelebration(true);
      setTimeout(() => setShowCelebration(false), 3500);
    }

    // Micro-celebration for any positive input
    if (["better", "good", "progress", "did", "completed", "finished", "accomplished"].some((t) => lower.includes(t)) && !lower.includes("overwhelm")) {
      addPoints(2);
      setCelebrationType("sparkle");
      setCelebrationMessage(microCelebrations[Math.floor(Math.random() * microCelebrations.length)]);
      setShowCelebration(true);
      setTimeout(() => setShowCelebration(false), 2500);
    }

    // Auto-show quick actions for overwhelm
    if (emotion === "concerned") {
      setQuickActions(["🌬️ Breathing exercise", "📝 Write what's on your mind", "🌱 Give me a tiny task"]);
    } else {
      setQuickActions([]);
    }

    sendMessage(text, username || "default");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const todaySessionCount = game.session_count;

  return (
    <div className="flex flex-col h-[calc(100vh-0px)]">
      <Celebration type={celebrationType} show={showCelebration} onComplete={() => setShowCelebration(false)} />

      {/* Header with adaptive avatar */}
      <div className="flex items-center justify-between p-4 border-b border-border">
        <div className="flex items-center gap-3">
          <motion.div
            key={currentExpression}
            initial={{ scale: 0.5, rotate: -10 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ type: "spring", stiffness: 300, damping: 15 }}
            className="text-2xl w-10 h-10 flex items-center justify-center rounded-full bg-surface border border-border"
          >
            {emotionalExpressions[currentExpression]}
          </motion.div>
          <div>
            <h1 className="text-xl font-bold text-foreground">
              {overwhelmMode ? "🌿 ADHD Companion" : "💬 ADHD Coach"}
            </h1>
            <p className="text-xs text-muted">
              {overwhelmMode
                ? "I'm here with you — no pressure, just support"
                : "Your emotionally intelligent productivity companion"}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {overwhelmMode && (
            <motion.span
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="px-2.5 py-1 rounded-full text-xs font-medium bg-danger-500/20 text-danger-400 border border-danger-500/30"
            >
              🌿 Gentle Mode
            </motion.span>
          )}
          <Button variant="ghost" size="sm" onClick={clearMessages}>
            Clear
          </Button>
        </div>
      </div>

      {/* Overwhelm banner */}
      <AnimatePresence>
        {overwhelmMode && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div className="overwhelm-banner mx-4 mt-3">
              <p className="text-danger-400 font-medium mb-1">🌿 You&apos;re in Gentle Mode</p>
              <p className="text-sm text-danger-400/80">
                Take a deep breath. Let&apos;s start small. I&apos;m here with you.
              </p>
              <div className="flex gap-2 mt-3 justify-center">
                <Button variant="ghost" size="sm" className="text-danger-400/80" onClick={() => {
                  setInput("I need to ground myself");
                  handleSend();
                }}>
                  🌬️ Ground me
                </Button>
                <Button variant="ghost" size="sm" onClick={() => setOverwhelmMode(false)}>
                  Exit Gentle Mode
                </Button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Quick Actions */}
      <AnimatePresence>
        {quickActions.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="flex gap-2 px-4 pt-3 overflow-x-auto"
          >
            {quickActions.map((action) => (
              <motion.button
                key={action}
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
                onClick={() => {
                  setInput(action.split(" ").slice(1).join(" "));
                }}
                className="shrink-0 px-3 py-1.5 text-xs rounded-full bg-surface border border-border text-muted hover:text-foreground hover:border-calm-500/50 transition-all"
              >
                {action}
              </motion.button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center text-muted space-y-3">
            <motion.div
              className="text-5xl"
              animate={{ y: [0, -8, 0] }}
              transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
            >
              {overwhelmMode ? "🌿" : "🧠"}
            </motion.div>
            <p className="text-lg font-medium text-foreground">
              {overwhelmMode ? "Hey, I'm here with you" : "Hey! I'm your ADHD Coach"}
            </p>
            <p className="text-sm max-w-md">
              {overwhelmMode
                ? "No pressure at all. Want to share just one thing? Or we can sit in silence together."
                : "Tell me what's on your mind — tasks, overwhelm, focus struggles, or just how your day is going."}
            </p>
            <AnimatePresence>
              {showSuggestions && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 10 }}
                  className="flex flex-wrap gap-2 justify-center mt-2"
                >
                  {suggestions.map((suggestion, i) => (
                    <motion.button
                      key={suggestion}
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: i * 0.05 }}
                      onClick={() => setInput(suggestion)}
                      className="px-3 py-1.5 text-xs rounded-full bg-surface border border-border text-muted hover:text-foreground hover:border-calm-500/50 transition-all"
                    >
                      {suggestion}
                    </motion.button>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}

        <AnimatePresence>
          {messages.map((msg, i) => {
            // Detect emotional tone from assistant messages
            const isAssistant = msg.role === "assistant";
            const isCelebratory = isAssistant && msg.content.includes("🎉");
            const isGentle = isAssistant && (msg.content.includes("🌿") || msg.content.includes("breathe") || msg.content.includes("gentle"));
            const isSupportive = isAssistant && (msg.content.includes("💪") || msg.content.includes("proud") || msg.content.includes("got this"));
            const isConcerned = isAssistant && (msg.content.includes("🤔") || msg.content.includes("tough") || msg.content.includes("okay?"));

            let bubbleStyle = "";
            let bubbleEmoji = "🧠";
            if (isCelebratory) { bubbleStyle = "from-calm-500/90 to-calm-400/80"; bubbleEmoji = "🎉"; }
            else if (isGentle) { bubbleStyle = "from-focus-500/90 to-purple-500/70"; bubbleEmoji = "🌿"; }
            else if (isSupportive) { bubbleStyle = "from-warm-500/90 to-warm-400/80"; bubbleEmoji = "💪"; }
            else if (isConcerned) { bubbleStyle = "from-purple-500/80 to-pink-500/60"; bubbleEmoji = "🤔"; }

            return (
              <motion.div
                key={i}
                variants={messageVariants}
                initial="hidden"
                animate="visible"
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div className={`max-w-[80%] ${msg.role === "user" ? "" : "flex items-end gap-2"}`}>
                  {isAssistant && (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      className="text-lg mb-1 shrink-0"
                    >
                      {bubbleEmoji}
                    </motion.div>
                  )}
                  <div
                    className={`p-3 rounded-2xl ${
                      msg.role === "user"
                        ? "bg-gradient-to-r from-calm-500 to-calm-400 text-black rounded-br-md"
                        : bubbleStyle
                          ? `bg-gradient-to-r ${bubbleStyle} text-white rounded-bl-md`
                          : "bg-surface border border-border rounded-bl-md"
                    }`}
                  >
                    <div className="prose prose-invert prose-sm max-w-none
                      prose-headings:text-white prose-headings:font-semibold prose-headings:mt-3 prose-headings:mb-1.5
                      prose-p:text-white/90 prose-p:leading-relaxed prose-p:mb-2 prose-p:last:mb-0
                      prose-a:text-calm-400 prose-a:no-underline hover:prose-a:underline
                      prose-strong:text-white prose-strong:font-semibold
                      prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded-md prose-code:bg-white/10 prose-code:text-calm-300 prose-code:text-xs prose-code:font-mono prose-code:before:content-none prose-code:after:content-none
                      prose-pre:bg-white/5 prose-pre:border prose-pre:border-white/10 prose-pre:rounded-xl prose-pre:p-3
                      prose-li:text-white/90 prose-li:my-0.5
                      prose-ul:my-1.5 prose-ol:my-1.5
                      prose-blockquote:border-l-calm-500 prose-blockquote:text-white/70 prose-blockquote:italic prose-blockquote:pl-3
                      prose-hr:border-white/10
                      [&_ul]:!list-disc [&_ol]:!list-decimal [&_li]:!text-sm
                    ">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                      >
                        {msg.content}
                      </ReactMarkdown>
                    </div>
                    {msg.tasks && msg.tasks.length > 0 && (
                      <div className="mt-2 pt-2 border-t border-white/20 space-y-1">
                        {msg.tasks.map((task, j) => (
                          <div key={j} className="flex items-center gap-2 text-xs">
                            <span>{task.emoji}</span>
                            <span className={msg.role === "user" ? "text-black/80" : "text-white/80"}>{task.text}</span>
                          </div>
                        ))}
                      </div>
                    )}
                    {msg.timestamp && (
                      <p className={`text-[10px] mt-1 ${
                        isCelebratory ? "text-white/60" : isGentle ? "text-white/60" : "text-muted/50"
                      }`}>
                        {new Date(msg.timestamp).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </p>
                    )}
                  </div>
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>

        {isThinking && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex justify-start"
          >
            <div className="bg-surface border border-border rounded-2xl rounded-bl-md p-4">
              <motion.div
                className="flex items-center gap-2"
                animate={{ opacity: [1, 0.5, 1] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              >
                <span className="text-lg">🧠</span>
                {[0, 150, 300].map((delay) => (
                  <motion.div
                    key={delay}
                    className="w-2 h-2 rounded-full bg-calm-500"
                    animate={{ y: [0, -6, 0] }}
                    transition={{ duration: 0.6, repeat: Infinity, delay: delay / 1000 }}
                  />
                ))}
              </motion.div>
            </div>
          </motion.div>
        )}

        {error && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center">
            <p className="text-sm text-danger-500 bg-danger-500/10 rounded-lg p-3 inline-block">
              {error}
            </p>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-border p-4">
        <div className="flex items-end gap-2">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              overwhelmMode
                ? "Start with something tiny... even one word 🌱"
                : "Tell me what's on your mind..."
            }
            rows={1}
            className="flex-1 resize-none px-4 py-3 rounded-2xl bg-surface border border-border text-foreground placeholder:text-muted/50 focus:outline-none focus:ring-2 focus:ring-calm-500/50 focus:border-calm-500/50 transition-all text-sm max-h-[150px]"
          />
          <Button
            onClick={handleSend}
            disabled={!input.trim() || isThinking}
            className={`rounded-2xl px-5 transition-all ${
              overwhelmMode ? "bg-danger-500/30 hover:bg-danger-500/40" : ""
            }`}
          >
            {overwhelmMode ? "🌿 Send" : "Send"}
          </Button>
        </div>
        <p className="text-[10px] text-muted/40 mt-1.5 text-center">
          {overwhelmMode
            ? "Gentle mode — take your time"
            : `Your ADHD-aware coach with behavioral memory · ${todaySessionCount} sessions`}
        </p>
      </div>
    </div>
  );
}
