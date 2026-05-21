"""
Authentication Module
=====================
JWT-based authentication with bcrypt password hashing,
rate limiting support, and input sanitization.
"""

from .auth_handler import AuthHandler, get_password_hash, verify_password, create_access_token, verify_token, sanitize_input

__all__ = [
    "AuthHandler", "get_password_hash", "verify_password",
    "create_access_token", "verify_token", "sanitize_input",
]
