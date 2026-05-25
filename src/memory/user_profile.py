"""
User Profile module for ADHD pattern tracking.
Tracks behavioral patterns, preferences, and historical data
to personalize the ADHD coaching experience.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class UserProfile:
    """
    Lightweight user profile that tracks ADHD-relevant patterns.
    Persists to a JSON file per user.

    Tracks:
      - Focus patterns (best hours, optimal session length)
      - Procrastination triggers (learned from chat)
      - Burnout history (stress levels over time)
      - Preferred work styles
      - Emotional patterns
      - Successful interventions (what worked)
      - Energy patterns throughout day
      - Task completion patterns
    """

    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.profile_dir = Path(".user_profiles")
        self.profile_dir.mkdir(exist_ok=True)
        self.profile_path = self.profile_dir / f"{user_id}.json"

        # Core profile data
        self.data: dict[str, Any] = {
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),

            # ADHD-specific profile
            "adhd_type": None,  # inattentive, hyperactive, combined, unknown
            "primary_challenges": [],  # e.g., ["task_initiation", "focus_maintenance", "time_blindness"]
            "strengths": [],  # e.g., ["hyperfocus", "creativity", "problem_solving"]
            "cognitive_styles": [],  # e.g. ["hyperfocus_driven", "crisis_motivated", "body_double_preferred"]
            "interests": [],  # e.g. ["programming", "music"]

            # Focus patterns
            "focus_patterns": {
                "best_focus_hours": [],  # e.g., ["09:00", "10:00", "22:00", "23:00"]
                "worst_focus_hours": [],
                "optimal_session_length_minutes": 25,
                "focus_quality_trend": [],  # list of {date, quality_score, session_length}
            },

            # Procrastination
            "procrastination_triggers": {
                "common_triggers": [],  # e.g., ["large_tasks", "administrative_work"]
                "avoidance_patterns": [],  # e.g., ["social_media", "snacking"]
                "task_types_avoided": [],
            },

            # Emotional patterns
            "emotional_patterns": {
                "mood_trend": [],  # list of {date, mood, energy, stress}
                "common_emotions": [],
                "burnout_indicators": [],
            },

            # Intervention effectiveness
            "intervention_history": {
                "successful_interventions": [],  # what worked
                "failed_interventions": [],  # what didn't
                "preferred_intervention_style": "gentle",  # gentle, direct, energetic
            },

            # Energy patterns
            "energy_patterns": {
                "peak_energy_times": [],
                "low_energy_times": [],
                "sleep_sensitivity": "moderate",  # how strongly sleep affects next day
            },

            # Task patterns
            "task_patterns": {
                "completion_rate": 0.0,
                "preferred_task_size": "small",  # small, medium, large
                "break_frequency_minutes": 30,
                "distraction_factors": [],
            },

            # User preferences
            "preferences": {
                "coach_tone": "empathetic",  # empathetic, direct, energetic
                "focus_area": "time_management",  # primary area of focus
                "language": "en",
                "notification_preference": "gentle_reminders",
            },

            # Session history summary
            "session_summary": {
                "total_sessions": 0,
                "total_chat_messages": 0,
                "total_focus_minutes": 0,
                "current_streak": 0,
                "highest_streak": 0,
                "badges_earned": [],
            },

            # Behavioral insights (computed by analytics engine)
            "insights": [],
        }

        self._load()

    # ---------- Persistence ----------

    def _load(self):
        """Load profile from disk."""
        if self.profile_path.exists():
            try:
                with open(self.profile_path) as f:
                    saved = json.load(f)
                # Merge saved data into default structure
                self._deep_merge(self.data, saved)
                logger.debug(f"Loaded profile for user: {self.user_id}")
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Failed to load profile: {e}")

    def save(self):
        """Persist profile to disk."""
        self.data["updated_at"] = datetime.now().isoformat()
        try:
            with open(self.profile_path, "w") as f:
                json.dump(self.data, f, indent=2)
        except OSError as e:
            logger.error(f"Failed to save profile: {e}")

    @staticmethod
    def _deep_merge(base: dict, override: dict):
        """Recursively merge override into base dict."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                UserProfile._deep_merge(base[key], value)
            else:
                base[key] = value

    # ---------- Pattern tracking ----------

    def record_focus_session(self, duration_minutes: int, quality: int, hour: int):
        """Record a focus session result."""
        patterns = self.data["focus_patterns"]
        quality = max(1, min(10, quality))

        patterns["focus_quality_trend"].append({
            "date": datetime.now().date().isoformat(),
            "quality_score": quality,
            "session_length": duration_minutes,
            "hour": hour,
        })

        # Update best/worst hours
        if quality >= 7:
            hour_str = f"{hour:02d}:00"
            if hour_str not in patterns["best_focus_hours"]:
                patterns["best_focus_hours"].append(hour_str)
                patterns["best_focus_hours"].sort()

        if quality <= 3:
            hour_str = f"{hour:02d}:00"
            if hour_str not in patterns["worst_focus_hours"]:
                patterns["worst_focus_hours"].append(hour_str)
                patterns["worst_focus_hours"].sort()

        # Keep trend manageable (last 30 entries)
        if len(patterns["focus_quality_trend"]) > 30:
            patterns["focus_quality_trend"] = patterns["focus_quality_trend"][-30:]

        # Update session summary
        self.data["session_summary"]["total_focus_minutes"] += duration_minutes

        # Update optimal session length (rolling average)
        recent_sessions = patterns["focus_quality_trend"][-10:]
        if recent_sessions:
            weighted_avg = sum(
                s["session_length"] * s["quality_score"] for s in recent_sessions
            ) / sum(max(s["quality_score"], 1) for s in recent_sessions)
            patterns["optimal_session_length_minutes"] = max(5, min(120, int(weighted_avg)))

        self.save()

    def record_emotion(self, emotion: str, stress: int, energy: Optional[int] = None):
        """Record an emotional data point."""
        patterns = self.data["emotional_patterns"]
        patterns["mood_trend"].append({
            "date": datetime.now().isoformat(),
            "mood": emotion,
            "stress": stress,
            "energy": energy or 5,
        })

        # Track common emotions
        if emotion not in patterns["common_emotions"]:
            patterns["common_emotions"].append(emotion)

        # Keep trend manageable (last 50 entries)
        if len(patterns["mood_trend"]) > 50:
            patterns["mood_trend"] = patterns["mood_trend"][-50:]

        self.save()

    def record_intervention_result(self, intervention: str, success: bool, context: str = ""):
        """Record whether an intervention was effective."""
        history = self.data["intervention_history"]
        entry = {"intervention": intervention, "context": context, "date": datetime.now().isoformat()}

        if success:
            history["successful_interventions"].append(entry)
        else:
            history["failed_interventions"].append(entry)

        # Keep lists manageable
        if len(history["successful_interventions"]) > 50:
            history["successful_interventions"] = history["successful_interventions"][-50:]
        if len(history["failed_interventions"]) > 50:
            history["failed_interventions"] = history["failed_interventions"][-50:]

        self.save()

    def record_procrastination_trigger(self, trigger: str, context: str = ""):
        """Record a common procrastination trigger."""
        triggers = self.data["procrastination_triggers"]["common_triggers"]
        if trigger not in triggers:
            triggers.append(trigger)

        self.save()

    def record_task_completion(self, task_size: str, completed: bool, difficulty: int = 5):
        """Record task completion patterns."""
        patterns = self.data["task_patterns"]
        patterns["completion_rate"] = (
            patterns["completion_rate"] * 0.8 + (1.0 if completed else 0.0) * 0.2
        )
        patterns["preferred_task_size"] = task_size if completed else patterns["preferred_task_size"]

        self.save()

    def update_streak(self, current_streak: int):
        """Update streak information."""
        summary = self.data["session_summary"]
        summary["current_streak"] = current_streak
        if current_streak > summary["highest_streak"]:
            summary["highest_streak"] = current_streak
        self.save()

    def update_preferences(self, preferences: dict):
        """Update user preferences."""
        self.data["preferences"].update(preferences)
        self.save()

    def record_cognitive_style(self, style: str):
        """Record a detected cognitive style."""
        styles = self.data.get("cognitive_styles", [])
        if style not in styles:
            styles.append(style)
            self.data["cognitive_styles"] = styles
            self.save()

    def record_interest(self, interest: str):
        """Record a user interest."""
        interests = self.data.get("interests", [])
        if interest not in interests:
            interests.append(interest)
            self.data["interests"] = interests
            self.save()

    def add_insight(self, insight: str):
        """Add a behavioral insight."""
        if insight not in self.data["insights"]:
            self.data["insights"].append(insight)
        if len(self.data["insights"]) > 20:
            self.data["insights"] = self.data["insights"][-20:]
        self.save()

    # ---------- Query methods ----------

    def get_focus_summary(self) -> dict:
        """Get a summary of focus patterns."""
        patterns = self.data["focus_patterns"]
        trend = patterns["focus_quality_trend"]
        recent = trend[-7:] if len(trend) >= 7 else trend

        avg_quality = (
            sum(s["quality_score"] for s in recent) / max(len(recent), 1)
        )

        return {
            "best_hours": patterns["best_focus_hours"][-3:],
            "worst_hours": patterns["worst_focus_hours"][-3:],
            "optimal_session_length": patterns["optimal_session_length_minutes"],
            "average_quality_7days": round(avg_quality, 1),
            "total_focus_minutes": self.data["session_summary"]["total_focus_minutes"],
        }

    def get_mood_summary(self) -> dict:
        """Get emotional/mood summary."""
        patterns = self.data["emotional_patterns"]
        trend = patterns["mood_trend"]
        recent = trend[-7:] if len(trend) >= 7 else trend

        if recent:
            avg_stress = sum(m["stress"] for m in recent) / len(recent)
            avg_energy = sum(
                (m.get("energy") or 5) for m in recent
            ) / len(recent)
        else:
            avg_stress = 5.0
            avg_energy = 5.0

        return {
            "average_stress": round(avg_stress, 1),
            "average_energy": round(avg_energy, 1),
            "common_emotions": patterns["common_emotions"][-5:],
            "mood_trend_count": len(patterns["mood_trend"]),
        }

    def get_intervention_recommendations(self) -> dict:
        """Get what types of interventions work best for this user."""
        history = self.data["intervention_history"]
        return {
            "preferred_style": self.data["preferences"]["coach_tone"],
            "successful_count": len(history["successful_interventions"]),
            "failed_count": len(history["failed_interventions"]),
            "last_successful": history["successful_interventions"][-1]
            if history["successful_interventions"] else None,
        }

    def get_personalization_context(self) -> dict:
        """
        Build a compact context dict for AI prompt injection.
        Used to personalize each AI response.
        """
        focus = self.get_focus_summary()
        mood = self.get_mood_summary()

        return {
            "adhd_type": self.data["adhd_type"] or "unknown",
            "primary_challenges": self.data["primary_challenges"][:3],
            "cognitive_styles": self.data.get("cognitive_styles", [])[:3],
            "interests": self.data.get("interests", [])[:5],
            "coach_tone": self.data["preferences"]["coach_tone"],
            "focus_area": self.data["preferences"]["focus_area"],
            "best_focus_hours": focus["best_hours"],
            "optimal_session_length": focus["optimal_session_length"],
            "avg_stress": mood["average_stress"],
            "avg_energy": mood["average_energy"],
            "task_completion_rate": round(self.data["task_patterns"]["completion_rate"] * 100),
            "preferred_task_size": self.data["task_patterns"]["preferred_task_size"],
            "insights": self.data["insights"][-3:],
            "session_count": self.data["session_summary"]["total_sessions"],
        }

    def to_dict(self) -> dict:
        """Return full profile as dict."""
        return self.data
