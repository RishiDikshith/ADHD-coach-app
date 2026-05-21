"""
RAG Engine (Retrieval Augmented Generation)
============================================
Retrieves relevant context from memory, facts, and database before LLM generation.
This is the missing piece for factual recall and persistent personalization.

Architecture:
- Multi-source retrieval (chromaDB memory, structured facts, chat history, mood trends)
- Re-ranking by relevance and recency
- Context window optimization (fits within LLM context limits)
- Query expansion for better retrieval
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class RAGEngine:
    """
    Retrieval Augmented Generation engine.
    Gathers context from multiple sources before response generation.
    """

    def __init__(self, memory_manager=None, db_manager=None):
        self.memory = memory_manager
        self.db = db_manager

    def retrieve_context(
        self,
        username: str,
        query: str,
        user_data: Optional[dict] = None,
        session_data: Optional[dict] = None,
        max_tokens: int = 2000,
    ) -> str:
        """
        Retrieve and assemble relevant context from all memory sources.
        Returns a formatted string for LLM prompt injection.

        Sources:
        1. Structured facts about the user (preferences, habits, goals)
        2. Recent emotional/mood trends
        3. Recent conversation history
        4. Session context (current stress, energy, state)
        5. Focus and intervention history
        6. Behavioral patterns and insights
        """
        parts = []

        # 1. Structured facts
        parts.append(self._get_fact_context(username))

        # 2. Emotional/mood trends
        parts.append(self._get_mood_context(username))

        # 3. Recent conversations from ChromaDB
        parts.append(self._get_memory_context(query))

        # 4. Session context
        parts.append(self._get_session_context(user_data, session_data))

        # 5. Focus and intervention history
        parts.append(self._get_activity_context(username))

        # 6. Behavioral insights
        parts.append(self._get_insight_context(username))

        # Filter empty parts and assemble
        non_empty = [p for p in parts if p]
        if not non_empty:
            return ""

        result = "\n\n".join(non_empty)

        # Truncate to max_tokens (rough char estimate)
        max_chars = max_tokens * 4
        if len(result) > max_chars:
            result = result[:max_chars]
            # Try to cut at a sentence boundary
            last_period = result.rfind(".")
            if last_period > max_chars // 2:
                result = result[:last_period + 1]

        return result

    def _get_fact_context(self, username: str) -> str:
        """Get structured facts about the user."""
        if not self.memory or not hasattr(self.memory, 'get_fact_context_for_prompt'):
            return ""

        try:
            fact_context = self.memory.get_fact_context_for_prompt()
            if fact_context:
                return fact_context
        except Exception as e:
            logger.debug(f"Fact context retrieval error: {e}")

        return ""

    def _get_mood_context(self, username: str) -> str:
        """Get recent emotional/mood trends."""
        if not self.db:
            return ""

        try:
            # Get 7-day mood summary
            mood_summary = self.db.get_mood_summary(username, days=7)
            if mood_summary and mood_summary.get("entry_count", 0) > 0:
                lines = ["[Mood Trend (7 days)]"]
                if mood_summary.get("avg_energy"):
                    lines.append(f"Average Energy: {mood_summary['avg_energy']}/10")
                if mood_summary.get("avg_focus"):
                    lines.append(f"Average Focus: {mood_summary['avg_focus']}/10")
                if mood_summary.get("avg_burnout"):
                    lines.append(f"Average Burnout: {mood_summary['avg_burnout']}/10")
                if mood_summary.get("avg_anxiety"):
                    lines.append(f"Average Anxiety: {mood_summary['avg_anxiety']}/10")
                if mood_summary.get("most_common_mood"):
                    lines.append(f"Most Common Mood: {mood_summary['most_common_mood']}")
                lines.append(f"Entries this week: {mood_summary['entry_count']}")
                return "\n".join(lines)

            # Check for recent emotions from chat
            emotions = self.db.get_recent_emotions(username, days=3)
            if emotions:
                emotion_counts = {}
                for e in emotions:
                    em = e.get("emotion", "neutral")
                    emotion_counts[em] = emotion_counts.get(em, 0) + 1
                total = sum(emotion_counts.values())
                if total > 0:
                    dominant = max(emotion_counts, key=emotion_counts.get)
                    return f"[Recent Emotions] Dominant: {dominant} | Entries: {total}"
        except Exception as e:
            logger.debug(f"Mood context retrieval error: {e}")

        return ""

    def _get_memory_context(self, query: str) -> str:
        """Get relevant memories from ChromaDB based on query similarity."""
        if not self.memory or not hasattr(self.memory, 'search_memories'):
            return ""

        try:
            # Semantic search for relevant memories
            results = self.memory.search_memories(query, n_results=5)
            if results:
                lines = ["[Relevant Memories]"]
                for r in results:
                    content = r.get("content", "")
                    if content:
                        lines.append(f"• {content[:200]}")
                return "\n".join(lines)
        except Exception as e:
            logger.debug(f"Memory context retrieval error: {e}")

        # Fallback to recent memories
        try:
            all_recent = self.memory.store.get_recent(limit=5)
            if all_recent:
                lines = ["[Recent Interactions]"]
                for r in all_recent:
                    content = r.get("content", "")
                    if content:
                        lines.append(f"• {content[:150]}")
                return "\n".join(lines)
        except Exception as e:
            logger.debug(f"Recent memory retrieval error: {e}")

        return ""

    def _get_session_context(self, user_data: Optional[dict], session_data: Optional[dict]) -> str:
        """Get current session context."""
        if not user_data and not session_data:
            return ""
        data = user_data or {}
        session = session_data or {}

        lines = ["[Current Session Context]"]
        if data.get("stress_level"):
            lines.append(f"Stress: {data['stress_level']}/10")
        if data.get("energy_level"):
            lines.append(f"Energy: {data['energy_level']}/10")
        if data.get("sleep_hours"):
            lines.append(f"Sleep: {data['sleep_hours']}h")
        if data.get("mood"):
            lines.append(f"Mood: {data['mood']}")
        if session.get("current_streak"):
            lines.append(f"Current Streak: {session['current_streak']} days")

        if len(lines) > 1:
            return "\n".join(lines)
        return ""

    def _get_activity_context(self, username: str) -> str:
        """Get recent focus sessions and intervention completions."""
        if not self.db:
            return ""

        try:
            parts = []

            # Focus stats (7 days)
            focus_stats = self.db.get_focus_stats(username, days=7)
            if focus_stats.get("total_sessions", 0) > 0:
                focus_line = (
                    f"[Focus Activity (7d)] {focus_stats['total_sessions']} sessions, "
                    f"{focus_stats['total_minutes']} total minutes, "
                    f"{focus_stats.get('avg_quality', 'N/A')}/10 avg quality"
                )
                parts.append(focus_line)

            # Intervention stats (7 days)
            inv_stats = self.db.get_intervention_stats(username, days=7)
            if inv_stats.get("total_completions", 0) > 0:
                inv_line = (
                    f"[Interventions (7d)] {inv_stats['total_completions']} completed, "
                    f"{inv_stats.get('daily_average', 0)}/day avg"
                )
                parts.append(inv_line)

            # Streak summary
            streaks = self.db.get_all_streak_summary(username)
            if streaks.get("types"):
                streak_parts = []
                for s_type, s_data in streaks["types"].items():
                    streak_parts.append(f"{s_type}: {s_data.get('current', 0)} days")
                if streak_parts:
                    parts.append(f"[Streaks] {' | '.join(streak_parts)}")

            return "\n".join(parts)
        except Exception as e:
            logger.debug(f"Activity context error: {e}")
            return ""

    def _get_insight_context(self, username: str) -> str:
        """Get behavioral insights from the user's profile."""
        if not self.memory or not hasattr(self.memory, 'profile'):
            return ""

        try:
            profile = self.memory.profile.data if hasattr(self.memory, 'profile') else {}
            insights = profile.get("insights", [])
            if insights:
                recent = insights[-3:]
                lines = ["[Behavioral Insights]"]
                for insight in recent:
                    lines.append(f"• {insight}")
                return "\n".join(lines)
        except Exception as e:
            logger.debug(f"Insight context error: {e}")

        return ""


class LLMRouter:
    """
    Routes LLM requests to the appropriate model based on task type.
    
    Task routing:
    - emotional_support → primary model (GPT-4o / Groq)
    - task_generation → local model / fast model
    - memory_classification → lightweight model
    - analytics → ML pipeline (no LLM needed)
    """

    ROUTE_TYPES = {
        "emotional_support": {
            "priority": "high",
            "requires_empathy": True,
            "max_tokens": 1024,
            "temperature": 0.7,
        },
        "task_generation": {
            "priority": "medium",
            "requires_empathy": False,
            "max_tokens": 512,
            "temperature": 0.3,
        },
        "memory_classification": {
            "priority": "low",
            "requires_empathy": False,
            "max_tokens": 128,
            "temperature": 0.1,
        },
        "analytics": {
            "priority": "low",
            "requires_empathy": False,
            "max_tokens": 256,
            "temperature": 0.3,
        },
    }

    def __init__(self, groq_api_key: Optional[str] = None):
        self.groq_api_key = groq_api_key

    def classify_intent(self, text: str) -> str:
        """
        Classify the user's intent to determine the appropriate routing.
        Uses keyword-based classification (no LLM call needed).
        """
        if not text:
            return "emotional_support"

        text_lower = text.lower()

        # Emotional support / crisis
        crisis_keywords = [
            "panic", "anxious", "anxiety", "overwhelmed", "scared", "worried",
            "can't cope", "need help", "not okay", "struggling", "depressed",
            "sad", "crying", "burned out", "exhausted", "hopeless",
        ]
        if any(kw in text_lower for kw in crisis_keywords):
            return "emotional_support"

        # Task generation / planning
        task_keywords = [
            "break down", "task", "to-do", "plan", "schedule", "organize",
            "prioritize", "list", "steps", "micro", "start",
        ]
        if any(kw in text_lower for kw in task_keywords):
            return "task_generation"

        # Memory classification / recording
        memory_keywords = [
            "remember", "remind", "note", "save", "store", "keep",
            "my favorite", "i like", "i love", "i hate",
            "i always", "i never", "i usually",
        ]
        if any(kw in text_lower for kw in memory_keywords):
            return "memory_classification"

        # Analytics / reflection
        analytics_keywords = [
            "analytics", "report", "summary", "trend", "progress",
            "how have i been", "stats", "statistics", "insight",
        ]
        if any(kw in text_lower for kw in analytics_keywords):
            return "analytics"

        # Default to emotional support for general chat
        return "emotional_support"

    def get_route_config(self, intent: str) -> dict:
        """Get the configuration for a specific route."""
        return self.ROUTE_TYPES.get(intent, self.ROUTE_TYPES["emotional_support"])

    def format_response_instruction(self, intent: str) -> str:
        """Get formatting instructions based on route type."""
        instructions = {
            "emotional_support": (
                "PRIORITY: Emotional support and validation. Use warm, empathetic tone. "
                "Short paragraphs. End with one gentle question."
            ),
            "task_generation": (
                "PRIORITY: Generate clear, tiny, actionable steps. "
                "Use bullet points. Each step should be 2-5 minutes. "
                "Include emojis. Make steps concrete, not abstract."
            ),
            "memory_classification": (
                "PRIORITY: Record the user's stated preferences or facts. "
                "Acknowledge and confirm what they've shared. "
                "Brief response, then ask a related question."
            ),
            "analytics": (
                "PRIORITY: Provide data-driven insights. Reference their actual data. "
                "Use numbers to show progress. Be encouraging about trends. "
                "Suggest one actionable change based on the data."
            ),
        }
        return instructions.get(intent, instructions["emotional_support"])
