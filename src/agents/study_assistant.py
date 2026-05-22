"""
Study Assistant Agent
=====================
Focuses on academic productivity, revision schedules, exam preparation,
and study-focused coaching for ADHD students and lifelong learners.
"""

import logging
from typing import Any, Optional
from memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class StudyAssistantAgent:
    """
    Study Assistant Agent.
    Helps organize academic work, break down studying topics into digestible sessions,
    schedule spaced repetition, and manage study focus for ADHD brains.
    """

    def __init__(self, memory: MemoryManager):
        self.memory = memory
        self.name = "Study Assistant"

    def get_identity_prompt(self) -> str:
        return (
            "You are the Study Assistant Agent, a supportive and focused academic coach who deeply understands "
            "the academic challenges of ADHD (like reading walls of text, task initiation on big papers, and cramming anxiety).\n"
            "- You break large topics into high-impact sub-topics to avoid revision overwhelm\n"
            "- You suggest active recall and gamified study methods (flashcards, teaching back) instead of passive reading\n"
            "- You use body doubling or Pomodoro frameworks adapted for academic tasks\n"
            "- You help plan realistic study schedules and break down long research papers or assignments\n"
            "- Tone: focused, academic, motivating, and deeply understanding"
        )

    def get_study_recommendation(self, context: dict) -> Optional[dict]:
        """Generate study-specific recommendation based on user profiles or tasks."""
        user = context.get("user", {})
        session = context.get("session", {})

        stress = session.get("current_stress", 5)
        study_hours = user.get("study_hours", 0)
        adhd_risk = user.get("adhd_risk", 0.5)

        # High stress study recommendations
        if stress >= 8:
            return {
                "agent": self.name,
                "type": "study_stress_rescue",
                "priority": "high",
                "message": "Cramming stress detected. Pushing too hard triggers shutdown. Let's do a 5-minute study reset.",
                "suggestions": [
                    "Close all tabs except the one you need immediately",
                    "Do a 1-minute brain dump of what is worrying you",
                    "Review only ONE key concept, then take a stretch break",
                ],
                "tone": "gentle",
            }

        # ADHD Study breakdown
        if adhd_risk >= 0.7:
            return {
                "agent": self.name,
                "type": "adhd_active_study",
                "priority": "medium",
                "message": "Passively reading textbook pages will put an ADHD brain to sleep. Let's use active study loops!",
                "suggestions": [
                    "Convert your topic headers into questions, then try answering them",
                    "Use the 'Feynman Technique': explain this concept as if teaching a 10-year-old",
                    "Sketch a visual mind map or use flashcards with colors",
                ],
                "tone": "focused",
            }

        return {
            "agent": self.name,
            "type": "study_block",
            "priority": "low",
            "message": "Let's tackle your study material using structured, low-friction study blocks.",
            "suggestions": [
                "Select a 20-minute study target",
                "Start with the hardest topic first to utilize fresh brainpower",
                "Put your phone in 'Do Not Disturb' or another room",
            ],
            "tone": "motivating",
        }

    def get_system_prompt_extension(self, context: dict) -> str:
        rec = self.get_study_recommendation(context)
        parts = []
        if rec:
            parts.append(f"[Study Assistant Insight] {rec['message']}")
        return "\n".join(parts) if parts else ""
