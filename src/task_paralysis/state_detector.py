"""
ADHD State Detection Engine
===========================
Core differentiator for the ADHD Coach platform.
Detects real-time ADHD cognitive states — overwhelm, burnout, hyperfocus,
avoidance, and emotional dysregulation — and triggers adaptive responses.

Architecture:
- Multi-signal detection (text analysis, behavioral patterns, temporal context)
- State machine with transitions between states
- Dynamic adaptation suggestions (UI, coaching, interventions, focus mode, task size)
"""

import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ==================== Signal Detectors ====================

SIGNAL_PATTERNS = {
    "overwhelm": {
        "keywords": [
            "too much", "overwhelmed", "can't handle", "too many", "so much to do",
            "spinning", "drowning", "sinking", "can't breathe", "everything at once",
            "too fast", "can't keep up", "freaking out", "panic", "can't cope",
            "stuck", "frozen", "paralyzed", "can't move", "so many things",
            "i'm done", "can't do this", "too hard", "too difficult",
        ],
        "weight": 0.15,  # Per keyword match weight
        "rapid_message_threshold": 3,  # Messages in 60s window
        "rapid_message_weight": 0.25,
        "intensifiers": ["really", "very", "so", "extremely", "completely", "totally"],
    },
    "burnout": {
        "keywords": [
            "exhausted", "burned out", "burnt out", "drained", "empty", "numb",
            "tired of everything", "no energy", "can't anymore", "done with everything",
            "nothing matters", "what's the point", "hopeless", "helpless",
            "so tired", "always tired", "never enough", "giving up",
            "can't even", "no motivation", "zero energy", "completely done",
        ],
        "weight": 0.12,
        "chronic_stress_days": 5,  # Days of high stress before flagging burnout
        "chronic_stress_weight": 0.3,
        "intensifiers": ["completely", "totally", "absolutely", "so", "really"],
    },
    "hyperfocus": {
        "keywords": [
            "can't stop", "lost track of time", "hours passed", "didn't notice",
            "hyperfocus", "in the zone", "deep focus", "can't pull away",
            "forgot to eat", "forgot to drink", "been hours", "can't stop working",
            "obsessed", "can't look away", "deep dive", "rabbit hole",
        ],
        "weight": 0.15,
        "long_session_minutes": 120,  # Extended session flag
        "long_session_weight": 0.2,
        "intensifiers": ["really", "so", "completely", "totally", "way too"],
    },
    "avoidance": {
        "keywords": [
            "procrastinating", "avoiding", "putting off", "can't start",
            "don't want to", "will do later", "starting tomorrow", "not ready yet",
            "scrolling", "distracting myself", "binge watching", "endless scrolling",
            "doing everything except", "finding excuses", "can't face it",
            "dreading", "not in the mood", "later", "tomorrow",
        ],
        "weight": 0.12,
        "task_paralysis_keywords": [
            "don't know where to start", "too big", "can't even begin",
            "where do i even start", "don't know how",
        ],
        "task_paralysis_weight": 0.35,
        "intensifiers": ["always", "constantly", "endlessly"],
    },
    "emotional_dysregulation": {
        "keywords": [
            "so angry", "furious", "rage", "snapped", "exploded", "overreacted",
            "so upset", "crying", "can't stop crying", "so frustrated",
            "so sad", "devastated", "crushed", "hurt", "rejected",
            "rsd", "rejection sensitivity", "over sensitive", "can't control",
            "emotional", "mood swing", "feeling everything", "too intense",
            "so anxious", "panic attack", "can't calm down",
        ],
        "weight": 0.15,
        "rapid_mood_shift_weight": 0.3,
        "intensifiers": ["so", "very", "extremely", "incredibly", "unbelievably"],
    },
}

# State definitions
ADHD_STATES = {
    "calm": {
        "id": "calm",
        "label": "Calm",
        "emoji": "😌",
        "strategies": ["maintain", "gentle_encouragement"],
        "ui_mode": "normal",
        "coaching_tone": "warm",
        "focus_mode": "standard",
        "task_size": "normal",
    },
    "focused": {
        "id": "focused",
        "label": "Focused",
        "emoji": "🎯",
        "strategies": ["protect_focus", "hydration_reminder"],
        "ui_mode": "normal",
        "coaching_tone": "encouraging",
        "focus_mode": "deep_focus",
        "task_size": "normal",
    },
    "overwhelmed": {
        "id": "overwhelmed",
        "label": "Overwhelmed",
        "emoji": "😰",
        "strategies": ["simplify_ui", "reduce_choices", "grounding", "focus_on_breath"],
        "ui_mode": "gentle",
        "coaching_tone": "gentle",
        "focus_mode": "gentle_start",
        "task_size": "micro",
    },
    "burnout": {
        "id": "burnout",
        "label": "Burnout Risk",
        "emoji": "🫠",
        "strategies": ["rest_first", "no_productivity", "self_care", "recovery_mode"],
        "ui_mode": "gentle",
        "coaching_tone": "nurturing",
        "focus_mode": "recovery",
        "task_size": "none",
    },
    "hyperfocus": {
        "id": "hyperfocus",
        "label": "Hyperfocus",
        "emoji": "🔮",
        "strategies": ["gentle_interruption", "hydration", "movement_break", "check_needs"],
        "ui_mode": "normal",
        "coaching_tone": "gentle_reminder",
        "focus_mode": "deep_focus",
        "task_size": "normal",
    },
    "avoidant": {
        "id": "avoidant",
        "label": "Avoidant",
        "emoji": "🙈",
        "strategies": ["start_tiny", "accountability_nudge", "remove_barriers", "2_minute_rule"],
        "ui_mode": "normal",
        "coaching_tone": "encouraging",
        "focus_mode": "sprint",
        "task_size": "micro",
    },
    "dysregulated": {
        "id": "dysregulated",
        "label": "Emotionally Dysregulated",
        "emoji": "🌊",
        "strategies": ["validate_first", "grounding", "breathing", "safe_space", "no_decisions"],
        "ui_mode": "gentle",
        "coaching_tone": "compassionate",
        "focus_mode": "recovery",
        "task_size": "none",
    },
}


class ADHDStateDetector:
    """
    Detects the user's current ADHD cognitive state based on multiple signals:
    - Message content analysis (keyword matching)
    - Behavioral patterns (message frequency, session duration)
    - Temporal context (time of day, day of week)
    - Conversation history (recent emotional trend)
    """

    def __init__(self, db_manager=None):
        self.db = db_manager
        self._message_timestamps: List[datetime] = []
        self._last_states: List[dict] = []
        self._max_history = 100

    def analyze(self, text: str, context: Optional[dict] = None) -> dict:
        """
        Analyze the current state based on text and context.
        Returns the detected state with confidence and adaptation suggestions.
        """
        context = context or {}
        text_lower = text.lower() if text else ""

        # Score each signal type
        signal_scores = self._score_signals(text_lower, context)

        # Determine dominant state
        state, confidence = self._determine_state(signal_scores, context)

        # Get adaptation strategies for this state
        state_config = ADHD_STATES.get(state, ADHD_STATES["calm"])

        # Generate specific adaptation suggestions
        adaptations = self._generate_adaptations(state, state_config, signal_scores, context)

        # Record state
        self._record_state(state, confidence, signal_scores)

        return {
            "state": state,
            "state_label": state_config["label"],
            "state_emoji": state_config["emoji"],
            "confidence": confidence,
            "signal_scores": signal_scores,
            "adaptations": adaptations,
            "strategies": state_config["strategies"],
            "ui_mode": state_config["ui_mode"],
            "coaching_tone": state_config["coaching_tone"],
            "focus_mode": state_config["focus_mode"],
            "task_size": state_config["task_size"],
            "is_crisis": state in ("overwhelmed", "dysregulated") and confidence >= 0.7,
        }

    def _score_signals(self, text_lower: str, context: dict) -> Dict[str, float]:
        """Score each signal type based on text analysis and context."""
        scores = {}

        for signal_type, config in SIGNAL_PATTERNS.items():
            score = 0.0

            # 1. Keyword matching
            keyword_matches = 0
            for keyword in config["keywords"]:
                if keyword in text_lower:
                    keyword_matches += 1
                    # Check for intensifiers nearby
                    for intensifier in config.get("intensifiers", []):
                        if intensifier in text_lower:
                            score += config["weight"] * 1.3
                            break
                    else:
                        score += config["weight"]

            # 2. Rapid message detection (for overwhelm)
            if "rapid_message_threshold" in config and config["rapid_message_threshold"] > 0:
                self._message_timestamps.append(datetime.now(timezone.utc))
                recent = [t for t in self._message_timestamps if (datetime.now(timezone.utc) - t).total_seconds() < 60]
                if len(recent) >= config["rapid_message_threshold"]:
                    score += config.get("rapid_message_weight", 0.2)

            # 3. Task paralysis detection (for avoidance)
            if "task_paralysis_keywords" in config:
                for tp_kw in config["task_paralysis_keywords"]:
                    if tp_kw in text_lower:
                        score += config.get("task_paralysis_weight", 0.3)
                        break

            # 4. Context signals from session data
            if context:
                stress_level = context.get("current_stress", 5)
                energy_level = context.get("current_energy", 5)

                # High stress boosts overwhelm/burnout signals
                if signal_type in ("overwhelm", "burnout") and stress_level >= 7:
                    score += (stress_level - 5) * 0.05

                # Low energy boosts burnout
                if signal_type == "burnout" and energy_level <= 3:
                    score += (5 - energy_level) * 0.05

            scores[signal_type] = round(min(1.0, score), 3)

        return scores

    def _determine_state(self, signal_scores: dict, context: dict) -> Tuple[str, float]:
        """
        Determine the dominant ADHD state based on signal scores and context.
        Returns (state_id, confidence).
        """

        # Crisis states take priority
        if signal_scores.get("emotional_dysregulation", 0) >= 0.5:
            return "dysregulated", signal_scores["emotional_dysregulation"]

        if signal_scores.get("overwhelm", 0) >= 0.4:
            return "overwhelmed", signal_scores["overwhelm"]

        if signal_scores.get("burnout", 0) >= 0.35:
            return "burnout", signal_scores["burnout"]

        # Check for hyperfocus (needs specific keywords)
        if signal_scores.get("hyperfocus", 0) >= 0.3:
            return "hyperfocus", signal_scores["hyperfocus"]

        if signal_scores.get("avoidance", 0) >= 0.3:
            return "avoidant", signal_scores["avoidance"]

        # Check context for sustained patterns
        if context:
            stress_level = context.get("current_stress", 5)
            # Chronic high stress with low energy suggests burnout
            if stress_level >= 7 and context.get("current_energy", 5) <= 3:
                return "burnout", 0.4

        # Positive states
        positive_keywords = ["focused", "productive", "in the zone", "great", "awesome", "accomplished"]
        if context.get("text", ""):
            text = context.get("text", "").lower()
            if any(kw in text for kw in ["hyperfocus", "deep focus", "in the zone"]) or \
               (signal_scores.get("hyperfocus", 0) > 0 and signal_scores.get("overwhelm", 0) == 0):
                return "hyperfocus", signal_scores.get("hyperfocus", 0.3)

        # Default to calm
        if all(score < 0.2 for score in signal_scores.values()):
            focused_words = ["focus", "working", "doing", "productive", "accomplished", "completed", "done"]
            if any(w in context.get("text", "").lower() for w in focused_words) if context.get("text") else False:
                return "focused", 0.3
            return "calm", 0.5

        return "calm", max(0.3, 1.0 - max(signal_scores.values()))

    def _generate_adaptations(self, state: str, state_config: dict, signal_scores: dict, context: dict) -> dict:
        """Generate specific adaptation suggestions based on the detected state."""
        adaptations = {
            "ui_changes": [],
            "coaching_style": state_config["coaching_tone"],
            "focus_mode": state_config["focus_mode"],
            "task_size": state_config["task_size"],
            "suggested_interventions": [],
            "messages": [],
        }

        if state == "overwhelmed":
            adaptations["ui_changes"] = ["simplify_dashboard", "reduce_sidebar", "single_column"]
            adaptations["suggested_interventions"] = [
                {"type": "grounding", "action": "5-4-3-2-1 grounding exercise", "priority": "immediate"},
                {"type": "breathing", "action": "Box breathing: 4-4-4-4", "priority": "immediate"},
                {"type": "micro_task", "action": "Pick ONE tiny thing to do", "priority": "high"},
            ]
            adaptations["messages"] = [
                "Let's make the world smaller. Breathe with me.",
                "You don't need to do everything. Just the next right thing.",
            ]

        elif state == "burnout":
            adaptations["ui_changes"] = ["simplify_dashboard", "hide_stats", "show_recovery"]
            adaptations["suggested_interventions"] = [
                {"type": "rest", "action": "Permission to rest — no productivity today", "priority": "immediate"},
                {"type": "self_care", "action": "Do something that feels good, not productive", "priority": "high"},
                {"type": "sleep", "action": "Prioritize sleep tonight", "priority": "high"},
            ]
            adaptations["messages"] = [
                "Rest is productive when you're burned out. Let's just be today.",
                "Your only job right now is to take care of you.",
            ]

        elif state == "hyperfocus":
            adaptations["ui_changes"] = ["show_reminders", "gentle_timer"]
            adaptations["suggested_interventions"] = [
                {"type": "hydration", "action": "Drink a glass of water", "priority": "medium"},
                {"type": "movement", "action": "Stand up and stretch for 60 seconds", "priority": "medium"},
                {"type": "break", "action": "Take a 5-minute break", "priority": "low"},
            ]
            adaptations["messages"] = [
                "You're in the zone! Quick check: have you had water recently?",
                "Deep focus is great. Let's just make sure your body is okay too.",
            ]

        elif state == "avoidant":
            adaptations["ui_changes"] = ["show_start_tiny", "hide_large_tasks"]
            adaptations["suggested_interventions"] = [
                {"type": "tiny_start", "action": "2-minute rule: just do 2 minutes", "priority": "high"},
                {"type": "accountability", "action": "Tell me one tiny step you'll take", "priority": "high"},
                {"type": "barrier_removal", "action": "What's ONE thing blocking you? Let's remove it.", "priority": "medium"},
            ]
            adaptations["messages"] = [
                "Starting is the hardest part. Let's make it so small it feels silly.",
                "What if we just did 2 minutes? You can stop after 2 minutes.",
            ]

        elif state == "dysregulated":
            adaptations["ui_changes"] = ["simplify_completely", "hide_all_stats", "calming_colors"]
            adaptations["suggested_interventions"] = [
                {"type": "grounding", "action": "5-4-3-2-1 grounding", "priority": "immediate"},
                {"type": "breathing", "action": "Deep breathing: in for 4, out for 6", "priority": "immediate"},
                {"type": "safe_space", "action": "Find a quiet space for 5 minutes", "priority": "immediate"},
            ]
            adaptations["messages"] = [
                "I'm here. You're safe. Let's breathe together.",
                "This feeling will pass. It's a wave — let it wash over and through.",
            ]

        return adaptations

    def _record_state(self, state: str, confidence: float, signal_scores: dict):
        """Record the detected state in history."""
        self._last_states.append({
            "state": state,
            "confidence": confidence,
            "signal_scores": signal_scores,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        if len(self._last_states) > self._max_history:
            self._last_states = self._last_states[-self._max_history:]

    def get_current_state_summary(self) -> Optional[dict]:
        """Get the most recent state detection summary."""
        if not self._last_states:
            return None
        return self._last_states[-1]

    def get_state_history(self, n: int = 10) -> List[dict]:
        """Get the last N state detections."""
        return self._last_states[-n:]

    def get_system_prompt_extension(self, text: str, context: Optional[dict] = None) -> str:
        """
        Generate a system prompt extension based on detected state.
        This gets injected into the LLM prompt to modulate coaching style.
        """
        result = self.analyze(text, context)
        state = result["state"]
        confidence = result["confidence"]
        state_config = ADHD_STATES.get(state, ADHD_STATES["calm"])

        if state == "calm" and confidence < 0.6:
            return ""  # Don't inject for low-confidence calm

        parts = [f"[ADHD State: {state_config['label']} | Confidence: {confidence:.0%}]"]

        # Add coaching instructions based on state
        if state == "overwhelmed":
            parts.append("PRIORITY: Reduce cognitive load. Use short sentences. Validate first.")
            parts.append("CRITICAL: Do NOT suggest long tasks or productivity. Focus on emotional safety.")
            parts.append("Adaptation: Use gentle tone. Suggest ONLY micro-steps (2 min or less).")

        elif state == "burnout":
            parts.append("PRIORITY: Do NOT push productivity. Validate exhaustion.")
            parts.append("CRITICAL: Suggest rest, self-care, and basic needs. NOT tasks.")
            parts.append("Adaptation: Use nurturing, gentle tone. Give permission to rest.")

        elif state == "hyperfocus":
            parts.append("PRIORITY: Gentle reminders about basic needs (water, food, movement).")
            parts.append("CRITICAL: Do NOT encourage continued focus. Suggest breaks gently.")
            parts.append("Adaptation: Use warm reminder tone. One suggestion at a time.")

        elif state == "avoidant":
            parts.append("PRIORITY: Lower the barrier to starting. Suggest TINY actions.")
            parts.append("CRITICAL: Use the 2-minute rule. Do NOT suggest large tasks.")
            parts.append("Adaptation: Encouraging, supportive tone. Celebrate small wins.")

        elif state == "dysregulated":
            parts.append("PRIORITY: Emotional safety. Validating feelings comes FIRST.")
            parts.append("CRITICAL: Grounding exercises only. No decisions, no tasks, no planning.")
            parts.append("Adaptation: Gentle, warm, compassionate tone. Use simple language.")

        # Add adaptation suggestions
        if result.get("strategies"):
            parts.append(f"Suggested strategies: {', '.join(result['strategies'])}")

        if result.get("adaptations", {}).get("messages"):
            parts.append(f"Suggested message: {result['adaptations']['messages'][0]}")

        return "\n".join(parts)


# State detection for quick API usage
def detect_adhd_state(text: str, context: Optional[dict] = None) -> dict:
    """Convenience function to quickly detect ADHD state."""
    detector = ADHDStateDetector()
    return detector.analyze(text, context)
