"""
Productivity Coach Agent
========================
Focuses on motivation, focus guidance, productivity coaching,
and burnout prevention for ADHD users.

Now includes emotionally intelligent response system with
adaptive tone, motivational continuity, and human-like coaching style.
"""

import logging
from typing import Any, Optional
from datetime import datetime, timedelta

from memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class ProductivityCoachAgent:
    """
    Productivity Coach Agent.
    Provides motivation, focus guidance, productivity tips,
    and burnout prevention tailored to the user's pattern.
    
    Improvement: Emotionally intelligent coaching with adaptive tone,
    conversational memory, and human-like encouragement.
    """

    def __init__(self, memory: MemoryManager):
        self.memory = memory
        self.name = "Productivity Coach"

    def get_identity_prompt(self) -> str:
        return (
            "You are the Productivity Coach Agent, an emotionally intelligent ADHD productivity specialist.\\n"
            "- You understand that productivity isn't linear for ADHD brains\\n"
            "- You celebrate small wins and progress, not just completion\\n"
            "- You adapt motivational style based on user's energy and stress\\n"
            "- You recognize hyperfocus vs. productive focus\\n"
            "- You recommend energy-aware productivity strategies\\n"
            "- You give specific, tiny, actionable steps — not vague advice\\n"
            "- You remember what was discussed before and refer back to it\\n"
            "- You adjust your warmth level: warmer when they're struggling, more energetic when they're winning\\n"
            "- Tone: warm, encouraging, realistic, never judgmental — like a supportive friend who understands ADHD"
        )

    def get_emotionally_aware_greeting(self, context: dict) -> str:
        """Generate an emotionally aware opening based on user state."""
        session = context.get("session", {})
        stress = session.get("current_stress", 5)
        mood = session.get("current_mood", "neutral")
        energy = session.get("current_energy", 5)
        turn_count = session.get("turn_count", 0)
        
        # First-time greeting
        if turn_count <= 1:
            if stress >= 7:
                return "Hey, I can sense today might feel heavy. That's okay — we don't need to fix everything right now. Let's just check in: how are you, really?"
            elif energy <= 3:
                return "Hi! You seem a bit low on energy. That's totally fine — we'll keep things super light today. What's one tiny thing that feels doable?"
            else:
                return "Hey there! Great to see you. Let's make today work for *you* — what kind of energy are you bringing?"
        
        # Returning user - reference continuity
        if stress >= 7:
            return "I remember you were dealing with a lot last time. No pressure today — we can just sit with whatever comes up."
        elif energy >= 7 and stress <= 4:
            last_completed = session.get("completed_tasks_count", 0)
            if last_completed > 0:
                return f"You made real progress last session! How are you feeling about continuing that momentum?"
            return "You seem in a good space today! This is a great time to tackle something you've been putting off."
        
        return ""

    def get_encouragement(self, context: dict) -> str:
        """Generate context-aware encouragement that feels human."""
        session = context.get("session", {})
        user = context.get("user", {})
        
        stress = session.get("current_stress", 5)
        turn_count = session.get("turn_count", 0)
        completed = session.get("completed_tasks_count", 0)
        streak = user.get("session_count", 0)
        
        # Progress acknowledgment
        if completed > 0 and turn_count > 1:
            return f"You got things done since we started talking — that's real progress! ADHD brains often don't give themselves credit for the small steps. I see you. 💛"
        
        # Showing up is winning
        if turn_count > 0 and turn_count % 3 == 0:
            return "Just showing up consistently is a HUGE win for ADHD brains. Most people don't understand how much energy that takes. I'm proud of you for being here."
        
        # Streak recognition
        if streak > 0 and streak % 5 == 0:
            return f"You've been showing up consistently. That's not luck — that's you building a system that works for your brain. Keep going at your own pace."
        
        # Gentle for stressed users
        if stress >= 7:
            return "Right now, just breathing is enough. You don't have to earn rest. You don't have to be productive to be worthy. Let's just be here for a moment."
        
        return ""

    def get_suggestion(self, context: dict) -> Optional[dict]:
        user = context.get("user", {})
        session = context.get("session", {})

        stress = session.get("current_stress", 5)
        energy = session.get("current_energy", 5)
        completion_rate = user.get("task_completion_rate", 50)
        focus_hours = user.get("best_focus_hours", [])
        mood = session.get("current_mood", "neutral")

        # High stress — focus on recovery, not productivity
        if stress >= 8:
            return {
                "agent": self.name,
                "type": "recovery",
                "priority": "high",
                "message": "Your stress is high right now. Let's focus on rest and recovery instead of pushing productivity.",
                "suggestions": [
                    "Take a 10-minute break — step away from screens",
                    "Do a quick grounding exercise: name 5 things you can see",
                    "Drink water and stretch for 2 minutes",
                ],
                "tone": "gentle",
            }

        # Low energy — suggest micro-productivity
        if energy <= 3 and stress < 8:
            return {
                "agent": self.name,
                "type": "micro_productivity",
                "priority": "medium",
                "message": "Low energy detected. Let's use the '2-minute rule' — do something for just 2 minutes.",
                "suggestions": [
                    "Pick the absolute smallest task you can finish in 2 minutes",
                    "Set a 2-minute timer and go",
                    "After 2 minutes, decide if you want to continue",
                ],
                "tone": "gentle",
            }

        # Low completion rate — suggest task breaking
        if completion_rate < 40:
            return {
                "agent": self.name,
                "type": "task_breaking",
                "priority": "medium",
                "message": "I notice tasks have been hard to complete. Let's try making them tiny!",
                "suggestions": [
                    "Break your current task into steps of 5 minutes or less",
                    "Focus on just the FIRST step — nothing else",
                    "Reward yourself after each tiny step",
                ],
                "tone": "encouraging",
            }

        # Good focus hours available — suggest timing optimization
        if focus_hours:
            return {
                "agent": self.name,
                "type": "timing_optimization",
                "priority": "low",
                "message": f"Your best focus hours are around {', '.join(focus_hours[:2])}. Try scheduling important tasks then!",
                "suggestions": [
                    f"Reserve your next deep work session during your peak focus time",
                    "Protect that time — no meetings, no notifications",
                    "Start with the hardest task first during this window",
                ],
                "tone": "encouraging",
            }

        return None

    def get_motivational_message(self, context: dict) -> str:
        """Generate a context-aware motivational message."""
        session = context.get("session", {})
        user = context.get("user", {})

        turn_count = session.get("turn_count", 0)
        stress = session.get("current_stress", 5)
        completion = user.get("task_completion_rate", 50)
        mood = session.get("current_mood", "neutral")

        if turn_count > 0 and turn_count % 5 == 0:
            return (
                "🌟 You've been putting in the work! Even showing up consistently "
                "is a huge win for ADHD brains. Take a moment to acknowledge that."
            )
        if completion > 70:
            return (
                "🔥 Amazing consistency! Your task completion rate is looking strong. "
                "Remember, progress > perfection."
            )
        if stress <= 3:
            return ""

        return ""

    def get_system_prompt_extension(self, context: dict) -> str:
        suggestion = self.get_suggestion(context)
        motivational = self.get_motivational_message(context)
        greeting = self.get_emotionally_aware_greeting(context)
        encouragement = self.get_encouragement(context)

        parts = []
        if greeting:
            parts.append(f"[Coach Greeting] {greeting}")
        if encouragement:
            parts.append(f"[Coach Encouragement] {encouragement}")
        if suggestion:
            parts.append(f"[Productivity Coach Insight] {suggestion['message']}")
        if motivational:
            parts.append(f"[Motivation] {motivational}")

        return "\n".join(parts) if parts else ""
