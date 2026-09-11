import os
from pathlib import Path

# Ensure tests NEVER connect to or drop the development/production database!
_test_db_path = (Path(__file__).resolve().parents[2] / "test_adhd_coach_temp.db").as_posix()
_current_db = os.environ.get("DATABASE_URL", "")
if not _current_db or "adhd_coach.db" in _current_db:
    os.environ["DATABASE_URL"] = f"sqlite:///{_test_db_path}"
os.environ.setdefault("GROQ_API_KEY", "mock_groq_key")
os.environ.setdefault(
    "JWT_SECRET_KEY", "test_jwt_secret_key_for_testing_only_must_be_long_enough_1234567890"
)

import pytest
from sqlalchemy.exc import SQLAlchemyError

from auth.auth_handler import rate_limiter
from database.models import Base, engine, init_db


@pytest.fixture(autouse=True)
def reset_rate_limiter_and_db():
    """Reset in-memory auth throttling and the test database schema between tests."""
    rate_limiter.reset_all()

    # SQLite in-memory databases are shared by connection pool and can leak schema
    # state across Celery/FastAPI threads if tables are not recreated before each test.
    try:
        Base.metadata.drop_all(bind=engine)
    except SQLAlchemyError:
        pass
    init_db()

    yield

    rate_limiter.reset_all()
    try:
        Base.metadata.drop_all(bind=engine)
    except SQLAlchemyError:
        pass
    init_db()
