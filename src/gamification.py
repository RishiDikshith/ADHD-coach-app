"""
Gamification System
===================
XP, levels, achievements, and skill trees for the ADHD Coach.

XP Rewards:
- +5 XP for focus session
- +10 XP for completing intervention
- +3 XP for mood check-in
- +15 XP for completing a task
- +1 XP for daily login (capped at 1/day)

Achievements:
- First Focus Session
- 3-Day Momentum
- 7-Day Streak (Week Warrior)
- 30-Day Streak (Monthly Master)
- Recovered From Burnout
- Task Slayer (10+ tasks completed)
- Focus Apprentice (10 focus sessions)
- Focus Master (50 focus sessions)
- Emotional Awareness (5+ mood check-ins/week)

Skill Trees:
- Focus: improved by pomodoro sessions
- Consistency: improved by streaks
- Emotional Resilience: improved by mood recovery
- Task Management: improved by task completions
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# Achievement definitions
ACHIEVEMENTS = {
    "first_focus_session": {
        "id": "first_focus_session",
        "title": "First Focus Session",
        "description": "Completed your first focus session!",
        "emoji": "🎯",
        "xp_reward": 10,
        "icon": "target",
    },
    "three_day_momentum": {
        "id": "three_day_momentum",
        "title": "3-Day Momentum",
        "description": "3-day streak — you're building momentum!",
        "emoji": "🔥",
        "xp_reward": 20,
        "icon": "flame",
    },
    "week_warrior": {
        "id": "week_warrior",
        "title": "Week Warrior",
        "description": "7-day streak — consistency is your superpower!",
        "emoji": "⚔️",
        "xp_reward": 50,
        "icon": "sword",
    },
    "monthly_master": {
        "id": "monthly_master",
        "title": "Monthly Master",
        "description": "30-day streak — you're unstoppable!",
        "emoji": "👑",
        "xp_reward": 200,
        "icon": "crown",
    },
    "recovered_from_burnout": {
        "id": "recovered_from_burnout",
        "title": "Recovered From Burnout",
        "description": "You took rest seriously and bounced back stronger!",
        "emoji": "🌿",
        "xp_reward": 30,
        "icon": "leaf",
    },
    "task_slayer": {
        "id": "task_slayer",
        "title": "Task Slayer",
        "description": "Completed 10+ tasks — you're getting things DONE!",
        "emoji": "💪",
        "xp_reward": 50,
        "icon": "muscle",
    },
    "focus_apprentice": {
        "id": "focus_apprentice",
        "title": "Focus Apprentice",
        "description": "10 focus sessions — focus is a skill, and you're building it!",
        "emoji": "📚",
        "xp_reward": 50,
        "icon": "book",
    },
    "focus_master": {
        "id": "focus_master",
        "title": "Focus Master",
        "description": "50 focus sessions — your focus is a superpower!",
        "emoji": "🏆",
        "xp_reward": 150,
        "icon": "trophy",
    },
    "emotional_awareness": {
        "id": "emotional_awareness",
        "title": "Emotional Awareness",
        "description": "Tracked mood 5+ times in a week — self-awareness is growth!",
        "emoji": "🧠",
        "xp_reward": 30,
        "icon": "brain",
    },
    "habit_builder": {
        "id": "habit_builder",
        "title": "Habit Builder",
        "description": "Completed 20+ interventions — habits are forming!",
        "emoji": "🔄",
        "xp_reward": 75,
        "icon": "refresh",
    },
    "burnout_recovery": {
        "id": "burnout_recovery",
        "title": "Burnout Bounce Back",
        "description": "Recovered from a burnout alert — resilience in action!",
        "emoji": "🦋",
        "xp_reward": 40,
        "icon": "butterfly",
    },
    "streak_saver": {
        "id": "streak_saver",
        "title": "Streak Saver",
        "description": "Came back after losing a streak — that's real grit!",
        "emoji": "💫",
        "xp_reward": 15,
        "icon": "star",
    },
    "overwhelm_victory": {
        "id": "overwhelm_victory",
        "title": "Overwhelm Victory",
        "description": "Used grounding exercises during overwhelm — you took control!",
        "emoji": "🌊",
        "xp_reward": 25,
        "icon": "wave",
    },
}


# Skill tree definitions
SKILL_TREES = {
    "focus": {
        "name": "Focus",
        "emoji": "🎯",
        "description": "Build deep focus and concentration",
        "improved_by": ["pomodoro_sessions", "deep_work", "distraction_management"],
        "xp_per_action": 5,
        "levels": {
            1: {"title": "Beginner Focus", "xp_required": 0},
            2: {"title": "Sprinter", "xp_required": 100},
            3: {"title": "Concentrator", "xp_required": 300},
            4: {"title": "Deep Worker", "xp_required": 600},
            5: {"title": "Focus Master", "xp_required": 1000},
        },
    },
    "consistency": {
        "name": "Consistency",
        "emoji": "🔥",
        "description": "Build reliable habits and routines",
        "improved_by": ["streaks", "daily_logins", "routine_following"],
        "xp_per_action": 3,
        "levels": {
            1: {"title": "First Steps", "xp_required": 0},
            2: {"title": "Regular", "xp_required": 80},
            3: {"title": "Reliable", "xp_required": 250},
            4: {"title": "Unstoppable", "xp_required": 500},
            5: {"title": "Legendary Consistency", "xp_required": 1000},
        },
    },
    "emotional_resilience": {
        "name": "Emotional Resilience",
        "emoji": "🧠",
        "description": "Build emotional regulation and recovery",
        "improved_by": ["mood_tracking", "grounding_exercises", "burnout_recovery"],
        "xp_per_action": 4,
        "levels": {
            1: {"title": "Self-Aware", "xp_required": 0},
            2: {"title": "Regulator", "xp_required": 100},
            3: {"title": "Resilient", "xp_required": 300},
            4: {"title": "Unshakable", "xp_required": 600},
            5: {"title": "Emotion Master", "xp_required": 1000},
        },
    },
    "task_management": {
        "name": "Task Management",
        "emoji": "📋",
        "description": "Master productivity and task completion",
        "improved_by": ["task_completions", "micro_tasks", "prioritization"],
        "xp_per_action": 4,
        "levels": {
            1: {"title": "Organizer", "xp_required": 0},
            2: {"title": "Executor", "xp_required": 100},
            3: {"title": "Slasher", "xp_required": 300},
            4: {"title": "Productivity Pro", "xp_required": 600},
            5: {"title": "Task Slayer", "xp_required": 1000},
        },
    },
}


class GamificationEngine:
    """
    Handles all gamification logic: XP, levels, achievements, skill trees.
    Integrates with the database layer for persistence.
    """

    def __init__(self, db_manager=None):
        self.db = db_manager

    # ==================== XP & Levels ====================

    def award_xp(self, username: str, action: str, metadata: Optional[dict] = None) -> dict:
        """
        Award XP for a specific action.
        Returns the updated XP/level state and any new achievements.
        """
        if not self.db:
            return {"state": {}, "new_achievements": [], "leveled_up": False}

        xp_amount = self._get_xp_for_action(action)
        skill = self._get_skill_for_action(action)

        if not skill or xp_amount <= 0:
            return {"state": {}, "new_achievements": [], "leveled_up": False}

        result = self.db.add_xp(username, xp_amount, skill)
        result["xp_awarded"] = xp_amount
        result["action"] = action

        # Check for new achievements
        new_achievements = self._check_achievements(username, action, metadata or {})
        if new_achievements:
            result["new_achievements"] = [
                {"id": a.achievement_id, "title": a.title, "xp_reward": a.xp_reward}
                for a in new_achievements
            ]
        else:
            result["new_achievements"] = []

        return result

    def _get_xp_for_action(self, action: str) -> int:
        """Get XP reward for an action."""
        xp_map = {
            "focus_session_completed": 5,
            "focus_session_high_quality": 8,
            "intervention_completed": 10,
            "mood_checkin": 3,
            "task_completed": 15,
            "task_completed_hard": 25,
            "micro_task_completed": 5,
            "daily_login": 1,
            "streak_milestone_3": 20,
            "streak_milestone_7": 50,
            "streak_milestone_30": 200,
            "achievement_unlocked": 0,  # XP included in achievement definition
            "grounding_exercise": 5,
            "breathing_exercise": 3,
            "hydration_logged": 2,
            "focus_mode_used": 3,
        }
        return xp_map.get(action, 0)

    def _get_skill_for_action(self, action: str) -> str:
        """Map an action to the skill tree it progresses."""
        skill_map = {
            "focus_session_completed": "focus",
            "focus_session_high_quality": "focus",
            "focus_mode_used": "focus",
            "intervention_completed": "consistency",
            "mood_checkin": "emotional_resilience",
            "task_completed": "task_management",
            "task_completed_hard": "task_management",
            "micro_task_completed": "task_management",
            "daily_login": "consistency",
            "streak_milestone_3": "consistency",
            "streak_milestone_7": "consistency",
            "streak_milestone_30": "consistency",
            "grounding_exercise": "emotional_resilience",
            "breathing_exercise": "emotional_resilience",
            "hydration_logged": "emotional_resilience",
        }
        return skill_map.get(action, "consistency")

    def _check_achievements(self, username: str, action: str, metadata: dict) -> list:
        """Check and award any newly unlocked achievements."""
        if not self.db:
            return []
        try:
            return self.db.check_and_award_achievements(username)
        except Exception as e:
            logger.warning(f"Achievement check error: {e}")
            return []

    # ==================== State Queries ====================

    def get_full_state(self, username: str) -> dict:
        """Get the full gamification state for a user."""
        if not self.db:
            return {}

        try:
            achievements = self.db.get_achievements(username)
            skills = self.db.get_skills(username)
            streaks = self.db.get_all_streak_summary(username)
        except Exception as e:
            logger.warning(f"Gamification state error: {e}")
            return {"achievements": [], "skills": [], "streaks": {}, "level": 1, "total_xp": 0}

        # Calculate overall level from total XP across all skills
        total_xp = sum(s.get("xp", 0) for s in skills)
        total_level = sum(s.get("level", 1) for s in skills)
        overall_level = max(1, total_level // max(len(skills), 1))

        # Map achievement IDs to full definitions
        achievement_details = []
        for a in achievements:
            defn = ACHIEVEMENTS.get(a["id"], {})
            achievement_details.append({
                **a,
                "emoji": defn.get("emoji", "⭐"),
                "icon": defn.get("icon", "star"),
            })

        # Map skill data to full definitions
        skill_details = []
        for s in skills:
            tree = SKILL_TREES.get(s["name"], {})
            levels = tree.get("levels", {})
            current_level_def = levels.get(s["level"], {})
            next_level_def = levels.get(s["level"] + 1, {})
            skill_details.append({
                **s,
                "emoji": tree.get("emoji", "⭐"),
                "title": current_level_def.get("title", f"Level {s['level']}"),
                "next_title": next_level_def.get("title", "Max Level"),
                "description": tree.get("description", ""),
                "progress_pct": s.get("progress_pct", 0),
            })

        return {
            "total_xp": total_xp,
            "overall_level": overall_level,
            "achievements": achievement_details,
            "skills": skill_details,
            "streaks": streaks,
            "achievement_count": len(achievement_details),
            "skill_count": len(skill_details),
        }

    def get_level_progress(self, total_xp: int) -> dict:
        """Calculate level from total XP using 100 XP per level scaling."""
        xp_per_level = 100
        level = max(1, (total_xp // xp_per_level) + 1)
        xp_in_level = total_xp % xp_per_level
        return {
            "level": level,
            "xp": xp_in_level,
            "xp_to_next": xp_per_level - xp_in_level,
            "progress_pct": round((xp_in_level / xp_per_level) * 100, 1),
        }

    def get_all_achievements(self) -> List[dict]:
        """Get all possible achievements with their definitions."""
        return list(ACHIEVEMENTS.values())

    def get_all_skill_trees(self) -> List[dict]:
        """Get all skill tree definitions with level details."""
        result = []
        for skill_id, tree in SKILL_TREES.items():
            levels = []
            for level_num, level_def in sorted(tree["levels"].items()):
                levels.append({
                    "level": level_num,
                    "title": level_def["title"],
                    "xp_required": level_def["xp_required"],
                })
            result.append({
                "id": skill_id,
                "name": tree["name"],
                "emoji": tree["emoji"],
                "description": tree["description"],
                "improved_by": tree["improved_by"],
                "xp_per_action": tree["xp_per_action"],
                "levels": levels,
            })
        return result

    # ==================== Prompt Integration ====================

    def get_gamification_context_for_prompt(self, username: str) -> str:
        """Generate a gamification context string for LLM prompt injection."""
        state = self.get_full_state(username)
        if not state:
            return ""

        parts = ["[Gamification State]"]

        if state.get("overall_level"):
            parts.append(f"Level: {state['overall_level']} | Total XP: {state.get('total_xp', 0)}")

        if state.get("achievements"):
            parts.append(f"Achievements: {len(state['achievements'])} unlocked")

        if state.get("skills"):
            skill_lines = []
            for s in state["skills"][:3]:
                skill_lines.append(f"{s['emoji']} {s['name']}: Level {s['level']} ({s['title']})")
            parts.append("Skills: " + " | ".join(skill_lines))

        if state.get("streaks", {}).get("types"):
            streak_lines = []
            for s_type, s_data in state["streaks"]["types"].items():
                streak_lines.append(f"{s_type}: {s_data.get('current', 0)}d")
            parts.append("Streaks: " + ", ".join(streak_lines))

        return "\n".join(parts)


# Convenience function for quick XP awards
def award_xp(db_manager, username: str, action: str) -> dict:
    """Quick XP award via convenience function."""
    engine = GamificationEngine(db_manager)
    return engine.award_xp(username, action)


# Convenience function for quick celebration messages
def get_celebration_message(action: str, level_up: bool = False, achievement: Optional[dict] = None) -> str:
    """Generate a celebration message for an action."""
    if achievement:
        return (
            f"🏆 **Achievement Unlocked: {achievement['title']}**\n"
            f"{achievement.get('description', '')}\n"
            f"+{achievement.get('xp_reward', 0)} XP"
        )

    if level_up:
        return "🌟 **Level Up!** You're growing stronger every day!"

    celebration_messages = {
        "focus_session_completed": "🎯 Focus session complete! Your focus muscle is getting stronger!",
        "intervention_completed": "✅ Intervention completed! Every small step adds up!",
        "mood_checkin": "📊 Mood logged! Self-awareness is the first step to growth!",
        "task_completed": "✨ Task completed! Progress > Perfection!",
        "micro_task_completed": "⚡ Micro-task done! Small wins compound into big results!",
        "grounding_exercise": "🌿 Grounding complete! You're learning to anchor yourself!",
        "breathing_exercise": "💨 Deep breaths done! Your calm is your superpower!",
        "hydration_logged": "💧 Hydration logged! Your brain thanks you!",
    }

    return celebration_messages.get(action, f"✨ +{action} completed!")
