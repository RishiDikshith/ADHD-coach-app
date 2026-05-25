"""
Celery Background Task Queue Integration Tests
==============================================
Verifies task configurations, eager-mode task execution,
and FastAPI asynchronous task route handling.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Force Celery eager mode during testing to run in-process without Redis
os.environ["CELERY_ALWAYS_EAGER"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["GROQ_API_KEY"] = "mock_groq_key"

# Add project root to python search path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.celery_app import celery_app
from utils.celery_tasks import (
    calculate_ml_scores_task,
    generate_analytics_task,
    synthesize_personality_task,
    compile_context_task
)
from api.main_api import app
from tests.test_api import SyncTestClient


class TestADHDBackgroundQueue(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up the HTTP test client wrapper."""
        cls.client = SyncTestClient(app)

    @classmethod
    def tearDownClass(cls):
        """Close HTTP test client wrapper."""
        cls.client.close()

    def test_celery_eager_mode_active(self):
        """Verify Celery app loads task_always_eager successfully during tests."""
        self.assertTrue(celery_app.conf.task_always_eager)
        self.assertEqual(celery_app.conf.task_serializer, "json")

    def test_ml_inference_offload_task(self):
        """Verify ML inference task runs successfully in eager mode and returns scores."""
        user_data = {
            "age": 22,
            "gender": 0,
            "study_hours_per_day": 5,
            "sleep_hours": 6,
            "phone_usage_hours": 4,
            "social_media_hours": 2,
            "youtube_hours": 1,
            "gaming_hours": 1,
            "breaks_per_day": 2,
            "coffee_intake_mg": 50,
            "exercise_minutes": 15,
            "stress_level": 6
        }
        
        # Trigger eagerly
        res = calculate_ml_scores_task.delay(
            user_data=user_data,
            text="I feel a bit overwhelmed and distracted today.",
            adhd_answers=["Often", "Sometimes", "Often", "Rarely", "Often"],
            username="test_user"
        )
        
        self.assertEqual(res.status, "SUCCESS")
        result_payload = res.result
        
        self.assertIn("scores", result_payload)
        self.assertIn("interventions", result_payload)
        scores = result_payload["scores"]
        self.assertIn("productivity_score", scores)
        self.assertIn("adhd_risk", scores)
        self.assertIn("mental_health_score", scores)
        self.assertIn("final_score", scores)

    @patch("utils.celery_tasks.DatabaseManager")
    def test_analytics_precomputation_task(self, mock_db):
        """Verify that analytics task compiles and precomputes trends."""
        # Set up a mock database manager
        mock_db_instance = mock_db.return_value
        mock_db_instance.get_user.return_value = MagicMock()
        mock_db_instance.get_weekly_report.return_value = {"weekly": "data"}
        mock_db_instance.get_peak_focus_hours.return_value = [{"hour": 9, "avg_quality": 8.0}]

        res = generate_analytics_task.delay(
            username="test_user",
            user_data={"stress_level": 5}
        )

        self.assertEqual(res.status, "SUCCESS")
        result = res.result
        self.assertIn("insights", result)
        self.assertIn("recommendations", result)
        self.assertIn("weekly_report", result)
        self.assertIn("peak_focus_hours", result)

    @patch("utils.celery_tasks.DatabaseManager")
    def test_personality_synthesis_task(self, mock_db):
        """Verify personality synthesis outputs a synthesized profile JSON."""
        mock_db_instance = mock_db.return_value
        mock_db_instance.get_chat_history.return_value = []
        mock_db_instance.get_mood_history.return_value = []
        mock_db_instance.get_focus_stats.return_value = {}
        mock_db_instance.get_facts_as_dict.return_value = {}

        res = synthesize_personality_task.delay(username="test_user")
        
        self.assertEqual(res.status, "SUCCESS")
        result = res.result
        self.assertIn("adhd_archetype", result)
        self.assertIn("primary_triggers", result)
        self.assertIn("coaching_response_strategy", result)

    @patch("utils.celery_tasks.DatabaseManager")
    def test_context_compilation_task(self, mock_db):
        """Verify context compiler aggregates profile details."""
        mock_db_instance = mock_db.return_value
        mock_db_instance.get_facts_as_dict.return_value = {}

        res = compile_context_task.delay(username="test_user")
        
        self.assertEqual(res.status, "SUCCESS")
        result = res.result
        self.assertIn("summary", result)

    def test_fastapi_async_inference_endpoint(self):
        """Verify async calculate scores endpoint returns a queued status and task ID."""
        payload = {
            "user_data": {"stress_level": 7, "sleep_hours": 6},
            "adhd_answers": ["Often", "Sometimes", "Often"],
            "text": "I can't focus"
        }
        
        # Test default async behaviour
        response = self.client.post("/tasks/calculate_scores?async_task=true&username=test_user", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("task_id", data)
        self.assertEqual(data["status"], "queued")

        # Test sync fallback via the same endpoint
        response = self.client.post("/tasks/calculate_scores?async_task=false&username=test_user", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("scores", data)
        self.assertIn("interventions", data)

    def test_fastapi_task_status_endpoint(self):
        """Verify task status endpoint retrieves mock or eager states."""
        # Trigger an eager task to get a real valid task id
        payload = {
            "user_data": {"stress_level": 5, "sleep_hours": 7},
            "adhd_answers": [],
            "text": "distracted"
        }
        response = self.client.post("/tasks/calculate_scores?async_task=true&username=test_user", json=payload)
        task_id = response.json()["task_id"]

        # Retrieve status
        status_resp = self.client.get(f"/tasks/status/{task_id}")
        self.assertEqual(status_resp.status_code, 200)
        status_data = status_resp.json()
        self.assertEqual(status_data["task_id"], task_id)
        self.assertEqual(status_data["status"], "SUCCESS")
        self.assertIsNotNone(status_data["result"])
        self.assertIn("scores", status_data["result"])


if __name__ == "__main__":
    unittest.main()
