"""
Recommendation Engine
=====================
Generates actionable, personalized recommendations based on
behavioral insights and pattern analysis.
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Generates actionable recommendations for ADHD users based on
    their behavioral data, patterns, and current context.
    """

    def __init__(self, memory=None):
        self.memory = memory

    def generate_recommendations(self, context: dict, user_profile: dict = None) -> list:
        """Generate personalized recommendations based on context and profile."""
        recommendations = []
        session = context.get("session", {})
        user = context.get("user", {})

        stress = session.get("current_stress", 5)
        energy = session.get("current_energy", 5)
        mood = session.get("current_mood", "neutral")
        completion_rate = user.get("task_completion_rate", 50)

        # Stress-based recommendations
        if stress >= 7:
            recommendations.append({
                "type": "immediate",
                "category": "stress_management",
                "priority": "high",
                "title": "Reduce Stress",
                "description": "Your stress is elevated. Prioritize calming activities.",
                "actions": [
                    "Take 5 slow, deep breaths",
                    "Step away from your current task for 10 minutes",
                    "Drink a glass of cold water slowly",
                    "Do a quick body scan — release tension in your shoulders and jaw",
                ],
                "reason": "High stress impairs executive function significantly.",
            })

        # Energy-based recommendations
        if energy <= 3:
            recommendations.append({
                "type": "immediate",
                "category": "energy_management",
                "priority": "high",
                "title": "Conserve Energy",
                "description": "Your energy is low. Focus on restoration, not productivity.",
                "actions": [
                    "Switch to a low-effort task or take a break",
                    "Have a healthy snack to stabilize blood sugar",
                    "Try the '5-minute power nap' (set a timer!)",
                    "Do a gentle stretch or short walk",
                ],
                "reason": "Working against low energy leads to burnout and reduced quality.",
            })

        # Task completion recommendations
        if completion_rate < 40:
            recommendations.append({
                "type": "habit",
                "category": "task_management",
                "priority": "medium",
                "title": "Improve Task Completion",
                "description": "Tasks may be too large. Break them down further.",
                "actions": [
                    "Use the '2-minute rule' — do just 2 minutes of any task",
                    "Break your current task into 3 smaller steps",
                    "Set a specific timer for each micro-task",
                    "Celebrate each tiny completion — even opening the file counts!",
                ],
                "reason": "Small wins build momentum and dopamine for ADHD brains.",
            })

        # Focus optimization
        best_hours = user.get("best_focus_hours", [])
        if best_hours:
            recommendations.append({
                "type": "planning",
                "category": "focus_optimization",
                "priority": "medium",
                "title": "Optimize Focus Timing",
                "description": f"Schedule deep work during your peak windows: {', '.join(best_hours[:2])}",
                "actions": [
                    f"Block out time around {best_hours[0]} for important tasks",
                    "Protect this time from meetings and notifications",
                    "Prepare your workspace before your peak window starts",
                    "Start with the hardest task during peak focus time",
                ],
                "reason": "Aligning tasks with natural energy cycles improves output quality and reduces effort.",
            })

        # Mood-based recommendations
        if mood in ["anxious", "stressed", "overwhelmed"]:
            recommendations.append({
                "type": "immediate",
                "category": "emotional_support",
                "priority": "high" if stress >= 7 else "medium",
                "title": "Emotional Regulation",
                "description": "Grounding techniques can help reset your nervous system.",
                "actions": [
                    "Try the 5-4-3-2-1 grounding technique",
                    "Name your feeling without judgment: 'I notice I'm feeling...'",
                    "Put your hand on your chest and breathe slowly",
                    "Remind yourself: 'This feeling is temporary'",
                ],
                "reason": "Emotional regulation is a core executive function challenge for ADHD.",
            })

        # General wellness recommendations
        recommendations.append({
            "type": "wellness",
            "category": "daily_habits",
            "priority": "low",
            "title": "Daily Wellness Check",
            "description": "Small daily habits create the foundation for good executive function.",
            "actions": [
                "Have you had water recently? Drink a glass now.",
                "When did you last eat? A protein-rich snack helps focus.",
                "Have you moved your body today? Even 5 minutes counts.",
                "When did you last take a screen break? Give your eyes 20 seconds.",
            ],
            "reason": "Basic needs directly impact ADHD symptom severity.",
        })

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda r: priority_order.get(r.get("priority", "low"), 3))

        return recommendations

    def format_for_display(self, recommendations: list, max_items: int = 3) -> str:
        """Format recommendations for display in the UI."""
        if not recommendations:
            return "✨ No specific recommendations right now. Keep up the good work!"

        lines = ["📋 Personalized Recommendations:\n"]
        for rec in recommendations[:max_items]:
            priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}
            icon = priority_icon.get(rec.get("priority", "low"), "⚪")

            lines.append(f"{icon} **{rec['title']}**")
            lines.append(f"   {rec['description']}")
            for action in rec["actions"][:2]:
                lines.append(f"   • {action}")
            lines.append(f"   💡 {rec['reason']}")
            lines.append("")

        return "\n".join(lines)

    def get_priority_recommendations(self, context: dict, user_profile: dict = None) -> list:
        """Get only high-priority recommendations."""
        all_recs = self.generate_recommendations(context, user_profile)
        return [r for r in all_recs if r.get("priority") == "high"]

    def get_recommendation_for_prompt(self, context: dict) -> str:
        """Get a formatted recommendation block for AI prompt injection."""
        recs = self.generate_recommendations(context)
        if not recs:
            return ""

        # Only include high priority in the prompt
        high_priority = [r for r in recs if r.get("priority") in ("high", "medium")][:2]
        if not high_priority:
            return ""

        lines = ["[PERSONALIZED RECOMMENDATIONS]"]
        for rec in high_priority:
            lines.append(f"Priority ({rec['priority']}): {rec['title']}")
            lines.append(f"Reason: {rec['reason']}")
            lines.append(f"Suggested actions: {'; '.join(rec['actions'][:2])}")

        return "\n".join(lines)
