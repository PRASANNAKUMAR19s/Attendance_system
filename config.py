"""
CONFIG — Class Schedule, Email & System Settings
=================================================
Edit this file to change timings, email credentials, etc.
Environment variables (via .env) override these defaults.
"""

import os
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

# ── Web Application ────────────────────────────────────────────────────────────
DATABASE_PATH       = os.environ.get("DATABASE_PATH", "attendance_web.db")
UPLOAD_FOLDER       = os.environ.get("UPLOAD_FOLDER", "dataset")
MAX_CONTENT_LENGTH  = 16 * 1024 * 1024   # 16 MB max file upload
ALLOWED_EXTENSIONS  = {"png", "jpg", "jpeg", "gif"}
WEB_PORT            = int(os.environ.get("WEB_PORT", 5000))
PHOTOS_PER_STUDENT  = 13   # number of angles captured during registration

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
EMAIL_SENDER        = os.environ.get("EMAIL_SENDER",   "your_email@gmail.com")
EMAIL_PASSWORD      = os.environ.get("EMAIL_PASSWORD", "your_app_password")
TUTOR_EMAIL         = os.environ.get("TUTOR_EMAIL",    "tutor_email@gmail.com")
HOD_EMAIL           = os.environ.get("HOD_EMAIL",      "hod_email@gmail.com")

# ── Department Info (for report header) ───────────────────────────────────────
COLLEGE_NAME        = os.environ.get("COLLEGE_NAME", "Paavai Engineering College (Autonomous)")
DEPARTMENT          = os.environ.get("DEPARTMENT",   "Artificial Intelligence & Data Science")
TUTOR_NAME          = os.environ.get("TUTOR_NAME",   "MR.M.SATHYA SUNDARAM")
HOD_NAME            = os.environ.get("HOD_NAME",     "DR.A.MANIKANDAN")

# ── Paths ──────────────────────────────────────────────────────────────────────
CASCADE_PATH        = "haarcascade/haarcascade_frontalface_default.xml"
TRAINER_FILE        = "trainer/trainer.yml"
NAME_MAP            = "name_map.csv"
ATTENDANCE_DIR      = "attendance"
REPORTS_DIR         = "reports"
LATE_REASONS_FILE   = "late_reasons.csv"
STUDENTS_FILE       = "students.csv"
DATASET_DIR         = "dataset"

# ── Face Recognition ──────────────────────────────────────────────────────────
CONFIDENCE_THRESHOLD = int(os.environ.get("CONFIDENCE_THRESHOLD", 70))
MIN_FACE_SIZE        = (60, 60)

# ── API / Web Security ─────────────────────────────────────────────────────────
SECRET_KEY          = os.environ.get("SECRET_KEY",      "change-me-in-production-use-strong-random-key")
JWT_SECRET_KEY      = os.environ.get("JWT_SECRET_KEY",  "change-jwt-secret-in-production")
TUTOR_USERNAME      = os.environ.get("TUTOR_USERNAME",  "tutor")
TUTOR_PASSWORD_HASH = os.environ.get("TUTOR_PASSWORD_HASH", "")   # bcrypt hash; empty = use plain fallback

# ── Firebase ──────────────────────────────────────────────────────────────────
FIREBASE_CREDENTIALS_PATH  = os.environ.get("FIREBASE_CREDENTIALS_PATH", "serviceAccountKey.json")
FIREBASE_STORAGE_BUCKET     = os.environ.get("FIREBASE_STORAGE_BUCKET",  "")
USE_FIREBASE                = os.environ.get("USE_FIREBASE", "false").lower() == "true"

# ── Attendance thresholds ──────────────────────────────────────────────────────
DEFAULTER_THRESHOLD = int(os.environ.get("DEFAULTER_THRESHOLD", 75))
