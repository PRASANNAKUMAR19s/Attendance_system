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
from services.email_service import EmailService
from urllib.parse import urljoin

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
    """Return the currently logged-in user object, or None."""
    role = session.get("role", "")
    user_id = session.get("user_id")
    if role == "student":
        from models.student import Student

        reg_no = session.get("username", "")
        return Student.get_by_reg_no(reg_no)
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
        if user is not None:
            session.clear()
            session["user_id"] = user.id
            session["username"] = user.username
            session["role"] = user.role
            session["full_name"] = user.full_name
            session.permanent = True

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

        from models.student import Student

        student = Student.get_by_reg_no(username)
        if student is not None and password == username:
            session.clear()
            session["user_id"] = f"student:{student.reg_no}"
            session["username"] = student.reg_no
            session["role"] = "student"
            session["full_name"] = student.name
            session.permanent = True

            logger.info("Student %s logged in.", username)
            next_param = request.args.get("next", "")
            parsed = urlsplit(next_param)
            if parsed.scheme or parsed.netloc or not next_param.startswith("/"):
                next_url = _default_dashboard_url("student")
            else:
                next_url = next_param
            return redirect(next_url)

        logger.warning("Failed login attempt for username: %s", username)
        flash("Invalid username or password.", "danger")
        return render_template("login.html")

    return render_template("login.html")


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        if not identifier:
            flash("Enter register number or email.", "danger")
            return render_template("forgot_password.html")

        user, token = User.create_password_reset_token(identifier)
        if user and token:
            # Build reset URL relative to current host
            reset_path = url_for("auth.reset_password", _external=False) + f"?token={token}"
            reset_url = urljoin(request.host_url, reset_path.lstrip("/"))
            EmailService().send_password_reset_link(
                to_email=user.email or user.username,
                student_name=user.full_name or user.username,
                reg_no=user.username,
                reset_url=reset_url,
            )
            flash("Password reset link sent if the account exists.", "info")
            return redirect(url_for("auth.login"))

        # Always show generic message to avoid user enumeration
        flash("Password reset link sent if the account exists.", "info")
        return redirect(url_for("auth.login"))


@auth_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    token = request.args.get("token", "") if request.method == "GET" else request.form.get("token", "")
    if request.method == "POST":
        new_password = request.form.get("password", "")
        confirm = request.form.get("password_confirm", "")
        if not token or not new_password:
            flash("Invalid token or password.", "danger")
            return render_template("reset_password.html", token=token)
        if new_password != confirm:
            flash("Passwords do not match.", "danger")
            return render_template("reset_password.html", token=token)
        user = User.consume_password_reset_token(token)
        if not user:
            flash("Invalid or expired token.", "danger")
            return render_template("reset_password.html", token=token)
        # Update password
        User.set_password(user.id, new_password)
        flash("Password updated. You can now log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("reset_password.html", token=token)


@auth_bp.route("/logout")
def logout():
    username = session.get("username", "unknown")
    session.clear()
    logger.info("User %s logged out.", username)
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
