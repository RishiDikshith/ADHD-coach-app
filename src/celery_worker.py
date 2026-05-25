import os
import sys

# Add project 'src' directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Add parent directory to path to allow absolute 'src.x' imports
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from utils.celery_app import celery_app
import utils.celery_tasks  # Force task registrations

# Export celery_app for running the worker:
# celery -A celery_worker.celery_app worker --loglevel=info
app = celery_app

if __name__ == "__main__":
    import celery
    print("Celery Worker Configuration:")
    print(f"Broker URL: {celery_app.conf.broker_url}")
    print(f"Result Backend: {celery_app.conf.result_backend}")
    print(f"Registered Tasks: {list(celery_app.tasks.keys())}")
