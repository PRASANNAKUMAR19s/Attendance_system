"""
routes/faculty.py — Faculty portal routes (Tutor / HOD)
=========================================================
Provides the faculty-facing dashboard and management tools.
Accessible only to users with role 'tutor', 'hod', or 'admin'.
"""

from __future__ import annotations

import logging
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
