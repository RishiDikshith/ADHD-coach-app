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

from .accountability import AccountabilityAgent
from .focus_optimization import FocusOptimizationAgent
from .habit_builder import HabitBuilderAgent
from .intervention import InterventionAgent
from .mood_burnout import MoodBurnoutAgent
from .orchestrator import AgentOrchestrator
from .productivity_coach import ProductivityCoachAgent
from .task_breakdown import TaskBreakdownAgent

__all__ = [
    "AccountabilityAgent",
    "AgentOrchestrator",
    "FocusOptimizationAgent",
    "HabitBuilderAgent",
    "InterventionAgent",
    "MoodBurnoutAgent",
    "ProductivityCoachAgent",
    "TaskBreakdownAgent",
]
