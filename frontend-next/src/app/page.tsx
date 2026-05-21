"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";

const features = [
  { icon: "🤖", title: "7 AI Agents", desc: "Specialized ADHD agents — Productivity Coach, Task Breakdown, Focus Optimization, Mood & Burnout, Habit Builder, Intervention, Accountability" },
  { icon: "🧠", title: "Behavioral Memory", desc: "Remembers your patterns, triggers, focus hours, and what interventions work best for you" },
  { icon: "🎯", title: "Task Paralysis Recovery", desc: "AI-generated microtasks, Just Begin mode, overwhelm detection, and 2-minute starter tasks" },
  { icon: "🌙", title: "Time Blindness Helper", desc: "Visual day progress bar, time-of-day awareness, and gentle reminders" },
  { icon: "📊", title: "Behavioral Analytics", desc: "Focus patterns, mood correlations, sleep/productivity analysis, actionable insights" },
  { icon: "🎮", title: "Gamification", desc: "Points, levels, streaks, badges, and dopamine-friendly celebration effects" },
  { icon: "💬", title: "Emotionally Intelligent Chat", desc: "ADHD-aware conversational AI that adapts to your emotional state and energy level" },
  { icon: "⏱️", title: "Focus Mode", desc: "Full-screen immersive Pomodoro with ambient visuals, session tracking, and break reminders" },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-background via-[#0a1628] to-background flex flex-col">
      {/* Animated background */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-40 -left-40 w-80 h-80 rounded-full bg-calm-500/5 blur-3xl animate-float" />
        <div className="absolute -bottom-40 -right-40 w-96 h-96 rounded-full bg-focus-500/5 blur-3xl animate-float" style={{ animationDelay: "-2s" }} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-gradient-to-br from-calm-500/3 to-focus-500/3 blur-3xl animate-glow" />
      </div>

      {/* Nav */}
      <header className="relative z-10 flex items-center justify-between p-4 md:p-6 max-w-6xl mx-auto w-full">
        <h1 className="text-xl font-bold gradient-text">🧠 ADHD Coach</h1>
        <div className="flex items-center gap-3">
          <Link href="/login">
            <Button variant="ghost" size="sm">Sign In</Button>
          </Link>
          <Link href="/register">
            <Button size="sm">Get Started</Button>
          </Link>
        </div>
      </header>

      {/* Hero */}
      <main className="relative z-10 flex-1 flex flex-col items-center justify-center px-6 text-center">
        <div className="max-w-3xl animate-fade-in-up">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass text-sm text-calm-400 mb-6">
            <span className="w-2 h-2 rounded-full bg-calm-500 animate-pulse-soft" />
            ADHD-native AI · Free & Open Source
          </div>

          <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold mb-6 leading-tight">
            Your{" "}
            <span className="gradient-text">ADHD</span>
            <br />
            Executive Function Ecosystem
          </h1>

          <p className="text-lg md:text-xl text-muted mb-8 max-w-2xl mx-auto leading-relaxed">
            An emotionally intelligent AI coach that understands your ADHD brain.
            Personalized support for focus, task paralysis, burnout prevention,
            and building habits that actually stick.
          </p>

          <div className="flex items-center justify-center gap-4 flex-wrap">
            <Link href="/register">
              <Button size="xl" className="text-lg">
                🧠 Start Free →
              </Button>
            </Link>
            <Link href="/login">
              <Button variant="outline" size="xl" className="text-lg">
                Sign In
              </Button>
            </Link>
          </div>

          <p className="text-xs text-muted-foreground mt-4">
            No credit card required · Free forever · Open source
          </p>
        </div>

        {/* Features Grid */}
        <div className="mt-20 max-w-5xl w-full animate-fade-in-up" style={{ animationDelay: "0.2s" }}>
          <h2 className="text-2xl font-bold text-foreground mb-8 text-center">
            Built specifically for the{" "}
            <span className="gradient-text">ADHD brain</span>
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {features.map((f) => (
              <div
                key={f.title}
                className="p-5 rounded-2xl glass hover:border-calm-500/30 transition-all duration-300 text-left group"
              >
                <div className="text-2xl mb-3 group-hover:animate-bounce-in">{f.icon}</div>
                <h3 className="font-semibold text-foreground mb-1.5">{f.title}</h3>
                <p className="text-xs text-muted leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* How it works */}
        <div className="mt-20 max-w-4xl w-full animate-fade-in-up" style={{ animationDelay: "0.4s" }}>
          <h2 className="text-2xl font-bold text-foreground mb-8 text-center">How It Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[
              { step: "1", title: "Chat naturally", desc: "Talk to your AI coach about anything — tasks, overwhelm, focus struggles." },
              { step: "2", title: "AI analyzes in real-time", desc: "7 specialized agents analyze your input and detect patterns." },
              { step: "3", title: "Memory stores patterns", desc: "Behavioral memory tracks what works and adapts to you." },
              { step: "4", title: "Personalized support", desc: "Get adaptive coaching, microtasks, and interventions that fit." },
            ].map((s) => (
              <div key={s.step} className="text-center p-6 rounded-xl glass">
                <div className="w-10 h-10 rounded-full bg-calm-500/20 text-calm-400 font-bold flex items-center justify-center mx-auto mb-3 text-lg">
                  {s.step}
                </div>
                <h3 className="font-semibold text-foreground mb-1">{s.title}</h3>
                <p className="text-xs text-muted">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* CTA */}
        <div className="mt-20 mb-20 text-center animate-fade-in-up" style={{ animationDelay: "0.6s" }}>
          <h2 className="text-3xl font-bold text-foreground mb-4">
            Ready to transform your{" "}
            <span className="gradient-text">executive function</span>?
          </h2>
          <p className="text-muted mb-8 max-w-md mx-auto">
            Join thousands of ADHD users who have found their focus companion.
            Free forever, always improving.
          </p>
          <Link href="/register">
            <Button size="xl" className="text-lg">
              🚀 Start Your Journey
            </Button>
          </Link>
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 p-6 text-center text-xs text-muted border-t border-border">
        <p>ADHD AI Coach — Free & Open Source · Built with Next.js + FastAPI</p>
      </footer>
    </div>
  );
}
