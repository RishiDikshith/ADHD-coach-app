"""
Agent Orchestrator
==================
Lightweight orchestrator that coordinates all ADHD agents,
injects their context into AI prompts, and manages agent lifecycle.
Upgraded to support multi-chatbot prompt routing and cross-agent handoffs.
"""

import logging
from typing import Any, Optional

from memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Coordinates all specialized ADHD agents.
    Provides a unified interface for:
    - Building system prompt extensions
    - Getting agent suggestions
    - Detecting intervention needs
    - Managing agent lifecycle
    - Routing chat requests to specialized chatbots
    - Generating intelligent chatbot handoffs
    """

    _agent_classes = None

    def __init__(self, memory: MemoryManager):
        self.memory = memory
        self.agents = {}
        self._init_agents()

    def _init_agents(self):
        """Initialize all specialized agents with shared memory."""
        if self._agent_classes is None:
            from agents.productivity_coach import ProductivityCoachAgent
            from agents.task_breakdown import TaskBreakdownAgent
            from agents.focus_optimization import FocusOptimizationAgent
            from agents.mood_burnout import MoodBurnoutAgent
            from agents.habit_builder import HabitBuilderAgent
            from agents.intervention import InterventionAgent
            from agents.accountability import AccountabilityAgent
            from agents.study_assistant import StudyAssistantAgent

            self._agent_classes = {
                "productivity_coach": ProductivityCoachAgent,
                "task_breakdown": TaskBreakdownAgent,
                "focus_optimization": FocusOptimizationAgent,
                "mood_burnout": MoodBurnoutAgent,
                "habit_builder": HabitBuilderAgent,
                "intervention": InterventionAgent,
                "accountability": AccountabilityAgent,
                "study_assistant": StudyAssistantAgent,
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

    def detect_handoff_suggestion(self, user_message: str, current_agent_id: str) -> Optional[dict]:
        """
        Analyze user message along with real-time mood/stress levels to route 
        the user to the best chatbot agent.
        """
        msg_lower = user_message.lower()

        # Get active session state from memory
        session_state = self.memory.session.state if self.memory and self.memory.session else {}
        
        # Guard against MagicMock in testing or non-numeric types
        stress = session_state.get("current_stress", 5)
        if hasattr(stress, "__class__") and "Mock" in stress.__class__.__name__:
            stress = 5
        elif not isinstance(stress, (int, float)):
            try:
                stress = float(stress)
            except Exception:
                stress = 5

        energy = session_state.get("current_energy", 5)
        if hasattr(energy, "__class__") and "Mock" in energy.__class__.__name__:
            energy = 5
        elif not isinstance(energy, (int, float)):
            try:
                energy = float(energy)
            except Exception:
                energy = 5

        mood = session_state.get("current_mood", "neutral")
        if hasattr(mood, "__class__") and "Mock" in mood.__class__.__name__:
            mood = "neutral"
        elif not isinstance(mood, str):
            mood = str(mood)

        # 1. Handoff to Burnout Support if stress is high (>=8) or user talks about exhaustion, burnout, severe overwhelm, or resting guilt
        burnout_triggers = ["overwhelm", "stressed", "burnout", "burnt out", "anxious", "panic", "guilt", "resting", "tired", "exhausted", "shame", "can't take it"]
        if current_agent_id != "burnout-support" and (stress >= 8 or any(t in msg_lower for t in burnout_triggers)):
            return {
                "agent_id": "burnout-support",
                "message": "I'm noticing your stress levels are very high right now, and you might be feeling overwhelmed or exhausted. Let's step away from productivity. Would you like to switch to Burnout Support for some gentle, shame-free grounding? 🌿"
            }

        # 2. Handoff to Task Breakdown if stress is elevated (>=6) or they discuss starting, big tasks, or procrastination/avoidance
        task_triggers = ["big task", "massive project", "overwhelming project", "don't know where to start", "stuck on starting", "cant start", "procrastinating", "putting off", "break down", "start"]
        if current_agent_id != "task-breakdown" and (stress >= 6 or any(t in msg_lower for t in task_triggers)):
            return {
                "agent_id": "task-breakdown",
                "message": "It feels like starting this task is bringing up some stress and friction. Would you like to switch to Task Breakdown to slice this heavy task into tiny, ridiculous 2-minute steps? 🔨"
            }

        # 3. Handoff to Focus Coach if distracted, scrolling, or they need timer help
        focus_triggers = ["distracted", "can't focus", "scrolling", "phone distraction", "timer", "pomodoro", "concentration", "distraction", "attention"]
        if current_agent_id != "focus-coach" and any(t in msg_lower for t in focus_triggers):
            return {
                "agent_id": "focus-coach",
                "message": "Struggling with distractions or keeping your attention locked in? Would you like to switch to Focus Coach to open a Pomodoro flow and shield your focus? 🎯"
            }

        # 4. Handoff to Mood Support if they want to journal/reflect, or if their emotional state is negative and they mention talking/reflecting
        mood_triggers = ["journal", "diary", "mood", "feeling low", "sad", "angry", "emotional", "vent"]
        if current_agent_id != "mood-support" and (any(t in msg_lower for t in mood_triggers) or mood in ["sad", "frustrated", "angry"]):
            return {
                "agent_id": "mood-support",
                "message": "You're holding some heavy feelings right now. Would you like to switch to Mood Support to safely vent, journal, or process these emotions together? 😌"
            }

        # 5. Handoff to Habit Builder if talking about routines, consistency, streaks, or morning/night stacks
        habit_triggers = ["habit", "routine", "morning routine", "night routine", "consistency", "stick to", "streak", "stack"]
        if current_agent_id != "habit-builder" and any(t in msg_lower for t in habit_triggers):
            return {
                "agent_id": "habit-builder",
                "message": "Are you working on building a new routine or staying consistent? Let's switch to Habit Builder to design a low-friction routine with a dopamine-rich loop! 🔄"
            }

        # 6. Handoff to Study Assistant if talking about academic topics (exams, homework, revision, paper)
        study_triggers = ["study", "revision", "exam", "assignment", "paper", "homework", "school", "college", "test", "academic"]
        if current_agent_id != "study-assistant" and any(t in msg_lower for t in study_triggers):
            return {
                "agent_id": "study-assistant",
                "message": "Tackling academic revision, exam prep, or writing a paper? Let's switch to Study Assistant to design a realistic revision split! 🎓"
            }

        # 7. Handoff to Accountability Coach if celebrating a win, sharing check-ins, or wanting an active check-in
        accountability_triggers = ["accomplished", "finished", "did it", "done", "check in", "celebrate", "win"]
        if current_agent_id != "accountability-coach" and any(t in msg_lower for t in accountability_triggers):
            return {
                "agent_id": "accountability-coach",
                "message": "Celebrating a win or want a friendly, zero-judgment check-in on your goals? Let's switch to Accountability Coach to lock in your success! 🤝"
            }

        return None

    def build_agent_specific_prompt(
        self,
        agent_id: str,
        user_message: str,
        context: dict,
        current_streak: int = 0,
    ) -> str:
        """
        Builds a custom system prompt injecting shared global context, specialized memory,
        and chatbot-specific personality.
        """
        from agents.chatbot_registry import get_chatbot_system_prompt, retrieve_specialized_memory

        # 1. Get the custom chatbot base prompt
        system_prompt = get_chatbot_system_prompt(agent_id)

        # 2. Retrieve specialized local memory context
        specialized_memory = retrieve_specialized_memory(agent_id, self.memory)

        # 3. Assemble full system prompt extension
        parts = []

        if specialized_memory:
            parts.append(f"[SPECIALIZED LOCAL MEMORY FOR {agent_id.upper()}]\n{specialized_memory}")

        # Add any high-priority insights from specific agents (like task breakdown, focus, etc.)
        agent_insights = self.build_combined_prompt_extension(agent_id, user_message, context, current_streak)
        if agent_insights:
            parts.append(agent_insights)

        combined_context = "\n\n".join(parts)

        return system_prompt + "\n\n" + combined_context

    def build_combined_prompt_extension(
        self,
        agent_id: str,
        user_message: str,
        context: dict,
        current_streak: int = 0,
    ) -> str:
        """Build combined system prompt extension from standard heuristic agents based on active agent role."""
        if agent_id == "support-agent":
            return ""

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
        if agent_id == "task-breakdown":
            task_breakdown = self.agents.get("task_breakdown")
            if task_breakdown:
                try:
                    ext = task_breakdown.get_system_prompt_extension(user_message, context)
                    if ext:
                        parts.append(ext)
                except Exception as e:
                    logger.debug(f"Task Breakdown agent error: {e}")

        # 3. Mood & Burnout Agent
        if agent_id in ["mood-support", "burnout-support"]:
            mood = self.agents.get("mood_burnout")
            if mood:
                try:
                    ext = mood.get_system_prompt_extension(context)
                    if ext:
                        parts.append(ext)
                except Exception as e:
                    logger.debug(f"Mood/Burnout agent error: {e}")

        # 4. Focus Optimization Agent (maps to focus-coach)
        if agent_id == "focus-coach":
            focus = self.agents.get("focus_optimization")
            if focus:
                try:
                    ext = focus.get_system_prompt_extension(context)
                    if ext:
                        parts.append(ext)
                except Exception as e:
                    logger.debug(f"Focus agent error: {e}")

        # 5. Productivity Coach Agent
        if agent_id == "productivity-coach":
            coach = self.agents.get("productivity_coach")
            if coach:
                try:
                    ext = coach.get_system_prompt_extension(context)
                    if ext:
                        parts.append(ext)
                except Exception as e:
                    logger.debug(f"Productivity coach error: {e}")

        # 6. Habit Builder Agent
        if agent_id == "habit-builder":
            habit = self.agents.get("habit_builder")
            if habit:
                try:
                    ext = habit.get_system_prompt_extension(context, current_streak)
                    if ext:
                        parts.append(ext)
                except Exception as e:
                    logger.debug(f"Habit builder error: {e}")

        # 7. Accountability Agent
        if agent_id == "accountability-coach":
            accountability = self.agents.get("accountability")
            if accountability:
                try:
                    ext = accountability.get_system_prompt_extension(context)
                    if ext:
                        parts.append(ext)
                except Exception as e:
                    logger.debug(f"Accountability agent error: {e}")

        # 8. Study Assistant Agent
        if agent_id == "study-assistant":
            study = self.agents.get("study_assistant")
            if study:
                try:
                    ext = study.get_system_prompt_extension(context)
                    if ext:
                        parts.append(ext)
                except Exception as e:
                    logger.debug(f"Study Assistant agent error: {e}")

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

            # Study recommendations
            study = self.agents.get("study_assistant")
            if study:
                rec = study.get_study_recommendation(context)
                if rec:
                    suggestions.append(rec)

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

    def get_context_for_prompt(self, user_message: str, current_streak: int = 0, agent_id: str = "productivity-coach") -> dict:
        """
        Build complete context dict for prompt injection.
        Combines memory context, agent insights, and suggestions.
        """
        # Get base context from memory
        context = self.memory.build_context_for_prompt()

        # Add agent insights
        agent_extension = self.build_combined_prompt_extension(
            agent_id, user_message, context, current_streak
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

