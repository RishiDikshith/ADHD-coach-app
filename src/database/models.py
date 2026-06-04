"""
Database Models
===============
SQLAlchemy ORM models for the ADHD Coach ecosystem.
Supports SQLite (development) and PostgreSQL (production).
"""

import os
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey, create_engine
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# Determine database URL: PostgreSQL in production, SQLite in development
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    os.getenv(
        "POSTGRES_URL",  # Neon PostgreSQL
        "sqlite:///./adhd_coach.db"
    )
)

# Handle postgres:// vs postgresql:// dialect naming issue for SQLAlchemy
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Handle SQLite vs PostgreSQL engine creation
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_recycle=300,
        pool_pre_ping=True
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency for FastAPI to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Call on application startup."""
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Database startup connection health check passed.")
    except Exception as e:
        print(f"DATABASE INITIALIZATION ERROR: Database startup connection check failed: {e}")
        raise RuntimeError(f"Database connection failed: {e}") from e

    Base.metadata.create_all(bind=engine)
    
    # Custom dynamic migration to ensure 'role' column exists in SQLite/PostgreSQL
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    if "users" in inspector.get_table_names():
        columns = [c["name"] for c in inspector.get_columns("users")]
        if "role" not in columns:
            try:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'user'"))
                    conn.commit()
            except Exception as e:
                # Catch gracefully in case of locking or concurrency
                pass


# ==================== Refresh Tokens for RTR ====================

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String(500), unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=False, index=True)
    family_id = Column(String(100), nullable=False, index=True)
    is_used = Column(Boolean, default=False)
    is_revoked = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# ==================== User & Auth ====================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime, nullable=True)
    settings = Column(JSON, default=dict)
    role = Column(String(50), default="user", server_default="user")

    # Relationships
    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")
    mood_entries = relationship("MoodEntry", back_populates="user", cascade="all, delete-orphan")
    interventions = relationship("InterventionCompletion", back_populates="user", cascade="all, delete-orphan")
    streaks = relationship("Streak", back_populates="user", cascade="all, delete-orphan")
    facts = relationship("UserFact", back_populates="user", cascade="all, delete-orphan")
    focus_sessions = relationship("FocusSession", back_populates="user", cascade="all, delete-orphan")
    distraction_logs = relationship("DistractionLog", back_populates="user", cascade="all, delete-orphan")
    achievements = relationship("Achievement", back_populates="user", cascade="all, delete-orphan")
    skills = relationship("SkillProgress", back_populates="user", cascade="all, delete-orphan")
    feedback_entries = relationship("UserFeedback", back_populates="user", cascade="all, delete-orphan")
    support_tickets = relationship("SupportTicket", back_populates="user", cascade="all, delete-orphan")


# ==================== Chat History ====================

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    emotion = Column(String(50), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    user = relationship("User", back_populates="chat_messages")


# ==================== Mood Tracking ====================

class MoodEntry(Base):
    __tablename__ = "mood_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    mood = Column(String(50), nullable=False)  # "happy", "calm", "anxious", etc.
    emoji = Column(String(10), nullable=True)
    energy = Column(Integer, nullable=True)  # 1-10
    focus = Column(Integer, nullable=True)  # 1-10
    burnout = Column(Integer, nullable=True)  # 1-10
    anxiety = Column(Integer, nullable=True)  # 1-10
    productivity = Column(Integer, nullable=True)  # 1-10
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    user = relationship("User", back_populates="mood_entries")


# ==================== Intervention Completions ====================

class InterventionCompletion(Base):
    __tablename__ = "intervention_completions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    intervention_type = Column(String(100), nullable=False, index=True)  # "breathing", "focus_session", "hydration", "micro_task"
    title = Column(String(255), nullable=False)
    duration_minutes = Column(Integer, nullable=True)
    completed = Column(Boolean, default=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    user = relationship("User", back_populates="interventions")


# ==================== Streak System ====================

class Streak(Base):
    __tablename__ = "streaks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    streak_type = Column(String(50), nullable=False, default="daily")  # "daily", "focus", "emotional_recovery", "task_consistency"
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_activity_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="streaks")


# ==================== Structured Facts (Memory Upgrade) ====================

class UserFact(Base):
    __tablename__ = "user_facts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    fact_type = Column(String(50), nullable=False, index=True)  # "preference", "behavior", "life_event", "goal", "struggle"
    category = Column(String(100), nullable=True, index=True)  # "sleep", "focus", "food", "social", "work"
    key = Column(String(255), nullable=False)  # e.g. "favorite_color", "best_focus_time"
    value = Column(Text, nullable=False)
    confidence = Column(Float, default=1.0)  # 0.0 to 1.0 — how certain we are
    source = Column(String(50), nullable=True)  # "extraction", "user_input", "inference"
    context = Column(Text, nullable=True)  # original context where this was learned
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="facts")


# ==================== Focus Sessions ====================

class FocusSession(Base):
    __tablename__ = "focus_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    mode = Column(String(50), default="standard")  # "deep_focus", "gentle_start", "recovery", "sprint", "standard"
    duration_minutes = Column(Integer, nullable=False)
    completed = Column(Boolean, default=False)
    quality = Column(Integer, nullable=True)  # 1-10 user rating
    energy_before = Column(Integer, nullable=True)  # 1-10
    energy_after = Column(Integer, nullable=True)  # 1-10
    distractions = Column(Integer, default=0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    user = relationship("User", back_populates="focus_sessions")


# ==================== Distraction Tracking ====================

class DistractionLog(Base):
    __tablename__ = "distraction_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("focus_sessions.id"), nullable=True)
    distraction = Column(String(255), nullable=False)
    category = Column(String(50), nullable=True)  # "phone", "people", "noise", "thoughts", "urge", "other"
    energy_level = Column(Integer, nullable=True)  # 1-10
    recovery_time_minutes = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="distraction_logs")


# ==================== Gamification ====================

class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    achievement_id = Column(String(100), nullable=False)  # e.g. "first_focus_session", "three_day_streak"
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    xp_reward = Column(Integer, default=0)
    unlocked_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="achievements")


class SkillProgress(Base):
    __tablename__ = "skill_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    skill_name = Column(String(100), nullable=False)  # "focus", "consistency", "emotional_resilience", "task_management"
    level = Column(Integer, default=1)
    xp = Column(Integer, default=0)
    xp_to_next_level = Column(Integer, default=100)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="skills")


# ==================== Feedback & Support ====================

class UserFeedback(Base):
    __tablename__ = "user_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    rating = Column(Integer, nullable=False) # 1-5
    category = Column(String(100), nullable=False) # "coach", "app", "features", etc.
    feedback_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    user = relationship("User", back_populates="feedback_entries")


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String(50), nullable=False) # "glitch", "question", "urgency"
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(50), default="open") # "open", "resolved"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    user = relationship("User", back_populates="support_tickets")
