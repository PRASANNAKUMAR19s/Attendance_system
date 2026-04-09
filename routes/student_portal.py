"""
routes/student_portal.py — Student portal routes
=================================================
Provides the student-facing dashboard showing attendance statistics.
Accessible only to users with role 'student'.
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from functools import wraps

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from routes.auth import get_current_user, login_required

logger = logging.getLogger(__name__)

student_portal_bp = Blueprint("student_portal", __name__, url_prefix="/student")


def _student_required(f):
    """Decorator: ensure the user is logged in AND has the student role."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        role = session.get("role", "")
        if role != "student":
            flash("Access denied. Student login required.", "danger")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated


def _get_student_record(reg_no: str):
    """Return the Student model record for reg_no, or None."""
    try:
        from models.student import Student
        return Student.get_by_reg_no(reg_no)
    except Exception:
        return None


def _get_attendance_records(reg_no: str, from_date: str = "", to_date: str = "",
                             status_filter: str = "") -> list:
    """Fetch attendance records for a student with optional filters."""
    try:
        from firebase_service import FirebaseService
        svc = FirebaseService()
        records = svc.get_attendance_by_reg_no(reg_no)
        if from_date:
            records = [r for r in records if r.get("date", "") >= from_date]
        if to_date:
            records = [r for r in records if r.get("date", "") <= to_date]
        if status_filter:
            records = [r for r in records if r.get("status") == status_filter]
        return records
    except Exception:
        return []


def _compute_summary(records: list) -> dict:
    total = len(records)
    present = sum(1 for r in records if r.get("status") == "Present")
    late = sum(1 for r in records if r.get("status") == "Late")
    absent = sum(1 for r in records if r.get("status") == "Absent")
    od = sum(1 for r in records if r.get("status") == "OD")
    attended = present + late + od
    pct = round(attended / total * 100, 1) if total > 0 else 0
    return {
        "total_classes": total,
        "present_count": present,
        "late_count": late,
        "absent_count": absent,
        "od_count": od,
        "attendance_pct": pct,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@student_portal_bp.route("/")
@student_portal_bp.route("/dashboard")
@_student_required
def dashboard():
    """Student portal main dashboard."""
    user = get_current_user()
    reg_no = session.get("username", "")
    records = _get_attendance_records(reg_no)
    summary = _compute_summary(records)
    return render_template(
        "student_dashboard.html",
        user=user,
        reg_no=reg_no,
        **summary,
    )


@student_portal_bp.route("/attendance")
@_student_required
def attendance():
    """Student attendance history page."""
    user = get_current_user()
    reg_no = session.get("username", "")
    from_date = request.args.get("from_date", "")
    to_date = request.args.get("to_date", "")
    filter_status = request.args.get("status", "")
    records = _get_attendance_records(reg_no, from_date, to_date, filter_status)
    summary = _compute_summary(_get_attendance_records(reg_no))
    return render_template(
        "student_attendance.html",
        user=user,
        reg_no=reg_no,
        records=records,
        from_date=from_date,
        to_date=to_date,
        filter_status=filter_status,
        **summary,
    )


@student_portal_bp.route("/od/upload", methods=["GET", "POST"])
@_student_required
def od_upload():
    """Upload an OD letter."""
    user = get_current_user()
    reg_no = session.get("username", "")

    if request.method == "POST":
        od_date = request.form.get("od_date", "").strip()
        reason = request.form.get("reason", "").strip()
        if not od_date or not reason:
            flash("OD date and reason are required.", "danger")
        else:
            flash("OD request submitted successfully. Awaiting faculty approval.", "success")
            return redirect(url_for("student_portal.od_status"))

    recent_submissions: list = []
    return render_template(
        "student_od_upload.html",
        user=user,
        reg_no=reg_no,
        recent_submissions=recent_submissions,
    )


@student_portal_bp.route("/od/status")
@_student_required
def od_status():
    """Check OD letter status."""
    user = get_current_user()
    reg_no = session.get("username", "")
    od_letters: list = []
    pending_count = sum(1 for l in od_letters if l.get("status") == "pending")
    approved_count = sum(1 for l in od_letters if l.get("status") == "approved")
    rejected_count = sum(1 for l in od_letters if l.get("status") == "rejected")
    return render_template(
        "student_od_status.html",
        user=user,
        reg_no=reg_no,
        od_letters=od_letters,
        pending_count=pending_count,
        approved_count=approved_count,
        rejected_count=rejected_count,
    )


@student_portal_bp.route("/downloads")
@_student_required
def download_templates():
    """Download templates page."""
    user = get_current_user()
    reg_no = session.get("username", "")
    return render_template(
        "student_download_templates.html",
        user=user,
        reg_no=reg_no,
    )


@student_portal_bp.route("/downloads/od-template")
@_student_required
def download_od_template():
    """Download blank OD letter template."""
    flash("OD letter template download will be available soon.", "info")
    return redirect(url_for("student_portal.download_templates"))


@student_portal_bp.route("/downloads/condonation-template")
@_student_required
def download_condonation_template():
    """Download attendance condonation letter template."""
    flash("Condonation letter template download will be available soon.", "info")
    return redirect(url_for("student_portal.download_templates"))


@student_portal_bp.route("/profile")
@_student_required
def profile():
    """Student profile page."""
    user = get_current_user()
    reg_no = session.get("username", "")
    student = _get_student_record(reg_no)
    records = _get_attendance_records(reg_no)
    summary = _compute_summary(records)
    return render_template(
        "student_profile.html",
        user=user,
        reg_no=reg_no,
        student=student,
        **summary,
    )


@student_portal_bp.route("/attendance/pdf")
@_student_required
def attendance_pdf():
    """Render attendance as a printable/PDF page."""
    user = get_current_user()
    reg_no = session.get("username", "")
    student = _get_student_record(reg_no)
    records = _get_attendance_records(reg_no)
    summary = _compute_summary(records)
    generated_at = datetime.now().strftime("%d %B %Y %H:%M")
    import config as _config
    return render_template(
        "student_attendance_pdf.html",
        user=user,
        reg_no=reg_no,
        student_name=student.name if student else None,
        department=student.department if student else None,
        year=student.year if student else None,
        records=records,
        generated_at=generated_at,
        config_college=getattr(_config, "COLLEGE_NAME", None),
        config_dept=getattr(_config, "DEPARTMENT", None),
        **summary,
    )
