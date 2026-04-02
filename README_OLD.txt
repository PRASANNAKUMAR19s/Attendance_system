╔══════════════════════════════════════════════════════════════════╗
║      AUTOMATED STUDENT ATTENDANCE MONITORING SYSTEM              ║
║      Paavai Engineering College — AI & Data Science             ║
╚══════════════════════════════════════════════════════════════════╝

PROJECT TEAM:
  Afzal G | Pavithra P | Prasannakumar S | Shuruthihaa S

TECH STACK:
  Python | OpenCV | LBPH Face Recognition | Pandas | Matplotlib

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ★  QUICK START GUIDE  ★

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 0 — Install Python Libraries
──────────────────────────────────
Open terminal / command prompt in this folder and run:

    pip install -r requirements.txt

(If you get errors, try: pip install --upgrade pip first)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 1 — Collect Student Face Data
────────────────────────────────────
Run for EACH student (one at a time):

    python 1_dataset_collector.py

  → Enter the student's Roll Number (e.g., 21CS001)
  → Enter the student's Name
  → Look at the webcam — it captures 50 photos automatically
  → Repeat for ALL students before training

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 2 — Train the AI Model
─────────────────────────────
After collecting data for ALL students, run:

    python 2_train_model.py

  → This trains the LBPH face recognition model
  → Saves model to: trainer/trainer.yml
  → Re-run this whenever you add a new student

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 3 — Start Attendance System (Main Program)
─────────────────────────────────────────────────
Run this every day to mark attendance:

    python 3_face_recognition.py

  → Opens webcam with live face detection
  → Automatically marks Present when face is recognized
  → Saves to: attendance/attendance_YYYY-MM-DD.csv
  → Press 'S' to see today's summary in terminal
  → Press 'Q' to quit

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 4 — Generate Reports & Charts
─────────────────────────────────────
    python 4_attendance_report.py

  → Reads all attendance CSVs
  → Shows attendance % for each student
  → Identifies defaulters (below 75%)
  → Saves chart: attendance_report.png
  → Saves defaulters list: defaulters_list.csv

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  FOLDER STRUCTURE

  attendance_system/
  ├── 1_dataset_collector.py     ← Step 1: Collect face images
  ├── 2_train_model.py           ← Step 2: Train AI model
  ├── 3_face_recognition.py      ← Step 3: Live attendance
  ├── 4_attendance_report.py     ← Step 4: Reports & charts
  ├── requirements.txt           ← Python libraries list
  ├── students.csv               ← Auto-created: student names
  ├── attendance_report.png      ← Auto-created: chart image
  ├── defaulters_list.csv        ← Auto-created: defaulters
  ├── dataset/                   ← Auto-populated: face images
  ├── trainer/                   ← Auto-populated: trained model
  ├── attendance/                ← Auto-populated: daily CSVs
  └── haarcascade/               ← Auto-populated: cascade XML

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  TROUBLESHOOTING

  ❌ "Cannot open webcam"
     → Make sure no other app is using your camera
     → Try changing VideoCapture(0) to VideoCapture(1)

  ❌ "No module named cv2"
     → Run: pip install opencv-contrib-python

  ❌ Face not recognized / shows Unknown
     → Ensure good lighting
     → Collect more images (run Step 1 again for that student)
     → Lower CONFIDENCE_THRESHOLD in 3_face_recognition.py (try 85)

  ❌ "No images found in /dataset/"
     → Run Step 1 first before Step 2

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  REQUIREMENTS

  Python 3.8 or above
  Webcam (built-in or USB)
  Windows / Linux / macOS

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
