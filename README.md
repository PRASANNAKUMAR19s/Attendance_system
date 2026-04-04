# 🎓 AI-Powered Attendance System

[![CI/CD Pipeline](https://github.com/PRASANNAKUMAR19s/Attendance_system/actions/workflows/ci.yml/badge.svg)](https://github.com/PRASANNAKUMAR19s/Attendance_system/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1-green)](https://flask.palletsprojects.com)

Automated Student Attendance Monitoring System using **Face Recognition (LBPH)** + **OpenCV**, with a production-ready **REST API**, **Firebase** integration, **Docker** support, and a modern web portal.

---

## ✨ Features

| Feature | Status |
|---------|--------|
| Face Recognition (LBPH) | ✅ |
| Real-time attendance marking | ✅ |
| Period-wise tracking (7 periods) | ✅ |
| Late detection with grace period | ✅ |
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

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Attendance System                           │
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌────────────────────┐   │
│  │  Camera /    │    │  REST API    │    │   Web Portal       │   │
│  │  OpenCV      │───▶│  (api.py)    │◀──▶│  (8_web_portal.py) │   │
│  │  Face Recog. │    │  JWT+Swagger  │    │  Bootstrap 5 UI    │   │
│  └──────────────┘    └──────┬───────┘    └────────────────────┘   │
│                             │                                       │
│                    ┌────────▼────────┐                              │
│                    │ FirebaseService  │                              │
│                    └────────┬────────┘                              │
│                             │                                       │
│              ┌──────────────┴──────────────┐                       │
│    ┌─────────▼──────┐          ┌──────────▼────────┐              │
│    │ Firebase        │          │  Local CSV files   │              │
│    │ Firestore /     │          │  (default,         │              │
│    │ Storage / Auth  │          │   no setup needed) │              │
│    └────────────────┘          └───────────────────┘               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Install

```bash
git clone https://github.com/PRASANNAKUMAR19s/Attendance_system.git
cd Attendance_system
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # Edit .env with your settings
```

### 2. Run web portal

```bash
python 8_web_portal.py
# → http://localhost:5000
```

### 3. Run REST API

```bash
python api.py
# → http://localhost:5001
# → Swagger docs: http://localhost:5001/api/docs
```

### 4. Face recognition pipeline

```bash
python 1_dataset_collector.py   # Capture face images
python 2_train_model.py         # Train LBPH model
python 3_face_recognition.py    # Start attendance marking
python 4_attendance_report.py   # Generate reports
```

---

## 🔌 REST API

### Authentication

```bash
# Get JWT token
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "tutor", "password": "paavai123"}'

# Use token
curl http://localhost:5001/api/students/ \
  -H "Authorization: Bearer <your-token>"
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health/` | Health check (no auth) |
| POST | `/api/auth/login` | Get JWT token |
| GET/POST | `/api/students/` | List / add students |
| GET/PUT/DELETE | `/api/students/{reg_no}` | Student CRUD |
| GET | `/api/students/search?q=` | Search students |
| GET/POST | `/api/attendance/` | Get / mark attendance |
| GET | `/api/attendance/today` | Today's attendance |
| GET | `/api/attendance/summary/{reg_no}` | Student summary |
| GET/POST | `/api/attendance/late-reasons` | Late reasons |
| GET | `/api/reports/summary` | Summary report |
| GET | `/api/analytics/overview` | Advanced analytics |
| GET | `/api/analytics/periods` | Configured periods |

Full docs at: `http://localhost:5001/api/docs`

---

## 🔥 Firebase Setup

1. Create a Firebase project at https://console.firebase.google.com
2. Enable Firestore, Storage, and Authentication
3. Download `serviceAccountKey.json` (Project Settings → Service Accounts)
4. Deploy security rules: `firebase deploy --only firestore:rules,storage`
5. Set in `.env`:
   ```env
   USE_FIREBASE=true
   FIREBASE_CREDENTIALS_PATH=serviceAccountKey.json
   FIREBASE_STORAGE_BUCKET=your-project.appspot.com
   ```
6. Migrate existing data:
   ```bash
   python migrate_to_firebase.py --dry-run   # preview
   python migrate_to_firebase.py             # run
   ```

---

## 🐳 Docker Deployment

```bash
docker compose up --build    # start all services
# API: http://localhost:5001
# Web: http://localhost:5000
docker compose down          # stop
```

---

## ☁️ Cloud Deployment

### Render.com
1. Connect GitHub repo on https://render.com
2. Build command: `pip install -r requirements.txt`
3. Start command: `gunicorn -w 4 -b 0.0.0.0:$PORT api:app`
4. Add environment variables from `.env.example`

### AWS EC2
```bash
sudo apt update && sudo apt install -y docker.io docker-compose-plugin
git clone https://github.com/PRASANNAKUMAR19s/Attendance_system.git
cd Attendance_system && cp .env.example .env
docker compose up -d
```

### Google Cloud Run
```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT/attendance-system
gcloud run deploy attendance-system --image gcr.io/YOUR_PROJECT/attendance-system \
  --platform managed --allow-unauthenticated --port 5001
```

---

## ⚙️ Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | (required) | Flask secret key |
| `JWT_SECRET_KEY` | (required) | JWT signing key |
| `TUTOR_USERNAME` | `tutor` | Login username |
| `TUTOR_PASSWORD` | `paavai123` | Plain password (dev only) |
| `TUTOR_PASSWORD_HASH` | `""` | bcrypt hash (production) |
| `USE_FIREBASE` | `false` | Enable Firebase backend |
| `FIREBASE_CREDENTIALS_PATH` | `serviceAccountKey.json` | Credentials file |
| `FIREBASE_STORAGE_BUCKET` | `""` | Storage bucket name |
| `CONFIDENCE_THRESHOLD` | `70` | Face recognition confidence |
| `DEFAULTER_THRESHOLD` | `75` | Minimum attendance % |

Generate bcrypt hash:
```bash
python -c "import bcrypt; print(bcrypt.hashpw(b'your_password', bcrypt.gensalt()).decode())"
```

---

## 🧪 Testing

```bash
pytest tests/ -v
pytest tests/test_api.py -v       # API tests
pytest tests/test_config.py -v    # Unit tests
```

---

## 🔐 Security

- Passwords hashed with **bcrypt**
- **JWT tokens** protect all API endpoints
- **Rate limiting** (10 login attempts/min)
- **Security headers** on all responses
- **Input validation** with length limits
- **Firebase Rules** for least-privilege access
- **Non-root Docker** user in production

### Production Checklist

- [ ] Set strong random `SECRET_KEY` and `JWT_SECRET_KEY`
- [ ] Set `TUTOR_PASSWORD_HASH` (bcrypt)
- [ ] Set `FLASK_DEBUG=false`
- [ ] Use HTTPS (Nginx reverse proxy)
- [ ] Deploy Firebase security rules
- [ ] Add `serviceAccountKey.json` to `.gitignore`

---

## 📁 Project Structure

```
Attendance_system/
├── api.py                      # REST API (Flask-RESTX + JWT)
├── firebase_service.py         # Firebase / CSV service layer
├── config.py                   # Configuration (env-variable aware)
├── migrate_to_firebase.py      # CSV → Firebase migration script
├── firestore.rules             # Firebase Firestore security rules
├── storage.rules               # Firebase Storage security rules
├── 1_dataset_collector.py      # Capture student face images
├── 2_train_model.py            # Train LBPH model
├── 3_face_recognition.py       # Real-time attendance marking
├── 4_attendance_report.py      # Generate reports & charts
├── 5_tutor_portal.py           # CLI tutor portal
├── 6_send_report.py            # PDF generation & email
├── 7_student_portal.py         # Student web portal
├── 8_web_portal.py             # Combined web portal
├── Dockerfile                  # Docker build instructions
├── docker-compose.yml          # Multi-service Docker setup
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
├── .github/workflows/ci.yml    # GitHub Actions CI/CD
└── tests/                      # Test suite
```

---

## 👨‍💻 Author

**Prasannakumar S** — Paavai Engineering College, AI & Data Science  
Research Intern | Face Recognition & Attendance Automation
