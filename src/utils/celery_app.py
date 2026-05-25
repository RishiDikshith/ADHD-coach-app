import os
import logging
from celery import Celery
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Configure Celery Broker and Backend URLs
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

# Fallback to synchronous/eager execution if specified (useful for local dev without Redis / testing)
always_eager = os.getenv("CELERY_ALWAYS_EAGER", "false").lower() in ("true", "1", "yes")
is_testing = "unittest" in "".join(os.getenv("PYTEST_CURRENT_TEST", "")) or os.getenv("DATABASE_URL", "").startswith("sqlite:///:memory:")

if is_testing:
    logger.info("Test environment detected. Forcing Celery eager mode (synchronous).")
    always_eager = True

# Create Celery App instance
celery_app = Celery(
    "adhd_productivity_tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
)

# Apply settings
celery_app.conf.update(
    task_always_eager=always_eager,
    task_eager_propagates=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes maximum runtime
    task_soft_time_limit=240,  # Soft limit 4 minutes
    # Task failure recovery and retry options
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Auto-discover tasks in src.utils.celery_tasks module
celery_app.autodiscover_tasks(["utils"], related_name="celery_tasks")

logger.info(
    f"Celery initialized with Broker={CELERY_BROKER_URL}, EagerMode={always_eager}"
)
