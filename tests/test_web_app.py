"""
tests/test_web_app.py
======================
Integration tests for the Flask web application (app.py).
Tests login, admin dashboard, and student registration routes.

Run with:
    pytest tests/test_web_app.py -v
"""

from __future__ import annotations

import csv
import os
import tempfile

import pytest

os.environ.setdefault("SECRET_KEY", "test-web-secret-key")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret")
os.environ.setdefault("TUTOR_USERNAME", "tutor")
os.environ.setdefault("TUTOR_PASSWORD_HASH", "")
os.environ.setdefault("USE_FIREBASE", "false")

# Admin credentials used in login tests — matches the default TUTOR_USERNAME above.
_ADMIN_USER = os.environ.get("TUTOR_USERNAME", "tutor")
_ADMIN_PASS = os.environ.get("TUTOR_PASSWORD", "paavai123")


@pytest.fixture(scope="session")
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture(scope="session", autouse=True)
def patch_paths(tmp_dir):
    import config as cfg

    cfg.ATTENDANCE_DIR    = os.path.join(tmp_dir, "attendance")
    cfg.STUDENTS_FILE     = os.path.join(tmp_dir, "students.csv")
    cfg.LATE_REASONS_FILE = os.path.join(tmp_dir, "late_reasons.csv")
    cfg.REPORTS_DIR       = os.path.join(tmp_dir, "reports")
    cfg.UPLOAD_FOLDER     = os.path.join(tmp_dir, "dataset")
    cfg.DATABASE_PATH     = os.path.join(tmp_dir, "test_web.db")
    cfg.USE_FIREBASE      = False

    os.makedirs(cfg.ATTENDANCE_DIR, exist_ok=True)
    os.makedirs(cfg.REPORTS_DIR, exist_ok=True)
    os.makedirs(cfg.UPLOAD_FOLDER, exist_ok=True)

    # Seed students.csv
    with open(cfg.STUDENTS_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["RegNo", "Name"])
        writer.writerow(["622123207001", "TEST STUDENT A"])


@pytest.fixture(scope="session")
def flask_app():
    from app import create_app as _create
    web = _create()
    web.config["TESTING"]          = True
    web.config["WTF_CSRF_ENABLED"] = False
    yield web


@pytest.fixture()
def client(flask_app):
    with flask_app.test_client() as c:
        yield c


@pytest.fixture()
def logged_in_client(flask_app):
    """Client with an active admin session."""
    with flask_app.test_client() as c:
        with flask_app.app_context():
            resp = c.post(
                "/auth/login",
                data={"username": _ADMIN_USER, "password": _ADMIN_PASS},
                follow_redirects=True,
            )
            assert resp.status_code == 200
            yield c


# ── Auth tests ────────────────────────────────────────────────────────────────

class TestWebAuth:
    def test_login_page_loads(self, client):
        resp = client.get("/auth/login")
        assert resp.status_code == 200
        assert b"Sign In" in resp.data or b"login" in resp.data.lower()

    def test_root_redirects_to_dashboard_or_login(self, client):
        resp = client.get("/", follow_redirects=False)
        assert resp.status_code in (301, 302, 308)

    def test_login_success(self, flask_app, client):
        resp = client.post(
            "/auth/login",
            data={"username": _ADMIN_USER, "password": _ADMIN_PASS},
            follow_redirects=True,
        )
        assert resp.status_code == 200

    def test_login_wrong_password(self, client):
        resp = client.post(
            "/auth/login",
            data={"username": _ADMIN_USER, "password": "wrongpass"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"Invalid" in resp.data or b"invalid" in resp.data.lower()

    def test_login_missing_fields(self, client):
        resp = client.post(
            "/auth/login",
            data={},
            follow_redirects=True,
        )
        assert resp.status_code == 200

    def test_dashboard_requires_login(self, client):
        resp = client.get("/faculty/dashboard", follow_redirects=False)
        assert resp.status_code in (301, 302, 308)

    def test_logout(self, flask_app):
        with flask_app.test_client() as c:
            c.post(
                "/auth/login",
                data={"username": _ADMIN_USER, "password": _ADMIN_PASS},
                follow_redirects=True,
            )
            resp = c.get("/auth/logout", follow_redirects=True)
            assert resp.status_code == 200


# ── Admin dashboard tests ─────────────────────────────────────────────────────

class TestAdminDashboard:
    def test_dashboard_loads(self, logged_in_client):
        resp = logged_in_client.get("/faculty/dashboard")
        assert resp.status_code == 200
        assert b"Dashboard" in resp.data or b"dashboard" in resp.data.lower()

    def test_dashboard_shows_students(self, logged_in_client):
        resp = logged_in_client.get("/faculty/dashboard")
        assert resp.status_code == 200
        assert b"TEST STUDENT A" in resp.data or b"622123207001" in resp.data

    def test_register_page_loads(self, logged_in_client):
        resp = logged_in_client.get("/faculty/register-student")
        assert resp.status_code == 200
        assert b"Register" in resp.data

    def test_register_student(self, logged_in_client):
        resp = logged_in_client.post(
            "/faculty/register-student",
            data={
                "reg_no":     "622123207099",
                "name":       "NEW TEST STUDENT",
                "department": "AI&DS",
                "year":       "2",
                "email":      "",
                "phone":      "",
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"registered" in resp.data.lower() or b"success" in resp.data.lower()

    def test_register_missing_fields(self, logged_in_client):
        resp = logged_in_client.post(
            "/faculty/register-student",
            data={"reg_no": "", "name": ""},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"required" in resp.data.lower()
