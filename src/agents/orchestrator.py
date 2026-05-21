"""
Agent Orchestrator
==================
Lightweight orchestrator that coordinates all 7 ADHD agents,
injects their context into AI prompts, and manages agent lifecycle.
"""

import logging
from typing import Any, Optional

from memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Coordinates all 7 specialized ADHD agents.
    Provides a unified interface for:
    - Building system prompt extensions
    - Getting agent suggestions
    - Detecting intervention needs
    - Managing agent lifecycle
    """

    _agent_classes = None

    def __init__(self, memory: MemoryManager):
        self.memory = memory
        self.agents = {}
        self._init_agents()

    def _init_agents(self):
        """Initialize all 7 agents with shared memory."""
        if self._agent_classes is None:
            from agents.productivity_coach import ProductivityCoachAgent
            from agents.task_breakdown import TaskBreakdownAgent
            from agents.focus_optimization import FocusOptimizationAgent
            from agents.mood_burnout import MoodBurnoutAgent
            from agents.habit_builder import HabitBuilderAgent
            from agents.intervention import InterventionAgent
            from agents.accountability import AccountabilityAgent

            self._agent_classes = {
                "productivity_coach": ProductivityCoachAgent,
                "task_breakdown": TaskBreakdownAgent,
                "focus_optimization": FocusOptimizationAgent,
                "mood_burnout": MoodBurnoutAgent,
                "habit_builder": HabitBuilderAgent,
                "intervention": InterventionAgent,
                "accountability": AccountabilityAgent,
            }

        for name, cls in self._agent_classes.items():
            try:
                self.agents[name] = cls(self.memory)
            except Exception as e:
                logger.warning(f"Failed to initialize agent '{name}': {e}")

        logger.debug(f"Initialized {len(self.agents)} agents")

    def get_agent(self, name: str):
        """Get a specific agent by name."""
        return self.agents.get(name)

    def get_all_agents(self) -> dict:
        """Get all initialized agents."""
        return dict(self.agents)

    def get_all_identity_prompts(self) -> str:
        """Get all agent identity prompts as a formatted block."""
        prompts = []
        for name, agent in self.agents.items():
            try:
                prompt = agent.get_identity_prompt()
                if prompt:
                    prompts.append(prompt)
            except Exception as e:
                logger.debug(f"Error getting identity prompt for {name}: {e}")

        return "\n\n".join(prompts)

    def build_combined_prompt_extension(
        self,
        user_message: str,
        context: dict,
        current_streak: int = 0,
        existing_habits: list = None,
    ) -> str:
        """
        Build a combined system prompt extension from all agents.
        This is the primary method used by the chat system.
        """
        parts = []
        parts.append("[ADHD AGENT INSIGHTS]")

        # 1. Intervention Agent (highest priority — detect crises first)
        intervention = self.agents.get("intervention")
        if intervention:
            try:
                ext = intervention.get_system_prompt_extension(user_message, context)
                if ext:
                    parts.append(ext)
            except Exception as e:
                logger.debug(f"Intervention agent error: {e}")

        # 2. Task Breakdown Agent (detect task paralysis)
        task_breakdown = self.agents.get("task_breakdown")
        if task_breakdown:
            try:
                ext = task_breakdown.get_system_prompt_extension(user_message, context)
                if ext:
                    parts.append(ext)
            except Exception as e:
                logger.debug(f"Task Breakdown agent error: {e}")

        # 3. Mood & Burnout Agent
        mood = self.agents.get("mood_burnout")
        if mood:
            try:
                ext = mood.get_system_prompt_extension(context)
                if ext:
                    parts.append(ext)
            except Exception as e:
                logger.debug(f"Mood/Burnout agent error: {e}")

        # 4. Focus Optimization Agent
        focus = self.agents.get("focus_optimization")
        if focus:
            try:
                ext = focus.get_system_prompt_extension(context)
                if ext:
                    parts.append(ext)
            except Exception as e:
                logger.debug(f"Focus agent error: {e}")

        # 5. Productivity Coach Agent
        coach = self.agents.get("productivity_coach")
        if coach:
            try:
                ext = coach.get_system_prompt_extension(context)
                if ext:
                    parts.append(ext)
            except Exception as e:
                logger.debug(f"Productivity coach error: {e}")

        # 6. Habit Builder Agent
        habit = self.agents.get("habit_builder")
        if habit:
            try:
                ext = habit.get_system_prompt_extension(context, current_streak)
                if ext:
                    parts.append(ext)
            except Exception as e:
                logger.debug(f"Habit builder error: {e}")

        # 7. Accountability Agent
        accountability = self.agents.get("accountability")
        if accountability:
            try:
                ext = accountability.get_system_prompt_extension(context)
                if ext:
                    parts.append(ext)
            except Exception as e:
                logger.debug(f"Accountability agent error: {e}")

        return "\n\n".join(parts)

    def get_agent_suggestions(self, context: dict, current_streak: int = 0) -> list:
        """Get structured suggestions from all agents."""
        suggestions = []

        try:
            # Productivity Coach
            coach = self.agents.get("productivity_coach")
            if coach:
                suggestion = coach.get_suggestion(context)
                if suggestion:
                    suggestions.append(suggestion)

            # Task Breakdown
            task = self.agents.get("task_breakdown")
            if task and context.get("session", {}).get("active_tasks"):
                first_task = context["session"]["active_tasks"][0]
                breakdown = task.suggest_breakdown(first_task, context)
                if breakdown:
                    suggestions.append(breakdown)

            # Focus recommendations
            focus = self.agents.get("focus_optimization")
            if focus:
                rec = focus.get_focus_recommendation(context)
                if rec:
                    suggestions.append(rec)

            # Burnout assessment
            mood = self.agents.get("mood_burnout")
            if mood:
                burnout = mood.detect_burnout_risk(context)
                if burnout:
                    suggestions.append(burnout)

            # Habit recommendations
            habit = self.agents.get("habit_builder")
            if habit:
                rec = habit.get_habit_recommendation(context)
                if rec:
                    suggestions.append(rec)

            # Accountability summary
            accountability = self.agents.get("accountability")
            if accountability:
                summary = accountability.generate_session_summary(context)
                if summary:
                    suggestions.append(summary)

        except Exception as e:
            logger.error(f"Error collecting agent suggestions: {e}")

        # Sort by priority: critical > high > medium > low
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        suggestions.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 4))

        return suggestions

    def detect_and_respond_to_intervention(self, user_message: str, context: dict) -> Optional[dict]:
        """Check if an immediate intervention is needed and return it."""
        intervention = self.agents.get("intervention")
        if intervention:
            try:
                return intervention.detect_intervention_needed(user_message, context)
            except Exception as e:
                logger.debug(f"Intervention detection error: {e}")
        return None

    def get_context_for_prompt(self, user_message: str, current_streak: int = 0) -> dict:
        """
        Build complete context dict for prompt injection.
        Combines memory context, agent insights, and suggestions.
        """
        # Get base context from memory
        context = self.memory.build_context_for_prompt()

        # Add agent insights
        agent_extension = self.build_combined_prompt_extension(
            user_message, context, current_streak
        )
        context["agent_insights"] = agent_extension

        # Add structured suggestions
        suggestions = self.get_agent_suggestions(context, current_streak)
        context["agent_suggestions"] = suggestions

        # Check for interventions
        intervention = self.detect_and_respond_to_intervention(user_message, context)
        if intervention:
            context["intervention"] = intervention

        return context

    def get_stats(self) -> dict:
        """Get orchestrator statistics."""
        return {
            "agents_initialized": len(self.agents),
            "agent_names": list(self.agents.keys()),
            "memory_stats": self.memory.get_stats() if self.memory else {},
        }
