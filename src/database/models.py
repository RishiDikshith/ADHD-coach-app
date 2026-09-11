"""
Database Models
===============
SQLAlchemy ORM models for the ADHD Coach ecosystem.
Supports SQLite (development) and PostgreSQL (production).
"""

import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    event,
    inspect,
    text,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import TypeDecorator


class UTCDateTime(TypeDecorator):
    impl = DateTime
    cache_ok = True

    def process_result_value(self, value, dialect):
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value


# Determine database URL: PostgreSQL in production, SQLite in development
DATABASE_URL = os.getenv(
    "DATABASE_URL", os.getenv("POSTGRES_URL", "sqlite:///./adhd_coach.db")  # Neon PostgreSQL
)

# Handle postgres:// vs postgresql:// dialect naming issue for SQLAlchemy
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

REPO_ROOT = Path(__file__).resolve().parents[2]

# Resolve local SQLite files from the repository root, not the process cwd.
if DATABASE_URL.startswith("sqlite") and not DATABASE_URL.startswith("sqlite:///:memory:"):
    raw_path = DATABASE_URL
    for prefix in ("sqlite:///", "sqlite://"):
        if raw_path.startswith(prefix):
            raw_path = raw_path[len(prefix) :]
            break
    raw_path = raw_path.removeprefix("./")
    path_obj = Path(raw_path)
    if not path_obj.is_absolute():
        path_obj = (REPO_ROOT / path_obj).resolve()
    DATABASE_URL = f"sqlite:///{path_obj.as_posix()}"

# Handle SQLite vs PostgreSQL engine creation.
# SQLite in-memory databases need a shared connection pool so FastAPI and Celery
# can see the same schema and rows within the same test process.
# File-based SQLite databases use normal connection pooling with WAL mode.
if DATABASE_URL.startswith("sqlite"):
    if ":memory:" in DATABASE_URL:
        engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            pool_pre_ping=True,
        )
    else:
        engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False, "timeout": 30},
            pool_pre_ping=True,
        )

        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()

else:
    engine = create_engine(
        DATABASE_URL, pool_size=10, max_overflow=20, pool_recycle=300, pool_pre_ping=True
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


USER_SCHEMA_COLUMNS_SQLITE = {
    "email": "VARCHAR(255)",
    "security_pin_hash": "VARCHAR(255)",
    "is_active": "BOOLEAN DEFAULT 1",
    "auth_provider": "VARCHAR(50)",
    "created_at": "TIMESTAMP",
    "updated_at": "TIMESTAMP",
    "last_login": "TIMESTAMP",
    "settings": "JSON DEFAULT '{}'",
    "role": "VARCHAR(50) DEFAULT 'user'",
    "is_admin": "BOOLEAN DEFAULT 0",
    "has_pin_enabled": "BOOLEAN DEFAULT 0",
}

USER_SCHEMA_COLUMNS_PG = {
    "email": "VARCHAR(255)",
    "security_pin_hash": "VARCHAR(255)",
    "is_active": "BOOLEAN NOT NULL DEFAULT TRUE",
    "auth_provider": "VARCHAR(50)",
    "created_at": "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP",
    "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    "last_login": "TIMESTAMP",
    "settings": "JSON DEFAULT '{}'",
    "role": "VARCHAR(50) NOT NULL DEFAULT 'user'",
    "is_admin": "BOOLEAN NOT NULL DEFAULT FALSE",
    "has_pin_enabled": "BOOLEAN NOT NULL DEFAULT FALSE",
}

# Default dictionary mapped for backwards compatibility
USER_SCHEMA_COLUMNS = USER_SCHEMA_COLUMNS_SQLITE

TRUSTED_DEVICE_SCHEMA_COLUMNS = {
    "token_hash": "VARCHAR(255)",
    "expires_at": "TIMESTAMP",
    "revoked_at": "TIMESTAMP",
}


def migrate_users_schema():
    """Add missing non-destructive auth columns to an existing ``users`` table and backfill defaults."""
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("users")}
    missing_columns = [name for name in USER_SCHEMA_COLUMNS if name not in existing_columns]
    is_pg = engine.dialect.name == "postgresql"

    # Ensure password_hash is nullable to support OAuth users without local passwords
    if is_pg:
        try:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL"))
        except Exception as exc:  # noqa: BLE001
            logger.debug("PostgreSQL drop NOT NULL on password_hash: %s", exc)
    else:
        try:
            with engine.begin() as tx_conn:
                cols = tx_conn.execute(text("PRAGMA table_info(users)")).fetchall()
                pw_col = next((c for c in cols if c[1] == "password_hash"), None)
                if pw_col and pw_col[3] == 1:
                    tx_conn.execute(text("PRAGMA foreign_keys=OFF"))
                    col_names = [c[1] for c in cols]
                    col_str = ", ".join(col_names)
                    tx_conn.execute(text("DROP INDEX IF EXISTS ix_users_username"))
                    tx_conn.execute(text("ALTER TABLE users RENAME TO _users_old"))
                    User.__table__.create(tx_conn)
                    tx_conn.execute(
                        text(f"INSERT INTO users ({col_str}) SELECT {col_str} FROM _users_old")
                    )
                    tx_conn.execute(text("DROP TABLE _users_old"))
                    tx_conn.execute(text("PRAGMA foreign_keys=ON"))
                    logger.info(
                        "Applied non-destructive SQLite users migration: password_hash is now nullable."
                    )
        except Exception as exc:  # noqa: BLE001
            logger.warning("SQLite users migration for nullable password_hash encountered: %s", exc)

    if missing_columns:
        try:
            with engine.begin() as conn:
                for column_name in missing_columns:
                    if is_pg:
                        column_type = USER_SCHEMA_COLUMNS_PG.get(
                            column_name, USER_SCHEMA_COLUMNS[column_name]
                        )
                        statement = f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {column_name} {column_type}"
                    else:
                        column_type = USER_SCHEMA_COLUMNS_SQLITE.get(
                            column_name, USER_SCHEMA_COLUMNS[column_name]
                        )
                        statement = f"ALTER TABLE users ADD COLUMN {column_name} {column_type}"
                    conn.execute(text(statement))
        except Exception as exc:
            raise RuntimeError(
                f"Non-destructive users schema migration failed for columns: {', '.join(missing_columns)}"
            ) from exc

        print(f"Applied non-destructive users schema migration: {', '.join(missing_columns)}")

    # Backfill existing NULL values for updated_at, created_at, and defaults (idempotent)
    try:
        actual_columns = {column["name"] for column in inspect(engine).get_columns("users")}
        with engine.begin() as conn:
            if "updated_at" in actual_columns:
                if "created_at" in actual_columns:
                    conn.execute(
                        text(
                            "UPDATE users SET updated_at = COALESCE(created_at, CURRENT_TIMESTAMP) WHERE updated_at IS NULL"
                        )
                    )
                else:
                    conn.execute(
                        text(
                            "UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL"
                        )
                    )
            if "created_at" in actual_columns:
                conn.execute(
                    text("UPDATE users SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
                )
            if "is_active" in actual_columns:
                conn.execute(text("UPDATE users SET is_active = 1 WHERE is_active IS NULL"))
            if "role" in actual_columns:
                conn.execute(text("UPDATE users SET role = 'user' WHERE role IS NULL"))
            if "is_admin" in actual_columns:
                conn.execute(text("UPDATE users SET is_admin = 0 WHERE is_admin IS NULL"))
            if "has_pin_enabled" in actual_columns:
                conn.execute(
                    text("UPDATE users SET has_pin_enabled = 0 WHERE has_pin_enabled IS NULL")
                )
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Backfill for users schema encountered a non-fatal warning: {exc}")

    actual_columns = {column["name"] for column in inspect(engine).get_columns("users")}
    still_missing = set(USER_SCHEMA_COLUMNS) - actual_columns
    if still_missing:
        raise RuntimeError(
            f"Users schema is still missing columns: {', '.join(sorted(still_missing))}"
        )


def migrate_auth_schema():
    """Apply safe, non-destructive migrations for users and trusted_devices tables."""
    migrate_users_schema()

    inspector = inspect(engine)
    if "trusted_devices" in inspector.get_table_names():
        existing_cols = {col["name"] for col in inspector.get_columns("trusted_devices")}
        missing = [name for name in TRUSTED_DEVICE_SCHEMA_COLUMNS if name not in existing_cols]
        if missing:
            try:
                with engine.begin() as conn:
                    for col_name in missing:
                        col_type = TRUSTED_DEVICE_SCHEMA_COLUMNS[col_name]
                        if engine.dialect.name == "postgresql":
                            stmt = f"ALTER TABLE trusted_devices ADD COLUMN IF NOT EXISTS {col_name} {col_type}"
                        else:
                            stmt = f"ALTER TABLE trusted_devices ADD COLUMN {col_name} {col_type}"
                        conn.execute(text(stmt))
                print(
                    f"Applied non-destructive trusted_devices schema migration: {', '.join(missing)}"
                )
            except Exception as exc:
                raise RuntimeError(
                    f"Non-destructive trusted_devices schema migration failed for: {', '.join(missing)}"
                ) from exc


def init_db():
    """Verify connectivity, create new tables, and migrate existing auth schema."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Database startup connection health check passed.")
    except (AttributeError, KeyError, OSError, RuntimeError, TypeError, ValueError) as e:
        print(f"DATABASE INITIALIZATION ERROR: Database startup connection check failed: {e}")
        raise RuntimeError(f"Database connection failed: {e}") from e

    Base.metadata.create_all(bind=engine)
    migrate_auth_schema()


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


# ==================== OAuth Accounts ====================


class OAuthAccount(Base):
    __tablename__ = "oauth_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider = Column(String(50), nullable=False, index=True)
    provider_user_id = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="uq_oauth_provider_user_id"),
    )

    user = relationship("User", back_populates="oauth_accounts")


# ==================== Trusted Devices ====================


class TrustedDevice(Base):
    __tablename__ = "trusted_devices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    device_id = Column(String(255), nullable=False, index=True)
    device_name = Column(String(255), nullable=False)
    token_hash = Column(String(255), nullable=True, index=True)
    expires_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    pin_hash = Column(String(255), nullable=True)
    failed_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(UTCDateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_used = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="trusted_devices")

    @property
    def last_used_at(self):
        return self.last_used

    @last_used_at.setter
    def last_used_at(self, value):
        self.last_used = value


# ==================== User & Auth ====================


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=True)
    password_hash = Column(String(255), nullable=True)
    security_pin_hash = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    auth_provider = Column(String(50), nullable=True, default=None)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    last_login = Column(DateTime, nullable=True)
    settings = Column(JSON, default=dict)
    role = Column(String(50), default="user", server_default="user")
    is_admin = Column(Boolean, default=False, server_default="false")
    has_pin_enabled = Column(Boolean, default=False, server_default="false")

    # Relationships
    oauth_accounts = relationship(
        "OAuthAccount", back_populates="user", cascade="all, delete-orphan"
    )
    trusted_devices = relationship(
        "TrustedDevice", back_populates="user", cascade="all, delete-orphan"
    )
    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")
    mood_entries = relationship("MoodEntry", back_populates="user", cascade="all, delete-orphan")
    interventions = relationship(
        "InterventionCompletion", back_populates="user", cascade="all, delete-orphan"
    )
    streaks = relationship("Streak", back_populates="user", cascade="all, delete-orphan")
    facts = relationship("UserFact", back_populates="user", cascade="all, delete-orphan")
    focus_sessions = relationship(
        "FocusSession", back_populates="user", cascade="all, delete-orphan"
    )
    distraction_logs = relationship(
        "DistractionLog", back_populates="user", cascade="all, delete-orphan"
    )
    achievements = relationship("Achievement", back_populates="user", cascade="all, delete-orphan")
    skills = relationship("SkillProgress", back_populates="user", cascade="all, delete-orphan")
    feedback_entries = relationship(
        "UserFeedback", back_populates="user", cascade="all, delete-orphan"
    )
    support_tickets = relationship(
        "SupportTicket", back_populates="user", cascade="all, delete-orphan"
    )


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
    intervention_type = Column(
        String(100), nullable=False, index=True
    )  # "breathing", "focus_session", "hydration", "micro_task"
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
    streak_type = Column(
        String(50), nullable=False, default="daily"
    )  # "daily", "focus", "emotional_recovery", "task_consistency"
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
    fact_type = Column(
        String(50), nullable=False, index=True
    )  # "preference", "behavior", "life_event", "goal", "struggle"
    category = Column(
        String(100), nullable=True, index=True
    )  # "sleep", "focus", "food", "social", "work"
    key = Column(String(255), nullable=False)  # e.g. "favorite_color", "best_focus_time"
    value = Column(Text, nullable=False)
    confidence = Column(Float, default=1.0)  # 0.0 to 1.0 — how certain we are
    source = Column(String(50), nullable=True)  # "extraction", "user_input", "inference"
    context = Column(Text, nullable=True)  # original context where this was learned
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User", back_populates="facts")


# ==================== Focus Sessions ====================


class FocusSession(Base):
    __tablename__ = "focus_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    mode = Column(
        String(50), default="standard"
    )  # "deep_focus", "gentle_start", "recovery", "sprint", "standard"
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
    category = Column(
        String(50), nullable=True
    )  # "phone", "people", "noise", "thoughts", "urge", "other"
    energy_level = Column(Integer, nullable=True)  # 1-10
    recovery_time_minutes = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="distraction_logs")


# ==================== Gamification ====================


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    achievement_id = Column(
        String(100), nullable=False
    )  # e.g. "first_focus_session", "three_day_streak"
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    xp_reward = Column(Integer, default=0)
    unlocked_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="achievements")


class SkillProgress(Base):
    __tablename__ = "skill_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    skill_name = Column(
        String(100), nullable=False
    )  # "focus", "consistency", "emotional_resilience", "task_management"
    level = Column(Integer, default=1)
    xp = Column(Integer, default=0)
    xp_to_next_level = Column(Integer, default=100)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User", back_populates="skills")


# ==================== Feedback & Support ====================


class UserFeedback(Base):
    __tablename__ = "user_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)  # 1-5
    category = Column(String(100), nullable=False)  # "coach", "app", "features", etc.
    feedback_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    user = relationship("User", back_populates="feedback_entries")


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String(50), nullable=False)  # "glitch", "question", "urgency"
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(50), default="open")  # "open", "resolved"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    user = relationship("User", back_populates="support_tickets")
