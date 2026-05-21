"""
Task Paralysis Recovery System
===============================
Intelligent system to detect and help users overcome task paralysis.

Features:
- Overwhelm detection from user messages
- AI-generated microtask suggestions
- "Just Begin" mode with 2-minute starters
- Dynamic task simplification based on energy/stress
- Difficulty and energy estimation for tasks
"""

from .detector import TaskParalysisDetector
from .microtasks import MicroTaskGenerator
from .just_begin import JustBeginMode
from .recovery_engine import TaskParalysisRecoveryEngine

__all__ = [
    "TaskParalysisDetector",
    "MicroTaskGenerator",
    "JustBeginMode",
    "TaskParalysisRecoveryEngine",
]
