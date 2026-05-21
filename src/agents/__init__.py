"""
ADHD Agent System
=================
Lightweight specialized AI agents for ADHD coaching,
each with focus on a specific domain.

Agents:
  - ProductivityCoachAgent: Motivation, focus guidance, burnout prevention
  - TaskBreakdownAgent: Converts large tasks into microtasks
  - FocusOptimizationAgent: Analyzes focus sessions, optimizes timing
  - MoodBurnoutAgent: Detects emotional exhaustion, provides recovery
  - HabitBuilderAgent: Streak reinforcement, behavioral consistency
  - InterventionAgent: Detects overwhelm, triggers ADHD rescue interventions
  - AccountabilityAgent: Reminders, gentle check-ins, productivity summaries

All agents share a common interface and use the MemoryManager for context.
"""

from .productivity_coach import ProductivityCoachAgent
from .task_breakdown import TaskBreakdownAgent
from .focus_optimization import FocusOptimizationAgent
from .mood_burnout import MoodBurnoutAgent
from .habit_builder import HabitBuilderAgent
from .intervention import InterventionAgent
from .accountability import AccountabilityAgent
from .orchestrator import AgentOrchestrator

__all__ = [
    "ProductivityCoachAgent",
    "TaskBreakdownAgent",
    "FocusOptimizationAgent",
    "MoodBurnoutAgent",
    "HabitBuilderAgent",
    "InterventionAgent",
    "AccountabilityAgent",
    "AgentOrchestrator",
]
