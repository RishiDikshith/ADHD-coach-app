"""
Habit Builder Agent
===================
Specializes in streak reinforcement, behavioral consistency,
and ADHD-friendly habit recommendations.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Optional

logger = logging.getLogger(__name__)


class HabitBuilderAgent:
    """
    Habit Builder Agent.
    Helps users build and maintain habits using ADHD-friendly strategies.
    Focuses on streak reinforcement, habit stacking, and consistency.
    """

    def __init__(self, memory):
        self.memory = memory
        self.name = "Habit Builder"

    def get_identity_prompt(self) -> str:
        return (
            "You are the Habit Builder Agent, specialized in ADHD habit formation.\n"
            "- You know traditional habit advice often fails for ADHD brains\n"
            "- You focus on 'habit anchoring' — attaching new habits to existing ones\n"
            "- You celebrate streaks but NEVER shame for breaking them\n"
            "- You recommend starting with ridiculously small habits\n"
            "- You know that consistency > intensity for ADHD\n"
            "- Tone: patient, encouraging, gamified, non-judgmental"
        )

    def get_identity_prompt_extended(self) -> str:
        return (
            "Habit formation for ADHD:\n"
            "1. Start microscopic — 'floss one tooth' not 'floss every day'\n"
            "2. Habit stacking — attach new habit to existing one ('after I make coffee, I will...')\n"
            "3. Environment design — make good habits easy, bad habits hard\n"
            "4. Celebrate immediately — dopamine reward after every small win\n"
            "5. Never miss twice — one skip is okay, two in a row is a pattern\n"
            "6. Use external accountability — body doubling, check-ins, visible tracking"
        )

    def get_habit_recommendation(self, context: dict, habits: list = None) -> Optional[dict]:
        """
        Suggest habit improvements based on user patterns.
        """
        user = context.get("user", {})
        session = context.get("session", {})

        stress = session.get("current_stress", 5)
        energy = session.get("current_energy", 5)
        completion_rate = user.get("task_completion_rate", 50)
        current_streak = user.get("session_count", 0)

        existing_habits = habits or []

        # No habits yet — suggest starting with one
        if not existing_habits:
            return {
                "agent": self.name,
                "type": "habit_intro",
                "priority": "medium",
                "message": "Building habits starts with ONE small step. Let's start tiny!",
                "suggestions": [
                    "📌 Pick ONE habit that would make the biggest difference",
                    "🎯 Make it so small you can't fail: 'put on my walking shoes' not 'walk for 30 min'",
                    "🔗 Anchor it to something you already do daily (e.g., after brushing teeth)",
                    "✅ Track it with a simple checkmark — no apps needed",
                    "🎉 Celebrate every single time you do it",
                ],
                "starting_habit": "2-minute clean-up after meals",
                "tone": "encouraging",
            }

        # Has habits — suggest optimization
        if completion_rate < 40:
            return {
                "agent": self.name,
                "type": "habit_adjustment",
                "priority": "high",
                "message": "Your habits might be too big. Let's shrink them!",
                "suggestions": [
                    "✂️ Make each habit 50% smaller — literally halve it",
                    "🔄 Review your habit anchors — are they reliable daily triggers?",
                    "📉 If you missed a habit, just do a 'micro version' (30 seconds)",
                    "🗑️ Consider dropping a habit that's not working — focus on one",
                    "⭐ Celebrate that you're tracking — awareness is the first win",
                ],
                "tone": "gentle",
            }

        # Doing well — suggest leveling up
        return {
            "agent": self.name,
            "type": "habit_optimization",
            "priority": "low",
            "message": "You're doing great with consistency! Let's level up.",
            "suggestions": [
                "📈 Gradually increase habit difficulty by 10% (not 100%)",
                "🔗 Try habit stacking: chain 2-3 small habits together",
                "📊 Review which habits give you the most energy vs drain it",
                "🏆 Set a 'streek saver' — minimum viable version of each habit",
            ],
            "tone": "congratulatory",
        }

    def get_streak_milestone_message(self, streak: int) -> Optional[str]:
        """Generate celebratory message for streak milestones."""
        milestones = {
            1: "🌟 Day 1! The most important day. You showed up!",
            3: "🔥 3-day streak! You're building momentum!",
            5: "⭐ 5 days! Consistency is taking shape!",
            7: "🏆 One week! You're officially building a habit!",
            10: "💪 10 days! Almost 2 weeks of consistency!",
            14: "🎯 2 weeks! Your brain is rewiring!",
            21: "🚀 21 days! Science says habits are forming!",
            30: "👑 30 days! One month of dedication!",
            50: "🌟 50 days! You're a habit machine!",
            100: "🏅 100 days! Elite consistency level!",
        }

        # Check exact milestones
        if streak in milestones:
            return milestones[streak]

        # Check nearby milestones
        for milestone in [7, 14, 21, 30, 50, 100]:
            if abs(streak - milestone) <= 2:
                return f"🎯 Almost at {milestone} days! Keep going — you're so close!"

        return None

    def get_habit_stacking_suggestion(self, new_habit: str, existing_routine: list = None) -> str:
        """Suggest how to stack a new habit onto existing routines."""
        if existing_routine is None:
            existing_routine = [
                "morning coffee/tea",
                "brushing teeth",
                "after meals",
                "before bed",
                "after using phone",
            ]

        anchors = existing_routine[:3]
        return (
            f"To build '{new_habit}', try stacking it onto one of your existing routines:\n"
            + "\n".join([f"• After [routine], I will [new habit for 1 minute]" for routine in anchors])
        )

    def get_system_prompt_extension(self, context: dict, current_streak: int = 0) -> str:
        """Generate system prompt extension for habit context."""
        parts = []

        milestone = self.get_streak_milestone_message(current_streak)
        if milestone:
            parts.append(f"[Habit Milestone] {milestone}")

        rec = self.get_habit_recommendation(context)
        if rec:
            parts.append(f"[Habit Recommendation] {rec['message']}")

        return "\n".join(parts)
