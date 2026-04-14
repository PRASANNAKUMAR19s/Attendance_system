"""
REST API — Attendance System
=============================
Flask REST API with:
  - JWT authentication
  - Full CRUD for students
  - Attendance marking and retrieval
  - Analytics and reporting
  - Swagger/OpenAPI documentation (available at /api/docs)
  - Rate limiting
  - Security headers

HOW TO RUN:
    python api.py

    OR with gunicorn (production):
    gunicorn -w 4 -b 0.0.0.0:5001 api:app

ENVIRONMENT VARIABLES (see .env.example):
    SECRET_KEY, JWT_SECRET_KEY, TUTOR_USERNAME, TUTOR_PASSWORD_HASH, ...

API DOCS:
    http://localhost:5001/api/docs
"""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Dict, List, Tuple

import bcrypt
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
)
from flask_restx import Api, Namespace, Resource, fields

from extensions import limiter

from config import (
    ATTENDANCE_DIR,
    DEFAULTER_THRESHOLD,
    JWT_SECRET_KEY,
    PERIODS,
    SECRET_KEY,
    STUDENTS_FILE,
    TUTOR_PASSWORD_HASH,
    TUTOR_USERNAME,
)
from firebase_service import FirebaseService

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Flask app setup
# ---------------------------------------------------------------------------
api_bp = Blueprint("api_bp", __name__)



# ---------------------------------------------------------------------------
# Firebase service (singleton)
# ---------------------------------------------------------------------------
svc = FirebaseService()

# ---------------------------------------------------------------------------
# Swagger / OpenAPI  (flask-restx)
# ---------------------------------------------------------------------------
authorizations = {
    "BearerAuth": {
        "type": "apiKey",
        "in": "header",
        "name": "Authorization",
        "description": "Enter: **Bearer &lt;token&gt;**",
    }
}

api = Api(
    api_bp,
    version="1.0",
    title="Attendance System API",
    description=(
        "Production-ready REST API for the AI-powered Attendance System. "
        "Supports JWT authentication, student CRUD, attendance tracking, "
        "analytics and reporting."
    ),
    doc="/docs",
    authorizations=authorizations,
    security="BearerAuth",
)

# ---------------------------------------------------------------------------
# Namespaces
# ---------------------------------------------------------------------------
ns_auth       = Namespace("auth",       description="Authentication endpoints")
ns_students   = Namespace("students",   description="Student management")
ns_attendance = Namespace("attendance", description="Attendance operations")
ns_reports    = Namespace("reports",    description="Report generation")
ns_analytics  = Namespace("analytics",  description="Advanced analytics")
ns_health     = Namespace("health",     description="Health check")

api.add_namespace(ns_auth,       path="/auth")
api.add_namespace(ns_students,   path="/students")
api.add_namespace(ns_attendance, path="/attendance")
api.add_namespace(ns_reports,    path="/reports")
api.add_namespace(ns_analytics,  path="/analytics")
api.add_namespace(ns_health,     path="/health")

# ---------------------------------------------------------------------------
# Swagger models
# ---------------------------------------------------------------------------
login_model = ns_auth.model(
    "LoginRequest",
    {
        "username": fields.String(required=True, example="tutor"),
        "password": fields.String(required=True, example="paavai123"),
    },
)
token_model = ns_auth.model(
    "TokenResponse",
    {
        "access_token": fields.String(),
        "token_type": fields.String(default="bearer"),
        "username": fields.String(),
    },
)

student_model = ns_students.model(
    "Student",
    {
        "reg_no":     fields.String(required=True, example="622123207042"),
        "name":       fields.String(required=True, example="PRASANNAKUMAR S"),
        "department": fields.String(example="AI&DS"),
        "year":       fields.Integer(example=3),
        "email":      fields.String(example="student@paavai.edu.in"),
        "phone":      fields.String(example="+91-9876543210"),
    },
)

attendance_model = ns_attendance.model(
    "AttendanceRecord",
    {
        "reg_no":      fields.String(required=True),
        "name":        fields.String(),
        "date":        fields.String(example="2026-03-29"),
        "period":      fields.String(example="Period 1"),
        "status":      fields.String(example="ON_TIME"),
        "marked_time": fields.String(example="09:18:00"),
    },
)

mark_attendance_model = ns_attendance.model(
    "MarkAttendance",
    {
        "reg_no":  fields.String(required=True),
        "name":    fields.String(required=True),
        "date":    fields.String(example="2026-03-29"),
        "period":  fields.String(required=True, example="Period 1"),
        "status":  fields.String(required=True, example="ON_TIME"),
    },
)

late_reason_model = ns_attendance.model(
    "LateReason",
    {
        "reg_no":     fields.String(required=True),
        "name":       fields.String(required=True),
        "date":       fields.String(example="2026-03-29"),
        "period":     fields.String(required=True),
        "reason":     fields.String(required=True),
        "updated_by": fields.String(example="Tutor"),
    },
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _verify_password(plain: str, stored_hash: str) -> bool:
    """Verify a bcrypt-hashed password.  Falls back to plain comparison."""
    if stored_hash:
        try:
            return bcrypt.checkpw(
                plain.encode("utf-8"), stored_hash.encode("utf-8")
            )
        except Exception:
            return False
    # No hash stored → compare plain text (development fallback)
    fallback = os.environ.get("TUTOR_PASSWORD", "paavai123")
    return plain == fallback


def _ok(data: Any, status: int = 200):
    return jsonify({"success": True, "data": data}), status


def _err(msg: str, status: int = 400):
    return jsonify({"success": False, "error": msg}), status


def _validate_str(value: Any, name: str, max_len: int = 256) -> str:
    """Raise ValueError if value is not a non-empty string within max_len."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"'{name}' must be a non-empty string.")
    if len(value) > max_len:
        raise ValueError(f"'{name}' exceeds maximum length of {max_len}.")
    return value.strip()


_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _validate_date(value: Any, name: str = "date") -> str:
    """Validate YYYY-MM-DD date string to prevent path traversal."""
    s = _validate_str(value, name, 10)
    if not _DATE_RE.match(s):
        raise ValueError(f"'{name}' must be YYYY-MM-DD format.")
    return s


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@ns_health.route("/")
class HealthCheck(Resource):
    @ns_health.doc("health_check")
    def get(self):
        """System health check — no authentication required."""
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "backend": "firebase" if svc.use_firebase else "csv",
        }


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
@ns_auth.route("/login")
class AuthLogin(Resource):
    @ns_auth.expect(login_model)
    @ns_auth.marshal_with(token_model, code=200)
    @limiter.limit("10 per minute")
    def post(self):
        """Authenticate and receive a JWT access token."""
        data = request.get_json(silent=True) or {}
        username = data.get("username", "")
        password = data.get("password", "")

        if not username or not password:
            api.abort(400, "username and password are required")

        if username != TUTOR_USERNAME or not _verify_password(
            password, TUTOR_PASSWORD_HASH
        ):
            api.abort(401, "Invalid credentials")

        token = create_access_token(identity=username)
        return {"access_token": token, "token_type": "bearer", "username": username}


# ---------------------------------------------------------------------------
# Students
# ---------------------------------------------------------------------------
@ns_students.route("/")
class StudentList(Resource):
    @jwt_required()
    @ns_students.marshal_list_with(student_model)
    def get(self):
        """Return all students (requires JWT)."""
        return svc.get_students()

    @jwt_required()
    @ns_students.expect(student_model)
    @ns_students.marshal_with(student_model, code=201)
    def post(self):
        """Add a new student (requires JWT)."""
        data = request.get_json(silent=True) or {}
        try:
            reg_no = _validate_str(data.get("reg_no", ""), "reg_no", 20)
            name   = _validate_str(data.get("name", ""),   "name",   100)
        except ValueError as exc:
            api.abort(400, str(exc))

        dept  = str(data.get("department", ""))[:100]
        year  = int(data.get("year", 0))
        email = str(data.get("email", ""))[:254]
        phone = str(data.get("phone", ""))[:20]

        record = svc.add_student(reg_no, name, dept, year, email, phone)
        return record, 201


@ns_students.route("/<string:reg_no>")
@ns_students.param("reg_no", "Student registration number")
class Student(Resource):
    @jwt_required()
    @ns_students.marshal_with(student_model)
    def get(self, reg_no: str):
        """Get a single student by registration number (requires JWT)."""
        student = svc.get_student(reg_no)
        if student is None:
            api.abort(404, f"Student {reg_no} not found")
        return student

    @jwt_required()
    @ns_students.expect(student_model)
    @ns_students.marshal_with(student_model)
    def put(self, reg_no: str):
        """Update student details (requires JWT)."""
        data = request.get_json(silent=True) or {}
        safe: Dict[str, Any] = {}
        if "name" in data:
            safe["name"] = _validate_str(data["name"], "name", 100)
        if "department" in data:
            safe["department"] = str(data["department"])[:100]
        if "year" in data:
            safe["year"] = int(data["year"])
        if "email" in data:
            safe["email"] = str(data["email"])[:254]
        if "phone" in data:
            safe["phone"] = str(data["phone"])[:20]

        result = svc.update_student(reg_no, safe)
        if not result:
            api.abort(404, f"Student {reg_no} not found")
        return result

    @jwt_required()
    def delete(self, reg_no: str):
        """Delete a student (requires JWT)."""
        if not svc.delete_student(reg_no):
            api.abort(404, f"Student {reg_no} not found")
        return {"success": True, "message": f"Student {reg_no} deleted"}


# ---------------------------------------------------------------------------
# Attendance
# ---------------------------------------------------------------------------
@ns_attendance.route("/")
class AttendanceList(Resource):
    @jwt_required()
    @ns_attendance.doc(params={"date": "Filter by date (YYYY-MM-DD)", "reg_no": "Filter by student reg no"})
    @ns_attendance.marshal_list_with(attendance_model)
    def get(self):
        """Retrieve attendance records (requires JWT)."""
        raw_date = request.args.get("date")
        reg_no   = request.args.get("reg_no")
        try:
            date = _validate_date(raw_date) if raw_date else None
        except ValueError as exc:
            api.abort(400, str(exc))
        return svc.get_attendance(date=date, reg_no=reg_no)

    @jwt_required()
    @ns_attendance.expect(mark_attendance_model)
    @ns_attendance.marshal_with(attendance_model, code=201)
    def post(self):
        """Mark attendance for a student (requires JWT)."""
        data = request.get_json(silent=True) or {}
        try:
            reg_no = _validate_str(data.get("reg_no", ""), "reg_no", 20)
            name   = _validate_str(data.get("name", ""),   "name",   100)
            period = _validate_str(data.get("period", ""), "period",  50)
            status = _validate_str(data.get("status", ""), "status",  20)
            raw_date = data.get("date")
            date = _validate_date(raw_date) if raw_date else datetime.now().strftime("%Y-%m-%d")
        except ValueError as exc:
            api.abort(400, str(exc))

        record = svc.mark_attendance(reg_no, name, date, period, status)
        return record, 201


@ns_attendance.route("/summary/<string:reg_no>")
@ns_attendance.param("reg_no", "Student registration number")
class AttendanceSummary(Resource):
    @jwt_required()
    def get(self, reg_no: str):
        """Return attendance summary for a student (requires JWT)."""
        return svc.get_student_summary(reg_no)


@ns_attendance.route("/late-reasons")
class LateReasonList(Resource):
    @jwt_required()
    @ns_attendance.doc(params={"date": "Filter by date", "reg_no": "Filter by student"})
    def get(self):
        """Get late-reason records (requires JWT)."""
        raw_date = request.args.get("date")
        reg_no   = request.args.get("reg_no")
        try:
            date = _validate_date(raw_date) if raw_date else None
        except ValueError as exc:
            api.abort(400, str(exc))
        return svc.get_late_reasons(date=date, reg_no=reg_no)

    @jwt_required()
    @ns_attendance.expect(late_reason_model)
    def post(self):
        """Add a late-reason entry (requires JWT)."""
        data = request.get_json(silent=True) or {}
        try:
            reg_no = _validate_str(data.get("reg_no", ""), "reg_no", 20)
            name   = _validate_str(data.get("name", ""),   "name",   100)
            period = _validate_str(data.get("period", ""), "period",  50)
            reason = _validate_str(data.get("reason", ""), "reason",  500)
            raw_date = data.get("date")
            date = _validate_date(raw_date) if raw_date else datetime.now().strftime("%Y-%m-%d")
        except ValueError as exc:
            api.abort(400, str(exc))

        updated_by = str(data.get("updated_by", "Tutor"))[:50]
        record = svc.add_late_reason(reg_no, name, date, period, reason, updated_by)
        return record, 201


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------
@ns_reports.route("/")
class ReportList(Resource):
    @jwt_required()
    def get(self):
        """List available report dates (requires JWT)."""
        import glob as globmod
        import config as _cfg
        files = sorted(
            globmod.glob(os.path.join(_cfg.ATTENDANCE_DIR, "attendance_*.csv"))
        )
        dates = [
            os.path.basename(f).replace("attendance_", "").replace(".csv", "")
            for f in files
        ]
        return {"dates": dates, "count": len(dates)}


@ns_reports.route("/summary")
class ReportSummary(Resource):
    @jwt_required()
    @ns_reports.doc(params={"date": "Date for the report (YYYY-MM-DD); omit for all dates"})
    def get(self):
        """
        Generate an attendance summary report (requires JWT).
        Returns per-student percentages and defaulter status.
        """
        raw_date = request.args.get("date")
        try:
            date = _validate_date(raw_date) if raw_date else None
        except ValueError as exc:
            api.abort(400, str(exc))
        records = svc.get_attendance(date=date)
        students = {s["reg_no"]: s["name"] for s in svc.get_students()}

        # Build summary
        totals: Dict[str, int] = {}
        present: Dict[str, int] = {}

        for r in records:
            rn = r["reg_no"]
            totals[rn] = totals.get(rn, 0) + 1
            if r.get("status", "").upper() in ("ON_TIME", "LATE", "PRESENT"):
                present[rn] = present.get(rn, 0) + 1

        summary = []
        for rn, total in totals.items():
            pres = present.get(rn, 0)
            pct  = round(pres / total * 100, 2) if total else 0.0
            summary.append(
                {
                    "reg_no":      rn,
                    "name":        students.get(rn, "Unknown"),
                    "present":     pres,
                    "absent":      total - pres,
                    "total":       total,
                    "percentage":  pct,
                    "is_defaulter": pct < DEFAULTER_THRESHOLD,
                }
            )

        summary.sort(key=lambda x: x["reg_no"])
        defaulter_count = sum(1 for s in summary if s["is_defaulter"])

        return {
            "date_filter": date or "all",
            "total_students": len(summary),
            "defaulters": defaulter_count,
            "threshold": DEFAULTER_THRESHOLD,
            "records": summary,
        }


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------
@ns_analytics.route("/overview")
class AnalyticsOverview(Resource):
    @jwt_required()
    def get(self):
        """
        Advanced analytics overview (requires JWT).
        Returns attendance trends, period-wise stats, and top absentees.
        """
        records = svc.get_attendance()
        students = svc.get_students()

        if not records:
            return {
                "total_students": len(students),
                "total_records": 0,
                "period_stats": [],
                "daily_stats": [],
                "top_absentees": [],
            }

        # Period-wise stats
        period_counts: Dict[str, Dict[str, int]] = {}
        daily_counts: Dict[str, Dict[str, int]] = {}
        student_absent: Dict[str, int] = {}

        for r in records:
            period = r.get("period", "Unknown")
            date   = r.get("date",   "Unknown")
            rn     = r.get("reg_no", "")
            status = r.get("status", "").upper()
            is_present = status in ("ON_TIME", "LATE", "PRESENT")

            # Period stats
            if period not in period_counts:
                period_counts[period] = {"present": 0, "absent": 0}
            if is_present:
                period_counts[period]["present"] += 1
            else:
                period_counts[period]["absent"] += 1

            # Daily stats
            if date not in daily_counts:
                daily_counts[date] = {"present": 0, "absent": 0}
            if is_present:
                daily_counts[date]["present"] += 1
            else:
                daily_counts[date]["absent"] += 1
                student_absent[rn] = student_absent.get(rn, 0) + 1

        student_map = {s["reg_no"]: s["name"] for s in students}

        period_stats = [
            {"period": p, **counts} for p, counts in sorted(period_counts.items())
        ]
        daily_stats = [
            {"date": d, **counts} for d, counts in sorted(daily_counts.items())
        ]
        top_absentees = sorted(
            [
                {"reg_no": rn, "name": student_map.get(rn, "Unknown"), "absent_count": cnt}
                for rn, cnt in student_absent.items()
            ],
            key=lambda x: -x["absent_count"],
        )[:10]

        return {
            "total_students":  len(students),
            "total_records":   len(records),
            "period_stats":    period_stats,
            "daily_stats":     daily_stats,
            "top_absentees":   top_absentees,
        }


@ns_analytics.route("/periods")
class AnalyticsPeriods(Resource):
    @jwt_required()
    def get(self):
        """Return configured class periods (requires JWT)."""
        return {
            "periods": [
                {
                    "name":  p[0],
                    "start": p[1],
                    "late_after": p[2],
                    "end":   p[3],
                }
                for p in PERIODS
            ]
        }


# ---------------------------------------------------------------------------
# Mobile-friendly convenience endpoints (no extra auth overhead)
# ---------------------------------------------------------------------------
@ns_attendance.route("/today")
class TodayAttendance(Resource):
    @jwt_required()
    def get(self):
        """Return today's attendance (mobile shortcut, requires JWT)."""
        today = datetime.now().strftime("%Y-%m-%d")
        return svc.get_attendance(date=today)


@ns_students.route("/search")
class StudentSearch(Resource):
    @jwt_required()
    @ns_students.doc(params={"q": "Search term (name or reg_no)"})
    def get(self):
        """Search students by name or registration number (requires JWT)."""
        query = (request.args.get("q") or "").lower().strip()
        if not query:
            return []
        return [
            s for s in svc.get_students()
            if query in s.get("name", "").lower()
            or query in s.get("reg_no", "").lower()
        ]


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------
@api_bp.app_errorhandler(404)
def not_found(e):
    return jsonify({"success": False, "error": "Endpoint not found"}), 404

@api_bp.app_errorhandler(405)
def method_not_allowed(e):
    return jsonify({"success": False, "error": "Method not allowed"}), 405

@api_bp.app_errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"success": False, "error": "Rate limit exceeded", "retry_after": str(e.description)}), 429

@api_bp.app_errorhandler(500)
def internal_error(e):
    logger.error("Internal error: %s", e)
    return jsonify({"success": False, "error": "Internal server error"}), 500


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
# Entry point moved to app.py
