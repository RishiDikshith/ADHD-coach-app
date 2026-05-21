"""
Pattern Analyzer
================
Analyzes behavioral patterns from user data, focus sessions,
and emotional trends to identify meaningful patterns.
"""

import logging
from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Optional

logger = logging.getLogger(__name__)


class PatternAnalyzer:
    """
    Analyzes user data to identify behavioral patterns.
    Focuses on ADHD-relevant patterns like focus windows,
    energy cycles, procrastination triggers, and burnout signals.
    """

    def __init__(self, memory=None):
        self.memory = memory

    def analyze_focus_patterns(self, focus_data: list) -> dict:
        """Analyze focus session data for patterns."""
        if not focus_data:
            return {"pattern_detected": False}

        # Extract hours and quality scores
        hour_quality = {}
        for session in focus_data:
            hour = session.get("hour", 0)
            quality = session.get("quality_score", 5)
            if hour not in hour_quality:
                hour_quality[hour] = []
            hour_quality[hour].append(quality)

        # Average quality by hour
        avg_by_hour = {
            hour: sum(scores) / len(scores)
            for hour, scores in hour_quality.items()
        }

        # Find best and worst hours (with enough data)
        best_hours = [
            hour for hour, avg in sorted(avg_by_hour.items(), key=lambda x: x[1], reverse=True)
            if len(hour_quality[hour]) >= 2
        ][:3]

        worst_hours = [
            hour for hour, avg in sorted(avg_by_hour.items(), key=lambda x: x[1])
            if len(hour_quality[hour]) >= 2
        ][:3]

        # Calculate consistency score
        if len(focus_data) >= 5:
            recent = focus_data[-5:]
            qualities = [s.get("quality_score", 5) for s in recent]
            consistency = 1 - (max(qualities) - min(qualities)) / 10
        else:
            consistency = 0.5

        return {
            "pattern_detected": len(avg_by_hour) > 0,
            "best_focus_hours": [f"{h:02d}:00" for h in best_hours],
            "worst_focus_hours": [f"{h:02d}:00" for h in worst_hours],
            "peak_hour": f"{best_hours[0]:02d}:00" if best_hours else None,
            "quality_by_hour": avg_by_hour,
            "consistency_score": round(consistency, 2),
            "total_sessions_analyzed": len(focus_data),
        }

    def analyze_mood_patterns(self, mood_data: list) -> dict:
        """Analyze emotional/mood patterns."""
        if not mood_data:
            return {"pattern_detected": False}

        # Stress trend
        recent = mood_data[-10:] if len(mood_data) >= 10 else mood_data
        stress_values = [m.get("stress", 5) for m in recent]

        if len(stress_values) >= 3:
            first_half = sum(stress_values[:len(stress_values)//2]) / max(len(stress_values)//2, 1)
            second_half = sum(stress_values[len(stress_values)//2:]) / max(len(stress_values) - len(stress_values)//2, 1)
            trend = "increasing" if second_half > first_half + 0.5 else \
                    "decreasing" if second_half < first_half - 0.5 else "stable"
        else:
            trend = "insufficient_data"

        # Common emotions
        emotions = [m.get("mood", "neutral") for m in mood_data]
        emotion_counts = Counter(emotions)
        dominant_emotions = emotion_counts.most_common(3)

        return {
            "pattern_detected": len(mood_data) >= 3,
            "stress_trend": trend,
            "avg_stress": round(sum(stress_values) / len(stress_values), 1),
            "stress_range": (min(stress_values), max(stress_values)),
            "dominant_emotions": [
                {"emotion": e, "count": c, "percentage": round(c / len(emotions) * 100)}
                for e, c in dominant_emotions
            ],
            "entries_analyzed": len(mood_data),
        }

    def analyze_productivity_correlations(self, user_data: dict) -> list:
        """Find correlations between lifestyle factors and productivity."""
        correlations = []

        sleep = user_data.get("sleep_hours", 0)
        stress = user_data.get("stress_level", 5)
        phone = user_data.get("phone_distractions", 0)

        # Sleep correlation
        if sleep < 6 and stress >= 6:
            correlations.append({
                "factor": "sleep",
                "correlation": "negative",
                "strength": "strong",
                "insight": "Low sleep appears linked to higher stress levels.",
                "suggestion": "Prioritize 7-8 hours of sleep to improve stress management.",
            })

        # Phone distractions
        if phone > 4:
            correlations.append({
                "factor": "phone_distractions",
                "correlation": "negative",
                "strength": "strong",
                "insight": "High phone distraction hours may be reducing focus capacity.",
                "suggestion": "Try phone-free focus blocks using the 'phone in another room' method.",
            })

        # Sleep-productivity link
        if sleep >= 7 and stress <= 4:
            correlations.append({
                "factor": "sleep_stress_balance",
                "correlation": "positive",
                "strength": "positive",
                "insight": "Good sleep and low stress create optimal conditions for productivity.",
                "suggestion": "This is your peak state. Use it for your most important tasks!",
            })

        return correlations

    def analyze_temporal_patterns(self, activity_log: list) -> dict:
        """Analyze patterns based on time of day / day of week."""
        if not activity_log:
            return {"pattern_detected": False}

        hour_activity = Counter()
        day_activity = Counter()
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        for entry in activity_log:
            try:
                ts = entry.get("timestamp", "")
                if isinstance(ts, str):
                    dt = datetime.fromisoformat(ts)
                    hour_activity[dt.hour] += 1
                    day_activity[dt.weekday()] += 1
            except (ValueError, TypeError):
                continue

        if not hour_activity:
            return {"pattern_detected": False}

        most_active_hour = hour_activity.most_common(1)[0][0]
        most_active_day = day_activity.most_common(1)[0][0] if day_activity else None

        time_of_day = "morning" if 5 <= most_active_hour < 12 else \
                      "afternoon" if 12 <= most_active_hour < 17 else \
                      "evening" if 17 <= most_active_hour < 21 else "night"

        return {
            "pattern_detected": True,
            "most_active_hour": most_active_hour,
            "most_active_time_of_day": time_of_day,
            "most_active_day": day_names[most_active_day] if most_active_day is not None else None,
            "hour_distribution": dict(hour_activity.most_common(8)),
        }

    def get_summary_insights(self, user_profile: dict) -> list:
        """Get a comprehensive summary of all patterns."""
        insights = []

        focus_patterns = user_profile.get("focus_patterns", {})
        focus_analysis = self.analyze_focus_patterns(
            focus_patterns.get("focus_quality_trend", [])
        )
        if focus_analysis.get("pattern_detected"):
            if focus_analysis.get("best_focus_hours"):
                insights.append({
                    "type": "timing",
                    "message": f"Best focus time: {', '.join(focus_analysis['best_focus_hours'][:2])}",
                    "action": "Schedule deep work during these windows",
                })

        mood_patterns = user_profile.get("emotional_patterns", {})
        mood_analysis = self.analyze_mood_patterns(
            mood_patterns.get("mood_trend", [])
        )
        if mood_analysis.get("pattern_detected"):
            insights.append({
                "type": "stress",
                "message": f"Stress trend: {mood_analysis['stress_trend']} (avg {mood_analysis['avg_stress']}/10)",
                "action": "Adjust daily demands based on stress trend",
            })

        return insights
