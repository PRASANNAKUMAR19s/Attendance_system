"""
routes/student_portal.py — Student portal routes
=================================================
Provides the student-facing dashboard showing attendance statistics.
Accessible only to users with role 'student'.
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
    return render_template(
        "student_dashboard.html",
        user=user,
        reg_no=reg_no,
    )
