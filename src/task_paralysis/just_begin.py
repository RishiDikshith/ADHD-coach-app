"""
Just Begin Mode
===============
Specialized mode for overcoming task paralysis by reducing
the commitment to start. Based on the principle that 'starting'
is the hardest part for ADHD brains.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class JustBeginMode:
    """
    'Just Begin' mode — a structured approach to overcoming
    task paralysis by making the commitment to start as small
    as possible.

    Core principle: "You only have to start. You can stop after
    2 minutes if you want to."
    """

    def __init__(self):
        self.active_sessions = {}

    def create_begin_session(self, task: str, user_id: str = "default") -> dict:
        """Create a 'Just Begin' session for a task."""
        session = {
            "user_id": user_id,
            "task": task,
            "state": "offered",
            "commitment": "2 minutes",
            "micro_goal": self._generate_micro_goal(task),
            "started_at": None,
            "completed_at": None,
            "extended": False,  # Did they choose to continue after 2 min?
        }
        self.active_sessions[user_id] = session
        return self._format_session(session)

    def accept_begin(self, user_id: str = "default") -> dict:
        """User accepts the 'Just Begin' challenge."""
        session = self.active_sessions.get(user_id)
        if not session:
            return {"error": "No active session found"}

        session["state"] = "started"
        return {
            "type": "begin_accepted",
            "commitment": session["commitment"],
            "instructions": self._get_start_instructions(session["task"]),
            "message": (
                f"Perfect! You just need to do this for {session['commitment']}. "
                "Set a timer if that helps. After that, you can stop with zero guilt."
            ),
        }

    def complete_begin(self, extended: bool = False, user_id: str = "default") -> dict:
        """Complete (or extend) a 'Just Begin' session."""
        session = self.active_sessions.get(user_id)
        if not session:
            return {"error": "No active session found"}

        if extended:
            session["extended"] = True
            return {
                "type": "extended",
                "message": (
                    "You chose to keep going! That's the magic of starting — "
                    "it's almost always easier to continue than to start. "
                    "Want to set another mini-goal?"
                ),
            }

        session["state"] = "completed"
        return {
            "type": "completed",
            "message": (
                "✅ You did it! You started. That's the hardest part. "
                "Whether you continue or stop now, you've already won."
            ),
            "celebration": True,
        }

    def check_in(self, user_id: str = "default") -> Optional[dict]:
        """Check in on an active 'Just Begin' session."""
        session = self.active_sessions.get(user_id)
        if not session or session["state"] != "started":
            return None

        return {
            "type": "check_in",
            "message": "How's it going? Remember — you've already done the hard part by starting. You can stop anytime with pride.",
            "options": [
                "Keep going — I'm in a flow!",
                "I've done my 2 minutes, I'm stopping — but I'm proud!",
                "I haven't started yet... help me adjust",
            ],
        }

    def _generate_micro_goal(self, task: str) -> str:
        """Generate an ultra-specific micro goal."""
        task_lower = task.lower()

        if "write" in task_lower:
            return "Write ONE sentence"
        elif "read" in task_lower:
            return "Read ONE paragraph"
        elif "email" in task_lower:
            return "Open your inbox and read ONE email"
        elif "clean" in task_lower:
            return "Set a timer and clean for 2 minutes"
        elif "code" in task_lower or "program" in task_lower:
            return "Open your IDE and fix ONE line"
        elif "study" in task_lower:
            return "Read ONE page or one concept"
        elif "exercise" in task_lower:
            return "Put on your workout clothes (that's the goal)"
        elif "call" in task_lower or "phone" in task_lower:
            return "Dial the number — you can hang up after one ring"
        else:
            return f"Do any tiny part of: {task} for 2 minutes"

    def _get_start_instructions(self, task: str) -> list:
        """Get step-by-step start instructions."""
        return [
            f"1. Take one deep breath",
            f"2. Look at your task: '{task}'",
            f"3. Set a 2-minute timer (yes, just 2 minutes)",
            f"4. Begin the micro-goal: '{self._generate_micro_goal(task)}'",
            f"5. When the timer rings, you can stop — no guilt!",
        ]

    def _format_session(self, session: dict) -> dict:
        """Format session for display."""
        return {
            "type": "just_begin_offer",
            "task": session["task"],
            "commitment": session["commitment"],
            "micro_goal": session["micro_goal"],
            "message": (
                f"I hear you. Instead of thinking about '{session['task']}', "
                f"let's do something ridiculous: just begin for {session['commitment']}. "
                f"Your only goal: {session['micro_goal']}. "
                "After that, you can stop forever if you want. Deal? 🤝"
            ),
        }

    def get_mantra(self) -> str:
        """Get an ADHD-friendly 'just begin' mantra."""
        mantras = [
            "✨ Starting is the only victory I need right now.",
            "⏱️ I can do anything for 2 minutes.",
            "🎯 My only job is to begin. Finishing comes later.",
            "💪 Done is better than perfect. Started is better than nothing.",
            "🌟 The hardest step is the first one. And I've already taken it.",
        ]
        import random
        return random.choice(mantras)
