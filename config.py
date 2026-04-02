"""
CONFIG — Class Schedule, Email & System Settings
=================================================
Edit this file to change timings, email credentials, etc.
"""

# ── Class Periods ──────────────────────────────────────────────────────────────
# Format: ("Period Name", "HH:MM start", "HH:MM late after", "HH:MM end")
PERIODS = [
    ("Period 1",  "09:15", "09:25", "10:10"),
    ("Period 2",  "10:10", "10:20", "11:05"),
    # Break: 11:05 - 11:15 (no attendance)
    ("Period 3",  "11:15", "11:25", "12:10"),
    ("Period 4",  "12:10", "12:20", "13:00"),
    # Lunch: 13:00 - 14:00 (no attendance)
    ("Period 5",  "14:00", "14:10", "14:50"),
    ("Period 6",  "14:50", "15:00", "15:40"),
    ("Period 7",  "15:40", "15:50", "16:30"),
]

# ── Email Settings ─────────────────────────────────────────────────────────────
EMAIL_SENDER        = "your_email@gmail.com"       # ← change this
EMAIL_PASSWORD      = "your_app_password"           # ← Gmail App Password
TUTOR_EMAIL         = "tutor_email@gmail.com"       # ← change this
HOD_EMAIL           = "hod_email@gmail.com"         # ← change this

# ── Department Info (for report header) ───────────────────────────────────────
COLLEGE_NAME        = "Paavai Engineering College (Autonomous)"
DEPARTMENT          = "Artificial Intelligence & Data Science"
TUTOR_NAME          = "MR.M.SATHYA SUNDARAM"
HOD_NAME            = "DR.A.MANIKANDAN"

# ── Paths ──────────────────────────────────────────────────────────────────────
CASCADE_PATH        = "haarcascade/haarcascade_frontalface_default.xml"
TRAINER_FILE        = "trainer/trainer.yml"
NAME_MAP            = "name_map.csv"
ATTENDANCE_DIR      = "attendance"
REPORTS_DIR         = "reports"
LATE_REASONS_FILE   = "late_reasons.csv"
STUDENTS_FILE       = "students.csv"

# ── Face Recognition ──────────────────────────────────────────────────────────
CONFIDENCE_THRESHOLD = 70
MIN_FACE_SIZE        = (60, 60)
