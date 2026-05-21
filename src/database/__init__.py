"""
Database Module
===============
SQLAlchemy-based persistent data layer with SQLite (dev) / PostgreSQL (production) support.
Stores chat history, mood tracking, intervention completions, streaks, user facts, and more.
"""

from .models import Base, User, ChatMessage, MoodEntry, InterventionCompletion, Streak, UserFact, FocusSession, DistractionLog, Achievement, SkillProgress
from .crud import DatabaseManager

__all__ = [
    "Base", "User", "ChatMessage", "MoodEntry", "InterventionCompletion",
    "Streak", "UserFact", "FocusSession", "DistractionLog", "Achievement", "SkillProgress",
    "DatabaseManager",
]
