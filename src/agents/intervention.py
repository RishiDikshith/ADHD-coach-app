"""
Intervention Agent
==================
Detects overwhelm, triggers ADHD rescue interventions,
hyperfocus interruption alerts, and grounding exercises.

Upgraded with more nuanced crisis detection, emotionally
intelligent rescues, and human-like grounding support.
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class InterventionAgent:
    """
    Intervention Agent.
    Monitors for crisis signals, provides ADHD rescue interventions,
    grounding exercises, and hyperfocus management.

    Improvement: More nuanced detection of distress levels,
    emotionally intelligent rescue language, and personalized
    grounding exercises based on user state.
    """

    def __init__(self, memory):
        self.memory = memory
        self.name = "Intervention"

    def get_identity_prompt(self) -> str:
        return (
            "You are the Intervention Agent, an emotionally intelligent ADHD crisis companion.\\n"
            "- You detect when the user is overwhelmed, stuck, or in distress\\n"
            "- You know the difference between 'I'm stuck' and 'I'm in crisis'\\n"
            "- You provide immediate grounding and regulation strategies\\n"
            "- You know when to switch from coaching to emotional support\\n"
            "- You recognize hyperfocus and can help transition out of it gently\\n"
            "- You NEVER say things like 'calm down', 'relax', or 'it's not that bad'\\n"
            "- You have a toolkit of ADHD-specific rescue interventions\\n"
            "- Tone: calm, grounding, reassuring, like a steady presence in the storm"
        )

    def detect_intervention_needed(self, user_message: str, context: dict) -> Optional[dict]:
        session = context.get("session", {})
        stress = session.get("current_stress", 5)
        energy = session.get("current_energy", 5)
        mood = session.get("current_mood", "neutral")

        # CRITICAL urgency keywords — genuine distress signals
        critical_urgency = [
            "can't do this", "giving up", "I quit", "too much",
            "can't handle", "going to fail", "hate myself",
            "what's wrong with me", "I'm useless", "I'm a failure",
            "everything is wrong", "can't take it", "want to give up",
            "don't want to be here", "end it", "no point",
            "can't go on", "worthless", "nobody cares",
        ]

        high_urgency = [
            "overwhelmed", "stressed", "stuck", "can't focus",
            "distracted", "frustrated", "exhausted", "tired",
            "struggling", "lost", "confused", "no motivation",
            "can't start", "procrastinating", "avoiding",
            "spiral", "panicking", "breakdown",
        ]

        medium_urgency = [
            "unsure", "worried", "drained", "meh",
            "blah", "okay i guess", "bleh",
        ]

        msg_lower = user_message.lower()

        # 1. Check CRITICAL urgency — immediate emotional support needed
        for keyword in critical_urgency:
            if keyword in msg_lower:
                return {
                    "agent": self.name,
                    "type": "crisis_intervention",
                    "priority": "critical",
                    "urgency": "critical",
                    "message": "I'm here with you. Right now, nothing matters except this moment. Let's just breathe together.",
                    "intervention_type": "crisis_support",
                    "steps": [
                        "🛑 STOP. Put your hand on your chest. Feel your heartbeat.",
                        "🌬️ Breathe in slowly for 4 seconds. Hold for 4. Out for 6.",
                        "🌍 Look around and name 3 things you can physically see right now",
                        "💬 Say to yourself: 'I am safe in this moment. This feeling will pass.'",
                        "📞 If you need to talk to someone, reach out. You don't have to carry this alone.",
                    ],
                    "tone": "steady_presence",
                }

        # 2. Check HIGH urgency with high stress — need grounding
        if stress >= 7:
            for keyword in high_urgency:
                if keyword in msg_lower:
                    return {
                        "agent": self.name,
                        "type": "stress_intervention",
                        "priority": "high",
                        "urgency": "high",
                        "message": "You're dealing with a lot right now. Let's press pause and reset. Nothing else matters except this moment.",
                        "intervention_type": "grounding",
                        "steps": [
                            "🧘 Take 5 slow breaths — in through your nose, out through your mouth. Really slow.",
                            "💧 Drink a glass of cold water — it literally helps reset your nervous system",
                            "✋ Put your hand on your chest and just notice your heartbeat for 10 seconds",
                            "🗣️ Say out loud: 'I am okay right now, in this exact moment'",
                            "🧊 If you can, hold an ice cube or splash cold water on your face",
                        ],
                        "tone": "gentle_grounding",
                    }

        # 3. Check medium urgency with low energy — gentle reset
        if energy <= 3 and any(k in msg_lower for k in medium_urgency):
            return {
                "agent": self.name,
                "type": "low_energy_support",
                "priority": "medium",
                "urgency": "medium",
                "message": "You sound low on energy. That's okay — you don't need to perform right now. Let's just rest for a moment.",
                "intervention_type": "gentle_reset",
                "steps": [
                    "☕ Make yourself a warm drink — tea, coffee, or just hot water with lemon",
                    "🛋️ If you can, lie down for 5 minutes with no phone",
                    "🎵 Put on one song that feels like a warm blanket",
                    "🌬️ Close your eyes and take 5 slow breaths",
                ],
                "tone": "gentle",
            }

        # 4. Hyperfocus detection
        hyperfocus_signals = [
            "lost track of time", "hours passed", "forgot to eat",
            "didn't realize", "can't stop", "hyperfocus",
            "been working for", "can't pull away",
        ]
        if any(s in msg_lower for s in hyperfocus_signals):
            return {
                "agent": self.name,
                "type": "hyperfocus_intervention",
                "priority": "medium",
                "urgency": "medium",
                "message": "It sounds like you're in hyperfocus mode. That focus is incredible — but your body needs check-ins too.",
                "intervention_type": "hyperfocus_transition",
                "steps": [
                    "⏰ Check the current time — how long have you been at this?",
                    "🚽 Take a bathroom break right now (seriously, go)",
                    "💧 Drink water and eat something if you haven't",
                    "👀 Give your eyes a break — look at something 20 feet away for 20 seconds",
                    "🔄 Decide consciously: keep going because you want to, or transition because you should?",
                ],
                "tone": "gentle_reminder",
            }

        return None

    def get_grounding_exercise(self, exercise_type: str = "quick", user_state: str = "neutral") -> dict:
        exercises = {
            "quick": {
                "name": "5-4-3-2-1 Grounding",
                "duration": "1 minute",
                "steps": [
                    "See: Name 5 things you can see around you",
                    "Touch: Name 4 things you can physically feel",
                    "Hear: Name 3 things you can hear right now",
                    "Smell: Name 2 things you can smell (or want to smell)",
                    "Taste: Name 1 thing you can taste",
                ],
                "why_it_helps": "Forces your brain to process sensory information instead of anxious thoughts",
            },
            "breathing": {
                "name": "Box Breathing",
                "duration": "2 minutes",
                "steps": [
                    "Inhale slowly through your nose for 4 seconds",
                    "Hold your breath for 4 seconds",
                    "Exhale slowly through your mouth for 4 seconds",
                    "Hold for 4 seconds",
                    "Repeat 4 times",
                ],
                "why_it_helps": "Activates the parasympathetic nervous system — your 'rest and digest' mode",
            },
            "body": {
                "name": "Body Scan",
                "duration": "3 minutes",
                "steps": [
                    "Close your eyes and bring attention to your feet",
                    "Notice any sensations — temperature, pressure, tension",
                    "Slowly move attention up to your legs, torso, arms, hands",
                    "Notice your jaw — is it clenched? Let it soften",
                    "Take a deep breath and gently open your eyes",
                ],
                "why_it_helps": "Brings you out of your thinking brain and into your body",
            },
        }

        # Add personalized exercises based on user state
        if user_state in ["anxious", "panicking"]:
            exercises["emergency"] = {
                "name": "Emergency Anchor",
                "duration": "30 seconds",
                "steps": [
                    "🧊 Hold something cold (ice cube, cold water bottle)",
                    "🍋 Taste something strong (lemon, sour candy, mint)",
                    "👋 Slap your thighs gently 10 times — sensation brings you back",
                    "🌬️ One long exhale — longer than your inhale",
                ],
                "why_it_helps": "Strong physical sensations can interrupt panic loops",
            }

        return exercises.get(exercise_type, exercises["quick"])

    def get_system_prompt_extension(self, user_message: str, context: dict) -> str:
        intervention = self.detect_intervention_needed(user_message, context)
        if intervention:
            return (
                f"[Intervention Needed] Type: {intervention['intervention_type']}\\n"
                f"Urgency: {intervention.get('urgency', 'medium')}\\n"
                f"Message: {intervention['message']}\\n"
                f"Tone: {intervention['tone']}\\n"
                "CRITICAL: Emotional support is the ONLY priority. All productivity coaching is suspended."
            )
        return ""
