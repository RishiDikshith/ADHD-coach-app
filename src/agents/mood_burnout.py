"""
Mood & Burnout Agent
====================
Detects emotional exhaustion, analyzes mood trends,
and provides recovery recommendations for ADHD users.

Upgraded with deeper emotional intelligence, adaptive tone,
and human-like emotional continuity.
"""

import logging
from typing import Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class MoodBurnoutAgent:
    """
    Mood & Burnout Agent.
    Monitors emotional state, detects burnout indicators,
    and provides personalized recovery strategies.

    Improvement: Deeper emotional intelligence with empathetic tone,
    personalized recovery that adapts to user's emotional state,
    and conversation continuity.
    """

    def __init__(self, memory):
        self.memory = memory
        self.name = "Mood & Burnout"

    def get_identity_prompt(self) -> str:
        return (
            "You are the Mood & Burnout Agent, an emotionally intelligent ADHD wellness specialist.\\n"
            "- You deeply understand ADHD emotional dysregulation — it's not 'moodiness,' it's neurology\\n"
            "- You recognize the difference between a bad day, burnout, and depression\\n"
            "- You NEVER minimize feelings with empty positivity or 'just cheer up'\\n"
            "- You validate first: 'It makes sense you feel this way given what you're dealing with'\\n"
            "- You provide emotion regulation strategies specifically adapted for ADHD brains\\n"
            "- You know rest is productive for ADHD brains — recovery IS the work sometimes\\n"
            "- You remember emotional patterns and refer back to them gently\\n"
            "- Tone: warm, validating, gentle, like a friend who truly gets it"
        )

    def get_emotional_validation(self, emotion: str, context: dict) -> str:
        """Generate a validating response that normalizes the user's feelings."""
        validations = {
            "overwhelmed": "Feeling overwhelmed is your brain's way of saying 'too much input right now.' That's not a weakness — it's a sign you need to filter. Let's take something off the plate.",
            "anxious": "Anxiety for ADHD brains often comes from 'what if I forget/mess up/miss something.' Your brain is trying to protect you. Let's give it a break.",
            "frustrated": "Frustration often means your brain sees the gap between what you want and what's happening. That's awareness, not failure. Let's close that gap a tiny bit.",
            "sad": "Sadness is valid. ADHD comes with a lot of rejection sensitivity and past struggles. You don't need to 'fix' sad — you're allowed to feel it.",
            "angry": "Anger is energy. For ADHD brains, it often means something feels unfair or blocked. Let's channel that energy somewhere that serves you.",
            "hopeless": "Hopelessness is the heaviest feeling. You don't have to believe things will get better right now. Just stay. Stay in this moment. That's enough.",
            "guilty": "Guilt is so common for ADHD brains — all those 'should haves.' But you didn't 'fail.' Your brain works differently, and you're doing your best with what you have.",
            "ashamed": "Shame whispers 'there's something wrong with me.' But there isn't. You have a brain that works uniquely. Shame keeps us stuck. Let's move toward self-compassion instead.",
        }
        return validations.get(emotion, "That feeling is real and valid. You don't need to justify it or fix it right now. Just let it be here with us.")

    def detect_burnout_risk(self, context: dict) -> Optional[dict]:
        user = context.get("user", {})
        session = context.get("session", {})

        avg_stress = user.get("avg_stress", 5)
        avg_energy = user.get("avg_energy", 5)
        current_stress = session.get("current_stress", 5)
        current_energy = session.get("current_energy", 5)
        completion_rate = user.get("task_completion_rate", 50)
        turn_count = session.get("turn_count", 0)
        current_mood = session.get("current_mood", "neutral")

        risk_score = 0
        signals = []

        if avg_stress >= 7:
            risk_score += 3
            signals.append("sustained high stress")
        if current_stress >= 8:
            risk_score += 2
            signals.append("currently very stressed")

        if avg_energy <= 3:
            risk_score += 2
            signals.append("chronically low energy")
        if current_energy <= 2:
            risk_score += 2
            signals.append("extremely low energy right now")

        if completion_rate < 30:
            risk_score += 2
            signals.append("very low task completion")

        if turn_count >= 10 and current_stress >= 6:
            risk_score += 1
            signals.append("extended engagement with high stress")

        if risk_score == 0:
            return None

        level = "low"
        if risk_score >= 6:
            level = "high"
        elif risk_score >= 3:
            level = "moderate"

        return {
            "agent": self.name,
            "type": "burnout_assessment",
            "priority": "high" if level == "high" else "medium",
            "risk_level": level,
            "risk_score": risk_score,
            "signals": signals,
            "message": self._get_humanized_recommendation(level, signals, current_mood),
            "tone": "gentle",
        }

    def _get_humanized_recommendation(self, level: str, signals: list, mood: str) -> str:
        if level == "high":
            return (
                "I'm genuinely concerned about you. You're showing real signs of burnout — this isn't just a bad day. "
                "Your body and brain are telling you they need rest. Not 'a break so you can be more productive later.' "
                "Real, permission-to-do-nothing rest. Let's focus on that today."
            )
        elif level == "moderate":
            return (
                "I'm noticing some early burnout signals, and I want to catch this before it gets worse. "
                "Think of it like a check engine light — it's telling you something needs attention, "
                "not that the car is broken. Let's adjust your load together."
            )
        return "You're doing okay, but let's keep an eye on these signals. Prevention is easier than recovery."

    def get_recovery_strategies(self, level: str, current_mood: str = "neutral") -> list:
        if level == "high":
            strategies = [
                "🛑 Give yourself FULL permission to rest — no productivity today, no guilt",
                "🌿 Do something that brings you joy with absolutely zero pressure to 'optimize' it",
                "😴 Prioritize sleep tonight — it's the single best burnout recovery tool",
                "📵 Take a 2-hour break from ALL screens (yes, including this one)",
                "🧘 Try a 5-minute body scan — lie down and just notice what your body feels",
            ]
        elif level == "moderate":
            strategies = [
                "☕ Take a proper break — step away from work for 15-30 minutes",
                "✏️ Write down 3 things draining your energy right now (awareness helps)",
                "💬 Talk to someone who doesn't need anything from you",
                "🌳 Spend 10 minutes outside — fresh air changes neurochemistry",
                "🎵 Listen to one song you loved as a teenager (nostalgia dopamine)",
            ]
        else:
            strategies = [
                "✨ You're doing well! Your self-awareness is your superpower",
                "🌟 Take 5 minutes to do something that's 'just for you' today",
                "💧 Check your basic needs: water, food, movement, rest",
            ]
        
        # Personalize based on current mood
        if current_mood in ["overwhelmed", "anxious"]:
            strategies.insert(1, "🧠 Name 3 things you can physically feel right now — chair, feet on floor, air on skin")
        elif current_mood in ["sad", "hopeless"]:
            strategies.insert(1, "☀️ If you can, let sunlight hit your face for 30 seconds. Small sensory shifts help.")
        
        return strategies

    def get_emotion_regulation_tip(self, emotion: str) -> str:
        tips = {
            "overwhelmed": "Try the '5-4-3-2-1' grounding technique: name 5 things you see, 4 you can touch, 3 you hear, 2 you smell, 1 you taste.",
            "anxious": "Box breathing: inhale 4 seconds, hold 4, exhale 4, hold 4. Repeat 4 times. Your nervous system will thank you.",
            "frustrated": "Physical release: do 10 jumping jacks or run in place for 30 seconds. ADHD brains process emotions through the body.",
            "sad": "Opposite action: do one small thing that usually brings you joy, even if you don't feel like it. The action can come before the feeling.",
            "angry": "Use the '6-second rule': wait 6 seconds before responding. Your prefrontal cortex needs time to catch up with your amygdala.",
            "hopeless": "Future visualization: imagine your life 6 months from now after making one small change. What looks different? You don't have to make it happen today.",
            "rejection": "Rejection sensitivity is real. Ask yourself: 'Is this rejection, or is my RSD (Rejection Sensitivity Dysphoria) speaking?' Give it 20 minutes before reacting.",
            "scattered": "Brain dump time: write down EVERYTHING in your head for 2 minutes. No filtering, no organizing. Just get it out.",
        }
        return tips.get(emotion, "Take 5 slow deep breaths. You're safe and this feeling will pass. Feelings are visitors — let them come and go.")

    def get_mood_trend_summary(self, context: dict) -> str:
        """Generate a human-readable summary of recent mood trends."""
        user = context.get("user", {})
        session = context.get("session", {})
        
        mood_trend = user.get("mood_trend", [])
        avg_stress = user.get("avg_stress", 5)
        current_stress = session.get("current_stress", 5)
        current_mood = session.get("current_mood", "neutral")
        
        if not mood_trend:
            return ""
        
        # Determine trend
        if current_stress > avg_stress + 2:
            return "I notice your stress is higher than usual. That's important data — not a problem to solve. Let's just acknowledge that."
        elif current_stress < avg_stress - 1:
            return "You seem calmer than usual today. That's worth noticing. What's different? Let's figure out what's working."
        else:
            return ""

    def get_system_prompt_extension(self, context: dict) -> str:
        burnout = self.detect_burnout_risk(context)
        trend_summary = self.get_mood_trend_summary(context)
        
        parts = []
        if burnout:
            parts.append(
                f"[Burnout Risk Detected] Level: {burnout['risk_level']}\\n"
                f"Signals: {', '.join(burnout['signals'])}\\n"
                f"{burnout['message']}\\n"
                "Adjust coaching style: prioritize emotional support over ALL productivity goals."
            )
        if trend_summary:
            parts.append(f"[Mood Trend] {trend_summary}")
        
        return "\\n\\n".join(parts)
