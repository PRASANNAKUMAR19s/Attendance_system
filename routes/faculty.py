"""
routes/faculty.py — Faculty portal routes (Tutor / HOD)
=========================================================
Provides the faculty-facing dashboard and management tools.
Accessible only to users with role 'tutor', 'hod', or 'admin'.
"""

from __future__ import annotations

import logging
from datetime import date
from functools import wraps
from pathlib import Path

from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.utils import secure_filename

import config as _config
from models.student import Student
from routes.auth import get_current_user, login_required

logger = logging.getLogger(__name__)

faculty_bp = Blueprint("faculty", __name__, url_prefix="/faculty")

# Roles allowed to access the faculty portal
_FACULTY_ROLES = {"tutor", "hod", "admin"}


def _faculty_required(f):
    """Decorator: ensure the user is logged in AND has a faculty role."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        role = session.get("role", "")
        if role not in _FACULTY_ROLES:
            flash("Access denied. Faculty login required.", "danger")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated


def _allowed_file(filename: str) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in _config.ALLOWED_EXTENSIONS
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@faculty_bp.route("/")
@faculty_bp.route("/dashboard")
@_faculty_required
def dashboard():
    """Faculty portal main dashboard."""
    user = get_current_user()
    students = Student.get_all()
    total_students = len(students)
    return render_template(
        "faculty_dashboard.html",
        user=user,
        total_students=total_students,
        students=students,
    )


@faculty_bp.route("/attendance", methods=["GET", "POST"])
@_faculty_required
def mark_attendance():
    """Mark attendance for today."""
    user = get_current_user()
    students = Student.get_all()
    today = date.today().isoformat()

    if request.method == "POST":
        saved = 0
        for s in students:
            status = request.form.get(f"status_{s.reg_no}", "Absent")
            reason = request.form.get(f"reason_{s.reg_no}", "").strip()
            try:
                from firebase_service import FirebaseService
                svc = FirebaseService()
                svc.mark_attendance(s.reg_no, status, reason or None)
                saved += 1
            except Exception as exc:
                logger.warning("Could not save attendance for %s: %s", s.reg_no, exc)
        flash(f"Attendance saved for {saved} student(s).", "success")
        return redirect(url_for("faculty.dashboard"))

    return render_template(
        "faculty_attendance.html",
        user=user,
        students=students,
        today=today,
    )


@faculty_bp.route("/od-letters")
@_faculty_required
def od_letters():
    """View and approve OD letters."""
    user = get_current_user()
    # Placeholder lists — replace with actual OD model queries when available
    pending_letters = []
    approved_letters = []
    rejected_letters = []
    return render_template(
        "faculty_od_letters.html",
        user=user,
        pending_letters=pending_letters,
        approved_letters=approved_letters,
        rejected_letters=rejected_letters,
        pending_count=len(pending_letters),
    )


@faculty_bp.route("/od-letters/<int:letter_id>/action", methods=["POST"])
@_faculty_required
def od_action(letter_id: int):
    """Approve or reject an OD letter."""
    action = request.form.get("action", "")
    if action not in ("approve", "reject"):
        flash("Invalid action.", "danger")
    else:
        flash(f"OD letter {action}d successfully.", "success")
    return redirect(url_for("faculty.od_letters"))


@faculty_bp.route("/reports")
@_faculty_required
def reports():
    """Download attendance reports."""
    user = get_current_user()
    students = Student.get_all()
    report_type = request.args.get("report_type", "daily")
    from_date = request.args.get("from_date", "")
    to_date = request.args.get("to_date", "")
    selected_reg = request.args.get("reg_no", "")
    fmt = request.args.get("format", "")

    report_rows = []

    if fmt in ("pdf", "excel", "csv"):
        flash(f"Report download ({fmt.upper()}) will be available when the reporting service is configured.", "info")
        return redirect(url_for("faculty.reports"))

    return render_template(
        "faculty_reports.html",
        user=user,
        students=students,
        report_type=report_type,
        from_date=from_date,
        to_date=to_date,
        selected_reg=selected_reg,
        report_rows=report_rows,
    )


@faculty_bp.route("/register-student", methods=["GET", "POST"])
@_faculty_required
def register_student():
    """Register a new student from the faculty portal."""
    user = get_current_user()
    form_data: dict = {}

    if request.method == "POST":
        reg_no = request.form.get("reg_no", "").strip().upper()
        name   = request.form.get("name", "").strip().upper()
        dept   = request.form.get("department", "AI&DS").strip()
        year   = request.form.get("year", "1")
        email  = request.form.get("email", "").strip().lower()
        phone  = request.form.get("phone", "").strip()
        form_data = {"reg_no": reg_no, "name": name, "department": dept,
                     "year": year, "email": email, "phone": phone}

        if not reg_no or not name:
            flash("Register number and name are required.", "danger")
            return render_template("faculty_register_student.html", user=user,
                                   form_data=form_data,
                                   photos_required=_config.PHOTOS_PER_STUDENT)
        try:
            year_int = int(year)
        except ValueError:
            flash("Year must be a number.", "danger")
            return render_template("faculty_register_student.html", user=user,
                                   form_data=form_data,
                                   photos_required=_config.PHOTOS_PER_STUDENT)

        try:
            Student.register(reg_no, name, dept, year_int, email, phone)
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template("faculty_register_student.html", user=user,
                                   form_data=form_data,
                                   photos_required=_config.PHOTOS_PER_STUDENT)

        # Save uploaded photos
        photo_dir = Path(_config.UPLOAD_FOLDER) / secure_filename(reg_no)
        photo_dir.mkdir(parents=True, exist_ok=True)
        photos = request.files.getlist("photos")
        saved = 0
        for idx, photo in enumerate(photos[:_config.PHOTOS_PER_STUDENT]):
            if photo and photo.filename and _allowed_file(photo.filename):
                filename = f"{secure_filename(reg_no)}_{idx + 1}.jpg"
                photo.save(photo_dir / filename)
                saved += 1

        flash(
            f"Student {name} ({reg_no}) registered successfully"
            + (f" with {saved} photo(s)." if saved else "."),
            "success",
        )
        return redirect(url_for("faculty.dashboard"))

    return render_template("faculty_register_student.html", user=user,
                           form_data=form_data,
                           photos_required=_config.PHOTOS_PER_STUDENT)


@faculty_bp.route("/monitoring")
@_faculty_required
def monitoring():
    """Live classroom monitoring page."""
    user = get_current_user()
    classroom_status = {
        "lights": False,
        "fans": False,
        "windows": False,
        "occupancy": "—",
        "temperature": "—",
    }
    alert_log = []
    camera_url = None
    return render_template(
        "faculty_monitoring.html",
        user=user,
        classroom_status=classroom_status,
        alert_log=alert_log,
        camera_url=camera_url,
    )


@faculty_bp.route("/monitoring/status")
@_faculty_required
def monitoring_status():
    """JSON endpoint for live classroom status updates."""
    return jsonify({"status": "ok", "alert": None})
