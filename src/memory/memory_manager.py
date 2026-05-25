"""
Memory Manager — central orchestrator for the ADHD Behavioral Memory System.

Upgraded with:
  - Importance ranking for memories
  - Emotional tagging for mood-contextual recall
  - Memory summarization for long-term patterns
  - Better contextual retrieval with recency+relevance scoring
  - Structured fact extraction for long-term personalization
  - Multi-layer memory architecture (short-term, long-term, emotional, behavioral, contextual)
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from memory.chroma_store import ChromaMemoryStore
from memory.user_profile import UserProfile
from memory.session_memory import SessionMemory
from memory.fact_extractor import FactExtractor, FactMemoryConsolidator

logger = logging.getLogger(__name__)

# Importance weights for different memory types
MEMORY_IMPORTANCE = {
    "intervention": 0.9,       # Interventions are highly important
    "crisis": 1.0,             # Crisis events are critical
    "emotion": 0.7,            # Emotional patterns matter
    "insight": 0.8,            # Behavioral insights are important
    "focus_session": 0.6,      # Focus data is moderately important
    "procrastination": 0.7,    # Triggers matter for prediction
    "task_completed": 0.5,     # Task completion is useful
    "conversation": 0.3,       # General conversation is less critical
    "commitment_made": 0.6,    # Commitments are important to track
    "commitment_kept": 0.7,    # Keeping commitments is very important
    "streak_update": 0.5,      # Streak tracking is useful
    "achievement": 0.6,        # Achievements boost motivation
    "habit": 0.6,              # Habit data is useful
    "goal": 0.8,               # Goals are important
    "default": 0.3,
}


class MemoryManager:
    """
    Central memory orchestrator.
    All memory operations go through this class.

    Improvement: Importance ranking, emotional tagging,
    memory summarization, and smarter retrieval.
    """

    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.store = ChromaMemoryStore(user_id=user_id)
        self.profile = UserProfile(user_id=user_id)
        self.session = SessionMemory(user_id=user_id)
        logger.debug(f"MemoryManager initialized for user: {user_id}")

    # ---------- Lifecycle ----------

    def on_chat_start(self):
        self.profile.data["session_summary"]["total_sessions"] += 1
        self.profile.save()
        logger.debug(f"Chat session started for user: {self.user_id}")

    def on_chat_end(self):
        self.session.save()
        self.profile.save()
        logger.debug(f"Chat session ended for user: {self.user_id}")

    # ---------- Fact Extraction Integration ----------

    def set_db_manager(self, db_manager):
        """Set the database manager for fact persistence."""
        self._db = db_manager
        self.fact_extractor = FactExtractor()
        self.fact_consolidator = FactMemoryConsolidator(db_manager)

    def extract_and_store_facts(self, message: str) -> List[dict]:
        """
        Extract structured facts from a user message and store them.
        Returns extracted facts.
        """
        if not hasattr(self, 'fact_extractor'):
            self.fact_extractor = FactExtractor()
            self.fact_consolidator = FactMemoryConsolidator()

        if not hasattr(self, '_db') or not self._db:
            # Just extract without persisting
            if self.fact_extractor.should_process(message):
                return self.fact_extractor.extract_facts(message)
            return []

        return self.fact_consolidator.process_message(self.user_id, message)

    def get_fact_context_for_prompt(self) -> str:
        """Get structured fact knowledge for prompt injection."""
        if not hasattr(self, 'fact_consolidator'):
            return ""
        return self.fact_consolidator.get_fact_context_prompt(self.user_id)

    # ---------- Core Recording with Importance Scoring ----------

    def _get_importance(self, memory_type: str, metadata: Optional[dict] = None) -> float:
        """Calculate importance score for a memory based on type and context."""
        base = MEMORY_IMPORTANCE.get(memory_type, MEMORY_IMPORTANCE["default"])
        
        # Boost importance based on emotional intensity
        if metadata:
            stress = metadata.get("stress", 5)
            if stress >= 8:
                base = min(1.0, base + 0.2)
            elif stress >= 6:
                base = min(1.0, base + 0.1)
            
            # Boost for successful interventions
            if metadata.get("success"):
                base = min(1.0, base + 0.2)
            
            # Boost for repeated patterns
            if metadata.get("is_pattern", False):
                base = min(1.0, base + 0.15)
        
        return round(base, 2)

    def _tag_emotion(self, content: str, emotion: Optional[str] = None) -> list:
        """Tag memory with emotional context for better retrieval."""
        emotional_tags = []
        
        if emotion:
            emotional_tags.append(f"emotion:{emotion}")
        
        # Content-based emotion detection
        content_lower = content.lower()
        emotion_keywords = {
            "anxious": ["anxious", "anxiety", "worried", "nervous", "panic"],
            "overwhelmed": ["overwhelmed", "overwhelming", "too much"],
            "frustrated": ["frustrated", "frustration", "annoyed", "irritated"],
            "sad": ["sad", "depressed", "down", "hopeless", "lonely"],
            "happy": ["happy", "great", "wonderful", "excellent", "amazing"],
            "calm": ["calm", "peaceful", "relaxed", "grounded"],
            "motivated": ["motivated", "energized", "inspired", "excited"],
            "tired": ["tired", "exhausted", "drained", "burned out"],
            "stressed": ["stressed", "stress", "pressure"],
        }
        
        for tag, keywords in emotion_keywords.items():
            if any(k in content_lower for k in keywords):
                emotional_tags.append(f"emotion:{tag}")
        
        return list(set(emotional_tags))

    def _summarize_for_memory(self, content: str, max_length: int = 200) -> str:
        """Summarize content for efficient storage and retrieval."""
        if len(content) <= max_length:
            return content
        # Smart truncation at sentence boundary
        truncated = content[:max_length]
        last_period = truncated.rfind(".")
        if last_period > max_length // 2:
            return content[:last_period + 1]
        return truncated + "..."

    # ---------- Conversation Recording ----------

    def record_conversation_turn(
        self,
        user_message: str,
        assistant_message: str,
        interaction_type: str = "chat",
        metadata: Optional[dict] = None,
        emotion: Optional[str] = None,
    ):
        metadata = metadata or {}
        
        # Session memory
        self.session.record_turn(user_message, assistant_message, interaction_type)

        # Tag with emotional context
        emotional_tags = self._tag_emotion(user_message, emotion)
        
        # Calculate importance
        importance = self._get_importance("conversation", {**metadata, "emotion": emotion})
        
        # Store user message with emotional tags and importance
        self.store.store(
            content=self._summarize_for_memory(user_message),
            metadata={
                "type": "user_message",
                "interaction_type": interaction_type,
                "importance": importance,
                "emotional_tags": emotional_tags,
                **(metadata or {}),
            },
            memory_type="conversation",
        )

        # Store assistant response summary
        summary = self._summarize_for_memory(assistant_message, 300)
        self.store.store(
            content=summary,
            metadata={
                "type": "assistant_response",
                "interaction_type": interaction_type,
                "importance": importance * 0.7,
                **(metadata or {}),
            },
            memory_type="conversation",
        )

        # Extract and store structured facts from user message
        extracted_facts = self.extract_and_store_facts(user_message)
        if extracted_facts:
            for fact in extracted_facts:
                ftype = fact.get("type")
                val = fact.get("value")
                if ftype == "cognitive_style":
                    self.profile.record_cognitive_style(val)
                elif ftype == f"interest":
                    self.profile.record_interest(val)

    # ---------- Emotion Recording ----------

    def record_emotion(self, emotion: str, stress: int, energy: Optional[int] = None):
        self.session.record_emotion(emotion)
        self.session.set_stress(stress)
        if energy:
            self.session.set_energy(energy)

        self.profile.record_emotion(emotion, stress, energy)

        importance = self._get_importance("emotion", {"stress": stress})
        
        self.store.store(
            content=f"Mood: {emotion}, Stress: {stress}/10, Energy: {energy or 'N/A'}/10",
            metadata={
                "type": "emotion",
                "emotion": emotion,
                "stress": stress,
                "energy": energy,
                "importance": importance,
            },
            memory_type="emotion",
        )

    # ---------- Focus Recording ----------

    def record_focus_session(self, duration_minutes: int, quality: int, hour: int):
        self.profile.record_focus_session(duration_minutes, quality, hour)

        importance = self._get_importance("focus_session", {})
        
        self.store.store(
            content=f"Focus session: {duration_minutes}min, quality {quality}/10 at hour {hour}",
            metadata={
                "type": "focus_session",
                "duration": duration_minutes,
                "quality": quality,
                "hour": hour,
                "importance": importance,
            },
            memory_type="focus",
        )

    # ---------- Intervention Tracking ----------

    def record_intervention(self, intervention: str):
        self.session.add_intervention(intervention)

        self.store.store(
            content=f"Applied intervention: {intervention}",
            metadata={
                "type": "intervention_applied",
                "intervention": intervention,
                "importance": MEMORY_IMPORTANCE["intervention"],
            },
            memory_type="intervention",
        )

    def record_intervention_result(self, intervention: str, success: bool, context: str = ""):
        self.session.mark_intervention_result(intervention, success)
        self.profile.record_intervention_result(intervention, success, context)

        result = "effective" if success else "ineffective"
        self.store.store(
            content=f"Intervention '{intervention}' was {result}. Context: {context}",
            metadata={
                "type": "intervention_result",
                "intervention": intervention,
                "success": success,
                "importance": MEMORY_IMPORTANCE["intervention"],
                "emotional_tags": self._tag_emotion(context),
            },
            memory_type="intervention",
        )

    # ---------- Task Tracking ----------

    def record_task_added(self, task: str, source: str = "ai"):
        self.session.add_task(task, source)

    def record_task_completed(self, task: str, difficulty: int = 5):
        self.profile.record_task_completion(
            task_size="small" if difficulty <= 3 else "medium" if difficulty <= 7 else "large",
            completed=True,
            difficulty=difficulty,
        )

        importance = self._get_importance("task_completed", {})
        
        self.store.store(
            content=f"Completed task: {task} (difficulty: {difficulty}/10)",
            metadata={
                "type": "task_completed",
                "task": task,
                "difficulty": difficulty,
                "importance": importance,
            },
            memory_type="task",
        )

    # ---------- Procrastination & Overwhelm ----------

    def record_procrastination_trigger(self, trigger: str, context: str = ""):
        self.profile.record_procrastination_trigger(trigger, context)

        emotional_tags = self._tag_emotion(context)
        importance = self._get_importance("procrastination", {"stress": self.session.state.get("current_stress", 5)})
        
        self.store.store(
            content=f"Procrastination trigger: {trigger}. Context: {self._summarize_for_memory(context, 100)}",
            metadata={
                "type": "procrastination",
                "trigger": trigger,
                "importance": importance,
                "emotional_tags": emotional_tags,
            },
            memory_type="behavior",
        )

    def set_overwhelm(self, detected: bool):
        self.session.set_overwhelm(detected)
        if detected:
            self.store.store(
                content="Overwhelm detected — user needs gentle support and grounding",
                metadata={
                    "type": "overwhelm_event",
                    "importance": MEMORY_IMPORTANCE["crisis"],
                    "emotional_tags": ["emotion:overwhelmed", "emotion:stressed"],
                },
                memory_type="intervention",
            )

    def set_task_paralysis(self, detected: bool):
        self.session.set_task_paralysis(detected)

    # ---------- Streak Tracking ----------

    def update_streak(self, current_streak: int, badges: Optional[list] = None):
        self.profile.update_streak(current_streak)

        if badges:
            self.profile.data["session_summary"]["badges_earned"] = list(
                set(self.profile.data["session_summary"]["badges_earned"] + badges)
            )
            self.profile.save()

        self.store.store(
            content=f"Streak updated: {current_streak} days. Badges: {badges or []}",
            metadata={
                "type": "streak_update",
                "streak": current_streak,
                "importance": MEMORY_IMPORTANCE["streak_update"],
            },
            memory_type="achievement",
        )

    # ---------- Behavioral Insights ----------

    def add_insight(self, insight: str):
        self.profile.add_insight(insight)
        self.store.store(
            content=f"Behavioral insight: {insight}",
            metadata={
                "type": "behavioral_insight",
                "importance": MEMORY_IMPORTANCE["insight"],
            },
            memory_type="insight",
        )

    # ---------- Context Retrieval (Upgraded) ----------

    def build_context_for_prompt(self) -> dict:
        personalization = self.profile.get_personalization_context()
        session_context = self.session.get_context_summary()

        # Get high-importance recent memories (prioritize quality over quantity)
        recent_focus = self.store.get_recent("focus", limit=5)
        recent_emotions = self.store.get_recent("emotion", limit=5)
        recent_interventions = self.store.get_recent("intervention", limit=5)
        recent_behaviors = self.store.get_recent("behavior", limit=5)
        all_recent = self.store.get_recent(limit=10)

        # Sort by importance for context priority
        high_priority = [
            m for m in all_recent
            if m.get("metadata", {}).get("importance", 0.3) >= 0.7
        ]

        return {
            "user": personalization,
            "session": session_context,
            "memories": {
                "recent_focus": [m["content"] for m in recent_focus],
                "recent_emotions": [m["content"] for m in recent_emotions],
                "recent_interventions": [m["content"] for m in recent_interventions],
                "recent_behaviors": [m["content"] for m in recent_behaviors],
            },
            "high_priority_memories": [m["content"] for m in high_priority[:5]],
            "memory_stats": self.store.get_stats(),
            "importance_context": self._get_importance_context(all_recent),
        }

    def _get_importance_context(self, memories: list) -> str:
        """Generate a summary of important memory patterns."""
        if not memories:
            return ""
        
        high_importance = [m for m in memories if m.get("metadata", {}).get("importance", 0.3) >= 0.6]
        if not high_importance:
            return ""
        
        types = {}
        for m in high_importance:
            mtype = m.get("metadata", {}).get("type", "unknown")
            if mtype not in types:
                types[mtype] = 0
            types[mtype] += 1
        
        parts = []
        for mtype, count in sorted(types.items(), key=lambda x: -x[1]):
            if count >= 2:
                parts.append(f"{count} significant {mtype} events")
        
        if parts:
            return "Recent important patterns: " + "; ".join(parts)
        return ""

    def get_context_for_prompt_text(self) -> str:
        context = self.build_context_for_prompt()
        lines = []

        # User profile summary
        u = context["user"]
        lines.append("[USER PROFILE]")
        lines.append(f"ADHD Type: {u.get('adhd_type', 'unknown')}")
        lines.append(f"Primary Challenges: {', '.join(u.get('primary_challenges', ['unknown']))}")
        lines.append(f"Cognitive Styles: {', '.join(u.get('cognitive_styles', ['unknown']))}")
        lines.append(f"Interests: {', '.join(u.get('interests', ['unknown']))}")
        lines.append(f"Coach Tone Preference: {u.get('coach_tone', 'empathetic')}")
        lines.append(f"Focus Area: {u.get('focus_area', 'time_management')}")
        lines.append(f"Best Focus Hours: {', '.join(u.get('best_focus_hours', ['unknown']))}")
        lines.append(f"Optimal Session Length: {u.get('optimal_session_length', 25)} min")
        lines.append(f"Average Stress (7 days): {u.get('avg_stress', 5)}/10")
        lines.append(f"Average Energy: {u.get('avg_energy', 5)}/10")
        lines.append(f"Task Completion Rate: {u.get('task_completion_rate', 0)}%")
        lines.append(f"Preferred Task Size: {u.get('preferred_task_size', 'medium')}")
        if u.get("insights"):
            lines.append(f"Behavioral Insights: {'; '.join(u['insights'])}")

        # Session context
        s = context["session"]
        lines.append("")
        lines.append("[SESSION CONTEXT]")
        lines.append(f"Turn Count: {s.get('turn_count', 0)}")
        lines.append(f"Current Mood: {s.get('current_mood', 'neutral')}")
        lines.append(f"Current Stress: {s.get('current_stress', 5)}/10")
        lines.append(f"Current Energy: {s.get('current_energy', 5)}/10")
        if s.get("overwhelm_detected"):
            lines.append("FLAG: Overwhelm detected — prioritize gentle support")
        if s.get("task_paralysis_detected"):
            lines.append("FLAG: Task paralysis detected — suggest micro-tasks")

        # High priority memories (most relevant)
        if context.get("high_priority_memories"):
            lines.append("")
            lines.append("[IMPORTANT RECENT MEMORIES]")
            for entry in context["high_priority_memories"][:3]:
                lines.append(f"- {entry}")

        # Recent patterns
        if context.get("importance_context"):
            lines.append("")
            lines.append(f"[PATTERNS] {context['importance_context']}")

        return "\n".join(lines)

    # ---------- Semantic Search ----------

    def search_memories(self, query: str, n_results: int = 5) -> list[dict]:
        return self.store.search(query, n_results=n_results)

    def search_by_emotion(self, emotion: str, n_results: int = 5) -> list[dict]:
        """Search memories by emotional context."""
        return self.store.search(f"emotion:{emotion}", n_results=n_results, memory_type=None)

    # ---------- Memory Statistics ----------

    def get_stats(self) -> dict:
        return {
            "store": self.store.get_stats(),
            "profile": {
                "sessions": self.profile.data["session_summary"]["total_sessions"],
                "focus_sessions": len(self.profile.data["focus_patterns"]["focus_quality_trend"]),
                "mood_records": len(self.profile.data["emotional_patterns"]["mood_trend"]),
                "interventions_tracked": (
                    len(self.profile.data["intervention_history"]["successful_interventions"]) +
                    len(self.profile.data["intervention_history"]["failed_interventions"])
                ),
                "insights_generated": len(self.profile.data["insights"]),
            },
            "session": {
                "turn_count": self.session.state["turn_count"],
                "active_tasks": len(self.session.state["current_tasks"]),
                "overwhelm_flag": self.session.state["overwhelm_detected"],
            },
        }

    # ---------- Cleanup ----------

    def clear_all(self):
        self.store.clear_user_memory()
        self.session.clear()
        self.profile = UserProfile(user_id=self.user_id)
        logger.warning(f"All memory cleared for user: {self.user_id}")
