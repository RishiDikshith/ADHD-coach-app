"""Pytest isolation for process-global application state."""

import pytest

from auth.auth_handler import rate_limiter


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Prevent one test's in-memory rate-limit history from affecting another."""
    rate_limiter.reset_all()
    yield
    rate_limiter.reset_all()
