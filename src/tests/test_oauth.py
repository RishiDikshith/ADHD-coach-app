"""
Comprehensive Unit and Integration Tests for OAuth 2.0 / OpenID Connect System
================================================================================
Covers:
- Google OIDC flow
- Complete removal and rejection of Microsoft OAuth
- Session-bound CSRF state & PKCE verification
- ID-token claims validation (iss, aud, exp, nonce, email_verified)
- Account linking security (preventing account takeover)
- Trusted device generation, hashing, token rotation, and resume
- Session cookie restoration via /auth/me and logout
"""

import asyncio
import os
import sys
import time
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

os.environ["DATABASE_URL"] = "sqlite:///./test_adhd_coach_temp.db"
os.environ["GROQ_API_KEY"] = "mock_groq_key"
os.environ["GOOGLE_CLIENT_ID"] = "mock_google_client_id.apps.googleusercontent.com"
os.environ["GOOGLE_CLIENT_SECRET"] = "mock_google_client_secret"

import httpx
import jwt as pyjwt

import api.main_api as main_api_module
from api.main_api import app
from auth.oauth_service import (
    AccountLinkingRequiredError,
    create_oauth_session,
    generate_trusted_device_token,
    get_oauth_config,
    hash_device_token,
    resolve_or_create_oauth_user,
    resume_trusted_device_session,
    verify_google_identity,
    verify_oauth_session_cookie,
)
from database.crud import DatabaseManager
from database.models import User, engine, init_db


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


class TestOAuthAuthentication(unittest.TestCase):
    def setUp(self):
        self.cleanup_db()
        init_db()
        self.db_manager = DatabaseManager()
        main_api_module._db_manager = self.db_manager
        self.client = SyncTestClient(app)

    def tearDown(self):
        self.client.close()
        self.db_manager.close()
        engine.dispose()
        self.cleanup_db()

    def cleanup_db(self):
        for f in ["./test_adhd_coach_temp.db", "./test_adhd_coach_temp.db-journal", "./test_adhd_coach_temp.db-wal", "./test_adhd_coach_temp.db-shm"]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except OSError:
                    pass

    # ==================== 1. Google OIDC Tests ====================

    def test_google_auth_url_generation(self):
        """Verify Google OAuth authorization URL contains required OpenID and PKCE parameters."""
        auth_url, state, _ = create_oauth_session(provider="google", remember_device=True)
        self.assertIn("accounts.google.com", auth_url)
        self.assertIn("client_id=mock_google_client_id.apps.googleusercontent.com", auth_url)
        self.assertIn("response_type=code", auth_url)
        self.assertIn("scope=openid+email+profile", auth_url)
        self.assertIn("code_challenge=", auth_url)
        self.assertIn("code_challenge_method=S256", auth_url)
        self.assertIn(f"state={state}", auth_url)

    def test_google_session_bound_state_validation(self):
        """Verify state is cryptographically bound to the browser session cookie."""
        _, state, cookie_val = create_oauth_session(provider="google", remember_device=True)
        session = verify_oauth_session_cookie(cookie_val, state, expected_provider="google")
        self.assertIsNotNone(session)
        self.assertEqual(session["provider"], "google")
        self.assertTrue(session["remember_device"])
        self.assertIsNotNone(session["nonce"])
        self.assertIsNotNone(session["code_verifier"])

    def test_google_session_bound_state_replay_tamper_rejection(self):
        """Verify tampered or mismatched session cookies are rejected."""
        _, state, cookie_val = create_oauth_session(provider="google", remember_device=False)
        # Mismatched state
        self.assertIsNone(verify_oauth_session_cookie(cookie_val, "wrong_state", "google"))
        # Provider mismatch
        self.assertIsNone(verify_oauth_session_cookie(cookie_val, state, "unsupported_provider"))
        # Tampered cookie
        self.assertIsNone(verify_oauth_session_cookie(cookie_val[:-3] + "xyz", state, "google"))

    def test_google_session_state_expiration(self):
        """Verify expired session cookies are rejected."""
        _, state, cookie_val = create_oauth_session(provider="google", remember_device=False)
        with patch("time.time", return_value=datetime.now(timezone.utc).timestamp() + 500):
            self.assertIsNone(verify_oauth_session_cookie(cookie_val, state, "google"))

    def test_google_identity_invalid_nonce(self):
        """Verify Google ID token with wrong nonce is rejected."""
        loop = asyncio.new_event_loop()
        try:
            token = pyjwt.encode(
                {"aud": "mock_google_client_id.apps.googleusercontent.com", "iss": "https://accounts.google.com", "sub": "123", "email": "a@b.com", "email_verified": True, "nonce": "nonce_a", "exp": time.time() + 1000},
                "secret",
                algorithm="HS256"
            )
            with self.assertRaises(ValueError) as ctx:
                loop.run_until_complete(verify_google_identity({"id_token": token}, expected_nonce="nonce_b"))
            self.assertIn("nonce mismatch", str(ctx.exception).lower())
        finally:
            loop.close()

    def test_google_identity_invalid_issuer(self):
        """Verify Google ID token with wrong issuer is rejected."""
        loop = asyncio.new_event_loop()
        try:
            token = pyjwt.encode(
                {"aud": "mock_google_client_id.apps.googleusercontent.com", "iss": "https://attacker.com", "sub": "123", "email": "a@b.com", "email_verified": True, "exp": time.time() + 1000},
                "secret",
                algorithm="HS256"
            )
            with self.assertRaises(ValueError) as ctx:
                loop.run_until_complete(verify_google_identity({"id_token": token}))
            self.assertIn("issuer", str(ctx.exception).lower())
        finally:
            loop.close()

    def test_google_identity_invalid_audience(self):
        """Verify Google ID token with wrong audience is rejected."""
        loop = asyncio.new_event_loop()
        try:
            token = pyjwt.encode(
                {"aud": "unauthorized_client_id", "iss": "https://accounts.google.com", "sub": "123", "email": "a@b.com", "email_verified": True, "exp": time.time() + 1000},
                "secret",
                algorithm="HS256"
            )
            with self.assertRaises(ValueError) as ctx:
                loop.run_until_complete(verify_google_identity({"id_token": token}))
            self.assertIn("audience", str(ctx.exception).lower())
        finally:
            loop.close()

    def test_google_identity_expired_token(self):
        """Verify expired Google ID token is rejected."""
        loop = asyncio.new_event_loop()
        try:
            token = pyjwt.encode(
                {"aud": "mock_google_client_id.apps.googleusercontent.com", "iss": "https://accounts.google.com", "sub": "123", "email": "a@b.com", "email_verified": True, "exp": time.time() - 100},
                "secret",
                algorithm="HS256"
            )
            with self.assertRaises(ValueError) as ctx:
                loop.run_until_complete(verify_google_identity({"id_token": token}))
            self.assertIn("expired", str(ctx.exception).lower())
        finally:
            loop.close()

    def test_google_identity_unverified_email(self):
        """Verify unverified email from Google is rejected."""
        loop = asyncio.new_event_loop()
        try:
            token = pyjwt.encode(
                {"aud": "mock_google_client_id.apps.googleusercontent.com", "iss": "https://accounts.google.com", "sub": "123", "email": "unverified@gmail.com", "email_verified": False, "exp": time.time() + 1000},
                "secret",
                algorithm="HS256"
            )
            with self.assertRaises(ValueError) as ctx:
                loop.run_until_complete(verify_google_identity({"id_token": token}))
            self.assertIn("not verified", str(ctx.exception).lower())
        finally:
            loop.close()

    def test_google_new_user_provisioning(self):
        """Verify new OAuth user gets nullable password_hash and initial OAuthAccount."""
        user, is_new = resolve_or_create_oauth_user(
            db=self.db_manager,
            provider="google",
            provider_user_id="google_sub_1001",
            email="brand_new@gmail.com",
            name="New ADHD User"
        )
        self.assertTrue(is_new)
        self.assertIsNone(user.password_hash)
        self.assertEqual(user.auth_provider, "google")
        self.assertEqual(user.email, "brand_new@gmail.com")

        acc = self.db_manager.get_oauth_account("google", "google_sub_1001")
        self.assertIsNotNone(acc)
        self.assertEqual(acc.user_id, user.id)

    def test_google_existing_oauth_user_login(self):
        """Verify existing OAuth user is authenticated without duplicate account creation."""
        user1, is_new1 = resolve_or_create_oauth_user(
            db=self.db_manager,
            provider="google",
            provider_user_id="google_sub_repeat",
            email="repeat@gmail.com"
        )
        self.assertTrue(is_new1)

        user2, is_new2 = resolve_or_create_oauth_user(
            db=self.db_manager,
            provider="google",
            provider_user_id="google_sub_repeat",
            email="repeat@gmail.com"
        )
        self.assertFalse(is_new2)
        self.assertEqual(user1.id, user2.id)

    # ==================== 2. Rejection of Removed / Unsupported Providers ====================

    def test_microsoft_login_endpoint_rejected(self):
        """Verify /auth/oauth/microsoft/login is rejected with 400 Bad Request."""
        resp = self.client.get("/auth/oauth/microsoft/login")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("unsupported", resp.json()["detail"].lower())

    def test_microsoft_callback_endpoint_rejected(self):
        """Verify /auth/oauth/microsoft/callback is rejected and redirects with unsupported_provider."""
        resp = self.client.get("/auth/oauth/microsoft/callback?code=mock_code&state=mock_state", follow_redirects=False)
        self.assertEqual(resp.status_code, 303)
        self.assertIn("error=unsupported_provider", resp.headers.get("location", ""))

    def test_create_oauth_session_rejects_microsoft(self):
        """Verify create_oauth_session raises ValueError when provider is microsoft."""
        with self.assertRaises(ValueError) as ctx:
            create_oauth_session(provider="microsoft", remember_device=False)
        self.assertIn("unsupported", str(ctx.exception).lower())

    def test_get_oauth_config_rejects_microsoft(self):
        """Verify get_oauth_config raises ValueError when provider is microsoft."""
        with self.assertRaises(ValueError) as ctx:
            get_oauth_config("microsoft")
        self.assertIn("unsupported", str(ctx.exception).lower())

    def test_legacy_microsoft_account_in_db_does_not_break_system(self):
        """Verify existing/legacy Microsoft database records do not cause runtime errors."""
        user = User(
            username="legacy_ms_user",
            email="legacy_ms@example.com",
            password_hash=None,
            auth_provider="microsoft",
            role="user",
            is_active=True
        )
        self.db_manager.db.add(user)
        self.db_manager.db.commit()

        self.db_manager.create_oauth_account(
            user_id=user.id,
            provider="microsoft",
            provider_user_id="legacy_ms_guid_123",
            email="legacy_ms@example.com"
        )

        from auth.auth_handler import create_access_token
        token = create_access_token({"sub": user.username})

        resp = self.client.get("/auth/oauth/connected-accounts", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(resp.status_code, 200)
        providers = [acc["provider"] for acc in resp.json()]
        self.assertEqual(providers, ["google"])
        self.assertNotIn("microsoft", providers)

    # ==================== 3. Account Linking & Takeover Prevention ====================

    def test_account_linking_unsafe_password_user_prevented(self):
        """Verify an existing password-based account CANNOT be silently merged via OAuth (takeover prevention)."""
        local_user = User(
            username="original_local_user",
            email="victim@example.com",
            password_hash="argon2_or_bcrypt_secret_hash",
            role="user",
            is_active=True
        )
        self.db_manager.db.add(local_user)
        self.db_manager.db.commit()

        # Attempt to log in with Google using that email: must raise AccountLinkingRequiredError
        with self.assertRaises(AccountLinkingRequiredError):
            resolve_or_create_oauth_user(
                db=self.db_manager,
                provider="google",
                provider_user_id="attacker_or_separate_google_id",
                email="victim@example.com"
            )

    def test_account_linking_authenticated_user_succeeds(self):
        """Verify that an authenticated user can safely link OAuth provider from Settings."""
        local_user = User(
            username="safe_user",
            email="safe@example.com",
            password_hash="existing_password",
            role="user",
            is_active=True
        )
        self.db_manager.db.add(local_user)
        self.db_manager.db.commit()

        # Explicit authenticated link passing authenticated_user_id
        linked_user, is_new = resolve_or_create_oauth_user(
            db=self.db_manager,
            provider="google",
            provider_user_id="google_safe_link_id",
            email="safe@example.com",
            authenticated_user_id=local_user.id
        )
        self.assertFalse(is_new)
        self.assertEqual(linked_user.id, local_user.id)

        acc = self.db_manager.get_oauth_account("google", "google_safe_link_id")
        self.assertIsNotNone(acc)
        self.assertEqual(acc.user_id, local_user.id)

    def test_account_linking_verified_existing_oauth_user_succeeds(self):
        """Verify that an existing OAuth user (without password) can safely link another OAuth identity."""
        oauth_user = User(
            username="multi_oauth_user",
            email="shared_oauth@example.com",
            password_hash=None,
            auth_provider="google",
            role="user",
            is_active=True
        )
        self.db_manager.db.add(oauth_user)
        self.db_manager.db.commit()

        # Link secondary Google identity to existing OAuth account
        user, is_new = resolve_or_create_oauth_user(
            db=self.db_manager,
            provider="google",
            provider_user_id="google_sub_linked_2",
            email="shared_oauth@example.com"
        )
        self.assertFalse(is_new)
        self.assertEqual(user.id, oauth_user.id)

    # ==================== 4. Trusted Device & Token Rotation Tests ====================

    def test_trusted_device_creation_and_hash_only_storage(self):
        """Verify raw device token is never stored in SQLite; only SHA-256 hash is persisted."""
        user, _ = resolve_or_create_oauth_user(
            db=self.db_manager,
            provider="google",
            provider_user_id="dev_sub_1",
            email="dev1@example.com"
        )
        raw_token, token_hash = generate_trusted_device_token()
        self.assertEqual(hash_device_token(raw_token), token_hash)

        expires = datetime.now(timezone.utc) + timedelta(days=30)
        self.db_manager.save_hashed_trusted_device(user.id, token_hash, "Work Laptop", expires)

        device = self.db_manager.get_trusted_device_by_hash(token_hash)
        self.assertIsNotNone(device)
        self.assertEqual(device.token_hash, token_hash)
        self.assertNotEqual(device.token_hash, raw_token)

    def test_trusted_device_resume_endpoint_and_token_rotation(self):
        """Verify POST /auth/trusted-devices/resume restores session and rotates device token."""
        user, _ = resolve_or_create_oauth_user(
            db=self.db_manager,
            provider="google",
            provider_user_id="resume_sub",
            email="resume@example.com"
        )
        raw_token, token_hash = generate_trusted_device_token()
        expires = datetime.now(timezone.utc) + timedelta(days=30)
        self.db_manager.save_hashed_trusted_device(user.id, token_hash, "Test Device", expires)

        # Call resume endpoint
        resp = self.client.post("/auth/trusted-devices/resume", headers={"Cookie": f"trusted_device_token={raw_token}"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["username"], user.username)

        # Check that old token no longer exists (rotated)
        self.assertIsNone(self.db_manager.get_trusted_device_by_hash(token_hash))

        # Check that new token was delivered in Set-Cookie
        cookies = resp.headers.get_list("set-cookie")
        new_trusted_cookie = [c for c in cookies if c.startswith("trusted_device_token=")]
        self.assertTrue(len(new_trusted_cookie) > 0)

    def test_trusted_device_expired_token_rejected(self):
        """Verify expired trusted device token is rejected."""
        user, _ = resolve_or_create_oauth_user(
            db=self.db_manager,
            provider="google",
            provider_user_id="exp_sub",
            email="expired@example.com"
        )
        raw_token, token_hash = generate_trusted_device_token()
        expired_date = datetime.now(timezone.utc) - timedelta(days=2)
        self.db_manager.save_hashed_trusted_device(user.id, token_hash, "Old Device", expired_date)

        result = resume_trusted_device_session(self.db_manager, raw_token)
        self.assertIsNone(result)

    def test_trusted_device_revoked_token_rejected(self):
        """Verify revoked trusted device token is rejected."""
        user, _ = resolve_or_create_oauth_user(
            db=self.db_manager,
            provider="google",
            provider_user_id="rev_sub",
            email="revoked@example.com"
        )
        raw_token, token_hash = generate_trusted_device_token()
        expires = datetime.now(timezone.utc) + timedelta(days=30)
        self.db_manager.save_hashed_trusted_device(user.id, token_hash, "Stolen Device", expires)

        self.db_manager.revoke_trusted_device_by_hash(token_hash)
        result = resume_trusted_device_session(self.db_manager, raw_token)
        self.assertIsNone(result)

    def test_trusted_device_revoke_one_and_revoke_all(self):
        """Verify individual and bulk device revocation."""
        user, _ = resolve_or_create_oauth_user(
            db=self.db_manager,
            provider="google",
            provider_user_id="multi_sub",
            email="multi@example.com"
        )
        from auth.auth_handler import create_access_token
        token = create_access_token({"sub": user.username})

        _, h1 = generate_trusted_device_token()
        _, h2 = generate_trusted_device_token()
        exp = datetime.now(timezone.utc) + timedelta(days=30)
        d1 = self.db_manager.save_hashed_trusted_device(user.id, h1, "D1", exp)
        self.db_manager.save_hashed_trusted_device(user.id, h2, "D2", exp)

        # Revoke one
        resp1 = self.client.post(f"/auth/trusted-devices/{d1.device_id}/revoke", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(resp1.status_code, 200)
        self.assertIsNone(self.db_manager.get_trusted_device_by_hash(h1))
        self.assertIsNotNone(self.db_manager.get_trusted_device_by_hash(h2))

        # Revoke all
        resp2 = self.client.post("/auth/trusted-devices/revoke-all", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(resp2.status_code, 200)
        self.assertIsNone(self.db_manager.get_trusted_device_by_hash(h2))

    # ==================== 5. Session & Cookie Authentication ====================

    def test_auth_me_with_valid_cookie(self):
        """Verify GET /auth/me validates access_token delivered via HttpOnly cookie."""
        user, _ = resolve_or_create_oauth_user(
            db=self.db_manager,
            provider="google",
            provider_user_id="me_sub",
            email="me@example.com"
        )
        from auth.auth_handler import create_access_token
        access_token = create_access_token({"sub": user.username})

        resp = self.client.get("/auth/me", headers={"Cookie": f"access_token={access_token}"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["username"], user.username)

    def test_auth_me_without_session_returns_401(self):
        """Verify GET /auth/me without cookies or tokens returns 401."""
        resp = self.client.get("/auth/me")
        self.assertEqual(resp.status_code, 401)

    def test_auth_me_inactive_user_returns_401(self):
        """Verify GET /auth/me returns 401 if user account is deactivated."""
        user, _ = resolve_or_create_oauth_user(
            db=self.db_manager,
            provider="google",
            provider_user_id="inactive_sub",
            email="inactive@example.com"
        )
        user.is_active = False
        self.db_manager.db.commit()

        from auth.auth_handler import create_access_token
        access_token = create_access_token({"sub": user.username})

        resp = self.client.get("/auth/me", headers={"Cookie": f"access_token={access_token}"})
        self.assertEqual(resp.status_code, 401)

    def test_auth_logout_clears_all_cookies(self):
        """Verify POST /auth/logout sends Set-Cookie deletions for access, refresh, trusted device, and oauth state."""
        raw_token, token_hash = generate_trusted_device_token()
        user, _ = resolve_or_create_oauth_user(
            db=self.db_manager,
            provider="google",
            provider_user_id="logout_sub",
            email="logout@example.com"
        )
        exp = datetime.now(timezone.utc) + timedelta(days=30)
        self.db_manager.save_hashed_trusted_device(user.id, token_hash, "Logout Dev", exp)

        resp = self.client.post("/auth/logout", headers={"Cookie": f"trusted_device_token={raw_token}"})
        self.assertEqual(resp.status_code, 200)

        # Device is revoked in DB
        self.assertIsNone(self.db_manager.get_trusted_device_by_hash(token_hash))

        # Check Set-Cookie headers contain deletions
        cookies = resp.headers.get_list("set-cookie")
        self.assertTrue(any(c.startswith("access_token=") for c in cookies))
        self.assertTrue(any(c.startswith("refresh_token=") for c in cookies))
        self.assertTrue(any(c.startswith("trusted_device_token=") for c in cookies))
        self.assertTrue(any(c.startswith("oauth_state=") for c in cookies))

    # ==================== 6. End-to-End Callback Integration ====================

    @patch("auth.oauth_service.exchange_google_code")
    @patch("auth.oauth_service.verify_google_identity")
    def test_google_full_callback_flow_success(self, mock_verify, mock_exchange):
        """Verify complete Google callback verifies session cookie, exchanges code, provisions user, sets cookies, and clears state."""
        _, state, cookie_val = create_oauth_session(provider="google", remember_device=True)

        mock_exchange.return_value = {"access_token": "at_123", "id_token": "id_123"}
        mock_verify.return_value = {
            "provider": "google",
            "provider_user_id": "google_prod_sub",
            "email": "e2e_google@gmail.com",
            "name": "Google Tester"
        }

        resp = self.client.get(
            f"/auth/oauth/google/callback?code=mock_google_code&state={state}",
            headers={"Cookie": f"oauth_state={cookie_val}"},
            follow_redirects=False,
        )
        self.assertEqual(resp.status_code, 303)
        self.assertIn("/register?step=focus", resp.headers.get("location", ""))

        # Cookies check
        cookies = resp.headers.get_list("set-cookie")
        cookie_names = [c.split("=")[0] for c in cookies]
        self.assertIn("access_token", cookie_names)
        self.assertIn("refresh_token", cookie_names)
        self.assertIn("trusted_device_token", cookie_names)

        # State cookie should be deleted to prevent replay
        deleted_state = [c for c in cookies if c.startswith("oauth_state=")]
        self.assertTrue(len(deleted_state) > 0)


if __name__ == "__main__":
    unittest.main()
