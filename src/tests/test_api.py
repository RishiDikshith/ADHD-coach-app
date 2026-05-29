"""
API Endpoint Integration Tests
=============================
Verifies FastAPI endpoint authentication, settings updates, scores calculation,
interventions suggestions, and conversational API routes.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add project root to python search path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Set database env to a temporary file before imports
os.environ["DATABASE_URL"] = "sqlite:///./test_adhd_coach_temp.db"
os.environ["GROQ_API_KEY"] = "mock_groq_key"

import asyncio
import httpx
from api.main_api import app


class SyncTestClient:
    def __init__(self, app):
        self.transport = httpx.ASGITransport(app=app)
        self.client = httpx.AsyncClient(transport=self.transport, base_url="http://testserver")
        self.loop = asyncio.new_event_loop()

    def get(self, url, **kwargs):
        return self.loop.run_until_complete(self.client.get(url, **kwargs))

    def post(self, url, **kwargs):
        return self.loop.run_until_complete(self.client.post(url, **kwargs))

    def put(self, url, **kwargs):
        return self.loop.run_until_complete(self.client.put(url, **kwargs))

    def delete(self, url, **kwargs):
        return self.loop.run_until_complete(self.client.delete(url, **kwargs))

    def close(self):
        self.loop.run_until_complete(self.client.aclose())
        self.loop.close()


class TestADHDProductivityAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up the database tables, global engines, and synchronous wrapper client."""
        import api.main_api as main_api
        from database.models import init_db
        from database.crud import DatabaseManager
        from task_paralysis.state_detector import ADHDStateDetector
        from intervention.adaptive_coach import AdaptiveCoach
        from focus.focus_engine import FocusEngine
        from gamification import GamificationEngine
        from ai_engine.rag_engine import RAGEngine

        # 1. Initialize DB tables
        init_db()

        # 2. Instantiate and assign global DB manager and dependent engines
        db_mgr = DatabaseManager()
        main_api._db_manager = db_mgr
        main_api.auth_handler.db = db_mgr
        main_api._state_detector = ADHDStateDetector(db_mgr)
        main_api._adaptive_coach = AdaptiveCoach(db_mgr, main_api._state_detector)
        main_api._focus_engine = FocusEngine(db_mgr)
        main_api._gamification = GamificationEngine(db_mgr)
        main_api._rag_engine = RAGEngine(None, db_mgr)

        # 3. Instantiate client
        cls.client = SyncTestClient(app)

    @classmethod
    def tearDownClass(cls):
        """Close the test client and clean up database files."""
        cls.client.close()
        
        # Force close main app database session
        import api.main_api as main_api
        if main_api._db_manager:
            main_api._db_manager.close()

        # Force engine disposal to release file locks on Windows
        from database.models import engine
        try:
            engine.dispose()
        except Exception:
            pass

        # Remove the temp database files
        try:
            import os
            for f in ["./test_adhd_coach_temp.db", "./test_adhd_coach_temp.db-journal"]:
                if os.path.exists(f):
                    os.remove(f)
        except Exception:
            pass

    def test_health_check_documentation(self):
        """Verify Swagger UI and OpenAPI schemas are accessible."""
        response = self.client.get("/openapi.json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("ADHD Productivity API", response.json()["info"]["title"])

    def test_auth_registration_validation(self):
        """Verify registration rejects invalid details and accepts valid formatting."""
        # Scenario 1: Reject short username
        payload = {"username": "ab", "password": "password123", "email": "test@example.com"}
        response = self.client.post("/auth/register", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["success"])
        self.assertIn("username", response.json()["error"].lower())

        # Scenario 2: Reject short password
        payload = {"username": "validuser", "password": "123", "email": "test@example.com"}
        response = self.client.post("/auth/register", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["success"])
        self.assertIn("password", response.json()["error"].lower())

    def test_scores_calculation_heuristics(self):
        """Verify scores are successfully computed with rule-based heuristics and fallbacks."""
        payload = {
            "user_data": {
                "age": 21,
                "gender": 1,
                "study_hours_per_day": 4,
                "sleep_hours": 7,
                "phone_usage_hours": 3,
                "social_media_hours": 1,
                "youtube_hours": 1,
                "gaming_hours": 1,
                "breaks_per_day": 3,
                "coffee_intake_mg": 100,
                "exercise_minutes": 30,
                "stress_level": 5
            },
            "adhd_answers": ["Often", "Sometimes", "Rarely", "Often", "Very Often"],
            "text": "I feel slightly distracted today"
        }
        response = self.client.post("/calculate_scores", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify scores dictionary contains essential metrics
        self.assertIn("scores", data)
        scores = data["scores"]
        self.assertIn("productivity_score", scores)
        self.assertIn("adhd_risk", scores)
        self.assertIn("mental_health_score", scores)
        self.assertIn("depression_score", scores)
        self.assertIn("final_score", scores)
        self.assertIn("level", scores)
        self.assertIn("focus_risk", scores)

    def test_interventions_endpoint(self):
        """Verify interventions are correctly derived from calculated score indicators."""
        payload = {
            "user_data": {
                "stress_level": 9,
                "sleep_hours": 5,
                "energy_level": 3
            },
            "scores": {
                "productivity_score": 40.0,
                "adhd_risk": 0.8,
                "mental_health_score": 30.0,
                "depression_score": 40.0
            }
        }
        response = self.client.post("/get_interventions", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("interventions", data)
        self.assertTrue(len(data["interventions"]) > 0)

    @patch("api.main_api.get_ai_reply")
    def test_task_paralysis_decomp(self, mock_ai):
        """Verify task paralysis analyzer suggests micro-steps."""
        mock_ai.return_value = 'REPLY:\nLet\'s smash this.\nTASKS:\n- Open your notes\n- Read one page'
        payload = {
            "task": "Write an entire marketing plan",
            "user_data": {"stress_level": 8, "energy_level": 4}
        }
        response = self.client.post("/task-paralysis/analyze", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("paralysis_detected", data)
        self.assertIn("microtasks", data)
        self.assertTrue(len(data["microtasks"]) > 0)

    def test_settings_retrieval_fallback(self):
        """Verify default settings are retrieved for uninitialized users."""
        response = self.client.get("/settings/non_existent_user")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["theme"], "dark")
        self.assertTrue(data["notifications_enabled"])

    def test_voice_assistant_settings(self):
        """Verify voice assistant preferences can be updated, saved to DB, and retrieved."""
        from auth.auth_handler import require_user
        # Override require_user dependency to bypass active JWT authentication logic in test environment
        app.dependency_overrides[require_user] = lambda: "test_user"
        
        try:
            # 1. Register test_user in SQLite DB so they exist
            register_payload = {
                "username": "test_user",
                "password": "password123",
                "email": "test@example.com"
            }
            self.client.post("/auth/register", json=register_payload)

            payload = {
                "theme": "dark",
                "language": "es",
                "notifications_enabled": True,
                "notification_frequency": "medium",
                "timer_duration": 30,
                "auto_check_in": True,
                "sound_enabled": True,
                "use_12h_format": False,
                "coach_tone": "gentle",
                "focus_area": "focus",
                "overwhelm_mode_enabled": False,
                "start_tiny_default": False,
                "time_blindness_enabled": True,
                "celebration_effects": True,
                "voice_autospeak": True,
                "voice_speed": 1.25,
                "voice_pitch": 0.95,
                "voice_accent": "es-ES"
            }
            # Put the updated preferences
            response = self.client.put("/settings/test_user", json=payload)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data.get("success", False))
            
            # Retrieve updated preferences and assert correct parsing
            response = self.client.get("/settings/test_user")
            self.assertEqual(response.status_code, 200)
            settings_data = response.json()
            self.assertEqual(settings_data["language"], "es")
            self.assertEqual(settings_data["coach_tone"], "gentle")
            self.assertEqual(settings_data["focus_area"], "focus")
            self.assertTrue(settings_data["voice_autospeak"])
            self.assertEqual(settings_data["voice_speed"], 1.25)
            self.assertEqual(settings_data["voice_pitch"], 0.95)
            self.assertEqual(settings_data["voice_accent"], "es-ES")
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.pop(require_user, None)


if __name__ == "__main__":
    unittest.main()
