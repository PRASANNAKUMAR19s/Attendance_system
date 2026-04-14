"""
tests/test_api.py
=================
Integration tests for the REST API (api.py).
Uses pytest-flask to test endpoints without a real HTTP server.

Run with:
    pytest tests/test_api.py -v
"""

from __future__ import annotations

import csv
import json
import os
import tempfile
from typing import Generator

import pytest

# ─── Patch environment before importing app ────────────────────────────────────
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret")
os.environ.setdefault("TUTOR_USERNAME", "tutor")
os.environ.setdefault("TUTOR_PASSWORD", "paavai123")
os.environ.setdefault("TUTOR_PASSWORD_HASH", "")
os.environ.setdefault("USE_FIREBASE", "false")


@pytest.fixture(scope="session")
def tmp_dir():
    """Temporary directory for CSV files used during tests."""
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture(scope="session", autouse=True)
def patch_paths(tmp_dir):
    """Redirect file-system paths to the temp directory."""
    import config as cfg

    cfg.ATTENDANCE_DIR    = os.path.join(tmp_dir, "attendance")
    cfg.STUDENTS_FILE     = os.path.join(tmp_dir, "students.csv")
    cfg.LATE_REASONS_FILE = os.path.join(tmp_dir, "late_reasons.csv")
    cfg.REPORTS_DIR       = os.path.join(tmp_dir, "reports")
    cfg.USE_FIREBASE      = False

    os.makedirs(cfg.ATTENDANCE_DIR, exist_ok=True)
    os.makedirs(cfg.REPORTS_DIR, exist_ok=True)

    # Write a minimal students.csv
    with open(cfg.STUDENTS_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["RegNo", "Name"])
        writer.writerow(["622123207001", "TEST STUDENT A"])
        writer.writerow(["622123207002", "TEST STUDENT B"])


@pytest.fixture(scope="session")
def flask_app():
    """Create the Flask test application."""
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    yield app


@pytest.fixture()
def client(flask_app):
    """HTTP test client."""
    with flask_app.test_client() as c:
        yield c


@pytest.fixture(scope="session")
def auth_token(flask_app):
    """Obtain a valid JWT token once for the whole session."""
    with flask_app.test_client() as c:
        resp = c.post(
            "/api/auth/login",
            json={"username": "tutor", "password": "paavai123"},
            content_type="application/json",
        )
        assert resp.status_code == 200, resp.data
        data = resp.get_json()
        return data["access_token"]


@pytest.fixture()
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


# ─── Health check ──────────────────────────────────────────────────────────────
class TestHealth:
    def test_health_ok(self, client):
        resp = client.get("/api/health/")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["status"] == "healthy"
        assert "backend" in body


# ─── Auth ──────────────────────────────────────────────────────────────────────
class TestAuth:
    def test_login_success(self, client):
        resp = client.post(
            "/api/auth/login",
            json={"username": "tutor", "password": "paavai123"},
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    def test_login_wrong_password(self, client):
        resp = client.post(
            "/api/auth/login",
            json={"username": "tutor", "password": "wrong"},
        )
        assert resp.status_code == 401

    def test_login_missing_fields(self, client):
        resp = client.post("/api/auth/login", json={})
        assert resp.status_code == 400

    def test_protected_requires_auth(self, client):
        resp = client.get("/api/students/")
        assert resp.status_code == 401


# ─── Students ──────────────────────────────────────────────────────────────────
class TestStudents:
    def test_list_students(self, client, auth_headers):
        resp = client.get("/api/students/", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.get_json()
        assert isinstance(body, list)
        assert len(body) >= 2

    def test_add_student(self, client, auth_headers):
        resp = client.post(
            "/api/students/",
            json={"reg_no": "999999999001", "name": "NEW STUDENT", "year": 1},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["reg_no"] == "999999999001"
        assert body["name"] == "NEW STUDENT"

    def test_add_student_missing_name(self, client, auth_headers):
        resp = client.post(
            "/api/students/",
            json={"reg_no": "999999999999"},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_get_student(self, client, auth_headers):
        resp = client.get("/api/students/622123207001", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["reg_no"] == "622123207001"

    def test_get_student_not_found(self, client, auth_headers):
        resp = client.get("/api/students/000000000000", headers=auth_headers)
        assert resp.status_code == 404

    def test_search_students(self, client, auth_headers):
        resp = client.get("/api/students/search?q=test", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.get_json()
        assert isinstance(body, list)

    def test_delete_student(self, client, auth_headers):
        # Add then delete
        client.post(
            "/api/students/",
            json={"reg_no": "DELETE_ME_001", "name": "DELETE ME"},
            headers=auth_headers,
        )
        resp = client.delete("/api/students/DELETE_ME_001", headers=auth_headers)
        assert resp.status_code == 200

    def test_delete_nonexistent_student(self, client, auth_headers):
        resp = client.delete("/api/students/DOES_NOT_EXIST", headers=auth_headers)
        assert resp.status_code == 404


# ─── Attendance ────────────────────────────────────────────────────────────────
class TestAttendance:
    def test_mark_attendance(self, client, auth_headers):
        resp = client.post(
            "/api/attendance/",
            json={
                "reg_no": "622123207001",
                "name":   "TEST STUDENT A",
                "date":   "2026-01-01",
                "period": "Period 1",
                "status": "ON_TIME",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["reg_no"] == "622123207001"
        assert body["status"] == "ON_TIME"

    def test_mark_attendance_missing_fields(self, client, auth_headers):
        resp = client.post(
            "/api/attendance/",
            json={"reg_no": "622123207001"},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_get_attendance(self, client, auth_headers):
        resp = client.get("/api/attendance/", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.get_json()
        assert isinstance(body, list)

    def test_get_attendance_by_date(self, client, auth_headers):
        resp = client.get("/api/attendance/?date=2026-01-01", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.get_json()
        assert all(r["date"] == "2026-01-01" for r in body)

    def test_get_attendance_by_reg_no(self, client, auth_headers):
        resp = client.get(
            "/api/attendance/?reg_no=622123207001", headers=auth_headers
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert all(r["reg_no"] == "622123207001" for r in body)

    def test_student_summary(self, client, auth_headers):
        resp = client.get(
            "/api/attendance/summary/622123207001", headers=auth_headers
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert "percentage" in body
        assert "present" in body

    def test_today_attendance(self, client, auth_headers):
        resp = client.get("/api/attendance/today", headers=auth_headers)
        assert resp.status_code == 200

    def test_add_late_reason(self, client, auth_headers):
        resp = client.post(
            "/api/attendance/late-reasons",
            json={
                "reg_no": "622123207001",
                "name":   "TEST STUDENT A",
                "date":   "2026-01-01",
                "period": "Period 1",
                "reason": "Medical appointment",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201

    def test_get_late_reasons(self, client, auth_headers):
        resp = client.get("/api/attendance/late-reasons", headers=auth_headers)
        assert resp.status_code == 200


# ─── Reports ───────────────────────────────────────────────────────────────────
class TestReports:
    def test_list_report_dates(self, client, auth_headers):
        resp = client.get("/api/reports/", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.get_json()
        assert "dates" in body

    def test_summary_report(self, client, auth_headers):
        resp = client.get("/api/reports/summary", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.get_json()
        assert "records" in body
        assert "total_students" in body
        assert "threshold" in body


# ─── Analytics ─────────────────────────────────────────────────────────────────
class TestAnalytics:
    def test_overview(self, client, auth_headers):
        resp = client.get("/api/analytics/overview", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.get_json()
        assert "period_stats" in body
        assert "daily_stats" in body
        assert "top_absentees" in body

    def test_periods(self, client, auth_headers):
        resp = client.get("/api/analytics/periods", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.get_json()
        assert "periods" in body
        assert len(body["periods"]) == 7


# ─── Error handling ────────────────────────────────────────────────────────────
class TestErrorHandling:
    def test_404(self, client):
        resp = client.get("/api/nonexistent/endpoint")
        assert resp.status_code == 404

    def test_swagger_docs_accessible(self, client):
        resp = client.get("/api/docs")
        assert resp.status_code in (200, 301, 308)
