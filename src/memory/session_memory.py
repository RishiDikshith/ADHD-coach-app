"""
Session Memory module for ADHD coaching.
Tracks the current session context, recent interactions,
and state for continuity across chat turns.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class SessionMemory:
    """
    Lightweight session memory that persists across chat turns.
    Stores the current conversation context, user state, and
    session-level data.

    Unlike ChromaDB (long-term), this is short-term working memory
    that resets between sessions but persists within a session.
    """

    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.session_dir = Path(".session_memories")
        self.session_dir.mkdir(exist_ok=True)

        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_path = self.session_dir / f"{user_id}_{self.session_id}.json"

        # In-memory state (volatile)
        self._state: dict[str, Any] = {
            "user_id": user_id,
            "session_id": self.session_id,
            "started_at": datetime.now().isoformat(),

            # Current conversation context
            "current_topic": None,
            "current_stress_level": 5,
            "current_energy_level": 5,
            "current_mood": "neutral",
            "recent_emotions": [],

            # Active interventions
            "active_interventions": [],
            "intervention_results": [],

            # Task tracking
            "current_tasks": [],
            "completed_tasks": [],
            "struggling_with": None,

            # Focus tracking
            "focus_sessions": [],
            "current_focus_task": None,

            # Conversation turn tracking
            "turn_count": 0,
            "last_user_message": None,
            "last_assistant_message": None,
            "last_interaction_type": None,  # check-in, question, venting, planning, etc.

            # Context flags
            "overwhelm_detected": False,
            "task_paralysis_detected": False,
            "hyperfocus_detected": False,
            "burnout_warning": False,

            # Memory of recent context (for prompt building)
            "recent_context": [],
        }

        self._load()

    def _load(self):
        """Try to restore most recent session."""
        try:
            sessions = sorted(
                self.session_dir.glob(f"{self.user_id}_*.json"),
                reverse=True,
            )
            if sessions:
                # Load the most recent session data
                with open(sessions[0]) as f:
                    saved = json.load(f)
                self._state.update(saved)
                # Generate new session ID but keep useful context
                self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
                self._state["session_id"] = self.session_id
                self._state["started_at"] = datetime.now().isoformat()
                self._state["turn_count"] = 0
                logger.debug(f"Restored session context for {self.user_id}")
        except (json.JSONDecodeError, OSError, IndexError):
            pass

    def save(self):
        """Persist current session state."""
        try:
            with open(self.session_path, "w") as f:
                json.dump(self._state, f, indent=2)
        except OSError as e:
            logger.error(f"Failed to save session: {e}")

    # ---------- State accessors ----------

    @property
    def state(self) -> dict:
        return self._state

    def get(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)

    def set(self, key: str, value: Any):
        self._state[key] = value

    def update(self, data: dict):
        self._state.update(data)

    # ---------- Convenience methods ----------

    def record_turn(self, user_message: str, assistant_message: str, interaction_type: str = "chat"):
        """Record a conversation turn."""
        self._state["turn_count"] += 1
        self._state["last_user_message"] = user_message
        self._state["last_assistant_message"] = assistant_message
        self._state["last_interaction_type"] = interaction_type

        # Keep recent context for prompt building
        self._state["recent_context"].append({
            "turn": self._state["turn_count"],
            "user": user_message[:200],
            "assistant": assistant_message[:200],
            "type": interaction_type,
            "timestamp": datetime.now().isoformat(),
        })

        # Keep last 5 interactions
        if len(self._state["recent_context"]) > 5:
            self._state["recent_context"] = self._state["recent_context"][-5:]

        self.save()

    def record_emotion(self, emotion: str):
        """Record an emotion detected in this session."""
        emotions = self._state["recent_emotions"]
        emotions.append({
            "emotion": emotion,
            "turn": self._state["turn_count"],
            "timestamp": datetime.now().isoformat(),
        })
        if len(emotions) > 20:
            self._state["recent_emotions"] = emotions[-20:]
        self._state["current_mood"] = emotion

    def set_stress(self, level: int):
        """Update current stress level."""
        self._state["current_stress_level"] = max(1, min(10, level))

    def set_energy(self, level: int):
        """Update current energy level."""
        self._state["current_energy_level"] = max(1, min(10, level))

    def add_task(self, task: str, source: str = "ai"):
        """Add a task to current session."""
        self._state["current_tasks"].append({
            "task": task,
            "source": source,
            "added_at": datetime.now().isoformat(),
            "completed": False,
        })

    def complete_task(self, task_index: int):
        """Mark a task as completed."""
        tasks = self._state["current_tasks"]
        if 0 <= task_index < len(tasks):
            tasks[task_index]["completed"] = True
            tasks[task_index]["completed_at"] = datetime.now().isoformat()
            self._state["completed_tasks"].append(tasks[task_index])

    def set_overwhelm(self, detected: bool):
        """Set overwhelm detection flag."""
        self._state["overwhelm_detected"] = detected

    def set_task_paralysis(self, detected: bool):
        """Set task paralysis detection flag."""
        self._state["task_paralysis_detected"] = detected

    def add_intervention(self, intervention: str):
        """Track an active intervention."""
        self._state["active_interventions"].append({
            "intervention": intervention,
            "applied_at": datetime.now().isoformat(),
            "effective": None,  # Will be set later
        })

    def mark_intervention_result(self, intervention: str, effective: bool):
        """Mark whether an intervention was effective."""
        for inv in self._state["active_interventions"]:
            if inv["intervention"] == intervention:
                inv["effective"] = effective
                break
        self._state["intervention_results"].append({
            "intervention": intervention,
            "effective": effective,
            "timestamp": datetime.now().isoformat(),
        })

    def get_context_summary(self) -> dict:
        """
        Build a compact summary of session context for AI prompt injection.
        """
        return {
            "turn_count": self._state["turn_count"],
            "current_mood": self._state["current_mood"],
            "current_stress": self._state["current_stress_level"],
            "current_energy": self._state["current_energy_level"],
            "overwhelm_detected": self._state["overwhelm_detected"],
            "task_paralysis_detected": self._state["task_paralysis_detected"],
            "hyperfocus_detected": self._state["hyperfocus_detected"],
            "active_tasks": [
                t["task"] for t in self._state["current_tasks"]
                if not t.get("completed")
            ],
            "completed_tasks_count": len(self._state["completed_tasks"]),
            "recent_context": self._state["recent_context"][-3:],
            "last_interaction_type": self._state["last_interaction_type"],
        }

    def get_summary_text(self) -> str:
        """Generate a short human-readable session summary."""
        s = self._state
        parts = []
        parts.append(f"Turn {s['turn_count']}")
        parts.append(f"Mood: {s['current_mood']}")
        parts.append(f"Stress: {s['current_stress_level']}/10")
        parts.append(f"Energy: {s['current_energy_level']}/10")

        if s["overwhelm_detected"]:
            parts.append("⚠️ Overwhelm detected")
        if s["task_paralysis_detected"]:
            parts.append("⚠️ Task paralysis detected")
        if s["hyperfocus_detected"]:
            parts.append("⚠️ Hyperfocus detected")

        return " | ".join(parts)

    def clear(self):
        """Clear session state."""
        self._state = {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "started_at": datetime.now().isoformat(),
            "current_topic": None,
            "current_stress_level": 5,
            "current_energy_level": 5,
            "current_mood": "neutral",
            "recent_emotions": [],
            "active_interventions": [],
            "intervention_results": [],
            "current_tasks": [],
            "completed_tasks": [],
            "struggling_with": None,
            "focus_sessions": [],
            "current_focus_task": None,
            "turn_count": 0,
            "last_user_message": None,
            "last_assistant_message": None,
            "last_interaction_type": None,
            "overwhelm_detected": False,
            "task_paralysis_detected": False,
            "hyperfocus_detected": False,
            "burnout_warning": False,
            "recent_context": [],
        }
        self.save()
