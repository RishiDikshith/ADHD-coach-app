"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Card, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useUserStore } from "@/stores/user-store";
import { api } from "@/lib/api-client";
import Link from "next/link";

interface Ticket {
  id: number;
  username: string;
  type: string;
  subject: string;
  description: string;
  status: "open" | "in_progress" | "resolved" | string;
  created_at: string;
}

interface Feedback {
  id: number;
  username: string;
  rating: number;
  category: string;
  feedback_text: string;
  created_at: string;
}

const containerVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.05 } },
};

const itemVariants = {
  hidden: { opacity: 0, y: 15 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.3 } },
};

export default function AdminDashboardPage() {
  const { role } = useUserStore();
  const [mounted, setMounted] = useState(false);
  const [activeTab, setActiveTab] = useState<"tickets" | "feedbacks">("tickets");
  
  // Data States
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [feedbacks, setFeedbacks] = useState<Feedback[]>([]);
  const [loading, setLoading] = useState(true);
  const [updatingTicketId, setUpdatingTicketId] = useState<number | null>(null);
  const [ticketFilter, setTicketFilter] = useState<"all" | "open" | "in_progress" | "resolved">("all");
  const [feedbackFilter, setFeedbackFilter] = useState<number | "all">("all");

  // Prevent hydration mismatch
  useEffect(() => {
    setMounted(true);
  }, []);

  // Fetch data
  const fetchData = async () => {
    if (role !== "admin") return;
    setLoading(true);
    try {
      const [ticketsRes, feedbacksRes] = await Promise.all([
        api.getAdminTickets(),
        api.getAdminFeedbacks(),
      ]);
      if (ticketsRes.success) setTickets(ticketsRes.tickets);
      if (feedbacksRes.success) setFeedbacks(feedbacksRes.feedbacks);
    } catch (err) {
      console.error("Failed to load admin data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (mounted && role === "admin") {
      fetchData();
    }
  }, [mounted, role]);

  const handleUpdateStatus = async (ticketId: number, newStatus: string) => {
    setUpdatingTicketId(ticketId);
    try {
      const res = await api.updateTicketStatus(ticketId, newStatus);
      if (res.success) {
        // Update local state dynamically
        setTickets((prev) =>
          prev.map((t) => (t.id === ticketId ? { ...t, status: newStatus } : t))
        );
      }
    } catch (err) {
      console.error("Failed to update status:", err);
    } finally {
      setUpdatingTicketId(null);
    }
  };

  if (!mounted) {
    return (
      <div className="flex items-center justify-center min-h-[70vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-calm-500" />
      </div>
    );
  }

  // Route Protection: If not admin, show beautiful permission error
  if (role !== "admin") {
    return (
      <div className="max-w-md mx-auto px-6 py-16 text-center">
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: "spring", stiffness: 200 }}
        >
          <Card variant="glass" className="border-danger-500/20 p-8">
            <span className="text-6xl block mb-4">🛡️</span>
            <CardTitle className="text-2xl font-bold text-foreground mb-2">Access Denied</CardTitle>
            <CardDescription className="text-muted-foreground mb-6">
              Shame-free boundary here! Only ADHD Coach administrators can view this dashboard. Let's redirect you back to safety.
            </CardDescription>
            <Link href="/dashboard">
              <Button variant="primary" className="w-full">
                Return to Dashboard
              </Button>
            </Link>
          </Card>
        </motion.div>
      </div>
    );
  }

  // Filter logics
  const filteredTickets = tickets.filter((t) => {
    if (ticketFilter === "all") return true;
    return t.status === ticketFilter;
  });

  const filteredFeedbacks = feedbacks.filter((f) => {
    if (feedbackFilter === "all") return true;
    return f.rating === feedbackFilter;
  });

  // Analytics helper variables
  const openCount = tickets.filter((t) => t.status === "open").length;
  const inProgressCount = tickets.filter((t) => t.status === "in_progress").length;
  const resolvedCount = tickets.filter((t) => t.status === "resolved").length;
  
  const avgRating =
    feedbacks.length > 0
      ? (feedbacks.reduce((sum, f) => sum + f.rating, 0) / feedbacks.length).toFixed(1)
      : "0.0";

  const renderStars = (rating: number) => {
    return Array.from({ length: 5 }).map((_, i) => (
      <span
        key={i}
        className={`text-lg ${i < rating ? "text-amber-400" : "text-border"}`}
      >
        ★
      </span>
    ));
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "open":
        return "bg-amber-500/15 border-amber-500/30 text-amber-400";
      case "in_progress":
        return "bg-sky-500/15 border-sky-500/30 text-sky-400";
      case "resolved":
        return "bg-emerald-500/15 border-emerald-500/30 text-emerald-400";
      default:
        return "bg-zinc-500/15 border-zinc-500/30 text-zinc-400";
    }
  };

  const getTicketTypeEmoji = (type: string) => {
    switch (type) {
      case "glitch":
        return "🐛";
      case "question":
        return "❓";
      case "suggestion":
        return "📣";
      default:
        return "🎫";
    }
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="p-4 md:p-6 space-y-6 max-w-6xl mx-auto"
    >
      {/* Title Header */}
      <motion.div variants={itemVariants} className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-foreground tracking-tight flex items-center gap-2">
            <span>🛡️</span> Admin Dashboard
          </h1>
          <p className="text-muted mt-1">
            Review user feedback, manage support tickets, and keep the coach app running flawlessly.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchData} loading={loading} className="self-start md:self-auto">
          🔄 Refresh Data
        </Button>
      </motion.div>

      {/* Tabs Controller */}
      <motion.div variants={itemVariants} className="flex border-b border-border">
        <button
          onClick={() => setActiveTab("tickets")}
          className={`px-6 py-3 font-semibold transition-all relative ${
            activeTab === "tickets" ? "text-calm-400" : "text-muted hover:text-foreground"
          }`}
        >
          Support Tickets 🎫
          {activeTab === "tickets" && (
            <motion.div
              layoutId="activeTabUnderline"
              className="absolute bottom-0 left-0 right-0 h-0.5 bg-calm-400"
            />
          )}
        </button>
        <button
          onClick={() => setActiveTab("feedbacks")}
          className={`px-6 py-3 font-semibold transition-all relative ${
            activeTab === "feedbacks" ? "text-calm-400" : "text-muted hover:text-foreground"
          }`}
        >
          User Feedbacks 📣
          {activeTab === "feedbacks" && (
            <motion.div
              layoutId="activeTabUnderline"
              className="absolute bottom-0 left-0 right-0 h-0.5 bg-calm-400"
            />
          )}
        </button>
      </motion.div>

      <AnimatePresence mode="wait">
        {activeTab === "tickets" ? (
          <motion.div
            key="tickets-tab"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-6"
          >
            {/* Tickets Analytics Row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card variant="glass" hover={false} className="text-center p-4">
                <span className="text-xs uppercase tracking-wider text-muted font-bold block mb-1">Total Tickets</span>
                <span className="text-3xl font-extrabold text-foreground">{tickets.length}</span>
              </Card>
              <Card variant="glass" hover={false} className="text-center p-4">
                <span className="text-xs uppercase tracking-wider text-muted font-bold block mb-1">Open 🟡</span>
                <span className="text-3xl font-extrabold text-amber-400">{openCount}</span>
              </Card>
              <Card variant="glass" hover={false} className="text-center p-4">
                <span className="text-xs uppercase tracking-wider text-muted font-bold block mb-1">In Progress 🔵</span>
                <span className="text-3xl font-extrabold text-sky-400">{inProgressCount}</span>
              </Card>
              <Card variant="glass" hover={false} className="text-center p-4">
                <span className="text-xs uppercase tracking-wider text-muted font-bold block mb-1">Resolved 🟢</span>
                <span className="text-3xl font-extrabold text-emerald-400">{resolvedCount}</span>
              </Card>
            </div>

            {/* Filter controls */}
            <div className="flex flex-wrap gap-2 items-center">
              <span className="text-sm font-semibold text-muted mr-2">Filter by Status:</span>
              {(["all", "open", "in_progress", "resolved"] as const).map((filter) => (
                <button
                  key={filter}
                  onClick={() => setTicketFilter(filter)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold capitalize border transition-all ${
                    ticketFilter === filter
                      ? "bg-calm-900/30 text-calm-300 border-calm-500/50"
                      : "bg-surface text-muted border-border hover:bg-border/30"
                  }`}
                >
                  {filter.replace("_", " ")}
                </button>
              ))}
            </div>

            {/* Tickets Main Content Grid */}
            {loading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="shimmer h-32 rounded-xl" />
                ))}
              </div>
            ) : filteredTickets.length === 0 ? (
              <Card variant="glass" className="p-8 text-center border-dashed border-border">
                <span className="text-4xl block mb-2">🥳</span>
                <p className="font-semibold text-foreground">All clear!</p>
                <p className="text-muted text-sm mt-1">No support tickets found matching this status.</p>
              </Card>
            ) : (
              <div className="space-y-4">
                {filteredTickets.map((ticket) => (
                  <motion.div
                    key={ticket.id}
                    layout
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                  >
                    <Card variant="glass" className="relative hover:border-calm-500/20">
                      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                        <div className="space-y-2 flex-1">
                          <div className="flex flex-wrap items-center gap-2">
                            {/* Type badge */}
                            <span className="px-2 py-0.5 rounded text-xs font-bold bg-border/40 text-foreground flex items-center gap-1">
                              <span>{getTicketTypeEmoji(ticket.type)}</span>
                              <span className="uppercase text-[10px] tracking-wide">{ticket.type}</span>
                            </span>
                            {/* Status badge */}
                            <span className={`px-2 py-0.5 rounded border text-[10px] uppercase tracking-wider font-bold ${getStatusColor(ticket.status)}`}>
                              {ticket.status.replace("_", " ")}
                            </span>
                            <span className="text-xs text-muted-foreground ml-2">
                              Ticket #{ticket.id}
                            </span>
                          </div>

                          <h2 className="text-lg font-bold text-foreground leading-tight">
                            {ticket.subject}
                          </h2>
                          
                          <p className="text-sm text-foreground/80 leading-relaxed max-w-3xl whitespace-pre-wrap">
                            {ticket.description}
                          </p>

                          <div className="flex items-center gap-4 text-xs text-muted mt-4 pt-2 border-t border-border/40">
                            <div>User: <span className="font-semibold text-foreground">{ticket.username}</span></div>
                            <div>•</div>
                            <div>Submitted: <span className="font-semibold">{new Date(ticket.created_at).toLocaleDateString()}</span></div>
                          </div>
                        </div>

                        {/* Status update buttons */}
                        <div className="flex flex-row md:flex-col gap-2 items-center self-start justify-end w-full md:w-auto border-t md:border-t-0 pt-3 md:pt-0 border-border/40">
                          <span className="text-[10px] uppercase font-bold tracking-wider text-muted hidden md:inline block mb-1">
                            Set Status
                          </span>
                          <div className="flex md:flex-col gap-1.5 w-full">
                            <Button
                              variant="glass"
                              size="xs"
                              disabled={ticket.status === "open" || updatingTicketId === ticket.id}
                              onClick={() => handleUpdateStatus(ticket.id, "open")}
                              className="flex-1 text-amber-500 hover:text-amber-400 hover:bg-amber-500/10 border border-amber-500/20"
                            >
                              Open 🟡
                            </Button>
                            <Button
                              variant="glass"
                              size="xs"
                              disabled={ticket.status === "in_progress" || updatingTicketId === ticket.id}
                              onClick={() => handleUpdateStatus(ticket.id, "in_progress")}
                              className="flex-1 text-sky-500 hover:text-sky-400 hover:bg-sky-500/10 border border-sky-500/20"
                            >
                              In Progress 🔵
                            </Button>
                            <Button
                              variant="glass"
                              size="xs"
                              disabled={ticket.status === "resolved" || updatingTicketId === ticket.id}
                              onClick={() => handleUpdateStatus(ticket.id, "resolved")}
                              className="flex-1 text-emerald-500 hover:text-emerald-400 hover:bg-emerald-500/10 border border-emerald-500/20"
                            >
                              Resolved 🟢
                            </Button>
                          </div>
                        </div>
                      </div>
                    </Card>
                  </motion.div>
                ))}
              </div>
            )}
          </motion.div>
        ) : (
          <motion.div
            key="feedbacks-tab"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-6"
          >
            {/* Feedbacks Analytics Row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card variant="glass" hover={false} className="text-center p-4">
                <span className="text-xs uppercase tracking-wider text-muted font-bold block mb-1">Total Feedbacks</span>
                <span className="text-3xl font-extrabold text-foreground">{feedbacks.length}</span>
              </Card>
              <Card variant="glass" hover={false} className="text-center p-4">
                <span className="text-xs uppercase tracking-wider text-muted font-bold block mb-1">Average Rating</span>
                <span className="text-3xl font-extrabold text-amber-400 flex items-center justify-center gap-1.5">
                  ⭐ {avgRating}
                </span>
              </Card>
              <Card variant="glass" hover={false} className="text-center p-4">
                <span className="text-xs uppercase tracking-wider text-muted font-bold block mb-1">Dopamine Awarded</span>
                <span className="text-3xl font-extrabold text-pink-400">100% Shame-Free</span>
              </Card>
            </div>

            {/* Filter controls */}
            <div className="flex flex-wrap gap-2 items-center">
              <span className="text-sm font-semibold text-muted mr-2">Filter by Stars:</span>
              <button
                onClick={() => setFeedbackFilter("all")}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold capitalize border transition-all ${
                  feedbackFilter === "all"
                    ? "bg-calm-900/30 text-calm-300 border-calm-500/50"
                    : "bg-surface text-muted border-border hover:bg-border/30"
                }`}
              >
                All Ratings
              </button>
              {([5, 4, 3, 2, 1] as const).map((stars) => (
                <button
                  key={stars}
                  onClick={() => setFeedbackFilter(stars)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold capitalize border transition-all flex items-center gap-1 ${
                    feedbackFilter === stars
                      ? "bg-calm-900/30 text-calm-300 border-calm-500/50"
                      : "bg-surface text-muted border-border hover:bg-border/30"
                  }`}
                >
                  {stars} ★
                </button>
              ))}
            </div>

            {/* Feedbacks Main Content Grid */}
            {loading ? (
              <div className="space-y-3">
                {[1, 2].map((i) => (
                  <div key={i} className="shimmer h-24 rounded-xl" />
                ))}
              </div>
            ) : filteredFeedbacks.length === 0 ? (
              <Card variant="glass" className="p-8 text-center border-dashed border-border">
                <span className="text-4xl block mb-2">🌸</span>
                <p className="font-semibold text-foreground">No feedbacks found</p>
                <p className="text-muted text-sm mt-1">No feedback logs match this criteria yet.</p>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {filteredFeedbacks.map((fb) => (
                  <motion.div
                    key={fb.id}
                    layout
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                  >
                    <Card variant="glass" className="h-full hover:border-calm-500/20 flex flex-col justify-between p-5 space-y-4">
                      <div className="space-y-3">
                        <div className="flex items-center justify-between gap-2">
                          <div className="flex items-center gap-1.5">
                            {renderStars(fb.rating)}
                          </div>
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-pink-500/10 border border-pink-500/25 text-pink-400 uppercase tracking-wider">
                            {fb.category || "General"}
                          </span>
                        </div>
                        
                        <p className="text-sm text-foreground/95 leading-relaxed italic">
                          &ldquo;{fb.feedback_text}&rdquo;
                        </p>
                      </div>

                      <div className="flex items-center justify-between text-xs text-muted pt-3 border-t border-border/40">
                        <div>User: <span className="font-semibold text-foreground">{fb.username}</span></div>
                        <div>{new Date(fb.created_at).toLocaleDateString()}</div>
                      </div>
                    </Card>
                  </motion.div>
                ))}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
