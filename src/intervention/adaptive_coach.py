"""
Adaptive Coaching Engine
========================
Intelligently adjusts coaching style, intervention types, and task suggestions
based on the user's detected ADHD state, mood, time of day, and behavioral history.

Key features:
- Mood-adaptive coaching (anxious → breathing, exhausted → low-energy tasks, etc.)
- Time-aware suggestions (morning activation, afternoon momentum, night reflection)
- Overwhelm detection with automatic intervention triggering
- Adaptive tone modulation
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ==================== Mood-Adaptive Strategies ====================

MOOD_STRATEGIES = {
    "anxious": {
        "tone": "calm_reassuring",
        "interventions": ["breathing", "grounding", "reassurance"],
        "task_style": "micro_only",
        "productivity_goals": False,
        "focus_mode": "gentle_start",
        "messages": [
            "Let's slow down together. You're safe here.",
            "Anxiety is your brain trying to protect you. Let's give it a break.",
            "One breath at a time. Nothing else matters right now.",
        ],
    },
    "exhausted": {
        "tone": "gentle_low_energy",
        "interventions": ["rest", "hydration", "basic_needs"],
        "task_style": "none_or_tiny",
        "productivity_goals": False,
        "focus_mode": "recovery",
        "messages": [
            "Low energy days are your body's way of asking for rest. Listen to it.",
            "Your only job today is to take care of you.",
            "Rest is not a reward for productivity. Rest is a need.",
        ],
    },
    "hyperfocused": {
        "tone": "warm_reminder",
        "interventions": ["hydration_reminder", "movement_break", "check_needs"],
        "task_style": "protect_focus",
        "productivity_goals": True,
        "focus_mode": "deep_focus",
        "messages": [
            "You're in the zone! Quick check: water? food? bathroom?",
            "Deep focus is amazing. Let's just make sure your body is okay.",
            "Time check: how long have you been going?",
        ],
    },
    "overwhelmed": {
        "tone": "gentle_simplify",
        "interventions": ["grounding", "simplify", "reduce_choices", "tiny_start"],
        "task_style": "one_micro_thing",
        "productivity_goals": False,
        "focus_mode": "gentle_start",
        "messages": [
            "Let's make the world smaller. One thing at a time.",
            "You don't have to do everything. Just the next tiny thing.",
            "Overwhelm means you care. Let's take something off your plate.",
        ],
    },
    "avoidant": {
        "tone": "encouraging_nudge",
        "interventions": ["accountability", "tiny_start", "barrier_removal"],
        "task_style": "two_minute_rule",
        "productivity_goals": True,
        "focus_mode": "sprint",
        "messages": [
            "Starting is the hardest part. What if we just do 2 minutes?",
            "The dread of doing is worse than the doing itself.",
            "What's ONE tiny step you could take right now?",
        ],
    },
    "positive": {
        "tone": "celebratory_energetic",
        "interventions": ["channel_energy", "plan_ahead", "celebrate"],
        "task_style": "capitalize_on_momentum",
        "productivity_goals": True,
        "focus_mode": "standard",
        "messages": [
            "You're in a great space! Let's channel this energy.",
            "This is your moment. What feels exciting to work on?",
            "Capture this feeling — this is what momentum feels like!",
        ],
    },
}


# ==================== Time-Aware Suggestions ====================

TIME_BASED_STRATEGIES = {
    "morning": {
        "hours": (5, 11),
        "label": "Morning",
        "emoji": "🌅",
        "focus": "activation",
        "suggestions": [
            "Start with ONE small win to build momentum",
            "What's the most important thing for today?",
            "Plan your 3 priorities (keep it small)",
            "Do a quick brain dump to clear your mind",
            "Set an intention for today — just one sentence",
        ],
        "intervention_focus": ["planning", "activation", "morning_routine"],
    },
    "afternoon": {
        "hours": (11, 17),
        "label": "Afternoon",
        "emoji": "☀️",
        "focus": "momentum",
        "suggestions": [
            "Time for a momentum check — how's your energy?",
            "Break tasks into smaller chunks for the afternoon",
            "Take a proper break to reset your focus",
            "Use body doubling if you're struggling to focus",
            "Consider a change of scenery",
        ],
        "intervention_focus": ["momentum_support", "energy_check", "body_doubling"],
    },
    "evening": {
        "hours": (17, 21),
        "label": "Evening",
        "emoji": "🌆",
        "focus": "winding_down",
        "suggestions": [
            "Start winding down — lower lights, less screen time",
            "Review what you accomplished today (even small things count)",
            "Plan 1-3 things for tomorrow (keeps your brain from holding onto them)",
            "Do a quick gratitude practice — 3 things that went well",
            "Set up your space for tomorrow's first task",
        ],
        "intervention_focus": ["reflection", "transition", "preparation"],
    },
    "night": {
        "hours": (21, 5),
        "label": "Night",
        "emoji": "🌙",
        "focus": "rest_and_reflection",
        "suggestions": [
            "Time to let go of today. Write down any lingering thoughts.",
            "Prepare for sleep: dim lights, no screens, calming activity",
            "Reflect on one good moment from today",
            "Tomorrow is a new day. Rest is productive.",
            "Brain dump anything on your mind so you can let it go",
        ],
        "intervention_focus": ["reflection", "sleep_prep", "calming_routine"],
    },
}


class AdaptiveCoach:
    """
    Adaptive coaching engine that adjusts style, interventions, and suggestions
    based on the user's current state, mood, and time context.
    """

    def __init__(self, db_manager=None, state_detector=None):
        self.db = db_manager
        self.state_detector = state_detector

    def get_time_context(self) -> dict:
        """Get time-of-day context for adaptive suggestions."""
        hour = datetime.now(timezone.utc).hour  # Note: consider user's timezone in production

        for period_name, period_config in TIME_BASED_STRATEGIES.items():
            start, end = period_config["hours"]
            if start <= end:
                if start <= hour < end:
                    return {"period": period_name, **period_config}
            else:  # Overnight period (e.g., 21-5)
                if hour >= start or hour < end:
                    return {"period": period_name, **period_config}

        return {"period": "afternoon", **TIME_BASED_STRATEGIES["afternoon"]}

    def get_mood_strategy(self, mood: str) -> dict:
        """Get coaching strategy for a specific mood."""
        return MOOD_STRATEGIES.get(mood, {
            "tone": "warm",
            "interventions": ["check_in", "gentle_support"],
            "task_style": "normal",
            "productivity_goals": True,
            "focus_mode": "standard",
            "messages": ["How are you feeling right now?"],
        })

    def get_coaching_plan(
        self,
        detected_state: dict,
        user_data: Optional[dict] = None,
        mood: Optional[str] = None,
    ) -> dict:
        """
        Generate a comprehensive coaching plan based on detected state, mood, and time.
        Returns adapted tone, interventions, tasks, and UI suggestions.
        """
        state_id = detected_state.get("state", "calm")
        time_context = self.get_time_context()

        # Determine coaching priority
        if detected_state.get("is_crisis", False):
            priority = "crisis"
        elif state_id in ("burnout", "dysregulated"):
            priority = "high"
        elif state_id in ("overwhelmed",):
            priority = "high"
        elif state_id in ("avoidant",):
            priority = "medium"
        else:
            priority = "normal"

        # Build coaching plan
        plan = {
            "priority": priority,
            "state": state_id,
            "time_context": time_context["focus"],
            "time_period": time_context["period"],
            "time_emoji": time_context["emoji"],
            "coaching_tone": detected_state.get("coaching_tone", "warm"),
            "focus_mode": detected_state.get("focus_mode", "standard"),
            "task_size": detected_state.get("task_size", "normal"),
            "ui_mode": detected_state.get("ui_mode", "normal"),
            "interventions": [],
            "messages": [],
            "strategies": detected_state.get("strategies", []),
        }

        # Add mood-specific strategy if mood is provided
        if mood and mood in MOOD_STRATEGIES:
            mood_strat = MOOD_STRATEGIES[mood]
            plan["coaching_tone"] = mood_strat["tone"]
            plan["interventions"].extend(mood_strat["interventions"])
            if mood_strat["messages"]:
                plan["messages"].append(mood_strat["messages"][0])
            if not mood_strat["productivity_goals"]:
                plan["productivity_safe"] = False

        # Add state-specific interventions
        if detected_state.get("adaptations", {}).get("suggested_interventions"):
            plan["interventions"].extend(
                [inv["action"] for inv in detected_state["adaptations"]["suggested_interventions"]]
            )

        # Add time-based suggestions
        plan["time_suggestions"] = time_context.get("suggestions", [])

        # Add state messages
        if detected_state.get("adaptations", {}).get("messages"):
            plan["messages"].extend(detected_state["adaptations"]["messages"])

        return plan

    def adapt_prompt_for_state(self, system_prompt: str, coaching_plan: dict) -> str:
        """
        Adapt the LLM system prompt based on coaching plan.
        Adds instructions for tone, focus, and intervention type.
        """
        additions = []

        time_context = coaching_plan.get("time_context", "")
        time_period = coaching_plan.get("time_period", "")
        time_emoji = coaching_plan.get("time_emoji", "")

        if time_period:
            additions.append(f"[Time Context] It's {time_period}. Focus: {time_context}.")

        tone = coaching_plan.get("coaching_tone", "warm")
        additions.append(f"[Coaching Tone] Use a {tone} tone.")

        if coaching_plan.get("priority") == "crisis":
            additions.append("[CRITICAL] The user is in a crisis state. Emotional safety is the ONLY priority.")

        if coaching_plan.get("task_size") == "micro":
            additions.append("[Task Size] Suggest ONLY micro-tasks (1-2 minutes). Nothing larger.")

        if not coaching_plan.get("productivity_safe", True):
            additions.append("[Productivity] Do NOT suggest productivity goals. Focus on rest and emotional support.")

        if coaching_plan.get("messages"):
            additions.append(f"[Suggested Message] {coaching_plan['messages'][0]}")

        if coaching_plan.get("interventions"):
            additions.append(f"[Intervention Focus] {', '.join(coaching_plan['interventions'][:3])}")

        if additions:
            return system_prompt + "\n\n" + "\n".join(additions)

        return system_prompt

    def get_system_prompt_extension(self, text: str, context: Optional[dict] = None,
                                    mood: Optional[str] = None) -> str:
        """Generate a system prompt extension combining state detection, mood, and time awareness."""
        if not self.state_detector:
            return ""

        detection_result = self.state_detector.analyze(text, context)
        coaching_plan = self.get_coaching_plan(detection_result, context, mood)

        parts = []
        # State info
        parts.append(
            f"[Adaptive Coach] State: {detection_result['state_label']} | "
            f"Tone: {coaching_plan['coaching_tone']} | "
            f"Time: {coaching_plan['time_emoji']} {coaching_plan['time_period']}"
        )

        # Priority
        if coaching_plan["priority"] == "crisis":
            parts.append("[CRITICAL] Crisis mode — emotional safety only. No tasks. No productivity.")

        # Focus mode
        parts.append(f"[Focus Mode] {coaching_plan['focus_mode']}")

        # Coaching instructions
        if coaching_plan["messages"]:
            parts.append(f"[Coach Message] {coaching_plan['messages'][0]}")

        if coaching_plan["strategies"]:
            parts.append(f"[Strategies] {', '.join(coaching_plan['strategies'][:3])}")

        return "\n".join(parts)
