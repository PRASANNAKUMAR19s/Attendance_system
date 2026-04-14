"""
app.py — Main Flask Web Application
=====================================
AI-Based Attendance System — Web Interface

Provides an HTML/browser-based interface for:
  - Admin login / logout
  - Student registration with photo capture (13 angles)
  - Admin dashboard (student list, stats)

The REST API (api.py) runs separately on port 5001 and is not affected.

HOW TO RUN:
    python app.py

    OR with gunicorn (production):
    gunicorn -w 2 -b 0.0.0.0:5000 app:app

ENVIRONMENT VARIABLES (see .env.example):
    SECRET_KEY, DATABASE_PATH, UPLOAD_FOLDER, ...
"""

from __future__ import annotations

import logging
import os
from datetime import timedelta

from flask import Flask, redirect, session, url_for

import config as _config
from database import init_db
from extensions import jwt, limiter
from routes import api_bp, auth_bp, faculty_bp, student_portal_bp

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

def create_app() -> Flask:
    """Create and configure the Flask web application."""
    flask_app = Flask(__name__)

    # ── Core settings ────────────────────────────────────────────────────────
    flask_app.config["SECRET_KEY"]            = _config.SECRET_KEY
    flask_app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=8)
    flask_app.config["MAX_CONTENT_LENGTH"]    = _config.MAX_CONTENT_LENGTH
    flask_app.config["UPLOAD_FOLDER"]         = _config.UPLOAD_FOLDER
    flask_app.config["WTF_CSRF_ENABLED"]      = True
    flask_app.config["JWT_SECRET_KEY"]        = _config.JWT_SECRET_KEY
    flask_app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False

    # ── Initialise database ──────────────────────────────────────────────────
    init_db(flask_app)

    # ── Register Blueprints ──────────────────────────────────────────────────
    flask_app.register_blueprint(auth_bp)
    flask_app.register_blueprint(faculty_bp)
    flask_app.register_blueprint(student_portal_bp)
    flask_app.register_blueprint(api_bp, url_prefix="/api")

    jwt.init_app(flask_app)
    limiter.init_app(flask_app)

    # ── Root redirect ────────────────────────────────────────────────────────
    @flask_app.route("/")
    def index():
        role = session.get("role", "")
        if role in ("tutor", "hod", "admin"):
            return redirect(url_for("faculty.dashboard"))
        if role == "student":
            return redirect(url_for("student_portal.dashboard"))
        return redirect(url_for("auth.login"))

    # ── Security headers ─────────────────────────────────────────────────────
    @flask_app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"]        = "SAMEORIGIN"
        response.headers["X-XSS-Protection"]       = "1; mode=block"
        response.headers["Referrer-Policy"]        = "strict-origin-when-cross-origin"
        return response

    # ── Error handlers ───────────────────────────────────────────────────────
    @flask_app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template("error.html", code=404,
                               message="Page not found."), 404

    @flask_app.errorhandler(500)
    def server_error(e):
        from flask import render_template
        return render_template("error.html", code=500,
                               message="Internal server error."), 500

    return flask_app


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
app = create_app()

if __name__ == "__main__":
    port = _config.WEB_PORT
    logger.info("Starting Flask web app on port %s", port)
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
