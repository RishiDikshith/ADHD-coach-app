"""
Accountability Agent
====================
Provides gentle accountability, check-ins, reminders,
and productivity summaries for ADHD users.

Upgraded with deeper conversational intelligence,
commitment tracking, and emotionally aware follow-ups.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Optional

logger = logging.getLogger(__name__)


class AccountabilityAgent:
    """
    Accountability Agent.
    Provides gentle, supportive accountability without shame or pressure.
    Tracks commitments and follows up appropriately.

    Improvement: Deeper conversational memory, emotionally intelligent
    follow-ups, and commitment tracking that adapts to user state.
    """

    def __init__(self, memory):
        self.memory = memory
        self.name = "Accountability"

    def get_identity_prompt(self) -> str:
        return (
            "You are the Accountability Agent, a supportive ADHD accountability partner.\\n"
            "- You NEVER use shame or guilt as motivation — it backfires for ADHD brains\\n"
            "- You follow up gently — a missed commitment is data, not failure\\n"
            "- You help users make realistic commitments they can actually keep\\n"
            "- You celebrate effort, not just outcomes\\n"
            "- You provide structured check-ins without being nagging\\n"
            "- You remember past commitments and reference them naturally\\n"
            "- You adjust your tone based on whether they're thriving or struggling\\n"
            "- Tone: supportive partner, like someone who's in your corner, not a manager"
        )

    def generate_check_in(self, context: dict, previous_commitments: list = None) -> dict:
        session = context.get("session", {})
        user = context.get("user", {})

        stress = session.get("current_stress", 5)
        turn_count = session.get("turn_count", 0)
        completed_tasks = session.get("completed_tasks_count", 0)
        active_tasks = session.get("active_tasks", [])
        energy = session.get("current_energy", 5)
        mood = session.get("current_mood", "neutral")

        # Previous commitments made in this session
        commitments_made = session.get("commitments_made", [])
        commitments_kept = session.get("commitments_kept", [])

        # Follow-up on previous commitments
        if commitments_made and len(commitments_kept) < len(commitments_made):
            last_commitment = commitments_made[-1]
            return {
                "agent": self.name,
                "type": "commitment_follow_up",
                "style": "supportive",
                "message": f"Hey, I remember you were going to {last_commitment[:60]}. No pressure at all — just checking if that's still feeling right or if it needs adjusting?",
                "tone": "gentle",
            }

        # High stress — no accountability, just support
        if stress >= 7:
            return {
                "agent": self.name,
                "type": "check_in",
                "style": "gentle_support",
                "message": "Just checking in — and I mean REALLY checking in. How are you doing right now, not 'fine' but actually?",
                "tone": "warm",
            }

        # Progress acknowledgment
        if completed_tasks > 0:
            return {
                "agent": self.name,
                "type": "progress_check_in",
                "style": "celebratory",
                "message": f"You've knocked out {completed_tasks} thing{'s' if completed_tasks != 1 else ''}! How does that feel? Let's sit with that win for a second.",
                "tone": "celebratory" if completed_tasks > 1 else "encouraging",
            }

        # Low energy check-in
        if energy <= 3:
            return {
                "agent": self.name,
                "type": "energy_check_in",
                "style": "gentle",
                "message": "You seem low on fuel today. What if we set the bar at 'just showing up' and nothing more?",
                "tone": "gentle",
            }

        # Active tasks — supportive nudge
        if active_tasks:
            return {
                "agent": self.name,
                "type": "task_check_in",
                "style": "supportive",
                "message": "You've got some things on your plate. Want to pick ONE that feels most doable right now? Just one.",
                "tone": "encouraging",
            }

        # Longer conversation — reflective check-in
        if turn_count > 3:
            return {
                "agent": self.name,
                "type": "reflective_check_in",
                "style": "reflective",
                "message": "We've been chatting a bit. What's the one thing you'd love to walk away from this conversation with?",
                "tone": "warm",
            }

        # Default — open check-in
        return {
            "agent": self.name,
            "type": "check_in",
            "style": "open",
            "message": "Hey, how's your headspace right now? No right answers — just checking in.",
            "tone": "warm",
        }

    def generate_session_summary(self, context: dict) -> dict:
        session = context.get("session", {})
        user = context.get("user", {})

        turn_count = session.get("turn_count", 0)
        current_mood = session.get("current_mood", "neutral")
        current_stress = session.get("current_stress", 5)
        energy = session.get("current_energy", 5)
        overwhelm = session.get("overwhelm_detected", False)
        task_paralysis = session.get("task_paralysis_detected", False)
        active_tasks = session.get("active_tasks", [])
        completed = session.get("completed_tasks_count", 0)
        commitments_made = session.get("commitments_made", [])
        commitments_kept = session.get("commitments_kept", [])

        mood_trend = user.get("avg_stress", 5)

        summary = {
            "agent": self.name,
            "type": "session_summary",
            "turns_this_session": turn_count,
            "mood_summary": current_mood,
            "stress_trend": "stable",
            "energy_level": energy,
            "tasks_active": len(active_tasks),
            "tasks_completed": completed,
            "commitments_made": len(commitments_made),
            "commitments_kept": len(commitments_kept),
            "flags": [],
            "overall_recommendation": "",
            "personal_note": "",
        }

        if mood_trend < current_stress:
            summary["stress_trend"] = "increasing"
        elif mood_trend > current_stress:
            summary["stress_trend"] = "decreasing"
        else:
            summary["stress_trend"] = "stable"

        if overwhelm:
            summary["flags"].append("overwhelm_detected")
        if task_paralysis:
            summary["flags"].append("task_paralysis_detected")
        if current_stress >= 7:
            summary["flags"].append("high_stress")
        if energy <= 3:
            summary["flags"].append("low_energy")

        # Generate human-sounding recommendation
        if summary["flags"]:
            summary["overall_recommendation"] = (
                "Let's focus on you, not your output. Productivity can wait. "
                "What feels supportive right now?"
            )
            summary["personal_note"] = self._get_emotional_personal_note(summary)
        elif completed > 0:
            summary["overall_recommendation"] = (
                f"You completed {completed} tasks — that's real progress. "
                "Keep the momentum gentle. One more small win?"
            )
            summary["personal_note"] = "Progress > perfection. You're doing it."
        else:
            summary["overall_recommendation"] = (
                "Good session! Sometimes the win is just showing up and talking it through."
            )
            summary["personal_note"] = "Being here counts."

        return summary

    def _get_emotional_personal_note(self, summary: dict) -> str:
        if "high_stress" in summary["flags"]:
            return "You're carrying a lot. You don't have to fix everything today. Just being here is enough."
        if "overwhelm_detected" in summary["flags"]:
            return "Things feel like too much right now. Let's make the world smaller — one breath, one thing at a time."
        if "low_energy" in summary["flags"]:
            return "Low energy days are your body's way of asking for rest. Listen to it."
        return "I see you showing up. That matters more than you think."

    def record_commitment(self, commitment: str, context: dict):
        """Record a commitment made by the user."""
        session = context.get("session", {})
        commitments = session.get("commitments_made", [])
        commitments.append(commitment)
        if self.memory:
            self.memory.store.store(
                content=f"User committed to: {commitment}",
                metadata={"type": "commitment", "commitment": commitment, "status": "made"},
                memory_type="accountability",
            )

    def mark_commitment_kept(self, commitment: str, context: dict):
        """Mark a commitment as completed."""
        session = context.get("session", {})
        kept = session.get("commitments_kept", [])
        kept.append(commitment)
        if self.memory:
            self.memory.store.store(
                content=f"User kept commitment: {commitment}",
                metadata={"type": "commitment", "commitment": commitment, "status": "kept"},
                memory_type="accountability",
            )

    def get_commitment_strategy(self, task: str, confidence: int = 5) -> str:
        if confidence >= 7:
            return (
                f"You feel good about '{task}' — let's lock it in:\\n"
                f"• Set a specific time: 'I will start at [TIME]' (time-blindness hack)\\n"
                f"• Remove ONE obstacle before starting (close tabs, get water first)\\n"
                f"• Tell someone your intention (even just writing it here counts)"
            )
        elif confidence >= 4:
            return (
                f"Moderate confidence is totally okay. For '{task}':\\n"
                f"• Commit to just 5 minutes — you have FULL permission to stop after\\n"
                f"• Set a timer and make it a game: 'Can I beat my last 5 minutes?'\\n"
                f"• What's the easiest possible version? Can you just open the file?"
            )
        else:
            return (
                f"Low confidence is important information. For '{task}':\\n"
                f"• Break it down into something so tiny it feels almost silly\\n"
                f"• Can you do just 1 minute of it? ONE minute.\\n"
                f"• If even that feels too much — can someone help you with the first step?"
            )

    def get_system_prompt_extension(self, context: dict) -> str:
        check_in = self.generate_check_in(context)
        summary = self.generate_session_summary(context)

        parts = []
        parts.append(f"[Accountability] {check_in['message']}")
        parts.append(f"[Accountability Style] {check_in['style']}")

        if summary["flags"]:
            parts.append(f"[Session Flags] {', '.join(summary['flags'])}")
        if summary.get("personal_note"):
            parts.append(f"[Personal Note] {summary['personal_note']}")

        parts.append(f"[Recommendation] {summary['overall_recommendation']}")

        return "\\n".join(parts)
