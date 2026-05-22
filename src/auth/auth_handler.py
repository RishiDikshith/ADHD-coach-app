"""
Auth Handler
============
Secure authentication with JWT tokens, bcrypt password hashing,
rate limiting, and comprehensive input sanitization.

Uses python-jose for JWT and passlib with bcrypt for password hashing.
"""

import os
import re
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from jose import JWTError, jwt
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", os.urandom(32).hex())
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Rate limiting defaults
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
RATE_LIMIT_MAX_REQUESTS = int(os.getenv("RATE_LIMIT_MAX", "30"))


# ==================== Password Hashing ====================

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ==================== JWT Tokens ====================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token with longer expiry."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> Optional[dict]:
    """Verify a JWT token and return the payload. Returns None if invalid."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        return None


def refresh_access_token(refresh_token: str) -> Optional[Tuple[str, str]]:
    """Exchange a refresh token for new access + refresh tokens."""
    payload = verify_token(refresh_token)
    if payload is None or payload.get("type") != "refresh":
        return None

    username = payload.get("sub")
    if not username:
        return None

    new_access = create_access_token({"sub": username})
    new_refresh = create_refresh_token({"sub": username})
    return new_access, new_refresh


# ==================== Input Sanitization ====================

# SQL injection patterns
SQL_INJECTION_PATTERN = re.compile(
    r"(\b(ALTER|CREATE|DELETE|DROP|EXEC|INSERT|MERGE|SELECT|TRUNCATE|UPDATE|UNION)\b)",
    re.IGNORECASE
)

# Script injection patterns
SCRIPT_PATTERN = re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL)

# Path traversal patterns
PATH_TRAVERSAL_PATTERN = re.compile(r"(\.\./|\.\.\\)")

# Dangerous characters for usernames
INVALID_USERNAME_CHARS = re.compile(r"[<>\"'%;()&+]")


def sanitize_input(text: str, max_length: int = 10000) -> str:
    """Sanitize user input by removing dangerous patterns."""
    if not text:
        return text

    # Truncate to max length
    text = text[:max_length]

    # Remove script tags
    text = SCRIPT_PATTERN.sub("", text)

    # Remove SQL injection patterns (case-insensitive)
    text = SQL_INJECTION_PATTERN.sub("", text)

    return text.strip()


def sanitize_username(username: str) -> Optional[str]:
    """Validate and sanitize username. Returns None if invalid."""
    if not username or len(username) < 3 or len(username) > 50:
        return None

    username = username.strip()

    # Check for dangerous characters
    if INVALID_USERNAME_CHARS.search(username):
        return None

    # Only allow alphanumeric, underscores, hyphens, and dots
    if not re.match(r"^[a-zA-Z0-9_.-]+$", username):
        return None

    return username


def sanitize_prompt(prompt: str) -> str:
    """Sanitize LLM prompts to prevent injection attacks."""
    if not prompt:
        return prompt

    # Remove any system prompt override attempts
    prompt = re.sub(
        r"(?i)(ignore\s+(all\s+)?(previous\s+)?instructions|system\s+prompt|you\s+are\s+(now|not)\s+)",
        "[redacted]",
        prompt
    )

    # Limit prompt length
    prompt = prompt[:4000]

    return prompt


# ==================== Rate Limiting (Simple In-Memory) ====================

class RateLimiter:
    """Simple in-memory rate limiter using sliding window."""

    def __init__(self):
        self._requests = {}  # key -> list of timestamps

    def check(self, key: str, max_requests: int = RATE_LIMIT_MAX_REQUESTS,
              window_seconds: int = RATE_LIMIT_WINDOW_SECONDS) -> Tuple[bool, int]:
        """
        Check if a request is allowed.
        Returns (allowed, remaining_requests).
        """
        now = datetime.now(timezone.utc).timestamp()
        cutoff = now - window_seconds

        if key not in self._requests:
            self._requests[key] = []

        # Clean old entries
        self._requests[key] = [t for t in self._requests[key] if t > cutoff]

        remaining = max_requests - len(self._requests[key])

        if remaining <= 0:
            return False, 0

        self._requests[key].append(now)
        return True, remaining - 1

    def reset(self, key: str):
        """Reset rate limit for a key."""
        self._requests.pop(key, None)


# Global rate limiter instance
rate_limiter = RateLimiter()


# ==================== Auth Handler Class ====================

class AuthHandler:
    """High-level authentication handler integrating JWT, bcrypt, and rate limiting."""

    def __init__(self, db_manager=None):
        self.db = db_manager

    def register_user(self, username: str, password: str, email: str = "") -> dict:
        """Register a new user with hashed password."""
        from src.database.crud import DatabaseManager

        sanitized_username = sanitize_username(username)
        if not sanitized_username:
            return {"success": False, "error": "Invalid username format"}

        if len(password) < 8:
            return {"success": False, "error": "Password must be at least 8 characters"}

        db = self.db or DatabaseManager()
        existing = db.get_user(sanitized_username)
        if existing:
            return {"success": False, "error": "Username already exists"}

        password_hash = get_password_hash(password)
        user = db.get_or_create_user(sanitized_username, password_hash, email)

        access_token = create_access_token({"sub": sanitized_username})
        refresh_token = create_refresh_token({"sub": sanitized_username})

        return {
            "success": True,
            "message": "Account created successfully",
            "token": access_token,
            "refresh_token": refresh_token,
            "username": sanitized_username,
            "role": getattr(user, "role", "user"),
        }

    def login_user(self, username: str, password: str) -> dict:
        """Authenticate a user and return JWT tokens."""
        from src.database.crud import DatabaseManager

        sanitized_username = sanitize_username(username)
        if not sanitized_username:
            return {"success": False, "error": "Invalid username format"}

        db = self.db or DatabaseManager()
        user = db.get_user(sanitized_username)

        if not user or not verify_password(password, user.password_hash):
            return {"success": False, "error": "Invalid username or password"}

        # Auto-promote "admin" user to admin role if they somehow don't have it
        if sanitized_username.lower() == "admin" and getattr(user, "role", "user") != "admin":
            try:
                user.role = "admin"
                db.db.commit()
            except Exception as e:
                logger.warning(f"Failed to auto-promote admin user: {e}")

        # Update last login
        db.update_last_login(sanitized_username)

        access_token = create_access_token({"sub": sanitized_username})
        refresh_token = create_refresh_token({"sub": sanitized_username})

        return {
            "success": True,
            "message": "Login successful",
            "token": access_token,
            "refresh_token": refresh_token,
            "username": sanitized_username,
            "role": getattr(user, "role", "user"),
        }

    def refresh_token(self, refresh_token_str: str) -> dict:
        """Refresh an access token using a refresh token."""
        result = refresh_access_token(refresh_token_str)
        if not result:
            return {"success": False, "error": "Invalid or expired refresh token"}
        access_token, new_refresh = result
        return {
            "success": True,
            "token": access_token,
            "refresh_token": new_refresh,
        }

    def get_current_user(self, token: str) -> Optional[str]:
        """Extract username from a valid access token."""
        payload = verify_token(token)
        if payload is None or payload.get("type") != "access":
            return None
        return payload.get("sub")
