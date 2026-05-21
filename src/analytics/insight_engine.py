"""
Insight Engine
==============
Generates actionable behavioral insights from user data,
memory patterns, and ML model outputs.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Optional

logger = logging.getLogger(__name__)


class InsightEngine:
    """
    Generates behavioral insights based on user patterns.
    Insights are personalized, actionable, and ADHD-aware.
    """

    def __init__(self, memory=None):
        self.memory = memory
        self._insight_templates = self._build_templates()

    def _build_templates(self) -> dict:
        """Build insight generation templates for different domains."""
        return {
            "focus": {
                "peak_hours": {
                    "pattern": "peak_focus_window",
                    "template": "Your focus is strongest between {hours}. Schedule important tasks during this window.",
                    "condition": lambda data: len(data.get("best_hours", [])) > 0,
                },
                "low_energy": {
                    "pattern": "low_energy_pattern",
                    "template": "Your energy tends to dip around {hours}. Plan lighter tasks or breaks during this time.",
                    "condition": lambda data: len(data.get("worst_hours", [])) > 0,
                },
                "session_length": {
                    "pattern": "optimal_session_length",
                    "template": "Your optimal focus session length is {minutes} minutes. Longer sessions may lead to diminishing returns.",
                    "condition": lambda data: data.get("optimal_length", 0) > 0,
                },
            },
            "sleep": {
                "sleep_productivity_link": {
                    "pattern": "sleep_productivity_correlation",
                    "template": "Sleep under 6 hours is linked to {percent}% lower productivity for you. Prioritizing sleep could significantly boost your focus.",
                    "condition": lambda data: data.get("sleep_hours", 0) > 0,
                },
                "sleep_stress_link": {
                    "pattern": "sleep_stress_correlation",
                    "template": "Low sleep nights ({hours}h) tend to increase your stress by {points} points the next day.",
                    "condition": lambda data: data.get("sleep_hours", 0) > 0,
                },
            },
            "productivity": {
                "morning_vs_evening": {
                    "pattern": "productivity_time_comparison",
                    "template": "You tend to be most productive during {time_of_day} hours. Try scheduling your most challenging work then.",
                    "condition": lambda data: True,
                },
                "task_completion": {
                    "pattern": "task_completion_rate",
                    "template": "Your task completion rate is {rate}%. Breaking tasks into smaller pieces could help improve this.",
                    "condition": lambda data: data.get("completion_rate", 0) > 0,
                },
            },
            "stress": {
                "stress_trend": {
                    "pattern": "stress_trend_analysis",
                    "template": "Your stress levels have been {trend} over the past week. {recommendation}",
                    "condition": lambda data: data.get("avg_stress", 0) > 0,
                },
                "stress_triggers": {
                    "pattern": "stress_triggers",
                    "template": "Phone distractions beyond {hours}h/day consistently increase your stress. Try setting screen time limits.",
                    "condition": lambda data: data.get("phone_hours", 0) > 0,
                },
            },
        }

    def generate_insights(self, user_profile: dict) -> list:
        """Generate insights from user profile data."""
        insights = []

        # Focus insights
        focus = user_profile.get("focus_patterns", {})
        focus_data = {
            "best_hours": focus.get("best_focus_hours", []),
            "worst_hours": focus.get("worst_focus_hours", []),
            "optimal_length": focus.get("optimal_session_length_minutes", 25),
        }

        # Peak hours
        if focus_data["best_hours"]:
            insights.append({
                "type": "focus",
                "category": "peak_focus_window",
                "message": f"Your focus is strongest around {', '.join(focus_data['best_hours'][:2])}. "
                          f"Try scheduling your most important work during these times.",
                "confidence": "high",
                "actionable": True,
                "suggested_action": f"Block out time around {focus_data['best_hours'][0]} for deep work.",
            })

        # Optimal session length
        if focus_data["optimal_length"]:
            insights.append({
                "type": "focus",
                "category": "optimal_session_length",
                "message": f"Your optimal focus session is about {focus_data['optimal_length']} minutes. "
                          f"Taking breaks after this duration can help maintain quality.",
                "confidence": "medium",
                "actionable": True,
                "suggested_action": f"Set your focus timer to {focus_data['optimal_length']} minutes.",
            })

        # Productivity insights
        task_patterns = user_profile.get("task_patterns", {})
        completion_rate = task_patterns.get("completion_rate", 0)
        if completion_rate > 0:
            rate_pct = round(completion_rate * 100)
            if rate_pct < 40:
                insights.append({
                    "type": "productivity",
                    "category": "task_completion",
                    "message": f"Your task completion rate is {rate_pct}%. "
                              f"Tasks might be too big — try breaking them into 5-minute chunks.",
                    "confidence": "high",
                    "actionable": True,
                    "suggested_action": "Use the '2-minute rule' for your next task.",
                })
            elif rate_pct > 75:
                insights.append({
                    "type": "productivity",
                    "category": "task_completion",
                    "message": f"Excellent task completion at {rate_pct}%! "
                              f"You're building strong consistency.",
                    "confidence": "high",
                    "actionable": False,
                })

        # Emotional insights
        emotional = user_profile.get("emotional_patterns", {})
        mood_trend = emotional.get("mood_trend", [])
        if len(mood_trend) >= 3:
            recent_moods = mood_trend[-3:]
            avg_stress = sum(m.get("stress", 5) for m in recent_moods) / len(recent_moods)
            if avg_stress >= 7:
                insights.append({
                    "type": "stress",
                    "category": "elevated_stress",
                    "message": f"Your stress has been consistently high (avg {avg_stress:.0f}/10). "
                              f"Consider a recovery day with minimal demands.",
                    "confidence": "high",
                    "actionable": True,
                    "suggested_action": "Schedule a 'low-demand' day to reset.",
                })

        # Session summary insights
        summary = user_profile.get("session_summary", {})
        total_sessions = summary.get("total_sessions", 0)
        if total_sessions > 5:
            insights.append({
                "type": "engagement",
                "category": "consistent_engagement",
                "message": f"You've had {total_sessions} coaching sessions. "
                          f"Consistent engagement is one of the strongest predictors of improvement.",
                "confidence": "medium",
                "actionable": False,
            })

        # Check for stored insights already in profile
        existing_insights = user_profile.get("insights", [])
        for existing in existing_insights:
            insights.append({
                "type": "stored",
                "category": "previous_insight",
                "message": existing,
                "confidence": "medium",
                "actionable": True,
            })

        # Deduplicate by message
        seen_messages = set()
        unique_insights = []
        for insight in insights:
            if insight["message"] not in seen_messages:
                seen_messages.add(insight["message"])
                unique_insights.append(insight)

        return unique_insights[:10]

    def format_insights_for_prompt(self, user_profile: dict) -> str:
        """Format insights for AI prompt injection."""
        insights = self.generate_insights(user_profile)
        if not insights:
            return ""

        lines = ["[BEHAVIORAL INSIGHTS]"]
        for insight in insights:
            lines.append(f"- {insight['message']}")
            if insight.get("suggested_action"):
                lines.append(f"  → Try: {insight['suggested_action']}")

        return "\n".join(lines)

    def get_insight_summary_text(self, user_profile: dict) -> str:
        """Generate a quick summary of key insights."""
        insights = self.generate_insights(user_profile)
        if not insights:
            return "No insights available yet. Continue using the coach to generate personalized insights."

        # Pick top 3 most impactful insights
        priority_insights = [i for i in insights if i.get("actionable")][:3]

        summary = "📊 Your Key Insights:\n\n"
        for insight in priority_insights:
            summary += f"• {insight['message']}\n"
            if insight.get("suggested_action"):
                summary += f"  💡 {insight['suggested_action']}\n"
            summary += "\n"

        return summary
