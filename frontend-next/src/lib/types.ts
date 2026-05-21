// ==================== Core ====================
export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
  is_voice?: boolean;
  lang?: string;
  audio?: string;
  audio_played?: boolean;
  tasks?: TaskItem[];
  display?: string;
  timestamp?: string;
}

export interface TaskItem {
  emoji: string;
  text: string;
  completed?: boolean;
  id?: string;
}

export interface ChatRequest {
  text: string;
  history: Partial<ChatMessage>[];
  user_data: UserData;
  session_data?: Record<string, unknown>;
  language: string;
  language_name: string;
  username: string;
}

export interface ChatResponse {
  reply: string;
  analysis: { emotion: string; sentiment?: string; topics?: string[] };
  scores: ScoreData;
  interventions: Intervention[];
}

// ==================== Scores ====================
export interface ScoreData {
  productivity_score?: number;
  adhd_risk?: number;
  adhd_health_score?: number;
  adhd_questionnaire_score?: number;
  adhd_questionnaire_level?: string;
  mental_health_score?: number;
  depression_score?: number;
  final_score?: number;
  level?: string;
  description?: string;
  focus_risk?: string;
  weights?: Record<string, number>;
  summary?: {
    sleep_hours: number;
    stress_level: number;
    phone_distractions: number;
    study_hours: number;
    total_screen_time: number;
  };
}

// ==================== User ====================
export interface UserData {
  sleep_hours: number;
  stress_level: number;
  phone_distractions: number;
  energy_level?: number;
  mood?: string;
  study_hours_per_day?: number;
  [key: string]: number | string | undefined;
}

export interface UserProfile {
  username: string;
  email?: string;
  contact_info?: string;
  settings: UserSettings;
}

export interface UserSettings {
  theme: string;
  language: string;
  notifications_enabled: boolean;
  notification_frequency: string;
  timer_duration: number;
  auto_check_in: boolean;
  sound_enabled: boolean;
  use_12h_format: boolean;
  coach_tone?: "encouraging" | "direct" | "gentle" | "humorous";
  focus_area?: string;
  overwhelm_mode_enabled?: boolean;
  start_tiny_default?: boolean;
  time_blindness_enabled?: boolean;
  celebration_effects?: boolean;
}

// ==================== Interventions ====================
export interface Intervention {
  title: string;
  action: string;
  emoji?: string;
  priority?: number;
  category?: string;
}

// ==================== Agents ====================
export interface AgentInfo {
  id: string;
  name: string;
  emoji: string;
  role: string;
  description: string;
  color: string;
  promptExamples: string[];
  systemPrompt?: string;
}

export interface AgentAnalysis {
  agent_type: string;
  insights: string[];
  suggestions: string[];
  sentiment?: "positive" | "neutral" | "concerned";
}

export const AGENTS: AgentInfo[] = [
  {
    id: "productivity-coach", name: "Productivity Coach", emoji: "⚡",
    role: "Focus & motivation guidance",
    description: "Dopamine-friendly productivity strategies tailored to ADHD brains. Helps channel energy, overcome procrastination, and maintain momentum.",
    color: "#6ee7b7", promptExamples: ["I can't focus today", "Help me get motivated", "What should I prioritize?"],
  },
  {
    id: "task-breakdown", name: "Task Breakdown", emoji: "🔨",
    role: "Microtask generation & overwhelm reduction",
    description: "Takes overwhelming tasks and breaks them into tiny, concrete micro-steps. Detects task paralysis and suggests the smallest possible starting point.",
    color: "#667eea", promptExamples: ["I'm overwhelmed by this project", "Break this task down for me", "This feels impossible"],
  },
  {
    id: "focus-optimization", name: "Focus Optimization", emoji: "🎯",
    role: "Focus session analysis & timing",
    description: "Analyzes focus patterns, detects distraction patterns, and optimizes Pomodoro timing. Recommends breaks and deep work structure.",
    color: "#fbbf24", promptExamples: ["I keep getting distracted", "Help me find my focus hours", "When should I take breaks?"],
  },
  {
    id: "mood-burnout", name: "Mood & Burnout", emoji: "😌",
    role: "Emotional exhaustion detection & recovery",
    description: "Detects burnout patterns, analyzes mood trends, and provides compassionate recovery recommendations grounded in ADHD psychology.",
    color: "#f87171", promptExamples: ["I feel burned out", "My mood is low today", "I need emotional support"],
  },
  {
    id: "habit-builder", name: "Habit Builder", emoji: "🔄",
    role: "Streak reinforcement & consistency",
    description: "Reinforces positive habits, tracks streaks, and builds routines that actually stick with an ADHD brain using behavioral consistency strategies.",
    color: "#c084fc", promptExamples: ["I can't stick to habits", "Help me build a routine", "How do I stay consistent?"],
  },
  {
    id: "intervention", name: "Intervention Agent", emoji: "🆘",
    role: "ADHD rescue interventions",
    description: "Detects overwhelm and triggers rescue modes. Provides grounding exercises, hyperfocus interruption cues, and immediate coping strategies.",
    color: "#34d399", promptExamples: ["I'm having a panic moment", "I can't stop hyperfocusing", "I need a grounding exercise"],
  },
  {
    id: "accountability", name: "Accountability", emoji: "🤝",
    role: "Gentle reminders & check-ins",
    description: "Non-judgmental accountability through reminders, check-ins, and productivity summaries. Designed to support, not shame.",
    color: "#f472b6", promptExamples: ["Check in on my progress", "Help me stay accountable", "Remind me of my goals"],
  },
];

// ==================== Analytics ====================
export interface AnalyticsInsight {
  type: string;
  title: string;
  description: string;
  value?: number;
  trend?: "up" | "down" | "stable";
  priority: "high" | "medium" | "low";
}

export interface FocusPattern {
  day: string;
  quality: number;
  sessions: number;
  total_focus_minutes: number;
  distractions: number;
}

export interface MoodEntry {
  emoji: string;
  label: string;
  timestamp: string;
  energy?: number;
  note?: string;
}

export interface ProductivityCorrelation {
  factor: string;
  strength: number;
  direction: "positive" | "negative";
  description: string;
}

export interface TemporalPattern {
  hour: number;
  productivity: number;
  focus_quality: number;
  energy: number;
}

// ==================== Gamification ====================
export interface GameState {
  points: number;
  level: number;
  streak: number;
  longest_streak: number;
  badges: string[];
  session_count: number;
  total_focus_minutes: number;
  tasks_completed: number;
  progress: { time: string; points: number }[];
}

// ==================== Memory ====================
export interface MemoryEntry {
  type: "conversation" | "emotion" | "intervention" | "behavioral";
  content: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

// ==================== Focus Session ====================
export interface FocusSession {
  id: string;
  startTime: Date;
  duration: number;
  completed: boolean;
  quality?: number;
  distractions?: number;
  notes?: string;
}

// ==================== Auth ====================
export interface AuthResponse {
  success: boolean;
  token?: string;
  message?: string;
  error?: string;
}

// ==================== Tasks ====================
export interface ADHDTask {
  id: string;
  title: string;
  description?: string;
  emoji?: string;
  energy_required?: number;
  difficulty?: "very_easy" | "easy" | "medium" | "hard";
  estimated_minutes?: number;
  completed: boolean;
  created_at: string;
  completed_at?: string;
  category?: string;
  subtasks?: ADHDTask[];
}

// ==================== Mood ====================
export const MOODS = [
  { emoji: "😊", label: "Happy", color: "#6ee7b7" },
  { emoji: "😌", label: "Calm", color: "#667eea" },
  { emoji: "😐", label: "Okay", color: "#9ca3af" },
  { emoji: "😟", label: "Worried", color: "#fbbf24" },
  { emoji: "😰", label: "Anxious", color: "#fb923c" },
  { emoji: "😤", label: "Frustrated", color: "#f87171" },
] as const;
