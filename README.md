# 🎓 AI-Powered Attendance System

[![CI/CD Pipeline](https://github.com/PRASANNAKUMAR19s/Attendance_system/actions/workflows/ci.yml/badge.svg)](https://github.com/PRASANNAKUMAR19s/Attendance_system/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1-green)](https://flask.palletsprojects.com)

Automated Student Attendance Monitoring System using **Face Recognition (LBPH + Deep Learning)**, **OpenCV**, **AI Analytics**, **REST API**, **Firebase**, **Docker**, and a modern web portal.

The system automatically detects and recognizes student faces in real time, records attendance, performs behavior analysis, identifies attendance irregularities, generates reports, and sends real-time SMS/Email notifications to parents and faculty members.

---

# **Objectives**

- Automate student attendance using robust face recognition (LBPH + deep learning).
- Support partial-face recognition (masks, occlusion) using landmark heuristics and model-based embeddings.
- Detect and manage late comers automatically, with tutor/HOD workflows for verification.
- Provide real-time SMS/Email notifications to parents, tutors and administrative staff.
- Generate daily attendance reports (PDF/CSV) and analytics dashboards; persist data to Firebase when enabled.


# **Modules**

- Face Recognition Module (LBPH + optional Deep Learning)
- Partial Face Recognition Module (eyes / nose / facial geometry heuristics)
- Attendance Marking Module (ON_TIME / LATE / PRESENT_PARTIAL / ABSENT)
- Late Comer Detection Module
- Notification Module (Email + SMS gateway, e.g., Twilio)
- Report Generation Module (PDF / charts / CSV)
- REST API & Web Portal (Tutor / Student views)
- Firebase Integration (optional)


# **Proposed System / Flow**

Classroom webcam → Face detection & recognition (LBPH / DL) → If full match, mark ON_TIME/PRESENT; if partial landmarks detected, mark PRESENT_PARTIAL → If detected after grace period mark LATE → Missing detections after period end marked ABSENT (auto) → Notification Module sends SMS/Email to Parents / Tutor / HOD → Reports archived in `attendance/` and `reports/`, optionally synced to Firebase.


# **Advantages**

- Real-Time Parent Notification
- Late Comer Monitoring and Management
- Partial Face Recognition Support (masks/occlusion)
- Improved Attendance Security and Audit Trail
- Automated Reports and Analytics


# **PPT Features (for slide updates)**

- Slide 6 (Modules): Add Notification Module, Late Comer Detection Module, Partial Face Recognition Module
- Slide 7 (System Architecture): Add SMS Gateway, Email Notification Module, Late Comer Detection, Partial Face Recognition
- Slide 12 (Advantages): Add Real-Time Parent Notification; Late Comer Monitoring; Partial Face Recognition Support; Improved Attendance Security


# **Results**

- The system produces daily Present / Absent / Late lists and generates defaulter reports.
- Notifications are sent automatically for Present, Absent, and Late events.
- Partial recognitions are recorded as `PRESENT_PARTIAL` and included in reports and analytics.
- Data and reports are available in `attendance/` and `reports/`, and can be synced to Firebase when enabled.

# 🚀 Features

| Feature | Status |
|---------|--------|
| Face Recognition (LBPH) | ✅ |
| Deep Learning Face Recognition | ✅ |
| Real-time attendance marking | ✅ |
| Period-wise tracking (7 periods) | ✅ |
| Late detection with grace period | ✅ |
| Partial Face Recognition (mask/occlusion support) | ✅ |
| AI-Based Student Behavior Analysis | ✅ |
| High Priority Attendance Alerts | ✅ |
| Smart Attendance Notification System | ✅ |
| Automated Present / Absent / OD Reports | ✅ |
| HOD / Tutor Alert System | ✅ |
| SMS Notifications (optional Twilio) | ✅ |
| REST API with Swagger docs | ✅ |
| JWT authentication | ✅ |
| Firebase Firestore backend | ✅ |
| Firebase Storage for face images | ✅ |
| Docker containerisation | ✅ |
| CI/CD with GitHub Actions | ✅ |
| Rate limiting & security headers | ✅ |
| bcrypt password hashing | ✅ |
| CSV → Firebase migration script | ✅ |
| Attendance reports (PDF + charts) | ✅ |
| Web portal (Tutor + Student) | ✅ |
| Email reports to Tutor / HOD | ✅ |
| Unit & integration tests | ✅ |

---

# 🏗️ Architecture

```text
┌─────────────────────────────────────────────────────────────────────┐
│                         Attendance System                           │
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌────────────────────┐   │
│  │  Camera /    │    │  REST API    │    │   Web Portal       │   │
│  │  OpenCV      │───▶│  (app.py)    │◀──▶│  Bootstrap 5 UI    │   │
│  │  AI Recog.   │    │ JWT+Swagger  │    │  Tutor + Student   │   │
│  └──────────────┘    └──────┬───────┘    └────────────────────┘   │
│                             │                                       │
│                    ┌────────▼────────┐                              │
│                    │ FirebaseService │                              │
│                    └────────┬────────┘                              │
│                             │                                       │
│              ┌──────────────┴──────────────┐                       │
│    ┌─────────▼──────┐          ┌──────────▼────────┐              │
│    │ Firebase        │          │  Local CSV files   │              │
│    │ Firestore /     │          │  Offline Storage   │              │
│    │ Storage / Auth  │          │                     │              │
│    └────────────────┘          └───────────────────┘               │
└─────────────────────────────────────────────────────────────────────┘
```

---

# 🧠 Deep Learning Face Recognition

The system integrates Deep Learning-based Face Recognition techniques to improve recognition accuracy and intelligent facial analysis.

### Capabilities
- Detect faces under different lighting conditions
- Handle mask and partial face recognition
- Analyze multiple face angles and expressions
- Improve recognition accuracy dynamically
- Support real-time intelligent facial analysis

### Deep Learning Operations
1. Capture student image
2. Preprocess image using OpenCV
3. Extract facial embeddings using CNN
4. Compare embeddings with trained dataset
5. Identify student accurately
6. Record attendance automatically

### Technologies Used
- TensorFlow
- CNN (Convolutional Neural Networks)
- OpenCV DNN Module
- Keras

---

# 🤖 AI-Based Student Behavior Analysis

The system continuously monitors student attendance behavior and classroom activity patterns using AI-based analytics.

### Features
- Continuous absence detection
- Late comer frequency monitoring
- Attendance irregularity tracking
- Student activity analysis
- Attendance trend monitoring
- Classroom behavior observation

### High Priority Alert System

If a student remains absent for a long duration and suddenly attends class again, the system automatically generates a HIGH ALERT notification.

The alert is sent to:
- Tutor
- HOD
- Attendance Management Staff

### Example Alert
"Warning: Student attendance irregularity detected. Immediate academic monitoring recommended."

---

# 📩 Smart Attendance Notification System

The system automatically sends:
- Present notifications
- Absent notifications
- OD updates
- Late comer alerts
- Attendance irregularity alerts

### Notification Recipients
- Parents
- Tutor
- HOD
- Attendance Management Staff

---

## ✅ Present Student Notification

When a student is detected through the webcam and attendance is marked successfully, an automatic notification is sent.

### Example
"Your son/daughter is present in today’s class."

---

## ✅ Absent Student Notification

If a student is not detected during attendance monitoring, the system automatically sends absence notifications to:
- Parents
- Tutor
- HOD
- Attendance Management Staff

---

## ✅ OD (On Duty) Monitoring

The system verifies approved OD students separately and updates attendance records automatically to avoid incorrect absence marking.

---

## ✅ Late Comer Detection & Alert

The system identifies students entering the classroom after the scheduled class start time.

Late comer notifications are automatically sent to:
- Parents
- Tutor
- HOD
- Attendance Management Staff

---

# 📄 Automated Attendance Report Sharing

After attendance completion, the system automatically generates attendance reports and shares them through:
- SMS
- Email
- Digital Dashboard

### Sample Attendance Report

```text
Class : AI&DS
Date : 07/01/2026
Session : Forenoon

Total No. of Students : 58
No. of Present Students : 52
No. of Absentees : 6

09. Brammavathi
18. Imayavarman
19. Jaiprakash
40. Pavithra P
49. Sanjay Aditya
54. Sriananya

No. of OD Students : 2

51. Shriram
55. Sridhar

Late Comer List : Automatically Generated
```

---

# 📊 Attendance Analytics

The system provides:
- Attendance percentage calculation
- Present/Absent analysis
- Late comer analysis
- Attendance dashboard visualization
- CSV data storage
- Graphical report generation
- Attendance trend analysis
- Student behavior reports
- Attendance prediction analytics
- Risk student identification

---

# 🚀 Quick Start

## 1. Install

```bash
git clone https://github.com/PRASANNAKUMAR19s/Attendance_system.git
cd Attendance_system
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

---

## 2. Run the Web App

```bash
python app.py
```

Open:

## Student Credentials & Notifications

- Student accounts are created by the faculty registration workflow and an email "set password" link is sent when an email is provided.
- Passwords are stored hashed with `bcrypt`. Password reset tokens are one-time and expire (configurable).
- Notifications (Email + SMS) are sent via `services/notification_service.py` which uses `services/email_service.py` and `services/sms_service.py`.
- For CI and offline runs, tests automatically mock email/SMS sends via `tests/conftest.py`.

## Running Tests in CI

- Unit and integration tests live under `tests/`. The suite avoids external network calls by mocking email and SMS in `tests/conftest.py`.
- To run tests locally:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m pytest tests -q
```

```text
http://localhost:5000
```

### Portal Login

- Tutor / HOD / admin users sign in with the normal portal login.
- Student users can sign in with their register number as both the username and password for the current demo workflow.
- After login, the app redirects automatically to the correct dashboard for that role.

### Automatic Web Workflow

Once the app is open, the main attendance flow happens from the web pages:

1. Log in as tutor, HOD, admin, or student.
2. Open the dashboard for the role.
3. Capture or review attendance records.
4. Automatically mark present, late, absent, or partial-face cases.
5. Send SMS/Email notifications when attendance events are recorded.
6. Generate reports, summaries, and defaulter lists from the portal.

The web portal is the day-to-day control center for attendance operations. Dataset collection and model training remain separate setup tasks.

---

## 3. Face Recognition Pipeline

Use these only for initial setup, dataset creation, or retraining:

```bash
python 1_dataset_collector.py
python 2_train_model.py
python 3_face_recognition.py
python 4_attendance_report.py
```

---

# 🔌 REST API

## Authentication

```bash
curl -X POST http://localhost:5000/api/auth/login \
-H "Content-Type: application/json" \
-d '{"username":"tutor","password":"paavai123"}'
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health/` | Health Check |
| POST | `/api/auth/login` | Get JWT Token |
| GET/POST | `/api/students/` | Student CRUD |
| GET/POST | `/api/attendance/` | Attendance Operations |
| GET | `/api/attendance/today` | Today Attendance |
| GET | `/api/reports/summary` | Summary Report |
| GET | `/api/analytics/overview` | Attendance Analytics |

---

# 🔥 Firebase Setup

1. Create Firebase Project
2. Enable Firestore & Storage
3. Download `serviceAccountKey.json`
4. Configure `.env`
5. Run migration script

```bash
python migrate_to_firebase.py
```

---

# 🐳 Docker Deployment

```bash
docker compose up --build
docker compose down
```

---

# ☁️ Cloud Deployment

## Render.com

```bash
Build Command:
pip install -r requirements.txt
```

```bash
Start Command:
gunicorn -w 4 -b 0.0.0.0:$PORT app:app
```

---

# ⚙️ Configuration

| Variable | Description |
|----------|-------------|
| SECRET_KEY | Flask Secret Key |
| JWT_SECRET_KEY | JWT Signing Key |
| USE_FIREBASE | Enable Firebase |
| FIREBASE_STORAGE_BUCKET | Storage Bucket |
| CONFIDENCE_THRESHOLD | Recognition Accuracy |
| DEFAULTER_THRESHOLD | Minimum Attendance % |

---

# 🧪 Testing

```bash
pytest tests/ -v
```

---

# 🔐 Security Features

- JWT Authentication
- bcrypt Password Hashing
- Rate Limiting
- Security Headers
- Firebase Security Rules
- Input Validation
- Non-root Docker User

---

# 📁 Project Structure

```text
Attendance_system/
├── app.py
├── firebase_service.py
├── config.py
├── migrate_to_firebase.py
├── 1_dataset_collector.py
├── 2_train_model.py
├── 3_face_recognition.py
├── 4_attendance_report.py
├── 5_tutor_portal.py
├── 6_send_report.py
├── 7_student_portal.py
├── 8_web_portal.py
├── 9_behavior_analysis.py
├── 10_notification_system.py
├── 11_deepface_recognition.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── tests/
└── .github/workflows/
```

---

# 🎯 Advantages

- Reduces manual attendance workload
- Prevents proxy attendance
- Improves attendance accuracy
- Supports Deep Learning recognition
- Supports partial face recognition
- Provides AI-based analytics
- Generates automatic reports
- Supports institutional monitoring
- Improves parent communication
- Real-time attendance alerts

---

# 🌍 Applications

- Schools
- Colleges
- Universities
- Coaching Centers
- Smart Campus Systems
- Training Institutions

---

# 🔮 Future Scope

- Mobile Application Integration
- ERP Integration
- Multi-Classroom Monitoring
- AI-Based Emotion Detection
- Smart Classroom Automation

---

# 👨‍💻 Author

**Prasannakumar S**  
Paavai Engineering College  
Department of Artificial Intelligence and Data Science

Research Intern | Face Recognition & Attendance Automation

---

# 📜 License

This project is developed for educational and research purposes.