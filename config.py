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
DATABASE_PATH = os.environ.get("DATABASE_PATH", "attendance_web.db")
UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "dataset")
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max file upload
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
WEB_PORT = int(os.environ.get("WEB_PORT") or 5000)
PHOTOS_PER_STUDENT = 13  # number of angles captured during registration

# Default plain-text password used only when TUTOR_PASSWORD_HASH is empty.
# Override with TUTOR_PASSWORD env var in production.
TUTOR_PASSWORD = os.environ.get("TUTOR_PASSWORD", "paavai123")

# ── Class Periods ──────────────────────────────────────────────────────────────
# Format: ("Period Name", "HH:MM start", "HH:MM late after", "HH:MM end")
PERIODS = [
    ("Period 1", "09:15", "09:25", "10:10"),  # 10 min grace
    ("Period 2", "10:10", "10:15", "11:05"),  # 5 min grace
    # Break: 11:05 - 11:15 (no attendance)
    ("Period 3", "11:15", "11:20", "12:10"),  # 5 min grace
    ("Period 4", "12:10", "12:15", "13:00"),  # 5 min grace
    # Lunch: 13:00 - 14:00 (no attendance)
    ("Period 5", "14:00", "14:05", "14:50"),  # 5 min grace
    ("Period 6", "14:50", "14:55", "15:40"),  # 5 min grace
    ("Period 7", "15:40", "15:45", "16:30"),  # 5 min grace
]

# ── Email Settings ─────────────────────────────────────────────────────────────
EMAIL_SENDER = os.environ.get("EMAIL_SENDER", "your_email@gmail.com")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "your_app_password")
TUTOR_EMAIL = os.environ.get("TUTOR_EMAIL", "tutor_email@gmail.com")
HOD_EMAIL = os.environ.get("HOD_EMAIL", "hod_email@gmail.com")

# ── SMS / SMS Gateway (optional — Twilio recommended) -------------------------
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER = os.environ.get("TWILIO_FROM_NUMBER", "")
# Optional flag or backup gateway URL (not used by default)
SMS_BACKUP_GATEWAY = os.environ.get("SMS_BACKUP_GATEWAY", "")
# Convenience boolean to quickly check if Twilio creds were provided
SMS_ENABLED = bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_FROM_NUMBER)

# ── Department Info (for report header) ───────────────────────────────────────
COLLEGE_NAME = os.environ.get("COLLEGE_NAME", "Paavai Engineering College (Autonomous)")
DEPARTMENT = os.environ.get("DEPARTMENT", "Artificial Intelligence & Data Science")
TUTOR_NAME = os.environ.get("TUTOR_NAME", "MR.M.SATHYA SUNDARAM")
HOD_NAME = os.environ.get("HOD_NAME", "DR.A.MANIKANDAN")

# ── Paths ──────────────────────────────────────────────────────────────────────
CASCADE_PATH = "haarcascade/haarcascade_frontalface_default.xml"
TRAINER_FILE = "trainer/trainer.yml"
NAME_MAP = "name_map.csv"
ATTENDANCE_DIR = "attendance"
REPORTS_DIR = "reports"
LATE_REASONS_FILE = "late_reasons.csv"
STUDENTS_FILE = "students.csv"
DATASET_DIR = "dataset"

# ── Face Recognition ──────────────────────────────────────────────────────────
CONFIDENCE_THRESHOLD = int(os.environ.get("CONFIDENCE_THRESHOLD") or 70)
MIN_FACE_SIZE = (60, 60)
# Enable partial face recognition processing (annotations + heuristic analysis)
PARTIAL_RECOG_ENABLED = os.environ.get("PARTIAL_RECOG_ENABLED", "true").lower() in (
    "1",
    "true",
    "yes",
)
PARTIAL_RECOG_THRESHOLD = int(os.environ.get("PARTIAL_RECOG_THRESHOLD", "60"))

# ── API / Web Security ─────────────────────────────────────────────────────────
SECRET_KEY = os.environ.get(
    "SECRET_KEY", "change-me-in-production-use-strong-random-key"
)
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "change-jwt-secret-in-production")
TUTOR_USERNAME = os.environ.get("TUTOR_USERNAME", "tutor")
TUTOR_PASSWORD_HASH = os.environ.get(
    "TUTOR_PASSWORD_HASH", ""
)  # bcrypt hash; empty = use plain fallback

# ── Firebase ──────────────────────────────────────────────────────────────────
FIREBASE_CREDENTIALS_PATH = os.environ.get(
    "FIREBASE_CREDENTIALS_PATH", "serviceAccountKey.json"
)
FIREBASE_STORAGE_BUCKET = os.environ.get("FIREBASE_STORAGE_BUCKET", "")
USE_FIREBASE = os.environ.get("USE_FIREBASE", "false").lower() == "true"

# Build credentials from individual env vars (used on Render)
FIREBASE_PROJECT_ID = os.environ.get("FIREBASE_PROJECT_ID", "")
FIREBASE_PRIVATE_KEY = os.environ.get("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n")
FIREBASE_CLIENT_EMAIL = os.environ.get("FIREBASE_CLIENT_EMAIL", "")

# ── Attendance thresholds ──────────────────────────────────────────────────────
DEFAULTER_THRESHOLD = int(os.environ.get("DEFAULTER_THRESHOLD") or 75)
