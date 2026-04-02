"""
STEP 7 — Student Attendance Portal (Web App)
=============================================
Students open this in their browser, enter their
Reg No and see their attendance % and status.

HOW TO RUN:
    python 7_student_portal.py

Then open browser and go to:
    http://localhost:5000
"""

from flask import Flask, request, render_template_string
import csv
import os
import glob
from datetime import datetime

app = Flask(__name__)

ATTENDANCE_DIR      = "attendance"
STUDENTS_FILE       = "students.csv"
DEFAULTER_THRESHOLD = 75

# ── HTML Template ─────────────────────────────────────────────────────────────
HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Student Attendance Portal</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }

    body {
      font-family: 'Times New Roman', Times, serif;
      background: linear-gradient(135deg, #1a237e 0%, #283593 50%, #1565c0 100%);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 30px 20px;
    }

    .header {
      text-align: center;
      color: white;
      margin-bottom: 30px;
    }
    .header h1 { font-size: 22px; font-weight: bold; margin-bottom: 4px; }
    .header p  { font-size: 14px; opacity: 0.85; }

    .card {
      background: white;
      border-radius: 16px;
      padding: 32px;
      width: 100%;
      max-width: 480px;
      box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    }

    .card h2 {
      font-size: 18px;
      color: #1a237e;
      margin-bottom: 20px;
      text-align: center;
      border-bottom: 2px solid #e8eaf6;
      padding-bottom: 12px;
    }

    input[type="text"] {
      width: 100%;
      padding: 14px 16px;
      border: 2px solid #c5cae9;
      border-radius: 10px;
      font-size: 16px;
      font-family: 'Times New Roman', serif;
      color: #1a237e;
      outline: none;
      transition: border 0.2s;
    }
    input[type="text"]:focus { border-color: #1a237e; }

    button {
      width: 100%;
      padding: 14px;
      background: #1a237e;
      color: white;
      border: none;
      border-radius: 10px;
      font-size: 16px;
      font-family: 'Times New Roman', serif;
      font-weight: bold;
      cursor: pointer;
      margin-top: 14px;
      transition: background 0.2s;
    }
    button:hover { background: #283593; }

    .result { margin-top: 24px; }

    .student-name {
      text-align: center;
      font-size: 20px;
      font-weight: bold;
      color: #1a237e;
      margin-bottom: 4px;
    }
    .reg-no {
      text-align: center;
      font-size: 13px;
      color: #78909c;
      margin-bottom: 20px;
    }

    .percentage-circle {
      width: 140px;
      height: 140px;
      border-radius: 50%;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      margin: 0 auto 20px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    }
    .percentage-circle .pct {
      font-size: 36px;
      font-weight: bold;
      color: white;
      line-height: 1;
    }
    .percentage-circle .label {
      font-size: 12px;
      color: rgba(255,255,255,0.9);
      margin-top: 4px;
    }

    .status-badge {
      text-align: center;
      padding: 8px 24px;
      border-radius: 30px;
      font-size: 15px;
      font-weight: bold;
      display: inline-block;
      margin: 0 auto 20px;
      width: 100%;
    }

    .stats-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
      margin-bottom: 16px;
    }
    .stat-box {
      background: #f5f5f5;
      border-radius: 10px;
      padding: 14px;
      text-align: center;
    }
    .stat-box .val {
      font-size: 24px;
      font-weight: bold;
      color: #1a237e;
    }
    .stat-box .lbl {
      font-size: 12px;
      color: #78909c;
      margin-top: 2px;
    }

    .warning-box {
      background: #fff3e0;
      border-left: 4px solid #e65100;
      border-radius: 8px;
      padding: 12px 16px;
      font-size: 13px;
      color: #e65100;
      margin-top: 12px;
    }
    .safe-box {
      background: #e8f5e9;
      border-left: 4px solid #2e7d32;
      border-radius: 8px;
      padding: 12px 16px;
      font-size: 13px;
      color: #2e7d32;
      margin-top: 12px;
    }

    .error-box {
      background: #ffebee;
      border-radius: 10px;
      padding: 16px;
      text-align: center;
      color: #c62828;
      font-size: 15px;
      margin-top: 16px;
    }

    .footer {
      text-align: center;
      color: rgba(255,255,255,0.6);
      font-size: 12px;
      margin-top: 24px;
    }
  </style>
</head>
<body>

  <div class="header">
    <h1>Paavai Engineering College (Autonomous)</h1>
    <p>Department of Artificial Intelligence & Data Science</p>
    <p>Student Attendance Portal</p>
  </div>

  <div class="card">
    <h2>Check Your Attendance</h2>
    <form method="POST" action="/">
      <input type="text" name="reg_no"
             placeholder="Enter Your Register Number"
             value="{{ reg_no or '' }}"
             autocomplete="off" />
      <button type="submit">Check Attendance</button>
    </form>

    {% if error %}
    <div class="error-box">{{ error }}</div>
    {% endif %}

    {% if data %}
    <div class="result">
      <div class="student-name">{{ data.name }}</div>
      <div class="reg-no">Reg No: {{ data.reg_no }}</div>

      <div class="percentage-circle"
           style="background: {{ data.circle_color }};">
        <div class="pct">{{ data.percentage }}%</div>
        <div class="label">Attendance</div>
      </div>

      <div class="status-badge"
           style="background: {{ data.badge_bg }}; color: {{ data.badge_color }};">
        {{ data.status_text }}
      </div>

      <div class="stats-grid">
        <div class="stat-box">
          <div class="val" style="color:#1a237e;">{{ data.total_days }}</div>
          <div class="lbl">Working Days</div>
        </div>
        <div class="stat-box">
          <div class="val" style="color:#2e7d32;">{{ data.present }}</div>
          <div class="lbl">Days Present</div>
        </div>
        <div class="stat-box">
          <div class="val" style="color:#e65100;">{{ data.late }}</div>
          <div class="lbl">Late Comers</div>
        </div>
        <div class="stat-box">
          <div class="val" style="color:#c62828;">{{ data.absent }}</div>
          <div class="lbl">Days Absent</div>
        </div>
      </div>

      {% if data.is_defaulter %}
      <div class="warning-box">
        ⚠️ Your attendance is below 75%. You need
        <strong>{{ data.days_needed }} more days</strong> present to reach 75%.
        Please meet your tutor immediately.
      </div>
      {% else %}
      <div class="safe-box">
        ✅ Your attendance is good! You can miss up to
        <strong>{{ data.can_miss }} more days</strong> and stay above 75%.
      </div>
      {% endif %}
    </div>
    {% endif %}
  </div>

  <div class="footer">
    <p>Automated Attendance Monitoring System &nbsp;|&nbsp;
       {{ now }}</p>
  </div>

</body>
</html>
"""

# ── Load all students ─────────────────────────────────────────────────────────
def load_students():
    students = {}
    if not os.path.isfile(STUDENTS_FILE):
        return students
    with open(STUDENTS_FILE, newline="") as f:
        for row in csv.DictReader(f):
            students[row["RegNo"].strip()] = row["Name"].strip()
    return students

# ── Load all attendance records ───────────────────────────────────────────────
def load_all_attendance():
    files  = glob.glob(os.path.join(ATTENDANCE_DIR, "attendance_*.csv"))
    frames = []
    for f in sorted(files):
        with open(f, newline="") as fp:
            frames.extend(list(csv.DictReader(fp)))
    return frames

# ── Calculate student stats ───────────────────────────────────────────────────
def get_student_stats(reg_no, records):
    my_records = [r for r in records if r["RegNo"].strip() == reg_no]
    if not my_records:
        return None

    dates        = set(r["Date"] for r in records)
    total_days   = len(dates)

    present_days = set(
        r["Date"] for r in my_records
        if r["Status"] in ("ON_TIME", "LATE", "Present(Reason)")
    )
    absent_days  = set(
        r["Date"] for r in my_records
        if r["Status"] == "Absent"
    )
    late_count   = sum(1 for r in my_records if r["Status"] == "LATE")
    present      = len(present_days)
    absent       = len(absent_days)
    percentage   = round((present / total_days * 100), 1) if total_days > 0 else 0

    # Days needed to reach 75%
    if percentage < DEFAULTER_THRESHOLD:
        # solve: (present + x) / (total + x) = 0.75
        x = 0
        while total_days > 0:
            if (present + x) / (total_days + x) * 100 >= DEFAULTER_THRESHOLD:
                break
            x += 1
        days_needed = x
        can_miss    = 0
    else:
        days_needed = 0
        # solve: (present) / (total + x) = 0.75
        x = 0
        while True:
            if present / (total_days + x + 1) * 100 < DEFAULTER_THRESHOLD:
                break
            x += 1
        can_miss = x

    return {
        "total_days" : total_days,
        "present"    : present,
        "absent"     : absent,
        "late"       : late_count,
        "percentage" : percentage,
        "days_needed": days_needed,
        "can_miss"   : can_miss,
        "is_defaulter": percentage < DEFAULTER_THRESHOLD,
    }

# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/", methods=["GET", "POST"])
def index():
    now     = datetime.now().strftime("%d %B %Y, %I:%M %p")
    data    = None
    error   = None
    reg_no  = None

    if request.method == "POST":
        reg_no   = request.form.get("reg_no", "").strip()
        students = load_students()
        records  = load_all_attendance()

        if not reg_no:
            error = "Please enter your Register Number."
        elif reg_no not in students:
            error = f"Register Number '{reg_no}' not found. Please check and try again."
        else:
            stats = get_student_stats(reg_no, records)
            if not stats:
                error = "No attendance records found for your register number yet."
            else:
                pct  = stats["percentage"]
                name = students[reg_no]

                if pct >= 85:
                    circle_color = "#2e7d32"
                    badge_bg     = "#e8f5e9"
                    badge_color  = "#2e7d32"
                    status_text  = "✅ Excellent Attendance"
                elif pct >= 75:
                    circle_color = "#1565c0"
                    badge_bg     = "#e3f2fd"
                    badge_color  = "#1565c0"
                    status_text  = "👍 Good Attendance"
                elif pct >= 65:
                    circle_color = "#e65100"
                    badge_bg     = "#fff3e0"
                    badge_color  = "#e65100"
                    status_text  = "⚠️ Low Attendance — Needs Improvement"
                else:
                    circle_color = "#c62828"
                    badge_bg     = "#ffebee"
                    badge_color  = "#c62828"
                    status_text  = "❌ Defaulter — Meet Tutor Immediately"

                data = {
                    "name"        : name,
                    "reg_no"      : reg_no,
                    "percentage"  : pct,
                    "circle_color": circle_color,
                    "badge_bg"    : badge_bg,
                    "badge_color" : badge_color,
                    "status_text" : status_text,
                    **stats,
                }

    return render_template_string(HTML,
                                  data=data, error=error,
                                  reg_no=reg_no, now=now)

# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "═" * 50)
    print("       STUDENT ATTENDANCE PORTAL")
    print("═" * 50)
    print("\n  Open your browser and go to:")
    print("  → http://localhost:5000\n")
    print("  Share this link with students on same WiFi:")
    import socket
    try:
        ip = socket.gethostbyname(socket.gethostname())
        print(f"  → http://{ip}:5000\n")
    except:
        pass
    print("  Press Ctrl+C to stop the server.\n")
    app.run(debug=False, host="0.0.0.0", port=5000)
