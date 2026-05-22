"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Card, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Celebration } from "@/components/shared/celebration";
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

const feedbackCategories = [
  { id: "coach", label: "Coach Effectiveness", emoji: "🤖" },
  { id: "app", label: "App Performance", emoji: "⚡" },
  { id: "features", label: "Feature Requests", emoji: "✨" },
  { id: "other", label: "General Thoughts", emoji: "💭" },
];

const satisfactionRatings = [
  { value: 1, emoji: "😠", label: "Frustrating" },
  { value: 2, emoji: "😐", label: "Could be Better" },
  { value: 3, emoji: "🙂", label: "Satisfactory" },
  { value: 4, emoji: "😌", label: "Super Helpful" },
  { value: 5, emoji: "🤩", label: "Life Changing!" },
];

export default function FeedbackPage() {
  const { username, addPoints } = useUserStore();
  const [category, setCategory] = useState("coach");
  const [rating, setRating] = useState(4);
  const [feedbackText, setFeedbackText] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showCelebration, setShowCelebration] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");
  const [xpAwarded, setXpAwarded] = useState(0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username) return;

    setIsSubmitting(true);
    try {
      const response = await api.submitFeedback(
        username,
        rating,
        category,
        feedbackText
      );

      if (response.success) {
        // Award XP on local Zustand store
        addPoints(15);
        setXpAwarded(15);
        setSuccessMessage("Thank you for your voice! Your thoughts directly build this ecosystem.");
        setShowCelebration(true);
        setFeedbackText("");
        setRating(4);
        setTimeout(() => setShowCelebration(false), 3000);
      }
    } catch (err) {
      console.error("Feedback error:", err);
      // Fallback local gamification if server fails to ensure a shame-free experience
      addPoints(15);
      setXpAwarded(15);
      setSuccessMessage("Offline mode: Thank you for your feedback! 💫");
      setShowCelebration(true);
      setFeedbackText("");
      setTimeout(() => setShowCelebration(false), 3000);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="max-w-3xl mx-auto p-6 space-y-6"
    >
      <Celebration type="confetti" show={showCelebration} onComplete={() => setShowCelebration(false)} />

      {/* Header */}
      <motion.div variants={itemVariants}>
        <h1 className="text-3xl font-bold text-foreground">📣 Gamified Feedback</h1>
        <p className="text-muted mt-1">Help shape your adaptive ADHD coach while earning points</p>
      </motion.div>

      {/* Dopamine Alert Box */}
      <motion.div variants={itemVariants}>
        <div className="bg-gradient-to-r from-calm-500/20 via-purple-500/10 to-transparent border border-calm-500/30 rounded-2xl p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">⚡</span>
            <div>
              <p className="text-sm font-semibold text-calm-400">Dopamine Reward Active</p>
              <p className="text-xs text-muted">Complete this quick check-in feedback to boost your momentum & unlock +15 XP instantly!</p>
            </div>
          </div>
          <Badge variant="purple" className="px-3 py-1 font-mono">+15 XP</Badge>
        </div>
      </motion.div>

      {/* Feedback Card */}
      <motion.div variants={itemVariants}>
        <Card className="glass-strong">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Category Select */}
            <div>
              <CardTitle className="text-base font-semibold">1. What area is your feedback about?</CardTitle>
              <CardDescription className="mt-1">Pick a topic to route your advice</CardDescription>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5 mt-3">
                {feedbackCategories.map((cat) => (
                  <button
                    key={cat.id}
                    type="button"
                    onClick={() => setCategory(cat.id)}
                    className={`flex flex-col items-center justify-center p-3.5 rounded-xl border text-center transition-all min-touch-target ${
                      category === cat.id
                        ? "bg-calm-500/10 border-calm-500/50 text-calm-400 ring-2 ring-calm-500/25"
                        : "bg-surface border-border hover:border-calm-500/20 text-muted hover:text-foreground"
                    }`}
                  >
                    <span className="text-2xl mb-1">{cat.emoji}</span>
                    <span className="text-xs font-medium">{cat.label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Satisfaction Rating Slider/Buttons */}
            <div>
              <CardTitle className="text-base font-semibold">2. Rate your experience</CardTitle>
              <CardDescription className="mt-1">How supportive has the coach felt in this area?</CardDescription>
              
              <div className="grid grid-cols-5 gap-2 mt-4">
                {satisfactionRatings.map((sat) => {
                  const isSelected = rating === sat.value;
                  return (
                    <button
                      key={sat.value}
                      type="button"
                      onClick={() => setRating(sat.value)}
                      className={`flex flex-col items-center justify-center p-3 rounded-xl transition-all border min-touch-target ${
                        isSelected
                          ? "bg-calm-500/20 border-calm-500/60 scale-105 shadow-lg shadow-calm-500/10"
                          : "bg-surface border-border opacity-70 hover:opacity-100 hover:border-calm-500/10"
                      }`}
                    >
                      <motion.span 
                        animate={isSelected ? { scale: [1, 1.2, 1] } : {}}
                        className="text-3xl block"
                      >
                        {sat.emoji}
                      </motion.span>
                      <span className="text-[10px] text-muted text-center mt-1.5 font-medium hidden md:block">
                        {sat.label}
                      </span>
                    </button>
                  );
                })}
              </div>

              {/* Dynamic feedback indicator description */}
              <div className="mt-3 text-center">
                <span className="text-xs font-semibold text-calm-400">
                  {satisfactionRatings.find(r => r.value === rating)?.label}
                </span>
              </div>
            </div>

            {/* Textarea */}
            <div>
              <CardTitle className="text-base font-semibold">3. Share your thoughts (ADHD-friendly check-in)</CardTitle>
              <CardDescription className="mt-1">
                Zero pressure. Write a sentence, bullet points, or paragraphs — whatever flows easiest for you!
              </CardDescription>
              <div className="mt-3">
                <textarea
                  value={feedbackText}
                  onChange={(e) => setFeedbackText(e.target.value)}
                  placeholder="What's working? What felt exhausting? What features would reward your brain the most? Write anything here..."
                  rows={4}
                  className="w-full px-4 py-3 rounded-xl bg-surface border border-border text-foreground placeholder:text-muted/40 focus:outline-none focus:ring-2 focus:ring-calm-500/50 text-sm resize-none"
                />
              </div>
            </div>

            {/* Submit Button */}
            <div className="flex flex-col md:flex-row items-center justify-between gap-3 pt-2">
              <span className="text-xs text-muted italic">
                💖 All reviews are processed with absolute zero-judgment.
              </span>
              <Button
                type="submit"
                variant="calm"
                className="w-full md:w-auto px-6 py-2.5 font-semibold text-sm transition-all"
                disabled={isSubmitting}
              >
                {isSubmitting ? "Saving Thoughts..." : "Submit & Collect 15 XP 🚀"}
              </Button>
            </div>
          </form>
        </Card>
      </motion.div>

      {/* Success banner */}
      {successMessage && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-calm-500/10 border border-calm-500/20 text-calm-400 p-4 rounded-xl text-center text-sm font-medium"
        >
          {successMessage}
          <div className="mt-1 text-xs text-muted-foreground font-mono">⚡ XP Awarded! Check your level progression in the sidebar.</div>
        </motion.div>
      )}
    </motion.div>
  );
}
