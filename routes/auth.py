"""
routes/auth.py — Login / logout routes
=======================================
Session-based authentication for the web application.
"""

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from urllib.parse import urlsplit

from models.user import User

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def login_required(f):
    """Decorator that redirects unauthenticated users to the login page."""
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return f(*args, **kwargs)

    return decorated


def get_current_user() -> User | None:
    """Return the currently logged-in User object, or None."""
    user_id = session.get("user_id")
    if user_id is None:
        return None
    return User.get_by_id(user_id)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

def _default_dashboard_url(role: str) -> str:
    """Return the default post-login URL based on the user's role."""
    if role in ("tutor", "hod", "admin"):
        return url_for("faculty.dashboard")  # ✅ Go to Faculty
    if role == "student":
        return url_for("student_portal.dashboard")  # ✅ Go to Student
    return url_for("faculty.dashboard")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(_default_dashboard_url(session.get("role", "admin")))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username and password are required.", "danger")
            return render_template("login.html")

        user = User.verify_password(username, password)
        if user is None:
            logger.warning("Failed login attempt for username: %s", username)
            flash("Invalid username or password.", "danger")
            return render_template("login.html")

        session.clear()
        session["user_id"]   = user.id
        session["username"]  = user.username
        session["role"]      = user.role
        session["full_name"] = user.full_name
        session.permanent    = True

        logger.info("User %s logged in.", username)
        # Only allow same-origin relative redirects (must start with /) to
        # prevent open-redirect attacks.  Any external URL is ignored.
        next_param = request.args.get("next", "")
        parsed = urlsplit(next_param)
        if parsed.scheme or parsed.netloc or not next_param.startswith("/"):
            next_url = _default_dashboard_url(user.role)
        else:
            next_url = next_param
        return redirect(next_url)

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    username = session.get("username", "unknown")
    session.clear()
    logger.info("User %s logged out.", username)
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
