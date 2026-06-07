"""
Unit and Integration Tests for Trusted Device and PIN Authentication System
==========================================================================
Verifies trusted device registration on login, set-pin flow, pin-login verification,
lockout timers, admin PIN verification, and device revocation.
"""

import os
import sys
import unittest
import logging
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

# Add project root to python search path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

os.environ["DATABASE_URL"] = "sqlite:///./test_adhd_coach_temp.db"
os.environ["GROQ_API_KEY"] = "mock_groq_key"

import asyncio
import httpx
from api.main_api import app
from database.models import init_db, User, TrustedDevice, engine
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


class TestDeviceAuthenticationSystem(unittest.TestCase):
    def setUp(self):
        """Set up fresh database tables for each test."""
        self.cleanup_db()
        init_db()
        self.db_manager = DatabaseManager()
        
        # Bind database manager to main_api and auth_handler globals
        import api.main_api as main_api
        main_api._db_manager = self.db_manager
        main_api.auth_handler.db = self.db_manager

    def tearDown(self):
        """Clean up database connection and files."""
        # Unbind database manager
        import api.main_api as main_api
        main_api._db_manager = None
        main_api.auth_handler.db = None
        
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

    def test_login_registers_trusted_device(self):
        """Verify that password login successfully registers a trusted device."""
        client = SyncTestClient(app)
        
        # 1. Create a user
        user = User(
            username="device_user",
            password_hash=get_password_hash("Password123!"),
            role="user"
        )
        self.db_manager.db.add(user)
        self.db_manager.db.commit()

        # 2. Login with device info
        payload = {
            "username": "device_user",
            "password": "Password123!",
            "device_id": "test_uuid_123",
            "device_name": "Chrome Browser"
        }
        response = client.post("/auth/login", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

        # 3. Verify trusted device in DB
        device = self.db_manager.get_trusted_device(user.id, "test_uuid_123")
        self.assertIsNotNone(device)
        self.assertEqual(device.device_name, "Chrome Browser")
        self.assertTrue(device.is_active)
        client.close()

    def test_set_and_login_with_pin(self):
        """Verify set-pin flow and subsequent PIN-only logins from the same device."""
        client = SyncTestClient(app)

        # 1. Create a user
        user = User(
            username="pin_user",
            password_hash=get_password_hash("Password123!"),
            role="user"
        )
        self.db_manager.db.add(user)
        self.db_manager.db.commit()

        # 2. Register device by simulating successful login
        self.db_manager.save_trusted_device(user.id, "dev_abc", "Firefox Browser")

        # Mock authentication dependency override to set PIN
        app.dependency_overrides[require_user] = lambda: "pin_user"
        
        try:
            # 3. Set PIN for this device
            set_pin_payload = {
                "pin": "4321",
                "device_id": "dev_abc",
                "device_name": "Firefox Browser"
            }
            res = client.post("/auth/set-pin", json=set_pin_payload)
            self.assertEqual(res.status_code, 200)
            self.assertTrue(res.json()["success"])

            # Verify PIN hash is updated
            updated_device = self.db_manager.get_trusted_device(user.id, "dev_abc")
            self.assertIsNotNone(updated_device.pin_hash)
            self.assertTrue(verify_password("4321", updated_device.pin_hash))

            # 4. Check device trust endpoint
            trust_res = client.get("/auth/trusted-device?device_id=dev_abc")
            self.assertEqual(trust_res.status_code, 200)
            trust_data = trust_res.json()
            self.assertTrue(trust_data["is_trusted"])
            self.assertEqual(trust_data["username"], "pin_user")
            self.assertTrue(trust_data["has_pin"])

            # 5. Log in with PIN
            pin_login_payload = {
                "username": "pin_user",
                "device_id": "dev_abc",
                "pin": "4321"
            }
            login_res = client.post("/auth/pin-login", json=pin_login_payload)
            self.assertEqual(login_res.status_code, 200)
            self.assertTrue(login_res.json()["success"])
            self.assertEqual(login_res.json()["role"], "user")
        finally:
            app.dependency_overrides.clear()
            client.close()

    def test_pin_failed_attempts_lockout(self):
        """Verify device locks temporarily after 5 consecutive failed PIN attempts."""
        client = SyncTestClient(app)

        # 1. Create a user and trusted device with a PIN
        user = User(
            username="lockout_user",
            password_hash=get_password_hash("Password123!"),
            role="user"
        )
        self.db_manager.db.add(user)
        self.db_manager.db.commit()

        self.db_manager.save_trusted_device(
            user_id=user.id,
            device_id="locked_dev",
            device_name="Safari Browser",
            pin_hash=get_password_hash("1111")
        )

        # 2. Try logging in with incorrect PIN 4 times
        for i in range(4):
            payload = {
                "username": "lockout_user",
                "device_id": "locked_dev",
                "pin": "9999"
            }
            res = client.post("/auth/pin-login", json=payload)
            self.assertEqual(res.status_code, 200)
            self.assertFalse(res.json()["success"])
            self.assertIn("attempts remaining", res.json()["error"])

        # 3. 5th attempt should lock the device
        payload = {
            "username": "lockout_user",
            "device_id": "locked_dev",
            "pin": "9999"
        }
        res = client.post("/auth/pin-login", json=payload)
        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.json()["success"])
        self.assertIn("Device temporarily locked", res.json()["error"])

        # 4. Verify DB indicates locked device
        device = self.db_manager.get_trusted_device(user.id, "locked_dev")
        self.assertEqual(device.failed_attempts, 5)
        self.assertIsNotNone(device.locked_until)
        self.assertTrue(device.locked_until > datetime.utcnow())

        # 5. Subsequent attempts (even with correct PIN) should fail immediately due to lock
        payload = {
            "username": "lockout_user",
            "device_id": "locked_dev",
            "pin": "1111"
        }
        res = client.post("/auth/pin-login", json=payload)
        self.assertFalse(res.json()["success"])
        self.assertIn("Device temporarily locked", res.json()["error"])
        client.close()

    @patch("api.main_api.os.getenv")
    def test_admin_pin_login(self, mock_getenv):
        """Verify admin login with administrative PIN matches env variables."""
        def getenv_mock(key, default=None):
            vals = {
                "ADMIN_PIN": "9876",
                "DATABASE_URL": "sqlite:///./test_adhd_coach_temp.db"
            }
            return vals.get(key, default)
        mock_getenv.side_effect = getenv_mock

        client = SyncTestClient(app)

        # 1. Create admin user
        admin_user = User(
            username="super_admin",
            password_hash=get_password_hash("AdminPassword123!"),
            role="admin",
            is_admin=True
        )
        self.db_manager.db.add(admin_user)
        self.db_manager.db.commit()

        # 2. Login with incorrect admin PIN
        admin_payload = {
            "username": "super_admin",
            "pin": "0000"
        }
        res = client.post("/auth/admin-pin-login", json=admin_payload)
        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.json()["success"])

        # 3. Login with correct admin PIN
        admin_payload = {
            "username": "super_admin",
            "pin": "9876"
        }
        res = client.post("/auth/admin-pin-login", json=admin_payload)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["success"])
        self.assertEqual(res.json()["role"], "admin")
        client.close()

    def test_get_and_revoke_trusted_devices(self):
        """Verify retrieving active trusted devices and revoking them via settings."""
        client = SyncTestClient(app)

        # 1. Create user and register two trusted devices
        user = User(
            username="devices_mgmt_user",
            password_hash=get_password_hash("Password123!"),
            role="user"
        )
        self.db_manager.db.add(user)
        self.db_manager.db.commit()

        self.db_manager.save_trusted_device(user.id, "dev_one", "Pixel Phone")
        self.db_manager.save_trusted_device(user.id, "dev_two", "iPad Pro")

        app.dependency_overrides[require_user] = lambda: "devices_mgmt_user"

        try:
            # 2. Retrieve devices list
            devices_res = client.get("/auth/devices")
            self.assertEqual(devices_res.status_code, 200)
            devices_list = devices_res.json()
            self.assertEqual(len(devices_list), 2)
            self.assertEqual(devices_list[0]["device_name"], "Pixel Phone")

            # 3. Revoke one device
            revoke_payload = {
                "device_id": "dev_one"
            }
            revoke_res = client.post("/auth/remove-device", json=revoke_payload)
            self.assertEqual(revoke_res.status_code, 200)
            self.assertTrue(revoke_res.json()["success"])

            # 4. Check active devices list again
            devices_res_after = client.get("/auth/devices")
            devices_list_after = devices_res_after.json()
            self.assertEqual(len(devices_list_after), 1)
            self.assertEqual(devices_list_after[0]["device_id"], "dev_two")
        finally:
            app.dependency_overrides.clear()
            client.close()


if __name__ == "__main__":
    unittest.main()
