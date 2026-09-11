"""
Database Module
===============
SQLAlchemy-based persistent data layer with SQLite (dev) / PostgreSQL (production) support.
Stores chat history, mood tracking, intervention completions, streaks, user facts, and more.
"""

from .crud import DatabaseManager
from .models import (
    Achievement,
    Base,
    ChatMessage,
    DistractionLog,
    FocusSession,
    InterventionCompletion,
    MoodEntry,
    SkillProgress,
    Streak,
    User,
    UserFact,
)

__all__ = [
    "Achievement",
    "Base",
    "ChatMessage",
    "DatabaseManager",
    "DistractionLog",
    "FocusSession",
    "InterventionCompletion",
    "MoodEntry",
    "SkillProgress",
    "Streak",
    "User",
    "UserFact",
]
