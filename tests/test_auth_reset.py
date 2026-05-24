"""
tests/test_auth_reset.py

Integration tests for forgot/reset password flows.
"""
from __future__ import annotations

import os
import pytest

os.environ.setdefault("SECRET_KEY", "test-web-secret-key")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret")
os.environ.setdefault("TUTOR_USERNAME", "tutor")
os.environ.setdefault("TUTOR_PASSWORD_HASH", "")
os.environ.setdefault("USE_FIREBASE", "false")

# rely on session fixtures in tests/test_web_app.py for path patching


@pytest.fixture(scope="session")
def app():
    from app import create_app as _create

    web = _create()
    web.config["TESTING"] = True
    web.config["WTF_CSRF_ENABLED"] = False
    return web
def test_forgot_and_reset_flow(client):
    # Create a student user within the application context
    from models.user import User

    username = "TESTSTU001"
    email = "teststudent@example.com"
    app = client.application
    with app.app_context():
        # Ensure user exists
        user = User.create(
            username=username,
            plain_password="initialpass",
            role="student",
            full_name="Test Student",
            email=email,
        )

        assert user is not None

        # Create a password reset token
        user_obj, token = User.create_password_reset_token(username)
        assert user_obj is not None and token is not None

    # POST reset-password with mismatch -> should show 'Passwords do not match.' when using client
    resp = client.post(
        "/auth/reset-password",
        data={"token": token, "password": "newpass1", "password_confirm": "newpass2"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Passwords do not match" in resp.data or b"Passwords do not match." in resp.data

    # Now post valid matching passwords
    resp2 = client.post(
        "/auth/reset-password",
        data={"token": token, "password": "newpass", "password_confirm": "newpass"},
        follow_redirects=True,
    )
    assert resp2.status_code == 200
    assert b"Password updated" in resp2.data or b"Password updated." in resp2.data

    # Verify login with new password
    resp3 = client.post(
        "/auth/login",
        data={"username": username, "password": "newpass"},
        follow_redirects=True,
    )
    assert resp3.status_code == 200
