"""
Focus Engine
============
Advanced ADHD focus management system with:
- 4 ADHD-specific focus modes (Deep Focus, Gentle Start, Recovery, Sprint)
- Adaptive Pomodoro timing based on focus score, fatigue, and completion history
- Distraction tracking and pattern analysis
- Break recommendations based on focus mode and session duration
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ==================== Data Classes ====================

@dataclass
class FocusMode:
    """
    ADHD-specific focus mode configuration.
    Each mode serves a different neurocognitive need.
    """
    id: str
    name: str
    emoji: str
    description: str
    default_duration_minutes: int
    min_duration: int
    max_duration: int
    recommended_break_minutes: int
    allow_extensions: bool
    use_distraction_blocking: bool
    use_background_noise: bool
    suggested_activities: List[str] = field(default_factory=list)

    @classmethod
    def get_all_modes(cls) -> Dict[str, 'FocusMode']:
        return {m.id: m for m in cls.get_modes_list()}

    @classmethod
    def get_modes_list(cls) -> List['FocusMode']:
        return [
            cls(
                id="deep_focus",
                name="Deep Focus",
                emoji="🎯",
                description="Maximum concentration with distraction blocking. Best for important, cognitively demanding tasks.",
                default_duration_minutes=25,
                min_duration=15,
                max_duration=60,
                recommended_break_minutes=10,
                allow_extensions=False,
                use_distraction_blocking=True,
                use_background_noise=True,
                suggested_activities=[
                    "Turn on 'Do Not Disturb' mode",
                    "Close all unrelated browser tabs",
                    "Put phone in another room",
                    "Use noise-canceling headphones",
                    "Have water nearby",
                    "Write down distracting thoughts to revisit later",
                ],
            ),
            cls(
                id="gentle_start",
                name="Gentle Start",
                emoji="🌱",
                description="Low-pressure start for overwhelmed or low-energy days. The goal is showing up, not performing.",
                default_duration_minutes=8,
                min_duration=2,
                max_duration=15,
                recommended_break_minutes=5,
                allow_extensions=True,
                use_distraction_blocking=False,
                use_background_noise=True,
                suggested_activities=[
                    "Just open the document/app - that's it",
                    "Set a 2-minute timer and do ANY tiny piece",
                    "Tell yourself 'I just need to sit here'",
                    "No pressure to finish anything",
                    "If you want to stop after 2 min, that's a win",
                ],
            ),
            cls(
                id="recovery",
                name="Recovery",
                emoji="🌿",
                description="For burnout recovery days. Focus on rest, self-care, and gentle grounding — not productivity.",
                default_duration_minutes=5,
                min_duration=2,
                max_duration=10,
                recommended_break_minutes=15,
                allow_extensions=False,
                use_distraction_blocking=False,
                use_background_noise=False,
                suggested_activities=[
                    "Do a breathing exercise",
                    "Drink water mindfully",
                    "Stretch gently",
                    "Listen to calming music",
                    "Just rest — doing nothing counts",
                ],
            ),
            cls(
                id="sprint",
                name="Sprint Mode",
                emoji="⚡",
                description="Short dopamine bursts of focused work. Great for building momentum or tackling dreaded tasks.",
                default_duration_minutes=10,
                min_duration=5,
                max_duration=20,
                recommended_break_minutes=3,
                allow_extensions=False,
                use_distraction_blocking=True,
                use_background_noise=True,
                suggested_activities=[
                    "Pick the task you're dreading most",
                    "Set a 10-minute sprint timer",
                    "Work FAST — no perfectionism allowed",
                    "When the timer rings, you're DONE",
                    "Celebrate with a small reward (dopamine!)",
                ],
            ),
        ]


@dataclass
class FocusSessionResult:
    """Result of a completed or analyzed focus session."""
    mode: str
    duration_minutes: int
    completed: bool
    quality: Optional[int] = None
    distractions: int = 0
    energy_before: Optional[int] = None
    energy_after: Optional[int] = None
    suggested_next_mode: Optional[str] = None
    suggested_next_duration: Optional[int] = None
    break_recommendation: Optional[str] = None


# ==================== Adaptive Pomodoro ====================

class AdaptivePomodoro:
    """
    Adaptive Pomodoro timer that adjusts session length based on:
    - User's current focus score (0-10)
    - Fatigue level (derived from completed sessions today)
    - Historical completion rates
    - Preferred session length from history
    """

    def __init__(self, db_manager=None):
        self.db = db_manager

    def calculate_optimal_duration(
        self,
        focus_score: float = 0.5,  # 0.0 to 1.0
        sessions_completed_today: int = 0,
        avg_historical_duration: Optional[int] = None,
        stress_level: int = 5,
        energy_level: int = 5,
        mode: str = "standard",
    ) -> dict:
        """
        Calculate the optimal focus duration based on multiple factors.
        Returns duration recommendation with reasoning.
        """
        # Get base duration from mode
        mode_configs = {
            "deep_focus": (15, 60, 25),
            "gentle_start": (2, 15, 8),
            "recovery": (2, 10, 5),
            "sprint": (5, 20, 10),
            "standard": (5, 60, 25),
        }
        min_dur, max_dur, default_dur = mode_configs.get(mode, (5, 60, 25))

        # 1. Adjust for focus score
        if focus_score < 0.3:
            focus_factor = 0.5  # Low focus → shorter sessions
        elif focus_score < 0.6:
            focus_factor = 0.8
        else:
            focus_factor = 1.0

        # 2. Adjust for fatigue (more sessions today = more fatigue)
        fatigue_factor = max(0.4, 1.0 - (sessions_completed_today * 0.08))

        # 3. Adjust for stress and energy
        stress_factor = max(0.5, 1.0 - ((stress_level - 5) * 0.08))
        energy_factor = max(0.4, energy_level / 10)

        # 4. Use historical average if available
        historical_factor = 1.0
        if avg_historical_duration and avg_historical_duration > 0:
            historical_factor = avg_historical_duration / default_dur
            historical_factor = max(0.5, min(1.5, historical_factor))

        # Calculate recommended duration
        recommended = int(
            default_dur
            * focus_factor
            * fatigue_factor
            * stress_factor
            * energy_factor
            * historical_factor
        )

        # Clamp to valid range
        recommended = max(min_dur, min(max_dur, recommended))

        # Generate reasoning
        reasons = []
        if focus_score < 0.3:
            reasons.append("Focus is low — shorter sessions recommended")
        if sessions_completed_today >= 3:
            reasons.append(f"Completed {sessions_completed_today} sessions today — rest needed")
        if stress_level >= 7:
            reasons.append("High stress — let's keep it gentle")
        if energy_level <= 3:
            reasons.append("Low energy — micro-sprints only")

        return {
            "recommended_duration": recommended,
            "min_duration": min_dur,
            "max_duration": max_dur,
            "reasoning": reasons or ["Standard session recommended"],
            "factors": {
                "focus_score": round(focus_score, 2),
                "fatigue_factor": round(fatigue_factor, 2),
                "stress_factor": round(stress_factor, 2),
                "energy_factor": round(energy_factor, 2),
                "historical_factor": round(historical_factor, 2),
            },
        }

    def recommend_break(self, mode: str, duration_minutes: int, quality: Optional[int] = None) -> dict:
        """Recommend break duration and activities based on focus mode and session."""
        mode_configs = {
            "deep_focus": (5, 15),
            "gentle_start": (2, 5),
            "recovery": (10, 30),
            "sprint": (2, 5),
            "standard": (5, 10),
        }
        min_break, max_break = mode_configs.get(mode, (5, 10))

        # Longer sessions need longer breaks
        if duration_minutes >= 45:
            break_dur = max_break
        elif duration_minutes >= 25:
            break_dur = (min_break + max_break) // 2
        else:
            break_dur = min_break

        # Lower quality → longer break needed
        if quality is not None and quality <= 4:
            break_dur = min(max_break, break_dur + 3)

        activities = self._get_break_activities(mode, duration_minutes)
        return {
            "duration_minutes": break_dur,
            "activities": activities,
            "reason": "Recovery mode" if mode == "recovery" else "Standard break",
        }

    def _get_break_activities(self, mode: str, duration: int) -> List[str]:
        """Get ADHD-friendly break activities based on mode and duration."""
        if mode == "recovery":
            return [
                "Lie down and close your eyes",
                "Do a 5-minute body scan",
                "Listen to calming music",
                "Step outside for fresh air",
                "Just breathe — no phone, no screen",
            ]

        if duration <= 10:
            return [
                "Stand up and stretch your arms",
                "Take 5 deep breaths",
                "Look out the window for 30 seconds",
                "Roll your shoulders and neck",
                "Drink some water",
            ]

        return [
            "Walk around the room or outside",
            "Do a quick stretching routine",
            "Get a healthy snack and water",
            "Change your environment briefly",
            "Close your eyes and take 10 breaths",
            "Do 5 jumping jacks (energy reset!)",
        ]


# ==================== Main Focus Engine ====================

class FocusEngine:
    """
    Main focus management engine.
    Coordinates focus modes, adaptive timing, distraction tracking,
    and session analysis.
    """

    def __init__(self, db_manager=None):
        self.db = db_manager
        self.adaptive_pomodoro = AdaptivePomodoro(db_manager)
        self._active_sessions: Dict[str, dict] = {}
        self._distraction_log: List[dict] = []

    def get_mode(self, mode_id: str) -> Optional[FocusMode]:
        """Get a focus mode by ID."""
        return FocusMode.get_all_modes().get(mode_id)

    def get_mode_for_state(self, state_id: str) -> str:
        """Map an ADHD state to the best focus mode."""
        state_mode_map = {
            "calm": "standard",
            "focused": "deep_focus",
            "overwhelmed": "gentle_start",
            "burnout": "recovery",
            "hyperfocus": "deep_focus",
            "avoidant": "sprint",
            "dysregulated": "recovery",
        }
        return state_mode_map.get(state_id, "standard")

    def recommend_session(
        self,
        mode_id: str,
        focus_score: float = 0.5,
        sessions_completed_today: int = 0,
        stress_level: int = 5,
        energy_level: int = 5,
        fatigue: int = 5,
        avg_historical_duration: Optional[int] = None,
        preferred_mode: Optional[str] = None,
    ) -> dict:
        """
        Generate a complete focus session recommendation.
        Returns mode, duration, break, and preparation tips.
        """
        # Use preferred mode or the one that matches current state
        if preferred_mode:
            mode_id = preferred_mode

        mode = self.get_mode(mode_id)
        if not mode:
            mode = FocusMode.get_all_modes()["standard"]
            mode_id = mode.id

        # Get optimal duration
        duration_rec = self.adaptive_pomodoro.calculate_optimal_duration(
            focus_score=focus_score,
            sessions_completed_today=sessions_completed_today,
            avg_historical_duration=avg_historical_duration,
            stress_level=stress_level,
            energy_level=energy_level,
            mode=mode_id,
        )

        # Get break recommendation
        break_rec = self.adaptive_pomodoro.recommend_break(
            mode_id, duration_rec["recommended_duration"]
        )

        return {
            "mode": {
                "id": mode.id,
                "name": mode.name,
                "emoji": mode.emoji,
                "description": mode.description,
            },
            "duration": duration_rec,
            "break": break_rec,
            "preparation_tips": mode.suggested_activities[:4],
            "can_extend": mode.allow_extensions,
        }

    def log_distraction(self, username: str, distraction: str, category: str = "other",
                        energy_level: Optional[int] = None):
        """Log a distraction event for pattern analysis."""
        entry = {
            "username": username,
            "distraction": distraction,
            "category": category,
            "energy_level": energy_level,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._distraction_log.append(entry)

        if self.db:
            self.db.log_distraction(
                username=username,
                distraction=distraction,
                category=category,
                energy_level=energy_level,
            )

    def get_distraction_patterns(self, username: str, days: int = 7) -> dict:
        """Analyze distraction patterns to identify trends."""
        if self.db:
            return self.db.get_distraction_stats(username, days)

        # Fallback to in-memory analysis
        recent = [d for d in self._distraction_log if d["username"] == username]
        categories = {}
        for d in recent:
            cat = d.get("category", "other")
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "total": len(recent),
            "by_category": categories,
            "most_common": max(categories, key=categories.get) if categories else None,
        }

    def get_session_feedback_questions(self, mode_id: str) -> List[str]:
        """Get post-session feedback questions specific to the focus mode."""
        questions = [
            "How was your focus quality? (1-10)",
            "How many distractions did you have?",
            "What was your energy level before? (1-10)",
            "What was your energy level after? (1-10)",
        ]

        mode_specific = {
            "gentle_start": [
                "Did you feel pressure to do more than planned?",
                "What helped you get started?",
            ],
            "recovery": [
                "Do you feel more rested now?",
                "What would help you rest more?",
            ],
            "sprint": [
                "Did the time pressure help or hurt?",
                "What reward did you give yourself?",
            ],
            "deep_focus": [
                "What was your biggest distraction?",
                "What helped you maintain focus?",
            ],
        }

        return questions + mode_specific.get(mode_id, [])

    def get_system_prompt_extension(self, context: dict) -> str:
        """Generate focus-related system prompt extension."""
        mode_id = context.get("focus_mode", "standard")
        mode = self.get_mode(mode_id)

        if not mode:
            return ""

        return (
            f"[Focus Mode: {mode.emoji} {mode.name}]\n"
            f"{mode.description}\n"
            f"Recommended session: {mode.default_duration_minutes} minutes with {mode.recommended_break_minutes} minute break.\n"
            f"Tone: Match the energy of this focus mode ({'low-pressure' if mode_id in ('gentle_start', 'recovery') else 'energetic' if mode_id == 'sprint' else 'balanced'})."
        )
