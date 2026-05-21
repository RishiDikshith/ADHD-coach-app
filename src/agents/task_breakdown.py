"""
Task Breakdown Agent
====================
Specializes in converting large, overwhelming tasks into
microtasks to reduce task paralysis and overwhelm for ADHD users.
"""

import logging
from typing import Any, Optional

from memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class TaskBreakdownAgent:
    """
    Task Breakdown Agent.
    Detects when a user is overwhelmed by a task and breaks it down
    into micro-actions. Suggests 'Just Begin' strategies and
    estimates task difficulty and energy requirements.
    """

    def __init__(self, memory: MemoryManager):
        self.memory = memory
        self.name = "Task Breakdown"

    def get_identity_prompt(self) -> str:
        return (
            "You are the Task Breakdown Agent, specialized in making tasks manageable for ADHD brains.\n"
            "- You break EVERY large task into tiny microtasks (2-5 minutes each)\n"
            "- You know that 'start' is the hardest part for ADHD\n"
            "- You always suggest a '2-minute starter' version of any task\n"
            "- You detect task paralysis phrases like 'too much', 'can't start'\n"
            "- You estimate energy needed for tasks (low/medium/high)\n"
            "- You NEVER suggest 'just do it' — you suggest 'just do this tiny piece'\n"
            "- Tone: calm, practical, step-by-step, never overwhelming"
        )

    def detect_task_paralysis(self, user_message: str) -> bool:
        """Detect if user is showing signs of task paralysis."""
        triggers = [
            "too much", "can't start", "don't know where to start",
            "overwhelming", "so much to do", "can't even",
            "stuck", "paralyzed", "frozen", "can't move",
            "too big", "too hard", "too many", "don't know how",
            "procrastinating", "avoiding", "putting off",
            "can't focus", "can't do it", "too difficult",
        ]
        msg_lower = user_message.lower()
        return any(t in msg_lower for t in triggers)

    def suggest_breakdown(self, task: str, context: dict) -> dict:
        """
        Break a task into microtasks.
        Returns structured breakdown suggestion.
        """
        session = context.get("session", {})
        stress = session.get("current_stress", 5)
        user = context.get("user", {})
        preferred_size = user.get("preferred_task_size", "small")

        # Adjust microtask size based on user state
        if stress >= 7 or preferred_size == "small":
            micro_size = "2_minute"
            steps = [
                f"Open the file/app you need for: {task}",
                f"Write/draft just the FIRST sentence or step",
                f"Set a 5-minute timer and work until it rings",
                f"Take a 2-minute break",
                f"Review what you did and decide the next tiny step",
            ]
        elif stress >= 4:
            micro_size = "5_minute"
            steps = [
                f"Gather everything you need for: {task}",
                f"Work for 5 focused minutes (set a timer!)",
                f"Check your progress — even one step counts!",
                f"Take a short break if needed",
                f"Decide on the next 5-minute block",
            ]
        else:
            micro_size = "10_minute"
            steps = [
                f"List 3 sub-tasks within: {task}",
                f"Pick the easiest sub-task and start",
                f"Set a 10-minute focus block",
                f"After the block, check in with yourself",
                f"Adjust your next block based on energy",
            ]

        return {
            "agent": self.name,
            "type": "task_breakdown",
            "priority": "high" if stress >= 6 else "medium",
            "original_task": task,
            "micro_size": micro_size,
            "steps": steps,
            "message": f"I've broken down '{task}' into tiny steps. Just focus on step 1 — nothing else.",
            "tone": "calm" if stress >= 7 else "encouraging",
        }

    def get_2_minute_starter(self, task: str) -> str:
        """Get a '2-minute starter' version of any task."""
        starters = {
            "write": "Open a blank document and write ONE sentence",
            "study": "Open your notes and read ONE paragraph",
            "clean": "Set a timer for 2 minutes and clean ONE surface",
            "email": "Open your inbox and reply to ONE email",
            "read": "Read ONE page or paragraph",
            "exercise": "Put on your workout clothes (that's it!)",
            "code": "Open your IDE and fix ONE line",
            "organize": "Sort ONE small area (a drawer, a shelf corner)",
            "plan": "Write down ONE thing you want to accomplish today",
        }

        task_lower = task.lower()
        for keyword, starter in starters.items():
            if keyword in task_lower:
                return starter

        return f"Set a 2-minute timer and do ANY tiny part of: {task}"

    def get_system_prompt_extension(self, user_message: str, context: dict) -> str:
        """Generate context-aware system prompt text."""
        if not self.detect_task_paralysis(user_message):
            return ""

        return (
            "[Task Paralysis Detected]\n"
            "The user is showing signs of task paralysis. "
            "Prioritize breaking down tasks into the SMALLEST possible steps. "
            "Suggest the '2-minute rule': just do something for 2 minutes. "
            "Do NOT suggest large tasks or long work sessions. "
            "Be extra gentle and encouraging. Remind them that starting is the win."
        )
