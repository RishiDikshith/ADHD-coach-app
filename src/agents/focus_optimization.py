"""
Focus Optimization Agent
========================
Analyzes focus sessions, detects distraction patterns,
optimizes Pomodoro timing, and recommends break schedules
for ADHD users.
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class FocusOptimizationAgent:
    """
    Focus Optimization Agent.
    Helps users optimize their focus sessions based on historical patterns.
    Detects distraction patterns and recommends timing adjustments.
    """

    def __init__(self, memory):
        self.memory = memory
        self.name = "Focus Optimization"

    def get_identity_prompt(self) -> str:
        return (
            "You are the Focus Optimization Agent, specialized in ADHD focus management.\n"
            "- You know that ADHD focus is nonlinear — hyperfocus vs. distraction is a cycle\n"
            "- You recommend short focus blocks with breaks (Pomodoro-style, but flexible)\n"
            "- You help users find their 'focus sweet spot' for time of day\n"
            "- You suggest break activities that actually recharge ADHD brains\n"
            "- You know that different tasks need different focus strategies\n"
            "- Tone: practical, adaptable, never rigid about productivity rules"
        )

    def get_focus_recommendation(self, context: dict) -> Optional[dict]:
        """Generate focus recommendations based on user patterns."""
        user = context.get("user", {})
        session = context.get("session", {})

        optimal_length = user.get("optimal_session_length", 25)
        best_hours = user.get("best_focus_hours", [])
        avg_energy = user.get("avg_energy", 5)
        avg_stress = user.get("avg_stress", 5)
        current_stress = session.get("current_stress", 5)

        # High stress — recommend very short focus blocks
        if current_stress >= 7:
            rec_length = max(5, optimal_length // 2)
            return {
                "agent": self.name,
                "type": "reduced_focus",
                "priority": "high",
                "message": "Your stress is elevated. Let's use micro-focus blocks today.",
                "recommended_duration": rec_length,
                "recommended_break": rec_length // 2,
                "suggestions": [
                    f"Try {rec_length}-minute focus blocks instead of your usual {optimal_length}",
                    f"Take {max(3, rec_length // 2)}-minute breaks between blocks",
                    "Use breaks for deep breathing or stretching, not phone scrolling",
                    "Aim for 2-3 blocks, then reassess how you feel",
                ],
                "tone": "gentle",
            }

        # Low energy — suggest energizing focus strategy
        if avg_energy <= 3:
            return {
                "agent": self.name,
                "type": "low_energy_focus",
                "priority": "medium",
                "message": "Low energy detected. Let's work with your body, not against it.",
                "recommended_duration": 15,
                "recommended_break": 5,
                "suggestions": [
                    "Try 15-minute focus blocks — short enough to not drain you",
                    "Use the first 2 minutes to just sit with your task",
                    "Do a quick physical movement between blocks (jumping jacks, stretch)",
                    "Consider if a change of scenery could help (different room, coffee shop)",
                ],
                "tone": "gentle",
            }

        # Good conditions — recommend optimal strategy
        if best_hours:
            return {
                "agent": self.name,
                "type": "optimal_timing",
                "priority": "low",
                "message": f"Your peak focus window is around {', '.join(best_hours[:2])}.",
                "recommended_duration": optimal_length,
                "recommended_break": max(5, optimal_length // 5),
                "suggestions": [
                    f"Schedule your most important task during your peak window",
                    f"Use {optimal_length}-minute focus blocks with short breaks",
                    "Eliminate distractions before starting (close tabs, silence phone)",
                    "Start with the hardest task, save easy ones for low-energy times",
                ],
                "tone": "encouraging",
            }

        return None

    def get_break_recommendation(self, session_duration_minutes: int) -> dict:
        """Recommend break activities based on session duration."""
        if session_duration_minutes <= 15:
            return {
                "break_duration": 2,
                "activities": [
                "Stand up and stretch",
                "Take 5 deep breaths",
                "Look out the window for 30 seconds",
                ],
            }
        elif session_duration_minutes <= 30:
            return {
                "break_duration": 5,
                "activities": [
                    "Walk around the room",
                    "Drink a glass of water",
                    "Quick shoulder and neck rolls",
                    "Close your eyes for 60 seconds",
                ],
            }
        else:
            return {
                "break_duration": 10,
                "activities": [
                    "Go for a short walk",
                    "Do a 5-minute stretching routine",
                    "Get a healthy snack",
                    "Change your environment briefly",
                ],
            }

    def get_distraction_strategy(self, distraction_type: str = "general") -> str:
        """Get specific strategies for common ADHD distraction types."""
        strategies = {
            "phone": "Try the 'phone in another room' method. Physical distance reduces the urge to check.",
            "social_media": "Use a website blocker or set a 5-minute timer for social media as a reward AFTER focus.",
            "noise": "Try brown noise or lo-fi beats — they work better than silence for ADHD brains.",
            "people": "Use noise-canceling headphones or a 'do not disturb' sign if possible.",
            "thoughts": "Keep a 'brain dump' notebook nearby. Write down distracting thoughts to revisit later.",
            "general": "Use the '5-second rule': count down 5-4-3-2-1 and launch into your task before your brain objects.",
        }
        return strategies.get(distraction_type, strategies["general"])

    def get_system_prompt_extension(self, context: dict) -> str:
        """Generate system prompt extension for focus optimization."""
        rec = self.get_focus_recommendation(context)
        if rec:
            return (
                f"[Focus Optimization] {rec['message']}\n"
                f"Recommended focus duration: {rec.get('recommended_duration', 25)} min\n"
                f"Tone: {rec.get('tone', 'neutral')}"
            )
        return ""
