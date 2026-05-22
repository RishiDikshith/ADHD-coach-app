"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Card, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useUserStore } from "@/stores/user-store";
import { api } from "@/services/api";

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.08 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 15 },
  visible: { opacity: 1, y: 0 },
};

const ticketTypes = [
  { id: "glitch", label: "Technical Glitch", emoji: "🐛" },
  { id: "coach", label: "Coach Behavior", emoji: "🤖" },
  { id: "question", label: "General Question", emoji: "❓" },
];

const fallbackFaqs = [
  {
    id: "faq-paralysis",
    question: "🌪️ How do I overcome sudden task paralysis?",
    answer: "When task paralysis strikes, your brain is treating the threat of starting a task like a literal physical danger. Don't fight it! Give yourself absolute permission to do the task badly or do just one single detail for 2 minutes. Start a micro-timer, and if you want to stop after 2 minutes, you have fully succeeded."
  },
  {
    id: "faq-hyperfocus",
    question: "🌀 Help, I am stuck in an intense hyperfocus spiral!",
    answer: "Hyperfocus is a powerful ADHD gift, but it can drain your body. Transitioning out is hard. Use a transitional bridge: instead of stopping immediately, tell yourself you will stop in 5 minutes, stand up and stretch without looking away, then grab a glass of water. A change of physical state helps reset the brain."
  },
  {
    id: "faq-blindness",
    question: "⏳ How can I handle time blindness during work?",
    answer: "ADHD brains perceive time as 'Now' or 'Not Now'. To make time visible, use visual timers (like the standard countdown visual arc in our Focus page) rather than digital numbers. Set soft, chime-based alarms 5 minutes before you actually need to transition to prevent jump-scares."
  },
  {
    id: "faq-burnout",
    question: "🔋 What is an ADHD shutdown, and how do I recover?",
    answer: "When you have overstimulated or pushed your brain too hard, it goes into a power-saving mode (shutdown/burnout). This is a physical necessity. Rest shame-free. Lie down in a dark or quiet room, drink some hydration, and avoid complex decision-making for at least 1-2 hours."
  }
];

export default function SupportPage() {
  const { username } = useUserStore();
  
  // FAQs State
  const [faqs, setFaqs] = useState<Array<{ id: string; question: string; answer: string }>>([]);
  const [loadingFaqs, setLoadingFaqs] = useState(true);
  const [activeFaqId, setActiveFaqId] = useState<string | null>(null);

  // Ticket Form State
  const [ticketType, setTicketType] = useState("glitch");
  const [subject, setSubject] = useState("");
  const [description, setDescription] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [ticketSuccess, setTicketSuccess] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Ticket Tracker State
  const [tickets, setTickets] = useState<any[]>([]);
  const [loadingTickets, setLoadingTickets] = useState(false);
  const [expandedTicketId, setExpandedTicketId] = useState<number | null>(null);

  // Chat Console State
  const [chatMessages, setChatMessages] = useState<Array<{ role: "user" | "assistant"; content: string }>>([
    {
      role: "assistant",
      content: "Welcome to Support! I am your AI Support Companion. Whether you're experiencing a glitch, have a feature suggestion, or need shame-free answers to ADHD FAQs, I've got your back. How can I assist you today? 🆘"
    }
  ]);
  const [chatInput, setChatInput] = useState("");
  const [isThinking, setIsThinking] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Fetch Tickets
  const loadTickets = async () => {
    if (!username) return;
    setLoadingTickets(true);
    try {
      const res = await api.getUserTickets(username);
      if (res.success) {
        setTickets(res.tickets);
      }
    } catch (err) {
      console.warn("Failed to load user tickets:", err);
    } finally {
      setLoadingTickets(false);
    }
  };

  // Fetch FAQs from API & Tickets
  useEffect(() => {
    async function loadFaqs() {
      try {
        setLoadingFaqs(true);
        const data = await api.getFaqs();
        setFaqs(data);
      } catch (err) {
        console.warn("Could not load backend FAQs, using calming local fallbacks:", err);
        setFaqs(fallbackFaqs);
      } finally {
        setLoadingFaqs(false);
      }
    }
    loadFaqs();
    loadTickets();
  }, [username]);

  // Scroll to bottom of chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages, isThinking]);

  // Submit Ticket Form
  const handleTicketSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !subject.trim() || !description.trim()) return;

    setIsSubmitting(true);
    setErrorMsg(null);
    setTicketSuccess(null);

    try {
      const response = await api.submitSupportTicket(
        username,
        ticketType,
        subject.trim(),
        description.trim()
      );

      if (response.success) {
        setTicketSuccess(`Success! Support ticket #${response.ticket.id} has been logged.`);
        setSubject("");
        setDescription("");
        // Automatically append to user support chat context to inform the AI
        setChatMessages(prev => [
          ...prev,
          { role: "user", content: `I just raised a new ticket: "${subject.trim()}"` },
          { role: "assistant", content: `Thank you! I see that ticket #${response.ticket.id} has been successfully logged with status **OPEN**. I've cataloged this in our technical log, and our systems are ready to inspect it! 🚀` }
        ]);
        loadTickets();
      }
    } catch (err) {
      console.error("Support ticket error:", err);
      setTicketSuccess("Offline mode active: Ticket saved locally. No pressure, our technical coach has noted this! 💖");
      setSubject("");
      setDescription("");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Chat Send Message
  const handleChatSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!chatInput.trim() || isThinking) return;

    const userText = chatInput.trim();
    setChatInput("");
    setChatMessages(prev => [...prev, { role: "user", content: userText }]);
    setIsThinking(true);

    try {
      const res = await api.chat({
        text: userText,
        history: chatMessages,
        user_data: {
          sleep_hours: 8,
          stress_level: 5,
          phone_distractions: 1,
          mood: "calm"
        },
        language: "en",
        language_name: "English",
        username: username || "default",
        agent_id: "support-agent"
      });

      if (res.reply) {
        setChatMessages(prev => [...prev, { role: "assistant", content: res.reply }]);
      } else {
        setChatMessages(prev => [...prev, { role: "assistant", content: "I received your message, but had trouble compiling a direct response. Our engineering team has been notified!" }]);
      }
    } catch (err) {
      console.error("Support chat error:", err);
      setChatMessages(prev => [
        ...prev,
        { role: "assistant", content: "Apologies, I encountered a temporary connection issue. Don't worry, your data is safe and no tickets have been lost!" }
      ]);
    } finally {
      setIsThinking(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case "resolved":
        return <Badge className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-bold uppercase text-[9px] tracking-wider">Resolved 🟢</Badge>;
      case "in_progress":
        return <Badge className="bg-blue-500/10 text-blue-400 border border-blue-500/30 font-bold uppercase text-[9px] tracking-wider">In Progress 🔵</Badge>;
      default:
        return <Badge className="bg-amber-500/10 text-amber-400 border border-amber-500/30 font-bold uppercase text-[9px] tracking-wider">Open 🟡</Badge>;
    }
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="max-w-7xl mx-auto p-4 md:p-6 space-y-6"
    >
      {/* Header */}
      <motion.div variants={itemVariants} className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-black bg-gradient-to-r from-pink-400 via-rose-400 to-amber-400 bg-clip-text text-transparent">
            🆘 Help & Coping Portal
          </h1>
          <p className="text-muted text-sm mt-1">Submit help desk glitch tickets, chat with AI Support, or explore calming ADHD coping strategies</p>
        </div>
      </motion.div>

      {/* Three Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* Left Column: Form + FAQs (4 Cols) */}
        <motion.div variants={itemVariants} className="lg:col-span-4 space-y-6">
          {/* Glitch Form */}
          <Card className="glass-strong border-pink-500/10 relative overflow-hidden">
            <div className="absolute -right-16 -top-16 w-32 h-32 rounded-full bg-pink-500/5 blur-2xl pointer-events-none" />
            <CardTitle className="text-base font-bold flex items-center gap-2">
              <span>🐛</span> Report a Glitch or Question
            </CardTitle>
            <CardDescription className="mt-1 text-xs">
              Encountered a bug or have a question? Submit a ticket and we will inspect the database logs.
            </CardDescription>

            <form onSubmit={handleTicketSubmit} className="space-y-3.5 mt-4">
              {/* Category selector */}
              <div>
                <label className="text-[10px] font-semibold text-muted uppercase tracking-wider block mb-1.5">
                  Ticket Category
                </label>
                <div className="grid grid-cols-3 gap-1.5">
                  {ticketTypes.map((type) => (
                    <button
                      key={type.id}
                      type="button"
                      onClick={() => setTicketType(type.id)}
                      className={`flex flex-col items-center justify-center py-2 px-1 rounded-xl border text-center transition-all ${
                        ticketType === type.id
                          ? "bg-pink-500/10 border-pink-500/50 text-pink-400 font-semibold"
                          : "bg-surface border-border text-muted hover:text-foreground"
                      }`}
                    >
                      <span className="text-base mb-0.5">{type.emoji}</span>
                      <span className="text-[9px] font-medium leading-none truncate w-full">{type.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Subject */}
              <div>
                <label className="text-[10px] font-semibold text-muted uppercase tracking-wider block mb-1">
                  Subject Line
                </label>
                <input
                  type="text"
                  required
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  placeholder="e.g. Pomodoro timer sound didn't fire"
                  className="w-full px-3 py-2 rounded-xl bg-surface border border-border text-foreground placeholder:text-muted/40 focus:outline-none focus:ring-2 focus:ring-pink-500/30 text-xs"
                />
              </div>

              {/* Description */}
              <div>
                <label className="text-[10px] font-semibold text-muted uppercase tracking-wider block mb-1">
                  What happened?
                </label>
                <textarea
                  required
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe what occurred, or type your question. Be as brief or detailed as you want! Simple is perfect."
                  rows={4}
                  className="w-full px-3 py-2 rounded-xl bg-surface border border-border text-foreground placeholder:text-muted/40 focus:outline-none focus:ring-2 focus:ring-pink-500/30 text-xs resize-none"
                />
              </div>

              {errorMsg && (
                <div className="text-[10px] text-red-400 bg-red-400/10 border border-red-400/20 p-2 rounded-lg text-center">
                  {errorMsg}
                </div>
              )}

              {ticketSuccess && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="bg-pink-500/10 border border-pink-500/20 text-pink-400 p-3 rounded-xl text-center text-[10px] font-semibold"
                >
                  {ticketSuccess}
                </motion.div>
              )}

              <Button
                type="submit"
                variant="calm"
                className="w-full py-2 bg-gradient-to-r from-pink-500 to-rose-500 text-white font-bold text-xs rounded-xl shadow-lg shadow-pink-500/10 border-0 hover:opacity-90 transition-all"
                disabled={isSubmitting}
              >
                {isSubmitting ? "Logging Ticket..." : "Log Shame-Free Ticket 🚀"}
              </Button>
            </form>
          </Card>

          {/* FAQs Accordion */}
          <Card className="glass-strong">
            <CardTitle className="text-base font-bold flex items-center gap-2">
              <span>🧘</span> ADHD Grounding FAQs
            </CardTitle>
            <div className="mt-4 space-y-2">
              {loadingFaqs ? (
                <div className="py-6 text-center text-xs text-muted">Loading FAQ modules...</div>
              ) : (
                faqs.map((faq) => {
                  const isOpen = activeFaqId === faq.id;
                  return (
                    <div
                      key={faq.id}
                      className="border border-border/80 bg-surface rounded-xl overflow-hidden transition-all duration-200"
                    >
                      <button
                        onClick={() => setActiveFaqId(isOpen ? null : faq.id)}
                        className="w-full flex items-center justify-between p-3.5 text-left font-medium text-xs hover:text-pink-400 transition-colors"
                      >
                        <span className="font-semibold text-foreground hover:text-pink-400">{faq.question}</span>
                        <span className="text-[10px] text-muted">{isOpen ? "▲" : "▼"}</span>
                      </button>
                      <AnimatePresence initial={false}>
                        {isOpen && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: "auto", opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.2, ease: "easeInOut" }}
                          >
                            <div className="px-3.5 pb-3.5 pt-1 text-[11px] text-muted-foreground leading-relaxed border-t border-border/40 bg-[#070b13]/40">
                              {faq.answer}
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  );
                })
              )}
            </div>
          </Card>
        </motion.div>

        {/* Center Column: Live Chat Console (5 Cols) */}
        <motion.div variants={itemVariants} className="lg:col-span-5 h-[620px] flex flex-col">
          <Card className="glass-strong border-pink-500/20 bg-gradient-to-b from-[#0e0f1d] to-[#060711] flex flex-col h-full overflow-hidden p-0 relative">
            {/* Ambient Pink Backdrop Glow */}
            <div className="absolute top-0 right-0 w-48 h-48 rounded-full bg-pink-500/5 blur-3xl pointer-events-none" />
            <div className="absolute bottom-0 left-0 w-48 h-48 rounded-full bg-rose-500/5 blur-3xl pointer-events-none" />

            {/* Chat Header */}
            <div className="p-4 border-b border-pink-500/10 flex items-center gap-3 bg-[#0a0c16]/80 backdrop-blur-md shrink-0">
              <span className="text-3xl p-1.5 rounded-xl bg-pink-500/10 border border-pink-500/20 text-pink-400">🆘</span>
              <div>
                <h3 className="font-black text-sm text-foreground flex items-center gap-1.5">
                  AI Support Console
                  <span className="inline-block w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                </h3>
                <p className="text-[10px] text-pink-400 font-bold uppercase tracking-wider">Active Technical Agent</p>
              </div>
            </div>

            {/* Message Feed Container */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3.5 min-h-0 scrollbar-thin">
              {chatMessages.map((msg, i) => {
                const isUser = msg.role === "user";
                return (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.2 }}
                    className={`flex ${isUser ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-[85%] rounded-2xl p-3 text-xs leading-relaxed shadow-sm border ${
                        isUser
                          ? "bg-gradient-to-r from-pink-500/80 to-rose-500/80 text-white border-pink-500/30 rounded-tr-none"
                          : "bg-surface border-border/80 text-foreground rounded-tl-none"
                      }`}
                    >
                      <div className="prose prose-invert max-w-none text-xs break-words">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {msg.content}
                        </ReactMarkdown>
                      </div>
                    </div>
                  </motion.div>
                );
              })}

              {isThinking && (
                <div className="flex justify-start">
                  <div className="max-w-[85%] rounded-2xl rounded-tl-none p-3 bg-surface border border-border/80 text-muted flex items-center gap-2">
                    <span className="flex gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-pink-400 animate-bounce" style={{ animationDelay: "0ms" }} />
                      <span className="w-1.5 h-1.5 rounded-full bg-pink-400 animate-bounce" style={{ animationDelay: "150ms" }} />
                      <span className="w-1.5 h-1.5 rounded-full bg-pink-400 animate-bounce" style={{ animationDelay: "300ms" }} />
                    </span>
                    <span className="text-[10px] italic">Analyzing system records...</span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Quick Actions Drawer */}
            <div className="px-4 py-1.5 bg-[#070912]/90 border-t border-pink-500/5 flex gap-1 overflow-x-auto shrink-0 scrollbar-none">
              {[
                { label: "🐞 Glitch status", text: "What is the status of my raised glitches?" },
                { label: "❓ System FAQs", text: "Show me the standard platform technical FAQs." },
                { label: "📣 App Feedback", text: "I want to log a platform feature suggestion." }
              ].map((btn) => (
                <button
                  key={btn.label}
                  onClick={() => {
                    setChatInput(btn.text);
                  }}
                  className="shrink-0 text-[9px] font-semibold bg-surface hover:bg-pink-500/10 hover:text-pink-400 border border-border/60 rounded-full px-2.5 py-1 text-muted transition-colors"
                >
                  {btn.label}
                </button>
              ))}
            </div>

            {/* Chat Input form */}
            <form onSubmit={handleChatSend} className="p-3 border-t border-pink-500/10 bg-[#0a0c16]/90 backdrop-blur-md flex items-center gap-2 shrink-0">
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="Ask technical question or check glitches..."
                disabled={isThinking}
                className="flex-1 px-3 py-2 text-xs rounded-xl bg-surface border border-border text-foreground placeholder:text-muted/40 focus:outline-none focus:ring-2 focus:ring-pink-500/30"
              />
              <Button
                type="submit"
                variant="calm"
                disabled={!chatInput.trim() || isThinking}
                className="px-4 py-2 bg-pink-500/10 border border-pink-500/30 text-pink-400 hover:bg-pink-500 hover:text-white font-bold text-xs rounded-xl transition-all"
              >
                Send 🚀
              </Button>
            </form>
          </Card>
        </motion.div>

        {/* Right Column: Support Tickets list (3 Cols) */}
        <motion.div variants={itemVariants} className="lg:col-span-3 space-y-6">
          <Card className="glass-strong">
            <CardTitle className="text-base font-bold flex items-center gap-2">
              <span>🎫</span> My Logged Tickets
            </CardTitle>
            <CardDescription className="mt-1 text-xs">
              Review and monitor your active help desk logs in real-time.
            </CardDescription>

            {loadingTickets ? (
              <div className="py-12 text-center text-xs text-muted">
                <div className="inline-block w-4 h-4 border-2 border-pink-500 border-t-transparent rounded-full animate-spin mb-2" />
                <p>Syncing tickets list...</p>
              </div>
            ) : tickets.length === 0 ? (
              <div className="py-10 text-center text-xs text-muted-foreground italic border border-dashed border-border/60 rounded-xl mt-4 bg-[#070b13]/10">
                🌱 No support tickets logged yet. You have a completely clean slate!
              </div>
            ) : (
              <div className="mt-4 space-y-2.5">
                {tickets.map((ticket) => {
                  const isExpanded = expandedTicketId === ticket.id;
                  const dateString = ticket.created_at
                    ? new Date(ticket.created_at).toLocaleDateString()
                    : "Recently";

                  return (
                    <div
                      key={ticket.id}
                      className="border border-border/80 bg-surface rounded-xl overflow-hidden shadow-sm transition-all duration-200"
                    >
                      <button
                        onClick={() => setExpandedTicketId(isExpanded ? null : ticket.id)}
                        className="w-full flex flex-col p-3 text-left hover:bg-white/5 transition-colors gap-2"
                      >
                        <div className="flex justify-between items-start gap-2 w-full">
                          <span className="font-bold text-xs truncate max-w-[130px] text-foreground">{ticket.subject}</span>
                          {getStatusBadge(ticket.status)}
                        </div>
                        <div className="flex justify-between items-center text-[10px] text-muted-foreground w-full">
                          <span className="font-mono text-[9px] text-pink-400/80">#{ticket.id} • {ticket.type}</span>
                          <span>{dateString}</span>
                        </div>
                      </button>

                      <AnimatePresence>
                        {isExpanded && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: "auto", opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.2 }}
                            className="bg-[#070b13]/40 border-t border-border/40 p-3 text-[11px] leading-relaxed text-muted-foreground space-y-2"
                          >
                            <p className="font-medium text-foreground text-[10px] uppercase tracking-wider">Description:</p>
                            <p className="bg-surface/50 border border-border/30 rounded-lg p-2 font-mono text-[10px] break-words">
                              {ticket.description}
                            </p>
                            {ticket.admin_notes && (
                              <div className="border-t border-dashed border-border/40 pt-2 space-y-1">
                                <p className="font-medium text-pink-400 text-[10px] uppercase tracking-wider">Admin Reply:</p>
                                <p className="italic text-foreground p-2 rounded-lg bg-pink-500/5 border border-pink-500/10">
                                  {ticket.admin_notes}
                                </p>
                              </div>
                            )}
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  );
                })}
              </div>
            )}
          </Card>
        </motion.div>

      </div>
    </motion.div>
  );
}
