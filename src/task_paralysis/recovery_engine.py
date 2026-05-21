"""
Task Paralysis Recovery Engine
===============================
Orchestrates task paralysis detection, microtask generation,
and 'Just Begin' mode into a cohesive recovery system.
"""

import logging
from typing import Any, Optional

from memory.memory_manager import MemoryManager
from task_paralysis.detector import TaskParalysisDetector
from task_paralysis.microtasks import MicroTaskGenerator
from task_paralysis.just_begin import JustBeginMode

logger = logging.getLogger(__name__)


class TaskParalysisRecoveryEngine:
    """
    Main engine for task paralysis recovery.
    Combines detection, microtask generation, and Just Begin mode
    into a complete recovery workflow.
    """

    def __init__(self, memory: MemoryManager):
        self.memory = memory
        self.detector = TaskParalysisDetector()
        self.microtask_gen = MicroTaskGenerator()
        self.just_begin = JustBeginMode()

    def process_user_message(self, user_message: str, context: dict = None) -> dict:
        """
        Process a user message through the entire recovery pipeline.
        Returns recovery suggestions if task paralysis is detected.
        """
        context = context or {}
        result = {
            "paralysis_detected": False,
            "recovery_suggestions": None,
            "just_begin_offer": None,
            "microtasks": None,
            "severity": "none",
        }

        # Step 1: Detect task paralysis
        detection = self.detector.detect(user_message, context)

        if not detection["detected"]:
            return result

        result["paralysis_detected"] = True
        result["severity"] = detection["level"]

        # Record in memory
        self.memory.set_task_paralysis(True)
        self.memory.record_procrastination_trigger(
            trigger=user_message[:100],
            context=f"Paralysis type: {detection['paralysis_type']}"
        )

        # Step 2: Generate recovery strategy
        recovery_level = detection["level"]
        recovery_type = detection["paralysis_type"]

        # Step 3: Extract task from message if possible
        detected_task = self._extract_task(user_message)

        if recovery_level == "severe":
            # Severe paralysis: Start with grounding, then Just Begin
            result["just_begin_offer"] = self.just_begin.create_begin_session(
                detected_task or "your current task"
            )
            result["recovery_suggestions"] = {
                "priority": "immediate",
                "steps": [
                    "Take 3 deep breaths — you are safe",
                    "Name what you're feeling without judgment",
                    "Try the 'Just Begin' challenge below",
                ],
                "message": detection["message"],
            }

        elif recovery_level == "moderate":
            # Moderate paralysis: Microtasks + Just Begin
            result["microtasks"] = self.microtask_gen.generate_breakthrough_sequence(
                detected_task or "your current task",
                recovery_level
            )
            result["just_begin_offer"] = self.just_begin.create_begin_session(
                detected_task or "your current task"
            )
            result["recovery_suggestions"] = {
                "priority": "high",
                "steps": [m["step"] for m in result["microtasks"][:3]],
                "message": detection["message"],
            }

        else:
            # Mild paralysis: Microtasks
            microtasks = self.microtask_gen.generate_microtasks(
                detected_task or "your current task",
                count=3
            )
            result["microtasks"] = microtasks
            result["recovery_suggestions"] = {
                "priority": "normal",
                "steps": [m["step"] for m in microtasks],
                "message": detection["message"],
            }

        logger.debug(
            f"Task paralysis detected: level={recovery_level}, "
            f"type={recovery_type}, priority={result['recovery_suggestions']['priority']}"
        )

        return result

    def _extract_task(self, message: str) -> Optional[str]:
        """
        Try to extract a task reference from the user message.
        Uses simple pattern matching.
        """
        message_lower = message.lower()

        # Common patterns for task mentions
        patterns = [
            "need to ", "have to ", "should ", "gotta ", "must ",
            "working on ", "trying to ", "supposed to ", "task:",
        ]

        for pattern in patterns:
            if pattern in message_lower:
                idx = message_lower.find(pattern) + len(pattern)
                # Extract text up to next sentence or comma
                remaining = message[idx:].strip()
                # Take up to first sentence end or comma
                import re
                match = re.match(r'^([^.,!?;]+)', remaining)
                if match:
                    task = match.group(1).strip()
                    if len(task) > 5:
                        return task

        return None

    def handle_begin_response(self, accepted: bool, user_id: str = "default") -> dict:
        """Handle user's response to 'Just Begin' offer."""
        if accepted:
            result = self.just_begin.accept_begin(user_id)
            self.memory.record_intervention("just_begin_mode")
            return result
        else:
            # User declined — offer microtask instead
            return {
                "type": "alternative_offered",
                "message": "No pressure! Let's find an even SMALLER step you can take.",
                "suggestions": [
                    "Can you just LOOK at the task for 5 seconds?",
                    "Can you gather ONE item you need for it?",
                    "Can you write ONE word related to it?",
                ],
            }

    def get_system_prompt_extension(self, user_message: str, context: dict) -> str:
        """Generate system prompt extension for task paralysis context."""
        detection = self.detector.detect(user_message, context)

        if not detection["detected"]:
            return ""

        return (
            f"[Task Paralysis Detected] Level: {detection['level']}\n"
            f"Type: {detection['paralysis_type']}\n"
            f"{detection['message']}\n"
            "Recovery priority: {}\n"
            "Adjust coaching: prioritize breaking ALL suggestions into the smallest possible steps. "
            "Suggest the '2-minute rule'. Be extra patient and encouraging."
        )

    def get_stats(self) -> dict:
        """Get statistics about the recovery system."""
        return {
            "detections": self.detector.detection_count,
            "microtasks_generated": self.microtask_gen.generated_count,
            "active_begin_sessions": len(self.just_begin.active_sessions),
        }
