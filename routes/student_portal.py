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

import config as _config
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
        records = svc.get_attendance(reg_no=reg_no)
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
    present = sum(1 for r in records if r.get("status") in ("Present", "Late", "ON_TIME"))
    absent = sum(1 for r in records if r.get("status") == "Absent")
    od = sum(1 for r in records if r.get("status") == "OD")
    attended = present + od
    pct = round(attended / total * 100, 1) if total > 0 else 0
    return {
        "total_classes": total,
        "present_count": present,
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
    
    # Get recent attendance - unique by date+period (deduplicated)
    seen = set()
    unique_records = []
    for r in records:
        key = (r.get("date", ""), r.get("period", ""))
        if key not in seen:
            seen.add(key)
            unique_records.append(r)
    recent_records = unique_records[:7]
    
    return render_template(
        "student_dashboard.html",
        user=user,
        reg_no=reg_no,
        recent_records=recent_records,
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
    
    # Deduplicate by date+period
    seen = set()
    unique_records = []
    for r in records:
        key = (r.get("date", ""), r.get("period", ""))
        if key not in seen:
            seen.add(key)
            unique_records.append(r)
    records = unique_records
    
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
    """Upload a signed OD letter (already signed by Tutor & HOD)."""
    import os
    from pathlib import Path
    from werkzeug.utils import secure_filename
    
    user = get_current_user()
    reg_no = session.get("username", "")
    
    od_uploads_dir = Path("od_uploads")
    od_uploads_dir.mkdir(exist_ok=True)

    if request.method == "POST":
        od_date = request.form.get("od_date", "").strip()
        reason = request.form.get("reason", "").strip()
        file = request.files.get("od_letter")
        
        if not od_date:
            flash("OD date is required.", "danger")
        elif not file or file.filename == "":
            flash("Please upload the signed OD letter.", "danger")
        else:
            # Save the uploaded file
            filename = secure_filename(f"{reg_no}_{od_date}_{file.filename}")
            filepath = od_uploads_dir / filename
            file.save(filepath)
            
            # Save metadata
            od_record = f"{reg_no},{od_date},{reason or 'OD'},{filename}\n"
            metadata_file = od_uploads_dir / "od_records.csv"
            with open(metadata_file, "a") as f:
                f.write(od_record)
            
            flash("OD letter uploaded successfully! Your attendance will be marked as OD.", "success")
            return redirect(url_for("student_portal.od_status"))
    
    # Get recent uploads
    recent_submissions = []
    metadata_file = od_uploads_dir / "od_records.csv"
    if metadata_file.exists():
        with open(metadata_file) as f:
            for line in f:
                parts = line.strip().split(",")
                if parts and parts[0] == reg_no:
                    recent_submissions.append({
                        "date": parts[1] if len(parts) > 1 else "",
                        "reason": parts[2] if len(parts) > 2 else "",
                        "file": parts[3] if len(parts) > 3 else "",
                    })
    
    return render_template(
        "student_od_upload.html",
        user=user,
        reg_no=reg_no,
        recent_submissions=recent_submissions[-5:],  # Last 5
    )


@student_portal_bp.route("/od/status")
@_student_required
def od_status():
    """View uploaded OD letters."""
    user = get_current_user()
    reg_no = session.get("username", "")
    
    od_letters = []
    metadata_file = Path("od_uploads/od_records.csv")
    if metadata_file.exists():
        with open(metadata_file) as f:
            for line in f:
                parts = line.strip().split(",")
                if parts and parts[0] == reg_no:
                    od_letters.append({
                        "date": parts[1] if len(parts) > 1 else "",
                        "reason": parts[2] if len(parts) > 2 else "OD",
                        "file": parts[3] if len(parts) > 3 else "",
                        "status": "Uploaded",  # Always uploaded since no approval needed
                    })
    
    return render_template(
        "student_od_status.html",
        user=user,
        reg_no=reg_no,
        od_letters=list(reversed(od_letters)),
    )


@student_portal_bp.route("/early-leave", methods=["GET", "POST"])
@_student_required
def early_leave():
    """Student reports early leave - sends immediate notification to Tutor & HOD."""
    user = get_current_user()
    reg_no = session.get("username", "")
    
    if request.method == "POST":
        reason = request.form.get("reason", "").strip()
        leave_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if not reason:
            flash("Please provide a reason for early leave.", "danger")
        else:
            # Send immediate notifications to Tutor and HOD
            from services.email_service import EmailService
            email_service = EmailService()
            
            # Get student info
            student = _get_student_record(reg_no)
            student_name = student.name if student else user.full_name
            
            # Save early leave record
            early_leave_file = Path("early_leaves.csv")
            with open(early_leave_file, "a") as f:
                f.write(f"{reg_no},{student_name},{leave_time},{reason}\n")
            
            # Send to Tutor
            tutor_email_sent = email_service.send_early_leave_alert(
                to_email=_config.TUTOR_EMAIL,
                student_name=student_name,
                reg_no=reg_no,
                reason=reason,
                leave_time=leave_time,
            )
            
            # Send to HOD
            hod_email_sent = email_service.send_early_leave_alert(
                to_email=_config.HOD_EMAIL,
                student_name=student_name,
                reg_no=reg_no,
                reason=reason,
                leave_time=leave_time,
            )
            
            if tutor_email_sent or hod_email_sent:
                flash("Early leave reported! Tutor and HOD have been notified.", "success")
            else:
                flash("Early leave recorded. Email notifications pending setup.", "warning")
            
            return redirect(url_for("student_portal.dashboard"))
    
    return render_template(
        "student_early_leave.html",
        user=user,
        reg_no=reg_no,
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
    from flask import make_response
    from datetime import datetime
    
    user = get_current_user()
    reg_no = session.get("username", "")
    
    # Simple text-based OD letter template
    template = f"""
═══════════════════════════════════════════════════════════════════════════════
                              ON DUTY APPLICATION
═══════════════════════════════════════════════════════════════════════════════

Date: {datetime.now().strftime('%d-%m-%Y')}

To,
The Head of Department
Department of Artificial Intelligence & Data Science
Paavai Engineering College
Namakkal - 637 018

Through,
The Class Tutor

Respected Sir/Madam,

    I, {user.full_name or '[Student Name]'} (Reg. No: {reg_no}), studying
{datetime.now().year} year in your college, request you to grant me On-Duty
leave for the following reason:

    _________________________________________________________________
    _________________________________________________________________

    Date of OD: _________________

    I shall be grateful if my request is sanctioned.

                                        Thanking You,

                                        Yours faithfully,


                                        Signature: _________________
                                        (Student)


VERIFICATION BY CLASS TUTOR                           APPROVED / NOT APPROVED

Signature: _________________                           Signature: _________________

Name: _________________                               Name: _________________

Date: _________________                                Date: _________________



APPROVED / NOT APPROVED                                REMARKS:

Signature: _________________

Name: _________________

Designation: HOD

Date: _________________

═══════════════════════════════════════════════════════════════════════════════
"""
    
    response = make_response(template)
    response.headers['Content-Type'] = 'text/plain'
    response.headers['Content-Disposition'] = f'attachment; filename=OD_Letter_Template_{reg_no}.txt'
    return response


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
    """Generate and download actual PDF attendance report."""
    from flask import make_response
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.enums import TA_CENTER

    user = get_current_user()
    reg_no = session.get("username", "")
    student = _get_student_record(reg_no)
    records = _get_attendance_records(reg_no)
    summary = _compute_summary(records)

    buffer = __import__('io').BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=16, alignment=TA_CENTER, spaceAfter=10)
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER, textColor=colors.grey)

    elements.append(Paragraph("Paavai Engineering College", title_style))
    elements.append(Paragraph("Department of Artificial Intelligence & Data Science", subtitle_style))
    elements.append(Spacer(1, 10*mm))

    student_name = student.name if student else user.full_name
    elements.append(Paragraph(f"Attendance Report - {student_name} ({reg_no})", styles['Heading2']))
    elements.append(Spacer(1, 5*mm))

    info_data = [
        ["Reg. No:", reg_no, "Name:", student_name],
        ["Department:", student.department if student else "AI&DS", "Year:", str(student.year) if student else "—"],
    ]
    info_table = Table(info_data, colWidths=[60, 120, 60, 120])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 10*mm))

    attendance_data = [["#", "Date", "Period", "Status", "Time"]]
    for i, record in enumerate(records[:50], 1):
        status = record.get("status", "")
        if status in ("ON_TIME", "PRESENT", "LATE"):
            status = "Present"
        elif status == "OD":
            status = "On Duty"
        else:
            status = "Absent"
        
        attendance_data.append([
            str(i),
            record.get("date", "-"),
            record.get("period", "-"),
            status,
            record.get("marked_time", "-"),
        ])

    table = Table(attendance_data, colWidths=[25, 70, 70, 60, 70])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 10*mm))

    attended = summary['present_count'] + summary['late_count']
    pct = round(attended / summary['total_classes'] * 100, 1) if summary['total_classes'] > 0 else 0
    
    summary_data = [
        ["Summary:", f"Total: {summary['total_classes']}", 
         f"Present: {attended}", f"Absent: {summary['absent_count']}", f"Attendance: {pct}%"]
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

    doc.build(elements)
    buffer.seek(0)

    filename = f"attendance_{reg_no}_{datetime.now().strftime('%Y-%m-%d')}.pdf"
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response
