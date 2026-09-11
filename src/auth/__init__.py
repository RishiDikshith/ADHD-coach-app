"""
Authentication Module
=====================
JWT-based authentication with bcrypt password hashing,
rate limiting support, and input sanitization.
"""

from .auth_handler import (
    AuthHandler,
    create_access_token,
    get_password_hash,
    sanitize_input,
    verify_password,
    verify_token,
)

__all__ = [
    "AuthHandler",
    "create_access_token",
    "get_password_hash",
    "sanitize_input",
    "verify_password",
    "verify_token",
]
