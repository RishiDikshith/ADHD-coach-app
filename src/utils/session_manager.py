import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


class SessionManager:
    """Manage user authentication session persistence"""

    def __init__(self, session_dir=".session_data"):
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(exist_ok=True)
        self.session_file = self.session_dir / "user_session.json"

    def save_session(self, username, token=None, expires_at=None):
        """Save authentication session to persistent storage"""
        if expires_at is None:
            expires_at = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

        session_data = {
            "username": username,
            "token": token or username,  # Simple token; enhance with JWT in production
            "login_time": datetime.now(timezone.utc).isoformat(),
            "expires_at": expires_at,
        }

        try:
            with open(self.session_file, "w") as f:
                json.dump(session_data, f)
        except (AttributeError, KeyError, OSError, RuntimeError, TypeError, ValueError) as e:
            print(f"Error saving session: {e}")

    def load_session(self):
        """Load authentication session from persistent storage"""
        if not self.session_file.exists():
            return None

        try:
            with open(self.session_file, "r") as f:
                session_data = json.load(f)

            # Check if session is still valid
            expires_at = datetime.fromisoformat(
                session_data.get(
                    "expires_at", datetime.min.replace(tzinfo=timezone.utc).isoformat()
                )
            )
            if expires_at > datetime.now(timezone.utc):
                return session_data
            else:
                self.clear_session()
                return None
        except (AttributeError, KeyError, OSError, RuntimeError, TypeError, ValueError) as e:
            print(f"Error loading session: {e}")
            return None

    def clear_session(self):
        """Clear authentication session"""
        if self.session_file.exists():
            try:
                self.session_file.unlink()
            except (AttributeError, KeyError, OSError, RuntimeError, TypeError, ValueError) as e:
                print(f"Error clearing session: {e}")

    def is_session_valid(self):
        """Check if a valid session exists"""
        return self.load_session() is not None
