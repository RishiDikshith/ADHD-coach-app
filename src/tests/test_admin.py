"""
Unit Tests for Admin Authentication, Bootstrapping, and Authorization
======================================================================
Verifies admin creation, production complexity checks, role checker access control,
and structured security audit logging.
"""

import os
import re
import sys
import unittest
import logging
from unittest.mock import patch, MagicMock

# Add project root to python search path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

os.environ["DATABASE_URL"] = "sqlite:///./test_adhd_coach_temp.db"
os.environ["GROQ_API_KEY"] = "mock_groq_key"

import asyncio
import httpx
from api.main_api import app, bootstrap_admin
from database.models import init_db, User, engine
from database.crud import DatabaseManager
from auth.auth_handler import require_admin, require_user, get_password_hash, verify_password


class SyncTestClient:
    def __init__(self, app):
        self.transport = httpx.ASGITransport(app=app)
        self.client = httpx.AsyncClient(transport=self.transport, base_url="http://testserver")
        self.loop = asyncio.new_event_loop()

    def get(self, url, **kwargs):
        return self.loop.run_until_complete(self.client.get(url, **kwargs))

    def post(self, url, **kwargs):
        return self.loop.run_until_complete(self.client.post(url, **kwargs))

    def close(self):
        self.loop.run_until_complete(self.client.aclose())
        self.loop.close()


class TestAdminSystem(unittest.TestCase):
    def setUp(self):
        """Set up fresh database tables for each test."""
        # Remove any existing DB files
        self.cleanup_db()
        init_db()
        self.db_manager = DatabaseManager()

    def tearDown(self):
        """Clean up database connection and files."""
        self.db_manager.close()
        engine.dispose()
        self.cleanup_db()

    def cleanup_db(self):
        for f in ["./test_adhd_coach_temp.db", "./test_adhd_coach_temp.db-journal"]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass

    @patch("api.main_api.os.getenv")
    @patch("utils.audit_logger.audit_log")
    def test_bootstrap_admin_creation_success(self, mock_audit, mock_getenv):
        """Verify bootstrap_admin successfully creates admin user when env vars are set."""
        def getenv_mock(key, default=None):
            vals = {
                "ADMIN_USERNAME": "superadmin",
                "ADMIN_PASSWORD": "SecurePassword123!",
                "ENVIRONMENT": "development",
            }
            return vals.get(key, default)
        mock_getenv.side_effect = getenv_mock

        bootstrap_admin(self.db_manager)

        # Check user in DB
        admin_user = self.db_manager.get_user("superadmin")
        self.assertIsNotNone(admin_user)
        self.assertEqual(admin_user.role, "admin")
        self.assertTrue(verify_password("SecurePassword123!", admin_user.password_hash))

        # Check audit log call
        mock_audit.assert_any_call(
            username="superadmin",
            action="admin_bootstrap_creation",
            status="SUCCESS",
            details={"message": "Admin user created successfully"}
        )

    @patch("api.main_api.os.getenv")
    @patch("utils.audit_logger.audit_log")
    def test_bootstrap_admin_promotion(self, mock_audit, mock_getenv):
        """Verify bootstrap_admin promotes an existing user to admin role."""
        # 1. Create a normal user first
        normal_user = User(
            username="promote_me",
            password_hash=get_password_hash("SomePassword123!"),
            role="user"
        )
        self.db_manager.db.add(normal_user)
        self.db_manager.db.commit()

        # 2. Configure environment variables for that user
        def getenv_mock(key, default=None):
            vals = {
                "ADMIN_USERNAME": "promote_me",
                "ADMIN_PASSWORD": "SecurePassword123!",
                "ENVIRONMENT": "development",
            }
            return vals.get(key, default)
        mock_getenv.side_effect = getenv_mock

        bootstrap_admin(self.db_manager)

        # 3. Verify they are promoted
        updated_user = self.db_manager.get_user("promote_me")
        self.assertEqual(updated_user.role, "admin")

        mock_audit.assert_any_call(
            username="promote_me",
            action="admin_bootstrap_promotion",
            status="SUCCESS",
            details={"message": "Existing user promoted to admin role"}
        )

    @patch("api.main_api.os.getenv")
    def test_bootstrap_admin_dev_missing_vars(self, mock_getenv):
        """Verify missing env vars in development do not raise errors."""
        def getenv_mock(key, default=None):
            vals = {
                "ADMIN_USERNAME": "",
                "ADMIN_PASSWORD": "",
                "ENVIRONMENT": "development",
            }
            return vals.get(key, default)
        mock_getenv.side_effect = getenv_mock

        # Should log a warning and return cleanly
        try:
            bootstrap_admin(self.db_manager)
        except RuntimeError as e:
            self.fail(f"bootstrap_admin raised RuntimeError in dev: {e}")

    @patch("api.main_api.os.getenv")
    @patch("utils.audit_logger.audit_log")
    def test_bootstrap_admin_prod_missing_vars_fatal(self, mock_audit, mock_getenv):
        """Verify missing env vars in production fail startup."""
        def getenv_mock(key, default=None):
            vals = {
                "ADMIN_USERNAME": "",
                "ADMIN_PASSWORD": "",
                "ENVIRONMENT": "production",
            }
            return vals.get(key, default)
        mock_getenv.side_effect = getenv_mock

        with self.assertRaises(RuntimeError) as context:
            bootstrap_admin(self.db_manager)
        
        self.assertIn("ADMIN_USERNAME or ADMIN_PASSWORD not configured", str(context.exception))
        mock_audit.assert_called_with(
            username="system",
            action="admin_bootstrap",
            status="FAILED",
            details={"reason": "missing_env_vars", "is_prod": True},
            severity="CRITICAL"
        )

    @patch("api.main_api.os.getenv")
    @patch("utils.audit_logger.audit_log")
    def test_bootstrap_admin_prod_weak_password_fatal(self, mock_audit, mock_getenv):
        """Verify weak admin password in production fails startup."""
        weak_passwords = [
            "weakpass",           # short, no upper/digit/special
            "Weakpassword",       # no digit/special
            "Weakpassword1",      # no special
            "Secure1!",           # too short (< 12 chars)
        ]

        for pwd in weak_passwords:
            def getenv_mock(key, default=None):
                vals = {
                    "ADMIN_USERNAME": "prodadmin",
                    "ADMIN_PASSWORD": pwd,
                    "ENVIRONMENT": "production",
                }
                return vals.get(key, default)
            mock_getenv.side_effect = getenv_mock

            with self.assertRaises(RuntimeError) as context:
                bootstrap_admin(self.db_manager)
            
            self.assertIn("fails complexity requirements", str(context.exception))
            
        mock_audit.assert_called_with(
            username="system",
            action="admin_bootstrap",
            status="FAILED",
            details={"reason": "weak_password", "reasons": unittest.mock.ANY},
            severity="CRITICAL"
        )

    def test_admin_health_route_auth_required(self):
        """Verify GET /admin/health rejects unauthenticated and non-admin requests."""
        client = SyncTestClient(app)
        
        try:
            # 1. Unauthenticated request -> 401 Unauthorized
            response = client.get("/admin/health")
            self.assertEqual(response.status_code, 401)

            # 2. Authenticated as non-admin user -> 403 Forbidden
            # Create standard user
            normal_user = User(
                username="normal_user",
                password_hash=get_password_hash("NormalPassword123!"),
                role="user"
            )
            self.db_manager.db.add(normal_user)
            self.db_manager.db.commit()

            # Override require_admin dependency to verify RoleChecker behavior
            # Let's test the endpoint directly with mock dependency overrides
            app.dependency_overrides[require_admin] = lambda: "normal_user"
            # Wait, RoleChecker is a class callable. Let's override require_admin directly.
            # If we override require_admin to return a username, FastAPI thinks it's authorized.
            # To test the actual role verification, let's override get_db or the token logic,
            # or just call RoleChecker manually.
            
            # Let's use FastAPI dependency override to simulate a normal user vs admin user.
            # First, test the dependency class itself manually.
            from fastapi import Request
            from auth.auth_handler import RoleChecker
            
            checker = RoleChecker(allowed_roles=["admin"])
            
            # Mock request
            mock_request = MagicMock(spec=Request)
            mock_request.headers = {"Authorization": "Bearer mock_token"}
            mock_request.cookies = {}
            mock_request.client = MagicMock()
            mock_request.client.host = "127.0.0.1"
            mock_request.url.path = "/admin/health"
            mock_request.method = "GET"
            
            with patch("auth.auth_handler.verify_token") as mock_verify:
                mock_verify.return_value = {"sub": "normal_user", "type": "access"}
                
                # RoleChecker should raise 403 for standard user
                from fastapi import HTTPException
                with self.assertRaises(HTTPException) as ctx:
                    checker(mock_request)
                self.assertEqual(ctx.exception.status_code, 403)
                self.assertIn("Permission denied", ctx.exception.detail)

            # 3. Authenticated as admin user -> Success
            # Create admin user
            admin_user = User(
                username="admin_user",
                password_hash=get_password_hash("AdminPassword123!"),
                role="admin"
            )
            self.db_manager.db.add(admin_user)
            self.db_manager.db.commit()

            with patch("auth.auth_handler.verify_token") as mock_verify:
                mock_verify.return_value = {"sub": "admin_user", "type": "access"}
                
                # Should return the admin's username
                allowed_user = checker(mock_request)
                self.assertEqual(allowed_user, "admin_user")
                
        finally:
            app.dependency_overrides.clear()
            client.close()


if __name__ == "__main__":
    unittest.main()
