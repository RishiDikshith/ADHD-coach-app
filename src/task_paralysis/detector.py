"""
Task Paralysis Detector
=======================
Detects when a user is experiencing task paralysis or overwhelm
based on their messages and behavioral context.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class TaskParalysisDetector:
    """
    Detects task paralysis signals from user messages and behavioral data.
    Uses keyword analysis, context evaluation, and pattern recognition.
    """

    # High-confidence paralysis signals
    PARALYSIS_KEYWORDS_HIGH = {
        "can't start", "can't even", "stuck", "frozen", "paralyzed",
        "can't move", "too overwhelmed to", "don't know where to start",
        "can't do anything", "staring at", "blank screen", "just sitting",
        "can't bring myself", "too much to do", "don't know how to start",
    }

    # Medium-confidence signals
    PARALYSIS_KEYWORDS_MEDIUM = {
        "overwhelmed", "too much", "too hard", "too big", "too many",
        "procrastinating", "avoiding", "putting off", "can't focus",
        "distracted", "can't decide", "don't know what to do",
        "spinning", "going in circles", "can't think straight",
        "brain fog", "mental block", "dreading",
    }

    # Avoidance behavior signals
    AVOIDANCE_KEYWORDS = {
        "scrolling", "watching videos", "cleaning instead", "organizing",
        "checking email", "social media", "phone", "anyone else",
        "doing anything but", "busy work", "avoiding",
    }

    def __init__(self):
        self.detection_count = 0

    def detect(self, user_message: str, context: dict = None) -> dict:
        """
        Detect task paralysis severity and type.
        Returns a structured detection result.
        """
        msg_lower = user_message.lower()
        context = context or {}

        # Check for high-confidence signals
        high_matches = {kw for kw in self.PARALYSIS_KEYWORDS_HIGH if kw in msg_lower}

        # Check for medium-confidence signals
        medium_matches = {kw for kw in self.PARALYSIS_KEYWORDS_MEDIUM if kw in msg_lower}

        # Check for avoidance signals
        avoidance_matches = {kw for kw in self.AVOIDANCE_KEYWORDS if kw in msg_lower}

        # Context factors
        stress = context.get("session", {}).get("current_stress", 5)
        energy = context.get("session", {}).get("current_energy", 5)
        overwhelm_flag = context.get("session", {}).get("overwhelm_detected", False)

        # Calculate severity
        severity = 0
        if high_matches:
            severity += 3
        if medium_matches:
            severity += 2
        if avoidance_matches:
            severity += 1
        if stress >= 7:
            severity += 2
        if energy <= 3:
            severity += 1
        if overwhelm_flag:
            severity += 2

        # Determine level
        if severity >= 5:
            level = "severe"
        elif severity >= 3:
            level = "moderate"
        elif severity >= 1:
            level = "mild"
        else:
            level = "none"

        paralysis_type = self._determine_type(high_matches, medium_matches, avoidance_matches)

        if level != "none":
            self.detection_count += 1

        return {
            "detected": level != "none",
            "level": level,
            "severity_score": severity,
            "paralysis_type": paralysis_type,
            "signals": {
                "high_confidence": list(high_matches),
                "medium_confidence": list(medium_matches),
                "avoidance": list(avoidance_matches),
            },
            "context_factors": {
                "stress": stress,
                "energy": energy,
                "overwhelm_flag": overwhelm_flag,
            },
            "message": self._get_message(level, paralysis_type),
        }

    def _determine_type(self, high: set, medium: set, avoidance: set) -> str:
        """Determine the type of paralysis."""
        if high or ("brain fog" in medium or "can't think" in medium):
            return "cognitive_paralysis"
        if any("decide" in kw for kw in medium):
            return "decision_paralysis"
        if avoidance:
            return "avoidance_pattern"
        if any("procrastinat" in kw for kw in medium):
            return "procrastination_cycle"
        return "general_overwhelm"

    def _get_message(self, level: str, paralysis_type: str) -> str:
        """Get supportive message based on level and type."""
        messages = {
            "severe": "You're experiencing significant task paralysis right now. This is a common ADHD challenge, not a personal failure. Let's start with something so tiny it feels almost silly.",
            "moderate": "I can sense you're feeling stuck. That's completely normal and there's a way through it. Let's find one micro-step you can take.",
            "mild": "There might be a hint of resistance to starting. Let's make the first step as easy as possible.",
        }
        return messages.get(level, "")

    def get_recovery_urgency(self, level: str) -> str:
        """Get how urgently recovery is needed."""
        urgency_map = {
            "severe": "immediate",
            "moderate": "high",
            "mild": "normal",
        }
        return urgency_map.get(level, "none")
