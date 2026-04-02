"""
STEP 6 — Daily Attendance Report (PDF + Email)
===============================================
Generates a professional PDF report and emails it
to Tutor and HOD.

HOW TO RUN:
    python 6_send_report.py

SETUP:
    1. Edit config.py with your Gmail and recipients
    2. Enable Gmail App Password:
       → Google Account → Security → 2-Step Verification → App Passwords
"""

import csv
import os
import smtplib
import glob
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from config import (
    EMAIL_SENDER, EMAIL_PASSWORD, TUTOR_EMAIL, HOD_EMAIL,
    ATTENDANCE_DIR, REPORTS_DIR, LATE_REASONS_FILE,
    COLLEGE_NAME, DEPARTMENT, TUTOR_NAME, HOD_NAME, PERIODS
)

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph,
        Spacer, HRFlowable
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB = True
except ImportError:
    REPORTLAB = False
    print("[WARNING] reportlab not installed. Install with: pip install reportlab")

# ── Font constants ────────────────────────────────────────────────────────────
F_NORMAL = "Times-Roman"
F_BOLD   = "Times-Bold"
F_ITALIC = "Times-Italic"

# ── Load attendance for a date ────────────────────────────────────────────────
def load_records(date_str):
    path = os.path.join(ATTENDANCE_DIR, f"attendance_{date_str}.csv")
    if not os.path.isfile(path):
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f))

# ── Load late reasons ─────────────────────────────────────────────────────────
def load_reasons(date_str):
    reasons = {}
    if not os.path.isfile(LATE_REASONS_FILE):
        return reasons
    with open(LATE_REASONS_FILE, newline="") as f:
        for row in csv.DictReader(f):
            if row["Date"] == date_str:
                key = f"{row['RegNo']}_{row['Period']}"
                reasons[key] = row["Reason"]
    return reasons

# ── Calculate per-student stats ───────────────────────────────────────────────
def calculate_stats(records):
    students     = {}
    period_names = [p[0] for p in PERIODS]
    for row in records:
        reg = row["RegNo"]
        if reg not in students:
            students[reg] = {"name": row["Name"], "periods": {}}
        students[reg]["periods"][row["Period"]] = row["Status"]
    return students, period_names

# ── Generate PDF ──────────────────────────────────────────────────────────────
def generate_pdf(date_str):
    if not REPORTLAB:
        print("[ERROR] Install reportlab: pip install reportlab")
        return None

    os.makedirs(REPORTS_DIR, exist_ok=True)
    pdf_path = os.path.join(REPORTS_DIR, f"attendance_report_{date_str}.pdf")

    records = load_records(date_str)
    reasons = load_reasons(date_str)

    if not records:
        print(f"[ERROR] No attendance records for {date_str}")
        return None

    students, period_names = calculate_stats(records)

    doc    = SimpleDocTemplate(pdf_path, pagesize=A4,
                               topMargin=1.5*cm, bottomMargin=1.5*cm,
                               leftMargin=1.5*cm, rightMargin=1.5*cm)
    styles = getSampleStyleSheet()
    story  = []

    # ── Header ────────────────────────────────────────────────────────────────
    title_style = ParagraphStyle(
        "title", parent=styles["Title"],
        fontName=F_BOLD,
        fontSize=15, textColor=colors.HexColor("#1a237e"),
        alignment=TA_CENTER, spaceAfter=4
    )
    sub_style = ParagraphStyle(
        "sub", parent=styles["Normal"],
        fontName=F_NORMAL,
        fontSize=10, textColor=colors.HexColor("#37474f"),
        alignment=TA_CENTER, spaceAfter=2
    )
    story.append(Paragraph(COLLEGE_NAME, title_style))
    story.append(Paragraph(f"Department of {DEPARTMENT}", sub_style))
    story.append(Paragraph("Daily Attendance Report", sub_style))
    story.append(HRFlowable(width="100%", thickness=2,
                             color=colors.HexColor("#1a237e")))
    story.append(Spacer(1, 0.3*cm))

    # ── Date & Info ───────────────────────────────────────────────────────────
    date_obj    = datetime.strptime(date_str, "%Y-%m-%d")
    date_pretty = date_obj.strftime("%d %B %Y (%A)")
    info_data   = [
        ["Date:", date_pretty, "Tutor:", TUTOR_NAME],
        ["Total Students:", str(len(students)), "HOD:", HOD_NAME],
    ]
    info_table = Table(info_data, colWidths=[3*cm, 7*cm, 2.5*cm, 5*cm])
    info_table.setStyle(TableStyle([
        ("FONTNAME",      (0, 0), (-1, -1), F_NORMAL),
        ("FONTNAME",      (0, 0), (0, -1),  F_BOLD),
        ("FONTNAME",      (2, 0), (2, -1),  F_BOLD),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("TEXTCOLOR",     (0, 0), (0, -1),  colors.HexColor("#1a237e")),
        ("TEXTCOLOR",     (2, 0), (2, -1),  colors.HexColor("#1a237e")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.4*cm))

    # ── Summary Stats ─────────────────────────────────────────────────────────
    total   = len(students)
    on_time = sum(1 for r in records if r["Status"] == "ON_TIME")
    late    = sum(1 for r in records if r["Status"] == "LATE")
    absent  = sum(1 for r in records if r["Status"] == "Absent")
    excused = sum(1 for r in records if r["Status"] == "Present(Reason)")

    stat_data = [
        ["Total Students", "On Time", "Late", "Absent", "Excused"],
        [str(total), str(on_time), str(late), str(absent), str(excused)],
    ]
    stat_colors = [
        colors.HexColor("#e8eaf6"),
        colors.HexColor("#1a237e"),
        colors.HexColor("#e65100"),
        colors.HexColor("#b71c1c"),
        colors.HexColor("#1b5e20"),
    ]
    stat_table = Table(stat_data, colWidths=[3.8*cm]*5)
    stat_style = TableStyle([
        ("ALIGN",          (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME",       (0, 0), (-1, 0),  F_BOLD),
        ("FONTSIZE",       (0, 0), (-1, 0),  9),
        ("FONTNAME",       (0, 1), (-1, 1),  F_BOLD),
        ("FONTSIZE",       (0, 1), (-1, 1),  14),
        ("ROWBACKGROUNDS", (0, 0), (-1, 0),  [colors.HexColor("#c5cae9")]),
        ("GRID",           (0, 0), (-1, -1), 0.5, colors.white),
        ("TOPPADDING",     (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 6),
    ])
    for i, c in enumerate(stat_colors):
        stat_style.add("TEXTCOLOR", (i, 1), (i, 1), c)
    stat_table.setStyle(stat_style)
    story.append(stat_table)
    story.append(Spacer(1, 0.5*cm))

    # ── Period-wise Attendance Table ──────────────────────────────────────────
    story.append(Paragraph("Period-wise Attendance", ParagraphStyle(
        "section", parent=styles["Heading2"],
        fontName=F_BOLD,
        fontSize=11, textColor=colors.HexColor("#1a237e"), spaceAfter=6
    )))

    header    = ["Reg No", "Student Name"] + period_names
    col_w     = [2.8*cm, 4.5*cm] + [1.8*cm] * len(period_names)
    table_data = [header]

    for reg, info in sorted(students.items()):
        row = [reg, info["name"]]
        for p in period_names:
            s = info["periods"].get(p, "—")
            if s == "ON_TIME":           s = "✓"
            elif s == "LATE":            s = "L"
            elif s == "Absent":          s = "A"
            elif s == "Present(Reason)": s = "P*"
            row.append(s)
        table_data.append(row)

    att_table = Table(table_data, colWidths=col_w, repeatRows=1)
    att_table.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0),  colors.HexColor("#1a237e")),
        ("TEXTCOLOR",      (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",       (0, 0), (-1, 0),  F_BOLD),
        ("FONTNAME",       (0, 1), (-1, -1), F_NORMAL),
        ("FONTSIZE",       (0, 0), (-1, -1), 8),
        ("ALIGN",          (0, 0), (-1, -1), "CENTER"),
        ("ALIGN",          (1, 1), (1, -1),  "LEFT"),
        ("GRID",           (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f5f5f5")]),
        ("TOPPADDING",     (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 4),
    ]))
    story.append(att_table)
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph(
        "Legend: ✓ = On Time | L = Late | A = Absent | P* = Present with Reason",
        ParagraphStyle("legend", parent=styles["Normal"],
                       fontName=F_ITALIC,
                       fontSize=8, textColor=colors.HexColor("#607d8b"))
    ))
    story.append(Spacer(1, 0.5*cm))

    # ── Absent Students Table ─────────────────────────────────────────────────
    absent_list = [r for r in records if r["Status"] == "Absent"]
    if absent_list:
        story.append(Paragraph("Absent Students", ParagraphStyle(
            "section2", parent=styles["Heading2"],
            fontName=F_BOLD,
            fontSize=11, textColor=colors.HexColor("#b71c1c"), spaceAfter=6
        )))
        ab_data = [["Reg No", "Name", "Period", "Action Required"]]
        for r in absent_list:
            ab_data.append([r["RegNo"], r["Name"], r["Period"], "Inform Parents"])
        ab_table = Table(ab_data, colWidths=[3*cm, 5*cm, 3*cm, 6*cm])
        ab_table.setStyle(TableStyle([
            ("BACKGROUND",     (0, 0), (-1, 0),  colors.HexColor("#b71c1c")),
            ("TEXTCOLOR",      (0, 0), (-1, 0),  colors.white),
            ("FONTNAME",       (0, 0), (-1, 0),  F_BOLD),
            ("FONTNAME",       (0, 1), (-1, -1), F_NORMAL),
            ("FONTSIZE",       (0, 0), (-1, -1), 9),
            ("GRID",           (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.HexColor("#ffebee"), colors.white]),
            ("TOPPADDING",     (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING",  (0, 0), (-1, -1), 5),
        ]))
        story.append(ab_table)
        story.append(Spacer(1, 0.5*cm))

    # ── Late Comer Reasons Table ──────────────────────────────────────────────
    if reasons:
        story.append(Paragraph("Late Comer Reasons (Tutor Verified)", ParagraphStyle(
            "section3", parent=styles["Heading2"],
            fontName=F_BOLD,
            fontSize=11, textColor=colors.HexColor("#e65100"), spaceAfter=6
        )))
        re_data = [["Reg No", "Name", "Period", "Reason"]]
        for key, reason_text in reasons.items():
            reg, period = key.split("_", 1)
            name = students.get(reg, {}).get("name", "Unknown")
            re_data.append([reg, name, period, reason_text])
        re_table = Table(re_data, colWidths=[2.5*cm, 4*cm, 3*cm, 7.5*cm])
        re_table.setStyle(TableStyle([
            ("BACKGROUND",     (0, 0), (-1, 0),  colors.HexColor("#e65100")),
            ("TEXTCOLOR",      (0, 0), (-1, 0),  colors.white),
            ("FONTNAME",       (0, 0), (-1, 0),  F_BOLD),
            ("FONTNAME",       (0, 1), (-1, -1), F_NORMAL),
            ("FONTSIZE",       (0, 0), (-1, -1), 9),
            ("GRID",           (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.HexColor("#fff3e0"), colors.white]),
            ("TOPPADDING",     (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING",  (0, 0), (-1, -1), 5),
        ]))
        story.append(re_table)
        story.append(Spacer(1, 0.5*cm))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1,
                             color=colors.HexColor("#1a237e")))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        f"Generated on {datetime.now().strftime('%d %B %Y at %I:%M %p')} "
        f"by Automated Attendance Monitoring System",
        ParagraphStyle("footer", parent=styles["Normal"],
                       fontName=F_ITALIC,
                       fontSize=8, textColor=colors.HexColor("#90a4ae"),
                       alignment=TA_CENTER)
    ))

    doc.build(story)
    print(f"[SAVED] PDF Report → {pdf_path}")
    return pdf_path

# ── Send Email ────────────────────────────────────────────────────────────────
def send_email(pdf_path, date_str, recipients):
    if not os.path.isfile(pdf_path):
        print("[ERROR] PDF not found. Generate it first.")
        return

    date_obj    = datetime.strptime(date_str, "%Y-%m-%d")
    date_pretty = date_obj.strftime("%d %B %Y")
    records     = load_records(date_str)
    on_time     = sum(1 for r in records if r["Status"] == "ON_TIME")
    late        = sum(1 for r in records if r["Status"] == "LATE")
    absent      = sum(1 for r in records if r["Status"] == "Absent")
    total       = len(set(r["RegNo"] for r in records))

    subject = f"Daily Attendance Report — {date_pretty} | {DEPARTMENT}"
    body    = f"""Dear {TUTOR_NAME} / {HOD_NAME},

Please find attached the Daily Attendance Report for {date_pretty}.

SUMMARY:
  Department     : {DEPARTMENT}
  Total Students : {total}
  On Time        : {on_time}
  Late Comers    : {late}
  Absent         : {absent}

Please review the attached PDF for the complete period-wise breakdown.

This is an auto-generated report from the AI Attendance Monitoring System.

Regards,
Automated Attendance System
{COLLEGE_NAME}
"""
    try:
        msg            = MIMEMultipart()
        msg["From"]    = EMAIL_SENDER
        msg["To"]      = ", ".join(recipients)
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with open(pdf_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition",
                        f"attachment; filename={os.path.basename(pdf_path)}")
        msg.attach(part)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, recipients, msg.as_string())

        print(f"[SENT] Email sent to: {', '.join(recipients)}")

    except smtplib.SMTPAuthenticationError:
        print("[ERROR] Gmail authentication failed.")
        print("        Use Gmail App Password in config.py (not your normal password)")
    except Exception as e:
        print(f"[ERROR] Email failed: {e}")

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("\n" + "═" * 50)
    print("       ATTENDANCE REPORT — PDF + EMAIL SENDER")
    print("═" * 50)

    print("\nEnter date (YYYY-MM-DD) or press Enter for today: ", end="")
    date_input = input().strip()
    date_str   = date_input if date_input else datetime.now().strftime("%Y-%m-%d")

    print("\n  1. Generate PDF only")
    print("  2. Generate PDF + Send Email to Tutor & HOD")
    print("  3. Send existing PDF via Email only")
    print("\n  Choose (1-3): ", end="")

    try:
        choice = int(input().strip())
    except ValueError:
        print("[ERROR] Invalid choice.")
        return

    pdf_path = os.path.join(REPORTS_DIR, f"attendance_report_{date_str}.pdf")

    if choice == 1:
        generate_pdf(date_str)
    elif choice == 2:
        pdf = generate_pdf(date_str)
        if pdf:
            send_email(pdf, date_str, [TUTOR_EMAIL, HOD_EMAIL])
    elif choice == 3:
        if not os.path.isfile(pdf_path):
            print(f"[ERROR] PDF not found: {pdf_path}")
            print("        Run option 1 first.")
        else:
            send_email(pdf_path, date_str, [TUTOR_EMAIL, HOD_EMAIL])
    else:
        print("[ERROR] Enter 1, 2, or 3.")


if __name__ == "__main__":
    main()