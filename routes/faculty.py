"""
routes/faculty.py — Faculty portal routes (Tutor / HOD)
=========================================================
Provides the faculty-facing dashboard and management tools.
Accessible only to users with role 'tutor', 'hod', or 'admin'.
"""

from __future__ import annotations

import logging
import json
import logging
from datetime import date, datetime
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


def _get_current_period() -> str:
    """Return the current period name based on system time, or 'Period 1' as fallback."""
    now = datetime.now().strftime("%H:%M")
    for name, late_after, end in _config.PERIODS:
        if late_after <= now <= end:
            return name
    return "Period 1"


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
    
    # Get today's attendance stats
    from firebase_service import FirebaseService
    svc = FirebaseService()
    today = date.today().isoformat()
    today_attendance = svc.get_attendance(date=today)
    
    present_today = sum(1 for r in today_attendance if r.get("status", "").upper() in ("PRESENT", "ON_TIME", "LATE"))
    absent_today = sum(1 for r in today_attendance if r.get("status", "").upper() == "ABSENT")
    
    # Count OD letters pending
    od_pending = 0
    od_uploads = Path("od_uploads")
    if od_uploads.exists():
        od_file = od_uploads / "od_records.csv"
        if od_file.exists():
            with open(od_file) as f:
                od_pending = len(f.readlines())
    
    return render_template(
        "faculty_dashboard.html",
        user=user,
        total_students=total_students,
        students=students,
        present_today=present_today,
        absent_today=absent_today,
        pending_od=od_pending,
        today_records=today_attendance,
    )


@faculty_bp.route("/api/dashboard-stats")
@_faculty_required
def dashboard_stats():
    """API endpoint to get real-time dashboard statistics."""
    from firebase_service import FirebaseService
    svc = FirebaseService()
    today = date.today().isoformat()
    today_attendance = svc.get_attendance(date=today)
    
    present_today = sum(1 for r in today_attendance if r.get("status", "").upper() in ("PRESENT", "ON_TIME", "LATE"))
    absent_today = sum(1 for r in today_attendance if r.get("status", "").upper() == "ABSENT")
    
    od_pending = 0
    od_uploads = Path("od_uploads")
    if od_uploads.exists():
        od_file = od_uploads / "od_records.csv"
        if od_file.exists():
            with open(od_file) as f:
                od_pending = len(f.readlines())
    
    return jsonify({
        "total_students": Student.count(),
        "present_today": present_today,
        "absent_today": absent_today,
        "pending_od": od_pending,
    })


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
                svc.mark_attendance(s.reg_no, s.name, today, _get_current_period(), status)
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
    selected_reg = request.args.get("reg_no", "")
    fmt = request.args.get("format", "")
    
    from_date = ""
    to_date = ""

    from firebase_service import FirebaseService
    svc = FirebaseService()

    attendance_records = svc.get_attendance(reg_no=selected_reg if selected_reg else None)

    if report_type == "daily":
        from_date = request.args.get("from_date", "")
        to_date = from_date
        if from_date:
            attendance_records = [r for r in attendance_records if r.get('date', '') == from_date]
    
    elif report_type == "weekly":
        week = request.args.get("week", "1")
        month = request.args.get("month", datetime.now().strftime("%m"))
        year = request.args.get("year", datetime.now().strftime("%Y"))
        from_date, to_date = get_week_date_range(int(year), int(month), int(week))
        attendance_records = [r for r in attendance_records if from_date <= r.get('date', '') <= to_date]
    
    elif report_type == "monthly":
        month = request.args.get("month", datetime.now().strftime("%m"))
        year = request.args.get("year", datetime.now().strftime("%Y"))
        from_date, to_date = get_month_date_range(int(year), int(month))
        attendance_records = [r for r in attendance_records if from_date <= r.get('date', '') <= to_date]
    
    elif report_type == "custom":
        from_date = request.args.get("from_date", "")
        to_date = request.args.get("to_date", "")
        if from_date and to_date:
            attendance_records = [r for r in attendance_records if from_date <= r.get('date', '') <= to_date]

    report_rows = []
    for r in attendance_records:
        status = r.get("status", "")
        if status in ("ON_TIME", "PRESENT"):
            status_text = "Present"
        elif status == "LATE":
            status_text = "Late"
        elif status == "OD":
            status_text = "OD"
        else:
            status_text = "Absent"
        
        student = next((s for s in students if s.reg_no == r.get('reg_no')), None)
        report_rows.append({
            "date": r.get("date", ""),
            "reg_no": r.get("reg_no", ""),
            "name": student.name if student else r.get("name", ""),
            "status": status_text,
            "period": r.get("period", ""),
            "time": r.get("marked_time", ""),
            "reason": r.get("reason", ""),
        })

    if fmt == "pdf":
        return generate_pdf_report(report_type, from_date, to_date, selected_reg, students, attendance_records, user)
    elif fmt == "csv":
        return generate_csv_report(selected_reg, students, attendance_records)
    elif fmt == "excel":
        flash("Excel export will be available when the reporting service is configured.", "info")
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


def get_week_date_range(year, month, week):
    """Return (from_date, to_date) for a given week of month."""
    import calendar
    cal = calendar.Calendar()
    month_days = list(cal.itermonthdates(year, month))
    
    weeks = {}
    current_week = 1
    week_start = None
    
    for day in month_days:
        if day.month == month:
            if week_start is None:
                week_start = day
            week_end = day
        else:
            if week_start is not None:
                weeks[current_week] = (week_start, week_end)
                current_week += 1
                week_start = None
    
    if week_start is not None:
        weeks[current_week] = (week_start, week_end)
    
    if week in weeks:
        start, end = weeks[week]
        return (start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
    
    first_day = datetime(year, month, 1).strftime("%Y-%m-%d")
    last_day = calendar.monthrange(year, month)[1]
    last_day = datetime(year, month, last_day).strftime("%Y-%m-%d")
    return (first_day, last_day)


def get_month_date_range(year, month):
    """Return (from_date, to_date) for a given month."""
    import calendar
    last_day = calendar.monthrange(year, month)[1]
    from_date = datetime(year, month, 1).strftime("%Y-%m-%d")
    to_date = datetime(year, month, last_day).strftime("%Y-%m-%d")
    return (from_date, to_date)


@faculty_bp.route("/notifications")
@_faculty_required
def notifications():
    """Email notifications page."""
    user = get_current_user()
    students = Student.get_all()
    today = date.today().isoformat()
    from firebase_service import FirebaseService
    svc = FirebaseService()
    attendance_today = svc.get_attendance(date=today)
    
    absent_students = []
    for r in attendance_today:
        if r.get("status", "").upper() == "ABSENT":
            for s in students:
                if s.reg_no == r.get("reg_no"):
                    absent_students.append({
                        "reg_no": s.reg_no,
                        "name": s.name,
                        "email": s.email,
                        "status": r.get("status", ""),
                        "period": r.get("period", ""),
                    })
    
    return render_template(
        "faculty_notifications.html",
        user=user,
        students=students,
        absent_students=absent_students,
        today=today,
        config=_config,
    )


@faculty_bp.route("/notifications/send-alert", methods=["POST"])
@_faculty_required
def send_alert():
    """Send attendance alert email to parent."""
    reg_no = request.form.get("reg_no", "")
    student_email = request.form.get("student_email", "")
    date_str = request.form.get("date", "")
    period = request.form.get("period", "")
    status = request.form.get("status", "")
    reason = request.form.get("reason", "")
    
    if not student_email:
        flash("No email address available for this student.", "warning")
        return redirect(url_for("faculty.notifications"))
    
    student = Student.get_by_reg_no(reg_no)
    if not student:
        flash("Student not found.", "danger")
        return redirect(url_for("faculty.notifications"))
    
    from services.email_service import EmailService
    email_service = EmailService()
    
    if email_service.is_configured():
        success = email_service.send_attendance_alert(
            to_email=student_email,
            student_name=student.name,
            reg_no=reg_no,
            date=date_str,
            period=period,
            status=status,
            reason=reason if reason else None,
        )
        if success:
            flash(f"Alert email sent to {student_email}", "success")
        else:
            flash("Failed to send email. Check email configuration.", "danger")
    else:
        flash("Email service not configured. Please set up SMTP credentials.", "warning")
    
    return redirect(url_for("faculty.notifications"))


@faculty_bp.route("/notifications/send-daily-summary", methods=["POST"])
@_faculty_required
def send_daily_summary():
    """Send daily attendance summary email."""
    date_str = request.form.get("date", date.today().isoformat())
    to_email = request.form.get("to_email", _config.TUTOR_EMAIL)
    
    from firebase_service import FirebaseService
    svc = FirebaseService()
    attendance_records = svc.get_attendance(date=date_str)
    students = Student.get_all()
    
    present = sum(1 for r in attendance_records if r.get("status", "").upper() in ("ON_TIME", "PRESENT"))
    late = sum(1 for r in attendance_records if r.get("status", "").upper() == "LATE")
    absent = sum(1 for r in attendance_records if r.get("status", "").upper() == "ABSENT")
    total = len(students)
    
    details = []
    for r in attendance_records:
        student = next((s for s in students if s.reg_no == r.get("reg_no")), None)
        details.append({
            "reg_no": r.get("reg_no", "-"),
            "name": student.name if student else r.get("name", "-"),
            "status": r.get("status", "-"),
        })
    
    from services.email_service import EmailService
    email_service = EmailService()
    
    if email_service.is_configured():
        success = email_service.send_daily_summary(
            to_email=to_email,
            date=date_str,
            present_count=present,
            late_count=late,
            absent_count=absent,
            total_students=total,
            details=details,
        )
        if success:
            flash(f"Daily summary sent to {to_email}", "success")
        else:
            flash("Failed to send email.", "danger")
    else:
        flash("Email service not configured.", "warning")
    
    return redirect(url_for("faculty.notifications"))


def generate_pdf_report(report_type, from_date, to_date, selected_reg, students, attendance_records, user):
    """Generate PDF attendance report."""
    from datetime import datetime
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.enums import TA_CENTER, TA_LEFT

    student = None
    if selected_reg:
        for s in students:
            if s.reg_no == selected_reg:
                student = s
                break

    buffer = __import__('io').BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=16, alignment=TA_CENTER, spaceAfter=10)
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER, textColor=colors.grey)
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=9)

    elements.append(Paragraph("Paavai Engineering College", title_style))
    elements.append(Paragraph("Department of Artificial Intelligence & Data Science", subtitle_style))
    elements.append(Spacer(1, 10*mm))

    report_title = f"Attendance Report - {report_type.title()}"
    if selected_reg and student:
        report_title += f" | Student: {student.name} ({student.reg_no})"
    if from_date and to_date:
        report_title += f" | {from_date} to {to_date}"
    
    elements.append(Paragraph(report_title, styles['Heading2']))
    elements.append(Spacer(1, 5*mm))

    if selected_reg and student:
        info_data = [
            ["Register No:", student.reg_no, "Name:", student.name],
            ["Department:", student.department, "Year:", f"{student.year}"],
        ]
        info_table = Table(info_data, colWidths=[60, 120, 60, 120])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 5*mm))

    attendance_data = [["#", "Reg. No", "Name", "Period", "Status", "Time"]]
    for i, record in enumerate(attendance_records[:50], 1):
        status = record.get("status", "Unknown")
        if status in ("ON_TIME", "PRESENT", "LATE"):
            status = "Present"
        elif status == "OD":
            status = "On Duty"
        else:
            status = "Absent"
        
        attendance_data.append([
            str(i),
            record.get("reg_no", "-"),
            record.get("name", "-"),
            record.get("period", "-"),
            status,
            record.get("marked_time", "-"),
        ])

    table = Table(attendance_data, colWidths=[25, 70, 100, 60, 55, 60])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066cc')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 10*mm))

    present = sum(1 for r in attendance_records if r.get("status", "").upper() in ("ON_TIME", "PRESENT", "LATE"))
    absent = sum(1 for r in attendance_records if r.get("status", "").upper() == "ABSENT")
    total = len(attendance_records)
    pct = round(present / total * 100, 1) if total > 0 else 0

    summary_data = [
        ["Summary:", f"Total: {total}", f"Present: {present}", f"Absent: {absent}", f"Attendance: {pct}%"]
    ]
    summary_table = Table(summary_data, colWidths=[60, 80, 80, 80, 80])
    summary_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e8f5e9')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    elements.append(summary_table)

    elements.append(Spacer(1, 10*mm))
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", subtitle_style))
    elements.append(Paragraph(f"Generated by: {user.full_name}", subtitle_style))

    doc.build(elements)
    buffer.seek(0)

    from flask import make_response
    filename = f"attendance_report_{selected_reg or 'all'}_{datetime.now().strftime('%Y-%m-%d')}.pdf"
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response


def generate_csv_report(selected_reg, students, attendance_records):
    """Generate CSV attendance report."""
    from flask import make_response
    import csv
    from io import StringIO

    output = StringIO()
    writer = csv.writer(output)
    
    writer.writerow(["#", "Register No", "Name", "Date", "Period", "Status", "Time"])
    
    for i, record in enumerate(attendance_records, 1):
        status = record.get("status", "")
        if status in ("ON_TIME", "PRESENT", "LATE"):
            status_text = "Present"
        elif status == "OD":
            status_text = "On Duty"
        else:
            status_text = "Absent"
        
        writer.writerow([
            i,
            record.get("reg_no", "-"),
            record.get("name", "-"),
            record.get("date", "-"),
            record.get("period", "-"),
            status_text,
            record.get("marked_time", "-"),
        ])
    
    output.seek(0)
    filename = f"attendance_report_{selected_reg or 'all'}_{datetime.now().strftime('%Y-%m-%d')}.csv"
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response


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

        # Auto-create user account for student
        try:
            from models.user import User
            default_password = reg_no  # Default password is register number
            User.create(
                username=reg_no,
                plain_password=default_password,
                role="student",
                full_name=name,
                email=email,
            )
            logger.info("Created student user account: %s", reg_no)
        except Exception as exc:
            logger.warning("Could not create student user %s: %s", reg_no, exc)

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
            + (f" with {saved} photo(s)." if saved else ".")
            + f" Login ID: {reg_no} | Default Password: {reg_no}",
            "success",
        )
        return redirect(url_for("faculty.dashboard"))

    return render_template("faculty_register_student.html", user=user,
                           form_data=form_data,
                           photos_required=_config.PHOTOS_PER_STUDENT)


@faculty_bp.route("/upload-photo/<reg_no>", methods=["POST"])
@_faculty_required
def upload_photo(reg_no):
    """Handle photo upload for student registration."""
    if "photo" not in request.files:
        return jsonify({"success": False, "error": "No photo provided"}), 400
    
    photo = request.files["photo"]
    if photo.filename == "":
        return jsonify({"success": False, "error": "No photo selected"}), 400
    
    if photo and _allowed_file(photo.filename):
        student = Student.get_by_reg_no(reg_no)
        if not student:
            return jsonify({"success": False, "error": "Student not found"}), 404
        
        photo_dir = Path(_config.UPLOAD_FOLDER) / secure_filename(reg_no)
        photo_dir.mkdir(parents=True, exist_ok=True)
        
        existing_photos = list(photo_dir.glob(f"{secure_filename(reg_no)}_*.jpg"))
        idx = len(existing_photos) + 1
        
        filename = f"{secure_filename(reg_no)}_{idx}.jpg"
        photo.save(photo_dir / filename)
        
        return jsonify({"success": True, "filename": filename, "index": idx})
    
    return jsonify({"success": False, "error": "Invalid file type"}), 400


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


@faculty_bp.route("/students")
@_faculty_required
def all_students():
    """View all registered students."""
    user = get_current_user()
    students = Student.get_all()
    return render_template(
        "faculty_all_students.html",
        user=user,
        students=students,
        total_students=len(students),
    )


@faculty_bp.route("/students/low-attendance")
@_faculty_required
def low_attendance_students():
    """View students with attendance below 75%."""
    user = get_current_user()
    from firebase_service import FirebaseService
    svc = FirebaseService()
    students = Student.get_all()
    
    low_attendance = []
    for s in students:
        reg_no = s.reg_no
        records = svc.get_attendance(reg_no=reg_no)
        total = len(records)
        if total == 0:
            continue
        present = sum(1 for r in records if r.get("status", "").upper() in ("PRESENT", "LATE", "ON_TIME", "OD"))
        pct = round(present / total * 100, 1)
        if pct < 75:
            low_attendance.append({
                "reg_no": reg_no,
                "name": s.name,
                "department": s.department,
                "year": s.year,
                "email": s.email,
                "total_classes": total,
                "present": present,
                "attendance_pct": pct,
            })
    
    low_attendance.sort(key=lambda x: x["attendance_pct"])
    return render_template(
        "faculty_low_attendance.html",
        user=user,
        students=low_attendance,
        total=len(low_attendance),
    )


@faculty_bp.route("/student/<reg_no>")
@_faculty_required
def view_student(reg_no):
    """View student details with attendance summary."""
    user = get_current_user()
    student = Student.get_by_reg_no(reg_no)
    if not student:
        flash("Student not found.", "danger")
        return redirect(url_for("faculty.all_students"))
    
    from firebase_service import FirebaseService
    svc = FirebaseService()
    attendance_records = svc.get_attendance(reg_no=reg_no)
    
    total = len(attendance_records)
    present = sum(1 for r in attendance_records if r.get("status", "").upper() in ("ON_TIME", "PRESENT"))
    late = sum(1 for r in attendance_records if r.get("status", "").upper() == "LATE")
    absent = sum(1 for r in attendance_records if r.get("status", "").upper() == "ABSENT")
    pct = round((present + late) / total * 100, 1) if total > 0 else 0
    
    return render_template(
        "faculty_student_detail.html",
        user=user,
        student=student,
        attendance_records=attendance_records[:50],
        total_classes=total,
        present_count=present,
        late_count=late,
        absent_count=absent,
        attendance_pct=pct,
    )


@faculty_bp.route("/student/<reg_no>/edit", methods=["GET", "POST"])
@_faculty_required
def edit_student(reg_no):
    """Edit student details."""
    user = get_current_user()
    student = Student.get_by_reg_no(reg_no)
    if not student:
        flash("Student not found.", "danger")
        return redirect(url_for("faculty.all_students"))
    
    if request.method == "POST":
        new_reg_no = request.form.get("reg_no", "").strip().upper()
        name = request.form.get("name", "").strip().upper()
        department = request.form.get("department", "").strip()
        year = request.form.get("year", "1").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        
        if not new_reg_no or not name:
            flash("Register number and name are required.", "danger")
            return render_template("faculty_edit_student.html", user=user, student=student)
        
        try:
            year_int = int(year)
        except ValueError:
            flash("Year must be a number.", "danger")
            return render_template("faculty_edit_student.html", user=user, student=student)
        
        from firebase_service import FirebaseService
        svc = FirebaseService()
        
        if new_reg_no != reg_no:
            svc.delete_student(reg_no)
            Student.register(new_reg_no, name, department, year_int, email, phone)
            flash(f"Student {name} ({new_reg_no}) updated successfully.", "success")
            return redirect(url_for("faculty.view_student", reg_no=new_reg_no))
        else:
            svc.update_student(reg_no, {
                "name": name,
                "department": department,
                "year": year_int,
                "email": email,
                "phone": phone,
            })
            flash(f"Student {name} updated successfully.", "success")
            return redirect(url_for("faculty.view_student", reg_no=reg_no))
    
    return render_template("faculty_edit_student.html", user=user, student=student)


@faculty_bp.route("/student/<reg_no>/delete", methods=["GET", "POST"])
@_faculty_required
def delete_student(reg_no):
    """Delete a student."""
    if request.method == "GET":
        return redirect(url_for("faculty.view_student", reg_no=reg_no))
    
    student = Student.get_by_reg_no(reg_no)
    if not student:
        flash("Student not found.", "danger")
    else:
        Student.delete(reg_no)
        # Also delete the user account
        try:
            from models.user import User
            User.delete(reg_no)
        except Exception:
            pass
        flash(f"Student {student.name} ({reg_no}) deleted successfully.", "success")
    return redirect(url_for("faculty.all_students"))


@faculty_bp.route("/face-recognition")
@_faculty_required
def face_recognition():
    """Real-time face recognition attendance page."""
    user = get_current_user()
    from services.face_recognition_service import FaceRecognitionService
    fr_service = FaceRecognitionService()
    is_ready = fr_service.is_ready()
    students_count = len(fr_service._student_map) if hasattr(fr_service, '_student_map') else 0
    error_msg = fr_service.get_last_error() if not is_ready else None
    return render_template(
        "faculty_face_recognition.html",
        user=user,
        is_ready=is_ready,
        students_count=students_count,
        periods=_config.PERIODS,
        error_msg=error_msg,
    )


@faculty_bp.route("/face-recognition/stream")
@_faculty_required
def face_recognition_stream():
    """MJPEG video stream for face recognition."""
    from services.face_recognition_service import FaceRecognitionService
    fr_service = FaceRecognitionService()
    fr_service.start_stream()
    
    def generate():
        while fr_service.is_streaming():
            frame = fr_service.get_stream_frame()
            if frame:
                yield (b"--frame\r\n"
                       b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
    
    from flask import Response
    return Response(
        generate(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@faculty_bp.route("/face-recognition/process", methods=["POST"])
@_faculty_required
def face_recognition_process():
    """Process a frame from the client for face recognition."""
    from services.face_recognition_service import FaceRecognitionService
    
    data = request.get_json()
    if not data or "frame" not in data:
        return jsonify({"success": False, "error": "No frame provided"}), 400
    
    fr_service = FaceRecognitionService()
    result = fr_service.process_frame_base64(data["frame"])
    return jsonify(result)


@faculty_bp.route("/face-recognition/stats")
@_faculty_required
def face_recognition_stats():
    """Get current attendance statistics."""
    from services.face_recognition_service import FaceRecognitionService
    fr_service = FaceRecognitionService()
    stats = fr_service.get_today_attendance()
    period = fr_service.get_current_period()
    return jsonify({
        "success": True,
        "stats": stats,
        "period": {
            "name": period.name if period else None,
            "status": period.status if period else None,
        } if period else None
    })


@faculty_bp.route("/face-recognition/status")
@_faculty_required
def face_recognition_status():
    """Check face recognition service status."""
    from services.face_recognition_service import FaceRecognitionService
    fr_service = FaceRecognitionService()
    return jsonify({
        "ready": fr_service.is_ready(),
        "streaming": fr_service.is_streaming(),
        "students_loaded": len(fr_service._student_map) if hasattr(fr_service, '_student_map') else 0,
        "period": fr_service.get_current_period(),
    })


@faculty_bp.route("/attendance/start-period", methods=["POST"])
@_faculty_required
def start_attendance_period():
    """Start attendance tracking for a period - marks all students as pending."""
    data = request.get_json()
    period = data.get("period", "")
    today = date.today().isoformat()
    
    if not period:
        return jsonify({"success": False, "error": "Period not specified"}), 400
    
    students = Student.get_all()
    from firebase_service import FirebaseService
    svc = FirebaseService()
    
    # Get already marked students for this period
    attendance = svc.get_attendance(date=today)
    marked = {r.get("reg_no"): r.get("status") for r in attendance if r.get("period") == period}
    
    # Return list of students and their status
    student_list = []
    for s in students:
        reg = s.reg_no
        status = marked.get(reg, "NOT_MARKED")
        student_list.append({
            "reg_no": reg,
            "name": s.name,
            "status": status,
            "is_marked": status != "NOT_MARKED"
        })
    
    return jsonify({
        "success": True,
        "period": period,
        "total_students": len(students),
        "marked_count": len([s for s in student_list if s["is_marked"]]),
        "students": student_list
    })


@faculty_bp.route("/attendance/end-period", methods=["POST"])
@_faculty_required
def end_attendance_period():
    """End attendance period - mark unmarked students as Absent and detect early leaves."""
    data = request.get_json()
    period = data.get("period", "")
    today = date.today().isoformat()
    
    if not period:
        return jsonify({"success": False, "error": "Period not specified"}), 400
    
    students = Student.get_all()
    from firebase_service import FirebaseService
    from services.face_recognition_service import FaceRecognitionService
    
    svc = FirebaseService()
    fr_service = FaceRecognitionService()
    
    # Get already marked students
    attendance = svc.get_attendance(date=today)
    marked = {r.get("reg_no") for r in attendance if r.get("period") == period}
    
    # Collect absent students for early leave detection
    absent_students = []
    
    # Mark unmarked students as Absent
    absent_count = 0
    for s in students:
        if s.reg_no not in marked:
            svc.mark_attendance(s.reg_no, s.name, today, period, "ABSENT")
            absent_students.append({"reg_no": s.reg_no, "name": s.name})
            absent_count += 1
    
    # Auto-detect early leaves and send notifications
    early_leaves = fr_service.detect_early_leaves(absent_students)
    early_leave_notifications_sent = 0
    
    if early_leaves:
        early_leave_notifications_sent = fr_service.send_early_leave_notifications(early_leaves)
        logger.info(f"Early leave alerts sent for {len(early_leaves)} students")
    
    # Get updated stats
    updated_attendance = svc.get_attendance(date=today)
    period_attendance = [r for r in updated_attendance if r.get("period") == period]
    present = sum(1 for r in period_attendance if r.get("status") != "ABSENT")
    absent = sum(1 for r in period_attendance if r.get("status") == "ABSENT")
    
    return jsonify({
        "success": True,
        "period": period,
        "marked_absent": absent_count,
        "total_students": len(students),
        "present": present,
        "absent": absent,
        "early_leaves_detected": len(early_leaves),
        "early_leave_notifications_sent": early_leave_notifications_sent,
        "early_leave_students": early_leaves
    })


@faculty_bp.route("/attendance/review")
@_faculty_required
def review_attendance():
    """Review and update attendance - mark absent students as present with reason."""
    user = get_current_user()
    today = date.today().isoformat()
    from firebase_service import FirebaseService
    svc = FirebaseService()
    
    # Get today's attendance with Absent status
    attendance = svc.get_attendance(date=today)
    absent_records = [r for r in attendance if r.get("status") == "ABSENT"]
    
    return render_template(
        "faculty_review_attendance.html",
        user=user,
        today=today,
        absent_records=absent_records,
    )


@faculty_bp.route("/attendance/update-status", methods=["POST"])
@_faculty_required
def update_attendance_status():
    """Update a student's attendance status (absent -> present with reason)."""
    data = request.get_json()
    reg_no = data.get("reg_no", "")
    period = data.get("period", "")
    new_status = data.get("status", "PRESENT")
    reason = data.get("reason", "")
    today = data.get("date", date.today().isoformat())
    
    if not reg_no or not period:
        return jsonify({"success": False, "error": "Missing required fields"}), 400
    
    from firebase_service import FirebaseService
    svc = FirebaseService()
    
    # Get student name
    student = Student.get_by_reg_no(reg_no)
    name = student.name if student else reg_no
    
    # Delete old record and insert new
    svc.delete_attendance(reg_no, today, period)
    svc.mark_attendance(reg_no, name, today, period, new_status)
    
    logger.info(f"Tutor updated attendance: {name} ({reg_no}) - {new_status} for {period}")
    
    return jsonify({
        "success": True,
        "message": f"Updated {name} to {new_status}"
    })


@faculty_bp.route("/send-low-attendance-alerts", methods=["POST"])
@_faculty_required
def send_low_attendance_alerts():
    """Send email alerts to students with attendance below 75%."""
    from firebase_service import FirebaseService
    from services.email_service import EmailService
    
    svc = FirebaseService()
    email_service = EmailService()
    
    students = svc.get_students()
    alerts_sent = 0
    failed = 0
    
    for student_data in students:
        reg_no = student_data.get("reg_no", student_data.get("RegNo", ""))
        name = student_data.get("name", student_data.get("Name", ""))
        email = student_data.get("email", student_data.get("Email", ""))
        
        if not reg_no:
            continue
        
        records = svc.get_attendance(reg_no=reg_no)
        total = len(records)
        if total == 0:
            continue
        
        present = sum(1 for r in records if r.get("status", "").upper() in ("PRESENT", "LATE", "ON_TIME", "OD"))
        pct = round(present / total * 100, 1)
        
        if pct < 75 and email:
            success = email_service.send_low_attendance_warning(
                to_email=email,
                student_name=name,
                reg_no=reg_no,
                attendance_pct=pct,
            )
            if success:
                alerts_sent += 1
            else:
                failed += 1
    
    if alerts_sent > 0:
        flash(f"Low attendance alerts sent to {alerts_sent} student(s).", "success")
    elif failed > 0:
        flash(f"Failed to send {failed} alert(s). Check email configuration.", "warning")
    else:
        flash("All students have adequate attendance (≥75%).", "info")
    
    return redirect(url_for("faculty.dashboard"))
