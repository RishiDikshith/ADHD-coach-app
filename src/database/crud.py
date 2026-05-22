"""
Database CRUD Operations
========================
High-level data access layer for the ADHD Coach ecosystem.
Provides clean async-friendly CRUD operations for all models.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import func, desc, and_, text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from .models import (
    User, ChatMessage, MoodEntry, InterventionCompletion, Streak,
    UserFact, FocusSession, DistractionLog, Achievement, SkillProgress,
    UserFeedback, SupportTicket,
    SessionLocal, init_db
)

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Central data access layer for all persistent storage operations."""

    def __init__(self, db: Optional[Session] = None):
        self._db = db

    @property
    def db(self) -> Session:
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def _ensure_session(self):
        """Ensure the session is in a working state. Reset if broken."""
        if self._db is None:
            self._db = SessionLocal()
        else:
            try:
                # Quick check if session is usable
                self._db.execute(text("SELECT 1"))
            except Exception:
                # Session is broken, create new one
                try:
                    self._db.close()
                except Exception:
                    pass
                self._db = SessionLocal()
        return self._db

    def _safe_commit(self):
        """Commit with automatic rollback on failure."""
        try:
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            logger.warning(f"Database commit failed, rolling back: {e}")
            try:
                self.db.rollback()
            except Exception:
                pass
            # Reset the session after rollback
            self._ensure_session()
            return False
        except Exception as e:
            logger.warning(f"Unexpected commit error: {e}")
            try:
                self.db.rollback()
            except Exception:
                pass
            return False

    def close(self):
        if self._db is not None:
            try:
                self._db.close()
            except Exception:
                pass
            self._db = None

    def reset_session(self):
        """Close and recreate the database session after errors."""
        try:
            if self._db is not None:
                self._db.close()
        except Exception:
            pass
        self._db = SessionLocal()
        return self._db

    # ==================== Session-safe Helpers ====================

    def _safe_get_user(self, username: str) -> Optional[User]:
        """Get user with automatic session recovery."""
        try:
            self._ensure_session()
            return self.db.query(User).filter(User.username == username).first()
        except Exception as e:
            logger.warning(f"User lookup failed, resetting session: {e}")
            self.reset_session()
            try:
                return self.db.query(User).filter(User.username == username).first()
            except Exception:
                return None

    # ==================== User Management ====================

    def get_or_create_user(self, username: str, password_hash: str = "", email: str = "") -> User:
        user = self._safe_get_user(username)
        if not user:
            role = "admin" if username.lower() == "admin" else "user"
            user = User(
                username=username,
                password_hash=password_hash,
                email=email,
                role=role,
                settings={
                    "theme": "dark", "language": "en",
                    "notifications_enabled": True, "coach_tone": "encouraging",
                }
            )
            self.db.add(user)
            self._safe_commit()
            try:
                self.db.refresh(user)
            except Exception:
                pass
            logger.info(f"Created user: {username} with role: {role}")
        return user

    def get_user(self, username: str) -> Optional[User]:
        return self._safe_get_user(username)

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def update_user_settings(self, username: str, settings: dict) -> Optional[User]:
        user = self.get_user(username)
        if user:
            current = dict(user.settings or {})
            current.update(settings)
            user.settings = current
            self.db.commit()
            self.db.refresh(user)
        return user

    def update_last_login(self, username: str):
        user = self.get_user(username)
        if user:
            user.last_login = datetime.now(timezone.utc)
            self.db.commit()

    # ==================== Chat History ====================

    def save_chat_message(
        self, username: str, role: str, content: str,
        emotion: Optional[str] = None, metadata_json: Optional[dict] = None
    ) -> Optional[ChatMessage]:
        user = self.get_user(username)
        if not user:
            return None
        msg = ChatMessage(
            user_id=user.id, role=role, content=content,
            emotion=emotion, metadata_json=metadata_json or {}
        )
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        return msg

    def get_chat_history(
        self, username: str, limit: int = 50, offset: int = 0
    ) -> List[ChatMessage]:
        user = self.get_user(username)
        if not user:
            return []
        return (
            self.db.query(ChatMessage)
            .filter(ChatMessage.user_id == user.id)
            .order_by(ChatMessage.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def search_chat_history(self, username: str, query: str, limit: int = 10) -> List[ChatMessage]:
        user = self.get_user(username)
        if not user:
            return []
        return (
            self.db.query(ChatMessage)
            .filter(
                ChatMessage.user_id == user.id,
                ChatMessage.content.ilike(f"%{query}%")
            )
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_recent_emotions(self, username: str, days: int = 7) -> List[dict]:
        """Get emotional trend data for the last N days."""
        user = self.get_user(username)
        if not user:
            return []
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        messages = (
            self.db.query(ChatMessage)
            .filter(
                ChatMessage.user_id == user.id,
                ChatMessage.emotion.isnot(None),
                ChatMessage.created_at >= cutoff
            )
            .order_by(ChatMessage.created_at.asc())
            .all()
        )
        return [{"emotion": m.emotion, "timestamp": m.created_at.isoformat()} for m in messages]

    # ==================== Mood Tracking ====================

    def save_mood(
        self, username: str, mood: str, emoji: Optional[str] = None,
        energy: Optional[int] = None, focus: Optional[int] = None,
        burnout: Optional[int] = None, anxiety: Optional[int] = None,
        productivity: Optional[int] = None, note: Optional[str] = None
    ) -> Optional[MoodEntry]:
        user = self.get_user(username)
        if not user:
            return None
        entry = MoodEntry(
            user_id=user.id, mood=mood, emoji=emoji,
            energy=energy, focus=focus, burnout=burnout,
            anxiety=anxiety, productivity=productivity, note=note
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def get_mood_history(self, username: str, days: int = 30) -> List[MoodEntry]:
        user = self.get_user(username)
        if not user:
            return []
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        return (
            self.db.query(MoodEntry)
            .filter(MoodEntry.user_id == user.id, MoodEntry.created_at >= cutoff)
            .order_by(MoodEntry.created_at.asc())
            .all()
        )

    def get_mood_summary(self, username: str, days: int = 7) -> dict:
        """Generate daily mood summary with averages."""
        entries = self.get_mood_history(username, days)
        if not entries:
            return {"avg_energy": None, "avg_focus": None, "avg_burnout": None, "avg_anxiety": None}

        energies = [e.energy for e in entries if e.energy]
        foci = [e.focus for e in entries if e.focus]
        burnouts = [e.burnout for e in entries if e.burnout]
        anxieties = [e.anxiety for e in entries if e.anxiety]

        return {
            "avg_energy": round(sum(energies) / len(energies), 1) if energies else None,
            "avg_focus": round(sum(foci) / len(foci), 1) if foci else None,
            "avg_burnout": round(sum(burnouts) / len(burnouts), 1) if burnouts else None,
            "avg_anxiety": round(sum(anxieties) / len(anxieties), 1) if anxieties else None,
            "entry_count": len(entries),
            "most_common_mood": max(set(e.mood for e in entries), key=lambda m: sum(1 for e in entries if e.mood == m)) if entries else None,
        }

    def detect_burnout_alert(self, username: str) -> Optional[dict]:
        """Check if user shows signs of burnout based on recent mood data."""
        entries = self.get_mood_history(username, days=3)
        if len(entries) < 2:
            return None

        recent = entries[-3:]
        avg_burnout = sum(e.burnout for e in recent if e.burnout) / max(sum(1 for e in recent if e.burnout), 1)
        avg_energy = sum(e.energy for e in recent if e.energy) / max(sum(1 for e in recent if e.energy), 1)

        if avg_burnout >= 7 and avg_energy <= 3:
            return {
                "alert": "burnout_high",
                "severity": "high",
                "avg_burnout": round(avg_burnout, 1),
                "avg_energy": round(avg_energy, 1),
                "message": "You're showing strong burnout signals. Please prioritize rest today.",
            }
        if avg_burnout >= 5 and avg_energy <= 4:
            return {
                "alert": "burnout_moderate",
                "severity": "medium",
                "avg_burnout": round(avg_burnout, 1),
                "avg_energy": round(avg_energy, 1),
                "message": "Early burnout signs detected. Consider scaling back today.",
            }
        return None

    # ==================== Intervention Completions ====================

    def record_intervention(
        self, username: str, intervention_type: str, title: str,
        duration_minutes: Optional[int] = None, metadata_json: Optional[dict] = None
    ) -> Optional[InterventionCompletion]:
        user = self.get_user(username)
        if not user:
            return None
        record = InterventionCompletion(
            user_id=user.id, intervention_type=intervention_type,
            title=title, duration_minutes=duration_minutes,
            completed=True, metadata_json=metadata_json or {}
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_intervention_stats(self, username: str, days: int = 30) -> dict:
        user = self.get_user(username)
        if not user:
            return {}
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        records = (
            self.db.query(InterventionCompletion)
            .filter(
                InterventionCompletion.user_id == user.id,
                InterventionCompletion.created_at >= cutoff
            )
            .all()
        )
        types = {}
        for r in records:
            types[r.intervention_type] = types.get(r.intervention_type, 0) + 1
        return {
            "total_completions": len(records),
            "by_type": types,
            "daily_average": round(len(records) / max(days, 1), 1),
        }

    def get_completions_by_type(self, username: str, intervention_type: str, days: int = 7) -> int:
        user = self.get_user(username)
        if not user:
            return 0
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        return (
            self.db.query(InterventionCompletion)
            .filter(
                InterventionCompletion.user_id == user.id,
                InterventionCompletion.intervention_type == intervention_type,
                InterventionCompletion.created_at >= cutoff
            )
            .count()
        )

    # ==================== Streaks ====================

    def update_streak(self, username: str, streak_type: str = "daily") -> dict:
        """Update a streak. Returns current streak info."""
        user = self.get_user(username)
        if not user:
            return {"current": 0, "longest": 0}

        streak = (
            self.db.query(Streak)
            .filter(Streak.user_id == user.id, Streak.streak_type == streak_type)
            .first()
        )

        now = datetime.now(timezone.utc)
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)

        if not streak:
            streak = Streak(
                user_id=user.id, streak_type=streak_type,
                current_streak=1, longest_streak=1,
                last_activity_date=now
            )
            self.db.add(streak)
        else:
            last = streak.last_activity_date
            if last:
                last_date = last.replace(hour=0, minute=0, second=0, microsecond=0)
                days_diff = (today - last_date).days
                if days_diff == 1:
                    streak.current_streak += 1
                elif days_diff > 1:
                    streak.current_streak = 1
                # If same day, no change
            else:
                streak.current_streak = 1

            streak.longest_streak = max(streak.longest_streak, streak.current_streak)
            streak.last_activity_date = now

        self.db.commit()
        self.db.refresh(streak)

        return {
            "current": streak.current_streak,
            "longest": streak.longest_streak,
            "type": streak_type,
        }

    def get_streaks(self, username: str) -> List[dict]:
        user = self.get_user(username)
        if not user:
            return []
        streaks = self.db.query(Streak).filter(Streak.user_id == user.id).all()
        return [
            {
                "type": s.streak_type,
                "current": s.current_streak,
                "longest": s.longest_streak,
                "last_activity": s.last_activity_date.isoformat() if s.last_activity_date else None,
            }
            for s in streaks
        ]

    def get_all_streak_summary(self, username: str) -> dict:
        """Get a combined summary of all streak types."""
        streaks = self.get_streaks(username)
        result = {"total_days": 0, "types": {}}
        for s in streaks:
            result["types"][s["type"]] = s
            result["total_days"] += s["current"]
        return result

    # ==================== Structured Facts (Memory Upgrade) ====================

    def save_fact(
        self, username: str, fact_type: str, key: str, value: str,
        category: Optional[str] = None, confidence: float = 1.0,
        source: str = "extraction", context: Optional[str] = None
    ) -> Optional[UserFact]:
        user = self.get_user(username)
        if not user:
            return None

        # Update existing fact if same key exists
        existing = (
            self.db.query(UserFact)
            .filter(
                UserFact.user_id == user.id,
                UserFact.key == key,
                UserFact.is_active == True
            )
            .first()
        )
        if existing:
            existing.value = value
            existing.confidence = confidence
            existing.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(existing)
            return existing

        fact = UserFact(
            user_id=user.id, fact_type=fact_type, category=category,
            key=key, value=value, confidence=confidence,
            source=source, context=context
        )
        self.db.add(fact)
        self.db.commit()
        self.db.refresh(fact)
        return fact

    def get_facts(self, username: str, fact_type: Optional[str] = None) -> List[UserFact]:
        user = self.get_user(username)
        if not user:
            return []
        query = self.db.query(UserFact).filter(
            UserFact.user_id == user.id, UserFact.is_active == True
        )
        if fact_type:
            query = query.filter(UserFact.fact_type == fact_type)
        return query.order_by(UserFact.updated_at.desc()).all()

    def get_facts_as_dict(self, username: str) -> dict:
        """Get all active facts as a flat dictionary organized by category."""
        facts = self.get_facts(username)
        result = {}
        for f in facts:
            cat = f.category or "general"
            if cat not in result:
                result[cat] = {}
            result[cat][f.key] = {
                "value": f.value,
                "confidence": f.confidence,
                "type": f.fact_type,
            }
        return result

    def search_facts(self, username: str, query: str) -> List[UserFact]:
        user = self.get_user(username)
        if not user:
            return []
        return (
            self.db.query(UserFact)
            .filter(
                UserFact.user_id == user.id,
                UserFact.is_active == True,
                (
                    UserFact.key.ilike(f"%{query}%") |
                    UserFact.value.ilike(f"%{query}%") |
                    UserFact.category.ilike(f"%{query}%")
                )
            )
            .all()
        )

    # ==================== Focus Sessions ====================

    def save_focus_session(
        self, username: str, mode: str, duration_minutes: int,
        completed: bool = False, quality: Optional[int] = None,
        energy_before: Optional[int] = None, energy_after: Optional[int] = None,
        distractions: int = 0, notes: Optional[str] = None
    ) -> Optional[FocusSession]:
        user = self.get_user(username)
        if not user:
            return None
        session = FocusSession(
            user_id=user.id, mode=mode, duration_minutes=duration_minutes,
            completed=completed, quality=quality,
            energy_before=energy_before, energy_after=energy_after,
            distractions=distractions, notes=notes
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_focus_sessions(self, username: str, days: int = 30) -> List[FocusSession]:
        user = self.get_user(username)
        if not user:
            return []
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        return (
            self.db.query(FocusSession)
            .filter(
                FocusSession.user_id == user.id,
                FocusSession.created_at >= cutoff
            )
            .order_by(FocusSession.created_at.desc())
            .all()
        )

    def get_focus_stats(self, username: str, days: int = 7) -> dict:
        sessions = self.get_focus_sessions(username, days)
        if not sessions:
            return {"total_sessions": 0, "total_minutes": 0}

        completed = [s for s in sessions if s.completed]
        return {
            "total_sessions": len(sessions),
            "completed_sessions": len(completed),
            "total_minutes": sum(s.duration_minutes for s in sessions),
            "avg_quality": round(sum(s.quality or 0 for s in completed) / len(completed), 1) if completed else None,
            "avg_distractions": round(sum(s.distractions or 0 for s in sessions) / len(sessions), 1),
            "by_mode": dict(
                self.db.query(
                    FocusSession.mode, func.count(FocusSession.id)
                ).filter(
                    FocusSession.user_id == (self.get_user(username).id if self.get_user(username) else 0),
                    FocusSession.created_at >= (datetime.now(timezone.utc) - timedelta(days=days))
                ).group_by(FocusSession.mode).all()
            ),
        }

    def get_optimal_focus_duration(self, username: str) -> int:
        """Analyze past focus sessions to recommend optimal duration."""
        sessions = self.get_focus_sessions(username, days=14)
        completed = [s for s in sessions if s.completed and s.quality and s.quality >= 6]
        if not completed:
            return 25  # Default
        avg_duration = sum(s.duration_minutes for s in completed) / len(completed)
        return round(avg_duration / 5) * 5  # Round to nearest 5

    # ==================== Distraction Tracking ====================

    def log_distraction(
        self, username: str, distraction: str,
        category: Optional[str] = None, energy_level: Optional[int] = None,
        session_id: Optional[int] = None
    ) -> Optional[DistractionLog]:
        user = self.get_user(username)
        if not user:
            return None
        log = DistractionLog(
            user_id=user.id, distraction=distraction,
            category=category, energy_level=energy_level,
            session_id=session_id
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def get_distraction_stats(self, username: str, days: int = 7) -> dict:
        user = self.get_user(username)
        if not user:
            return {}
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        logs = (
            self.db.query(DistractionLog)
            .filter(DistractionLog.user_id == user.id, DistractionLog.created_at >= cutoff)
            .all()
        )
        categories = {}
        for log in logs:
            cat = log.category or "other"
            categories[cat] = categories.get(cat, 0) + 1
        return {
            "total_distractions": len(logs),
            "by_category": categories,
            "most_common": max(categories, key=categories.get) if categories else None,
        }

    # ==================== Gamification ====================

    def add_xp(self, username: str, xp: int, skill: str = "focus") -> dict:
        """Add XP to a skill and check for level up. Returns current skill state."""
        user = self.get_user(username)
        if not user:
            return {"level": 1, "xp": 0}

        progress = (
            self.db.query(SkillProgress)
            .filter(SkillProgress.user_id == user.id, SkillProgress.skill_name == skill)
            .first()
        )
        if not progress:
            progress = SkillProgress(
                user_id=user.id, skill_name=skill,
                level=1, xp=0, xp_to_next_level=100
            )
            self.db.add(progress)

        progress.xp += xp
        leveled_up = False
        while progress.xp >= progress.xp_to_next_level:
            progress.xp -= progress.xp_to_next_level
            progress.level += 1
            progress.xp_to_next_level = progress.level * 100
            leveled_up = True
            # Auto-unlock level achievements
            if progress.level in [5, 10, 25, 50, 100]:
                self.unlock_achievement(
                    username,
                    f"{skill}_level_{progress.level}",
                    f"Reached {skill} level {progress.level}!",
                    xp_reward=50
                )

        progress.updated_at = datetime.now(timezone.utc)
        self._safe_commit()
        self.db.refresh(progress)

        return {
            "level": progress.level,
            "xp": progress.xp,
            "xp_to_next": progress.xp_to_next_level,
            "leveled_up": leveled_up,
            "skill": skill,
        }

    def unlock_achievement(
        self, username: str, achievement_id: str,
        title: str, description: Optional[str] = None, xp_reward: int = 0
    ) -> Optional[Achievement]:
        """Unlock an achievement for a user. No-op if already unlocked."""
        user = self.get_user(username)
        if not user:
            return None

        existing = (
            self.db.query(Achievement)
            .filter(
                Achievement.user_id == user.id,
                Achievement.achievement_id == achievement_id
            )
            .first()
        )
        if existing:
            return existing

        achievement = Achievement(
            user_id=user.id, achievement_id=achievement_id,
            title=title, description=description, xp_reward=xp_reward
        )
        self.db.add(achievement)
        self.db.commit()
        self.db.refresh(achievement)

        # Award XP for achievement
        if xp_reward > 0:
            self.add_xp(username, xp_reward, "consistency")

        logger.info(f"Achievement unlocked for {username}: {title}")
        return achievement

    def get_achievements(self, username: str) -> List[dict]:
        user = self.get_user(username)
        if not user:
            return []
        achievements = (
            self.db.query(Achievement)
            .filter(Achievement.user_id == user.id)
            .order_by(Achievement.unlocked_at.desc())
            .all()
        )
        return [
            {
                "id": a.achievement_id,
                "title": a.title,
                "description": a.description,
                "xp_reward": a.xp_reward,
                "unlocked_at": a.unlocked_at.isoformat(),
            }
            for a in achievements
        ]

    def get_skills(self, username: str) -> List[dict]:
        user = self.get_user(username)
        if not user:
            return []
        skills = self.db.query(SkillProgress).filter(SkillProgress.user_id == user.id).all()
        return [
            {
                "name": s.skill_name,
                "level": s.level,
                "xp": s.xp,
                "xp_to_next": s.xp_to_next_level,
                "progress_pct": round((s.xp / s.xp_to_next_level) * 100, 1) if s.xp_to_next_level > 0 else 0,
            }
            for s in skills
        ]

    def check_and_award_achievements(self, username: str) -> List[Achievement]:
        """Check all achievement conditions and award any that are met."""
        user = self.get_user(username)
        if not user:
            return []

        new_achievements = []
        existing_ids = {
            a.achievement_id
            for a in self.db.query(Achievement).filter(Achievement.user_id == user.id).all()
        }

        # Check streak-based achievements
        streaks = self.get_streaks(username)
        for s in streaks:
            if s["current"] >= 3 and f"streak_3_{s['type']}" not in existing_ids:
                a = self.unlock_achievement(username, f"streak_3_{s['type']}", "3-Day Momentum", "Maintained a 3-day streak!", 20)
                if a: new_achievements.append(a)
            if s["current"] >= 7 and f"streak_7_{s['type']}" not in existing_ids:
                a = self.unlock_achievement(username, f"streak_7_{s['type']}", "Week Warrior", "Maintained a 7-day streak!", 50)
                if a: new_achievements.append(a)
            if s["current"] >= 30 and f"streak_30_{s['type']}" not in existing_ids:
                a = self.unlock_achievement(username, f"streak_30_{s['type']}", "Monthly Master", "Maintained a 30-day streak!", 200)
                if a: new_achievements.append(a)

        # Check focus session achievements
        sessions = self.get_focus_sessions(username, days=30)
        completed_count = sum(1 for s in sessions if s.completed)
        if completed_count >= 1 and "first_focus_session" not in existing_ids:
            a = self.unlock_achievement(username, "first_focus_session", "First Focus Session", "Completed your first focus session!", 10)
            if a: new_achievements.append(a)
        if completed_count >= 10 and "ten_focus_sessions" not in existing_ids:
            a = self.unlock_achievement(username, "ten_focus_sessions", "Focus Apprentice", "Completed 10 focus sessions!", 50)
            if a: new_achievements.append(a)
        if completed_count >= 50 and "fifty_focus_sessions" not in existing_ids:
            a = self.unlock_achievement(username, "fifty_focus_sessions", "Focus Master", "Completed 50 focus sessions!", 150)
            if a: new_achievements.append(a)

        # Check intervention completions
        intervention_count = self.get_intervention_stats(username, days=30).get("total_completions", 0)
        if intervention_count >= 1 and "first_intervention" not in existing_ids:
            a = self.unlock_achievement(username, "first_intervention", "First Step", "Completed your first intervention!", 10)
            if a: new_achievements.append(a)
        if intervention_count >= 20 and "twenty_interventions" not in existing_ids:
            a = self.unlock_achievement(username, "twenty_interventions", "Building Habits", "Completed 20 interventions!", 75)
            if a: new_achievements.append(a)

        # Check mood tracking
        moods = self.get_mood_history(username, days=7)
        if len(moods) >= 5 and "mood_tracker" not in existing_ids:
            a = self.unlock_achievement(username, "mood_tracker", "Emotional Awareness", "Tracked your mood 5 times this week!", 30)
            if a: new_achievements.append(a)

        return new_achievements

    # ==================== Dashboard / Analytics Helpers ====================

    def get_daily_summary(self, username: str) -> dict:
        """Get a comprehensive daily summary for the dashboard."""
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        user = self.get_user(username)
        if not user:
            return {}

        # Today's chat count
        chat_count = (
            self.db.query(ChatMessage)
            .filter(
                ChatMessage.user_id == user.id,
                ChatMessage.created_at >= today,
                ChatMessage.role == "user"
            )
            .count()
        )

        # Today's focus minutes
        focus_minutes = (
            self.db.query(func.sum(FocusSession.duration_minutes))
            .filter(
                FocusSession.user_id == user.id,
                FocusSession.created_at >= today,
                FocusSession.completed == True
            )
            .scalar() or 0
        )

        # Latest mood
        latest_mood = (
            self.db.query(MoodEntry)
            .filter(MoodEntry.user_id == user.id)
            .order_by(MoodEntry.created_at.desc())
            .first()
        )

        # Today's interventions
        today_interventions = (
            self.db.query(InterventionCompletion)
            .filter(
                InterventionCompletion.user_id == user.id,
                InterventionCompletion.created_at >= today
            )
            .count()
        )

        return {
            "chat_messages_today": chat_count,
            "focus_minutes_today": focus_minutes,
            "interventions_today": today_interventions,
            "latest_mood": {
                "mood": latest_mood.mood if latest_mood else None,
                "emoji": latest_mood.emoji if latest_mood else None,
                "energy": latest_mood.energy if latest_mood else None,
            } if latest_mood else None,
            "streaks": self.get_all_streak_summary(username),
            "achievements": len(self.get_achievements(username)),
            "skills": self.get_skills(username),
        }

    def get_weekly_report(self, username: str) -> dict:
        """Generate a comprehensive weekly report."""
        mood_summary = self.get_mood_summary(username, days=7)
        focus_stats = self.get_focus_stats(username, days=7)
        intervention_stats = self.get_intervention_stats(username, days=7)
        distraction_stats = self.get_distraction_stats(username, days=7)
        streaks = self.get_all_streak_summary(username)
        emotions = self.get_recent_emotions(username, days=7)

        return {
            "period": "7_days",
            "mood": mood_summary,
            "focus": focus_stats,
            "interventions": intervention_stats,
            "distractions": distraction_stats,
            "streaks": streaks,
            "emotional_trend": emotions,
            "burnout_alert": self.detect_burnout_alert(username),
        }

    def get_top_distractions(self, username: str, days: int = 7, limit: int = 5) -> List[dict]:
        user = self.get_user(username)
        if not user:
            return []
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        logs = (
            self.db.query(DistractionLog.distraction, func.count(DistractionLog.id).label("count"))
            .filter(DistractionLog.user_id == user.id, DistractionLog.created_at >= cutoff)
            .group_by(DistractionLog.distraction)
            .order_by(func.count(DistractionLog.id).desc())
            .limit(limit)
            .all()
        )
        return [{"distraction": d, "count": c} for d, c in logs]

    def get_peak_focus_hours(self, username: str, days: int = 14) -> List[dict]:
        """Analyze which hours of the day have the best focus quality."""
        user = self.get_user(username)
        if not user:
            return []
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        sessions = (
            self.db.query(FocusSession)
            .filter(
                FocusSession.user_id == user.id,
                FocusSession.created_at >= cutoff,
                FocusSession.quality.isnot(None)
            )
            .all()
        )
        hour_map = {}
        for s in sessions:
            hour = s.created_at.hour
            if hour not in hour_map:
                hour_map[hour] = {"count": 0, "total_quality": 0, "total_minutes": 0}
            hour_map[hour]["count"] += 1
            hour_map[hour]["total_quality"] += s.quality or 0
            hour_map[hour]["total_minutes"] += s.duration_minutes

        result = []
        for hour in sorted(hour_map.keys()):
            data = hour_map[hour]
            result.append({
                "hour": hour,
                "avg_quality": round(data["total_quality"] / data["count"], 1),
                "total_minutes": data["total_minutes"],
                "sessions": data["count"],
            })
        return result

    # ==================== Feedback & Support ====================

    def save_feedback(
        self, username: str, rating: int, category: str, feedback_text: Optional[str] = None
    ) -> Optional[UserFeedback]:
        user = self.get_user(username)
        if not user:
            return None
        fb = UserFeedback(
            user_id=user.id, rating=rating, category=category, feedback_text=feedback_text
        )
        self.db.add(fb)
        self.db.commit()
        self.db.refresh(fb)
        return fb

    def save_support_ticket(
        self, username: str, type: str, subject: str, description: str
    ) -> Optional[SupportTicket]:
        user = self.get_user(username)
        if not user:
            return None
        ticket = SupportTicket(
            user_id=user.id, type=type, subject=subject, description=description, status="open"
        )
        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)
        return ticket

    def get_user_support_tickets(self, username: str) -> List[SupportTicket]:
        user = self.get_user(username)
        if not user:
            return []
        return (
            self.db.query(SupportTicket)
            .filter(SupportTicket.user_id == user.id)
            .order_by(SupportTicket.created_at.desc())
            .all()
        )
