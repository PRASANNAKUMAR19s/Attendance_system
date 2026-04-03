"""
tests/test_config.py
====================
Unit tests for config.py and firebase_service.py (CSV backend).

Run with:
    pytest tests/test_config.py -v
"""

from __future__ import annotations

import csv
import os
import tempfile

import pytest

os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt")
os.environ.setdefault("USE_FIREBASE", "false")


# ─── Config tests ──────────────────────────────────────────────────────────────
class TestConfig:
    def test_periods_count(self):
        import config
        assert len(config.PERIODS) == 7

    def test_periods_format(self):
        import config
        for name, start, late, end in config.PERIODS:
            assert isinstance(name, str)
            # Validate HH:MM format
            for t in (start, late, end):
                h, m = t.split(":")
                assert 0 <= int(h) <= 23
                assert 0 <= int(m) <= 59

    def test_confidence_threshold(self):
        import config
        assert 0 < config.CONFIDENCE_THRESHOLD <= 100

    def test_defaulter_threshold(self):
        import config
        assert 0 < config.DEFAULTER_THRESHOLD <= 100

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("CONFIDENCE_THRESHOLD", "80")
        import importlib
        import config
        importlib.reload(config)
        assert config.CONFIDENCE_THRESHOLD == 80


# ─── FirebaseService (CSV backend) ────────────────────────────────────────────
class TestFirebaseServiceCSV:
    """All tests run against the CSV backend (USE_FIREBASE=false)."""

    @pytest.fixture()
    def svc(self, tmp_path):
        import config
        config.STUDENTS_FILE     = str(tmp_path / "students.csv")
        config.ATTENDANCE_DIR    = str(tmp_path / "attendance")
        config.LATE_REASONS_FILE = str(tmp_path / "late_reasons.csv")
        config.USE_FIREBASE      = False
        os.makedirs(config.ATTENDANCE_DIR, exist_ok=True)

        # Seed students.csv
        with open(config.STUDENTS_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["RegNo", "Name"])
            writer.writerow(["111", "ALICE"])
            writer.writerow(["222", "BOB"])

        from firebase_service import FirebaseService
        return FirebaseService()

    # Students
    def test_get_students(self, svc):
        students = svc.get_students()
        assert len(students) == 2
        names = {s["name"] for s in students}
        assert "ALICE" in names

    def test_add_student(self, svc):
        svc.add_student("333", "CHARLIE", "CS", 2)
        students = svc.get_students()
        assert any(s["reg_no"] == "333" for s in students)

    def test_get_student(self, svc):
        student = svc.get_student("111")
        assert student is not None
        assert student["name"] == "ALICE"

    def test_get_student_not_found(self, svc):
        assert svc.get_student("999") is None

    def test_delete_student(self, svc):
        result = svc.delete_student("222")
        assert result is True
        assert svc.get_student("222") is None

    def test_delete_nonexistent_student(self, svc):
        result = svc.delete_student("999")
        assert result is False

    # Attendance
    def test_mark_attendance(self, svc):
        record = svc.mark_attendance("111", "ALICE", "2026-01-01", "Period 1", "ON_TIME")
        assert record["reg_no"] == "111"
        assert record["status"] == "ON_TIME"

    def test_get_attendance_all(self, svc):
        svc.mark_attendance("111", "ALICE", "2026-01-02", "Period 1", "ON_TIME")
        records = svc.get_attendance()
        assert len(records) >= 1

    def test_get_attendance_by_date(self, svc):
        svc.mark_attendance("111", "ALICE", "2026-02-01", "Period 1", "LATE")
        records = svc.get_attendance(date="2026-02-01")
        assert all(r["date"] == "2026-02-01" for r in records)

    def test_get_attendance_by_reg_no(self, svc):
        svc.mark_attendance("222", "BOB", "2026-03-01", "Period 2", "ABSENT")
        records = svc.get_attendance(reg_no="222")
        assert all(r["reg_no"] == "222" for r in records)

    def test_student_summary(self, svc):
        svc.mark_attendance("111", "ALICE", "2026-04-01", "Period 1", "ON_TIME")
        svc.mark_attendance("111", "ALICE", "2026-04-02", "Period 1", "ABSENT")
        summary = svc.get_student_summary("111")
        assert "percentage" in summary
        assert summary["total_records"] >= 2

    # Late reasons
    def test_add_and_get_late_reason(self, svc):
        svc.add_late_reason("111", "ALICE", "2026-01-01", "Period 1", "Doctor visit")
        reasons = svc.get_late_reasons()
        assert any(r["reason"] == "Doctor visit" for r in reasons)

    def test_get_late_reasons_by_date(self, svc):
        svc.add_late_reason("111", "ALICE", "2026-05-01", "Period 1", "Traffic")
        reasons = svc.get_late_reasons(date="2026-05-01")
        assert all(r["date"] == "2026-05-01" for r in reasons)

    def test_get_late_reasons_by_reg_no(self, svc):
        svc.add_late_reason("222", "BOB", "2026-06-01", "Period 2", "Bus delay")
        reasons = svc.get_late_reasons(reg_no="222")
        assert all(r["reg_no"] == "222" for r in reasons)
