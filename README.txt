╔══════════════════════════════════════════════════════════════════╗
║      AUTOMATED STUDENT ATTENDANCE MONITORING SYSTEM  v2.0        ║
║      Paavai Engineering College — AI & Data Science             ║
╚══════════════════════════════════════════════════════════════════╝

PROJECT TEAM:
  Afzal G | Pavithra P | Prasannakumar S | Shuruthihaa S

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  CLASS SCHEDULE (auto-configured)

  Period 1 : 9:15 AM  → Late after 9:25 AM
  Period 2 : 10:10 AM → Late after 10:20 AM
  Break    : 11:05 AM - 11:15 AM
  Period 3 : 11:15 AM → Late after 11:25 AM
  Period 4 : 12:10 PM → Late after 12:20 PM
  Lunch    : 1:00 PM  - 2:00 PM
  Period 5 : 2:00 PM  → Late after 2:10 PM
  Period 6 : 2:50 PM  → Late after 3:00 PM
  Period 7 : 3:40 PM  → Late after 3:50 PM

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ★  SETUP BEFORE FIRST RUN  ★

1. Install libraries:
   pip install -r requirements.txt

2. Edit config.py:
   - Add your Gmail and App Password
   - Add Tutor and HOD email addresses

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ★  DAILY WORKFLOW  ★

STEP 1 — Register each student (once only):
  python 1_dataset_collector.py

STEP 2 — Train model (after all students registered):
  python 2_train_model.py

STEP 3 — Run attendance (every day):
  python 3_face_recognition.py
  → Marks ON TIME / LATE / ABSENT automatically per period

STEP 4 — Tutor manages late comers:
  python 5_tutor_portal.py
  → Add reason → changes LATE to Present(Reason)

STEP 5 — Send report to Tutor & HOD:
  python 6_send_report.py
  → Generates PDF + emails it

STEP 6 — View analytics:
  python 4_attendance_report.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ATTENDANCE STATUS CODES

  ON_TIME         → Entered before grace period ends
  LATE            → Entered after grace period
  Present(Reason) → Late but tutor approved reason
  Absent          → Not detected during entire period

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  FOLDER STRUCTURE

  attendance_system/
  ├── config.py                ← ⚙️  All settings here
  ├── 1_dataset_collector.py
  ├── 2_train_model.py
  ├── 3_face_recognition.py   ← ⭐ Smart period-based marking
  ├── 4_attendance_report.py
  ├── 5_tutor_portal.py       ← ⭐ Tutor manages late comers
  ├── 6_send_report.py        ← ⭐ PDF + Email to Tutor & HOD
  ├── requirements.txt
  ├── students.csv            ← auto-created
  ├── name_map.csv            ← auto-created
  ├── late_reasons.csv        ← auto-created
  ├── dataset/                ← student face folders
  ├── trainer/                ← trained model
  ├── attendance/             ← daily CSV files
  ├── haarcascade/            ← cascade XML
  └── reports/                ← generated PDF reports

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
