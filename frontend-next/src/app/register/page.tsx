"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardTitle } from "@/components/ui/card";
import { useUserStore } from "@/stores/user-store";
import { api } from "@/services/api";

const registerSchema = z
  .object({
    username: z
      .string()
      .min(3, "Username must be at least 3 characters")
      .max(20, "Username must be at most 20 characters")
      .regex(/^[a-zA-Z0-9_]+$/, "Username can only contain letters, numbers, and underscores"),
    password: z.string().min(8, "Password must be at least 8 characters"),
    confirmPassword: z.string().min(1, "Please confirm your password"),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords must match",
    path: ["confirmPassword"],
  });

type RegisterForm = z.infer<typeof registerSchema>;

// ==================== ADHD Onboarding Steps ====================

type OnboardingData = {
  focusStyle: string;
  energyPattern: string;
  productivityStyle: string;
  overwhelmTriggers: string[];
  emotionalPreferences: string;
};

const FOCUS_STYLES = [
  { id: "deep", emoji: "🧘", label: "Deep Focus", desc: "I prefer long, uninterrupted focus sessions" },
  { id: "sprint", emoji: "⚡", label: "Sprint", desc: "Short bursts of intense focus with breaks" },
  { id: "adaptive", emoji: "🔄", label: "Adaptive", desc: "My focus varies — I go with the flow" },
  { id: "guided", emoji: "🎯", label: "Guided", desc: "I work best with structure and prompts" },
];

const ENERGY_PATTERNS = [
  { id: "morning", emoji: "🌅", label: "Morning Peak", desc: "Most energy right after waking" },
  { id: "afternoon", emoji: "☀️", label: "Afternoon Peak", desc: "Hit my stride midday" },
  { id: "night", emoji: "🌙", label: "Night Owl", desc: "Most productive late at night" },
  { id: "scattered", emoji: "🌊", label: "Scattered", desc: "Energy comes in unpredictable waves" },
];

const PRODUCTIVITY_STYLES = [
  { id: "visual", emoji: "👁️", label: "Visual", desc: "Diagrams, mind maps, color coding" },
  { id: "structured", emoji: "📋", label: "Structured", desc: "Lists, checklists, step-by-step" },
  { id: "social", emoji: "🤝", label: "Social", desc: "Body doubling, coworking, pair work" },
  { id: "gamified", emoji: "🎮", label: "Gamified", desc: "Rewards, points, progress tracking" },
  { id: "flexible", emoji: "🌿", label: "Flexible", desc: "I need options and variety to stay engaged" },
];

const OVERWHELM_TRIGGERS = [
  { id: "large_tasks", emoji: "🗻", label: "Large Tasks", desc: "Big projects feel impossible" },
  { id: "decisions", emoji: "⚖️", label: "Decision Overload", desc: "Too many choices paralyze me" },
  { id: "noise", emoji: "🔊", label: "Noise/Sensory", desc: "Loud or chaotic environments" },
  { id: "time_pressure", emoji: "⏰", label: "Time Pressure", desc: "Deadlines make me freeze" },
  { id: "social", emoji: "👥", label: "Social Expectations", desc: "People relying on me" },
  { id: "perfectionism", emoji: "✨", label: "Perfectionism", desc: "Must get it exactly right" },
  { id: "multitasking", emoji: "🌀", label: "Too Many Tasks", desc: "Multiple tasks at once" },
  { id: "transitions", emoji: "🔄", label: "Task Switching", desc: "Switching contexts is hard" },
];

const EMOTIONAL_PREFERENCES = [
  { id: "encouraging", emoji: "🌟", label: "Encouraging", desc: "Warm, positive, celebratory" },
  { id: "direct", emoji: "🎯", label: "Direct", desc: "Clear, concise, no fluff" },
  { id: "gentle", emoji: "🌿", label: "Gentle", desc: "Soft, calming, patient" },
  { id: "humorous", emoji: "😄", label: "Humorous", desc: "Light, funny, playful" },
];

const containerVariants = {
  enter: { opacity: 0, x: 40 },
  center: { opacity: 1, x: 0, transition: { duration: 0.4 } },
  exit: { opacity: 0, x: -40, transition: { duration: 0.3 } },
};

export default function RegisterPage() {
  const router = useRouter();
  const { login: loginUser } = useUserStore();
  const [step, setStep] = useState<"account" | "focus" | "energy" | "style" | "triggers" | "tone" | "complete">("account");
  const [onboarding, setOnboarding] = useState<OnboardingData>({
    focusStyle: "",
    energyPattern: "",
    productivityStyle: "",
    overwhelmTriggers: [],
    emotionalPreferences: "",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  const {
    register,
    handleSubmit,
    setError: setFormError,
    formState: { errors, isSubmitting: formSubmitting },
  } = useForm<RegisterForm>({ resolver: zodResolver(registerSchema) });

  const handleRegister = async (data: RegisterForm) => {
    try {
      const res = await api.register(data.username, data.password);
      if (res.success) {
        loginUser(data.username, res.role);
        setStep("focus");
      } else {
        setFormError("root", { message: res.error || "Registration failed." });
      }
    } catch {
      setFormError("root", { message: "Connection error. Please try again." });
    }
  };

  const saveProfile = async (data: OnboardingData) => {
    setIsSubmitting(true);
    try {
      // Save preferences to API using auth store username
      const currentUsername = useUserStore.getState().username;
      if (currentUsername) {
        await api.updateSettings(currentUsername, {
          coach_tone: (data.emotionalPreferences || "encouraging") as "encouraging" | "direct" | "gentle" | "humorous",
          start_tiny_default: data.overwhelmTriggers.includes("large_tasks"),
          overwhelm_mode_enabled: data.overwhelmTriggers.length >= 3,
        }).catch(() => {});
      }
      router.push("/dashboard");
    } catch {
      router.push("/dashboard");
    }
  };

  const toggleTrigger = (id: string) => {
    setOnboarding((prev) => ({
      ...prev,
      overwhelmTriggers: prev.overwhelmTriggers.includes(id)
        ? prev.overwhelmTriggers.filter((t) => t !== id)
        : [...prev.overwhelmTriggers, id],
    }));
  };

  // If account step, show registration form
  if (step === "account") {
    return (
      <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-b from-background via-[#0a1628] to-background">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-md"
        >
          <div className="text-center mb-8">
            <motion.div
              className="text-4xl mb-3 inline-block"
              animate={{ y: [0, -6, 0] }}
              transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
            >
              🧠
            </motion.div>
            <h1 className="text-2xl font-bold text-foreground">
              Create <span className="gradient-text">Account</span>
            </h1>
            <p className="text-sm text-muted mt-1">Start your ADHD coaching journey</p>
          </div>

          <Card className="p-6">
            <form onSubmit={handleSubmit(handleRegister)} className="space-y-4">
              <Input
                label="Username"
                id="username"
                placeholder="Choose a username"
                error={errors.username?.message}
                autoFocus
                {...register("username")}
              />
              <Input
                label="Password"
                id="password"
                type="password"
                placeholder="At least 6 characters"
                error={errors.password?.message}
                {...register("password")}
              />
              <Input
                label="Confirm Password"
                id="confirmPassword"
                type="password"
                placeholder="Repeat your password"
                error={errors.confirmPassword?.message}
                {...register("confirmPassword")}
              />

              {errors.root && (
                <motion.p
                  initial={{ opacity: 0, y: -5 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="text-sm text-danger-500 bg-danger-500/10 rounded-lg p-3"
                >
                  {errors.root.message}
                </motion.p>
              )}

              <Button type="submit" loading={formSubmitting} className="w-full">
                Create Account
              </Button>
            </form>
          </Card>

          <p className="text-center text-sm text-muted mt-6">
            Already have an account?{" "}
            <Link href="/login" className="text-calm-400 hover:text-calm-300 transition-colors font-medium">
              Sign in
            </Link>
          </p>
        </motion.div>
      </div>
    );
  }

  // ==================== Onboarding Steps ====================
  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-b from-background via-[#0a1628] to-background">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-lg"
      >
        {/* Progress Bar */}
        <div className="mb-8">
          {(() => {
            const stepsList = ["focus", "energy", "style", "triggers", "tone"];
            const stepIndex = step === "complete" ? 4 : stepsList.indexOf(step);
            const stepNumber = step === "complete" ? 5 : stepIndex + 1;
            const stepLabel = step === "complete" ? "Onboarding Complete!" : ["Focus Style", "Energy Pattern", "Work Style", "Overwhelm", "Tone"][stepIndex];
            const progressPercent = step === "complete" ? 100 : ((stepIndex + 1) / 5) * 100;

            return (
              <>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-xs text-muted font-medium">
                    Step {stepNumber} of 5
                  </span>
                  <span className="text-xs text-muted font-medium">
                    {stepLabel}
                  </span>
                </div>
                <div className="h-1.5 bg-border rounded-full overflow-hidden">
                  <motion.div
                    className="h-full rounded-full"
                    style={{ background: "linear-gradient(90deg, #6ee7b7, #667eea, #c084fc)" }}
                    initial={{ width: "20%" }}
                    animate={{ width: `${progressPercent}%` }}
                    transition={{ duration: 0.5, ease: "easeOut" }}
                  />
                </div>
              </>
            );
          })()}
        </div>

        <AnimatePresence mode="wait">
          {/* Focus Style */}
          {step === "focus" && (
            <motion.div key="focus" variants={containerVariants} initial="enter" animate="center" exit="exit">
              <Card className="p-6">
                <div className="text-center mb-6">
                  <span className="text-4xl block mb-2">🎯</span>
                  <CardTitle>What&apos;s Your Focus Style?</CardTitle>
                  <p className="text-sm text-muted mt-2">This helps me tailor focus sessions to how you naturally work.</p>
                </div>
                <div className="space-y-2">
                  {FOCUS_STYLES.map((style) => (
                    <motion.button
                      key={style.id}
                      whileHover={{ scale: 1.01 }}
                      whileTap={{ scale: 0.99 }}
                      onClick={() => { setOnboarding((p) => ({ ...p, focusStyle: style.id })); setStep("energy"); }}
                      className={`w-full p-4 rounded-xl text-left transition-all duration-200 border ${
                        onboarding.focusStyle === style.id
                          ? "bg-calm-500/10 border-calm-500/50"
                          : "bg-surface border-border hover:border-calm-500/30"
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <span className="text-2xl">{style.emoji}</span>
                        <div>
                          <p className="text-sm font-medium text-foreground">{style.label}</p>
                          <p className="text-xs text-muted mt-0.5">{style.desc}</p>
                        </div>
                      </div>
                    </motion.button>
                  ))}
                </div>
                <div className="mt-4 flex gap-2">
                  <Button variant="ghost" size="sm" onClick={() => setStep("account")} className="text-muted">Back</Button>
                  <Button variant="ghost" size="sm" onClick={() => setStep("energy")} className="text-muted ml-auto">Skip</Button>
                </div>
              </Card>
            </motion.div>
          )}

          {/* Energy Pattern */}
          {step === "energy" && (
            <motion.div key="energy" variants={containerVariants} initial="enter" animate="center" exit="exit">
              <Card className="p-6">
                <div className="text-center mb-6">
                  <span className="text-4xl block mb-2">⚡</span>
                  <CardTitle>When Are You Most Energized?</CardTitle>
                  <p className="text-sm text-muted mt-2">Understanding your energy rhythms helps me schedule tasks at your peak times.</p>
                </div>
                <div className="space-y-2">
                  {ENERGY_PATTERNS.map((pattern) => (
                    <motion.button
                      key={pattern.id}
                      whileHover={{ scale: 1.01 }}
                      whileTap={{ scale: 0.99 }}
                      onClick={() => { setOnboarding((p) => ({ ...p, energyPattern: pattern.id })); setStep("style"); }}
                      className={`w-full p-4 rounded-xl text-left transition-all duration-200 border ${
                        onboarding.energyPattern === pattern.id
                          ? "bg-focus-500/10 border-focus-500/50"
                          : "bg-surface border-border hover:border-focus-500/30"
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <span className="text-2xl">{pattern.emoji}</span>
                        <div>
                          <p className="text-sm font-medium text-foreground">{pattern.label}</p>
                          <p className="text-xs text-muted mt-0.5">{pattern.desc}</p>
                        </div>
                      </div>
                    </motion.button>
                  ))}
                </div>
                <div className="mt-4 flex gap-2">
                  <Button variant="ghost" size="sm" onClick={() => setStep("focus")} className="text-muted">Back</Button>
                  <Button variant="ghost" size="sm" onClick={() => setStep("style")} className="text-muted ml-auto">Skip</Button>
                </div>
              </Card>
            </motion.div>
          )}

          {/* Productivity Style */}
          {step === "style" && (
            <motion.div key="style" variants={containerVariants} initial="enter" animate="center" exit="exit">
              <Card className="p-6">
                <div className="text-center mb-6">
                  <span className="text-4xl block mb-2">📋</span>
                  <CardTitle>How Do You Work Best?</CardTitle>
                  <p className="text-sm text-muted mt-2">Your natural productivity style shapes how I&apos;ll suggest tasks and workflows.</p>
                </div>
                <div className="grid grid-cols-1 gap-2">
                  {PRODUCTIVITY_STYLES.map((style) => (
                    <motion.button
                      key={style.id}
                      whileHover={{ scale: 1.01 }}
                      whileTap={{ scale: 0.99 }}
                      onClick={() => { setOnboarding((p) => ({ ...p, productivityStyle: style.id })); setStep("triggers"); }}
                      className={`w-full p-4 rounded-xl text-left transition-all duration-200 border ${
                        onboarding.productivityStyle === style.id
                          ? "bg-purple-500/10 border-purple-500/50"
                          : "bg-surface border-border hover:border-purple-500/30"
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <span className="text-2xl">{style.emoji}</span>
                        <div>
                          <p className="text-sm font-medium text-foreground">{style.label}</p>
                          <p className="text-xs text-muted mt-0.5">{style.desc}</p>
                        </div>
                      </div>
                    </motion.button>
                  ))}
                </div>
                <div className="mt-4 flex gap-2">
                  <Button variant="ghost" size="sm" onClick={() => setStep("energy")} className="text-muted">Back</Button>
                  <Button variant="ghost" size="sm" onClick={() => setStep("triggers")} className="text-muted ml-auto">Skip</Button>
                </div>
              </Card>
            </motion.div>
          )}

          {/* Overwhelm Triggers */}
          {step === "triggers" && (
            <motion.div key="triggers" variants={containerVariants} initial="enter" animate="center" exit="exit">
              <Card className="p-6">
                <div className="text-center mb-6">
                  <span className="text-4xl block mb-2">🌊</span>
                  <CardTitle>What Overwhelms You?</CardTitle>
                  <p className="text-sm text-muted mt-2">Pick all that apply. This helps me prevent overwhelm before it hits.</p>
                </div>
                <div className="grid grid-cols-1 gap-2">
                  {OVERWHELM_TRIGGERS.map((trigger) => {
                    const selected = onboarding.overwhelmTriggers.includes(trigger.id);
                    return (
                      <motion.button
                        key={trigger.id}
                        whileHover={{ scale: 1.01 }}
                        whileTap={{ scale: 0.99 }}
                        onClick={() => toggleTrigger(trigger.id)}
                        className={`w-full p-4 rounded-xl text-left transition-all duration-200 border ${
                          selected
                            ? "bg-danger-500/10 border-danger-500/50"
                            : "bg-surface border-border hover:border-danger-500/30"
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          <span className="text-2xl">{trigger.emoji}</span>
                          <div className="flex-1">
                            <p className="text-sm font-medium text-foreground">{trigger.label}</p>
                            <p className="text-xs text-muted mt-0.5">{trigger.desc}</p>
                          </div>
                          <div className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-all ${
                            selected ? "bg-danger-500 border-danger-500" : "border-border"
                          }`}>
                            {selected && (
                              <motion.svg
                                initial={{ scale: 0 }}
                                animate={{ scale: 1 }}
                                className="w-3 h-3 text-white"
                                fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}
                              >
                                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                              </motion.svg>
                            )}
                          </div>
                        </div>
                      </motion.button>
                    );
                  })}
                </div>
                <div className="mt-4 flex gap-2">
                  <Button variant="ghost" size="sm" onClick={() => setStep("style")} className="text-muted">Back</Button>
                  <Button variant="ghost" size="sm" onClick={() => setStep("tone")} className="text-muted ml-auto">Skip</Button>
                </div>
                {onboarding.overwhelmTriggers.length > 0 && (
                  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-3">
                    <Button onClick={() => setStep("tone")} className="w-full">
                      Continue ({onboarding.overwhelmTriggers.length} selected)
                    </Button>
                  </motion.div>
                )}
              </Card>
            </motion.div>
          )}

          {/* Emotional Tone Preference */}
          {step === "tone" && (
            <motion.div key="tone" variants={containerVariants} initial="enter" animate="center" exit="exit">
              <Card className="p-6">
                <div className="text-center mb-6">
                  <span className="text-4xl block mb-2">💬</span>
                  <CardTitle>How Should I Speak to You?</CardTitle>
                  <p className="text-sm text-muted mt-2">This is how your AI coach will communicate. Pick what feels most supportive.</p>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  {EMOTIONAL_PREFERENCES.map((pref) => (
                    <motion.button
                      key={pref.id}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => { setOnboarding((p) => ({ ...p, emotionalPreferences: pref.id })); setStep("complete"); }}
                      className={`p-4 rounded-xl text-center transition-all duration-200 border ${
                        onboarding.emotionalPreferences === pref.id
                          ? "bg-calm-500/10 border-calm-500/50"
                          : "bg-surface border-border hover:border-calm-500/30"
                      }`}
                    >
                      <span className="text-3xl block mb-1">{pref.emoji}</span>
                      <p className="text-sm font-medium text-foreground">{pref.label}</p>
                      <p className="text-[10px] text-muted mt-0.5">{pref.desc}</p>
                    </motion.button>
                  ))}
                </div>
                <div className="mt-4 flex gap-2">
                  <Button variant="ghost" size="sm" onClick={() => setStep("triggers")} className="text-muted">Back</Button>
                  <Button variant="ghost" size="sm" onClick={() => { setOnboarding((p) => ({ ...p, emotionalPreferences: "encouraging" })); setStep("complete"); }} className="text-muted ml-auto">Skip</Button>
                </div>
              </Card>
            </motion.div>
          )}

          {/* Complete */}
          {step === "complete" && (
            <motion.div key="complete" variants={containerVariants} initial="enter" animate="center" exit="exit">
              <Card className="p-8 text-center">
                <motion.div
                  className="text-6xl mb-4"
                  animate={{ scale: [1, 1.15, 1], rotate: [0, -5, 5, 0] }}
                  transition={{ duration: 0.6 }}
                >
                  🎉
                </motion.div>
                <CardTitle>You&apos;re All Set!</CardTitle>
                <p className="text-sm text-muted mt-2 mb-6 max-w-sm mx-auto">
                  I&apos;ve learned your focus style, energy patterns, and what overwhelms you.
                  Let&apos;s start supporting your executive function!
                </p>
                <div className="space-y-2 text-left mb-6">
                  {onboarding.focusStyle && (
                    <div className="flex items-center gap-2 text-sm text-muted bg-surface rounded-lg p-2.5">
                      <span>🎯</span> Focus Style: <span className="text-foreground font-medium capitalize">{onboarding.focusStyle}</span>
                    </div>
                  )}
                  {onboarding.energyPattern && (
                    <div className="flex items-center gap-2 text-sm text-muted bg-surface rounded-lg p-2.5">
                      <span>⚡</span> Energy: <span className="text-foreground font-medium capitalize">{onboarding.energyPattern}</span>
                    </div>
                  )}
                  {onboarding.overwhelmTriggers.length > 0 && (
                    <div className="flex items-center gap-2 text-sm text-muted bg-surface rounded-lg p-2.5">
                      <span>🌊</span> {onboarding.overwhelmTriggers.length} overwhelm trigger{onboarding.overwhelmTriggers.length > 1 ? "s" : ""} tracked
                    </div>
                  )}
                  {onboarding.emotionalPreferences && (
                    <div className="flex items-center gap-2 text-sm text-muted bg-surface rounded-lg p-2.5">
                      <span>💬</span> Preferred tone: <span className="text-foreground font-medium capitalize">{onboarding.emotionalPreferences}</span>
                    </div>
                  )}
                </div>
                <Button onClick={() => saveProfile(onboarding)} loading={isSubmitting} size="lg" className="w-full">
                  🚀 Start My Journey
                </Button>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
}
