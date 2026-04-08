"""
routes/admin.py — Admin panel routes
======================================
Handles the admin dashboard and student management (register / delete).
Photo uploads for 13-angle face capture are also processed here.
"""

from __future__ import annotations

import logging
from pathlib import Path

from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from werkzeug.utils import secure_filename

import config as _config
from models.student import Student
from routes.auth import get_current_user, login_required

logger = logging.getLogger(__name__)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _allowed_file(filename: str) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in _config.ALLOWED_EXTENSIONS
    )


def _student_photo_dir(reg_no: str) -> Path:
    """Return the directory where a student's photos are stored."""
    safe_reg = secure_filename(reg_no)
    return Path(_config.UPLOAD_FOLDER) / safe_reg


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@admin_bp.route("/", methods=["GET"])
@admin_bp.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    students = Student.get_all()
    user = get_current_user()
    student_data = []
    for s in students:
        photo_dir = _student_photo_dir(s.reg_no)
        photo_count = len(list(photo_dir.glob("*.jpg"))) if photo_dir.exists() else 0
        student_data.append({
            "reg_no":    s.reg_no,
            "name":      s.name,
            "department": s.department,
            "year":      s.year,
            "email":     s.email,
            "phone":     s.phone,
            "photos":    photo_count,
        })
    return render_template(
        "admin_dashboard.html",
        students=student_data,
        total=len(student_data),
        user=user,
    )


@admin_bp.route("/students/register", methods=["GET", "POST"])
@login_required
def register_student():
    user = get_current_user()

    if request.method == "POST":
        reg_no = request.form.get("reg_no", "").strip().upper()
        name   = request.form.get("name", "").strip().upper()
        dept   = request.form.get("department", "AI&DS").strip()
        year   = request.form.get("year", "1")
        email  = request.form.get("email", "").strip().lower()
        phone  = request.form.get("phone", "").strip()

        if not reg_no or not name:
            flash("Register number and name are required.", "danger")
            return render_template("register_student.html", user=user,
                                   photos_required=_config.PHOTOS_PER_STUDENT)

        try:
            year_int = int(year)
        except ValueError:
            flash("Year must be a number.", "danger")
            return render_template("register_student.html", user=user,
                                   photos_required=_config.PHOTOS_PER_STUDENT)

        try:
            Student.register(reg_no, name, dept, year_int, email, phone)
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template("register_student.html", user=user,
                                   photos_required=_config.PHOTOS_PER_STUDENT)

        # Save uploaded photos (up to PHOTOS_PER_STUDENT)
        photo_dir = _student_photo_dir(reg_no)
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
        return redirect(url_for("admin.dashboard"))

    return render_template("register_student.html", user=user,
                           photos_required=_config.PHOTOS_PER_STUDENT)


@admin_bp.route("/students/<reg_no>/delete", methods=["POST"])
@login_required
def delete_student(reg_no: str):
    student = Student.get_by_reg_no(reg_no)
    if student is None:
        flash(f"Student {reg_no!r} not found.", "danger")
        return redirect(url_for("admin.dashboard"))

    Student.delete(reg_no)
    flash(f"Student {student.name} ({reg_no}) deleted.", "warning")
    logger.info("Admin deleted student %s", reg_no)
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/students/<reg_no>/upload-photo", methods=["POST"])
@login_required
def upload_photo(reg_no: str):
    """Ajax endpoint for uploading individual photos during registration."""
    student = Student.get_by_reg_no(reg_no)
    if student is None:
        return jsonify({"error": "Student not found"}), 404

    photo = request.files.get("photo")
    if photo is None or not photo.filename:
        return jsonify({"error": "No photo provided"}), 400

    if not _allowed_file(photo.filename):
        return jsonify({"error": "Invalid file type"}), 400

    photo_dir = _student_photo_dir(reg_no)
    photo_dir.mkdir(parents=True, exist_ok=True)

    existing = list(photo_dir.glob("*.jpg"))
    if len(existing) >= _config.PHOTOS_PER_STUDENT:
        return jsonify({"error": "Maximum photos already uploaded"}), 400

    idx = len(existing) + 1
    filename = f"{secure_filename(reg_no)}_{idx}.jpg"
    photo.save(photo_dir / filename)

    return jsonify({
        "success": True,
        "photo_index": idx,
        "total": len(list(photo_dir.glob("*.jpg"))),
        "max": _config.PHOTOS_PER_STUDENT,
    })
