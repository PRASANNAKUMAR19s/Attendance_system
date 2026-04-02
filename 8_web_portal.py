"""
STEP 8 — Complete Web Portal (Tutor + Student)
===============================================
Single web app with:
  - Student Portal  → Check attendance %
  - Tutor Portal    → Login, manage late comers,
                       view reports, download PDF

HOW TO RUN:
    python 8_web_portal.py

Then open browser:
    http://localhost:5000

TUTOR LOGIN:
    Username : tutor
    Password : paavai123   ← change in config.py
"""

from flask import (
    Flask, request, render_template_string,
    redirect, url_for, session, send_file
)
import csv, os, glob
from datetime import datetime
from config import (
    ATTENDANCE_DIR, REPORTS_DIR, STUDENTS_FILE,
    LATE_REASONS_FILE, COLLEGE_NAME, DEPARTMENT,
    TUTOR_NAME, HOD_NAME, PERIODS
)

app = Flask(__name__)
app.secret_key = "paavai_attendance_2024"

# ── Tutor credentials (change these!) ─────────────────────────────────────────
TUTOR_USERNAME = "tutor"
TUTOR_PASSWORD = "paavai123"

DEFAULTER_THRESHOLD = 75

# ══════════════════════════════════════════════════════════════════════════════
#  BASE STYLES
# ══════════════════════════════════════════════════════════════════════════════
BASE_CSS = """
* { margin:0; padding:0; box-sizing:border-box; }
body {
  font-family: 'Times New Roman', Times, serif;
  background: linear-gradient(135deg, #1a237e 0%, #283593 50%, #1565c0 100%);
  min-height: 100vh; padding: 24px 16px;
}
.header { text-align:center; color:white; margin-bottom:24px; }
.header h1 { font-size:22px; font-weight:bold; }
.header p  { font-size:13px; opacity:.85; margin-top:3px; }
.card {
  background:white; border-radius:16px; padding:28px;
  max-width:960px; margin:0 auto;
  box-shadow:0 20px 60px rgba(0,0,0,.3);
}
.card-sm { max-width:480px; }
h2 { font-size:18px; color:#1a237e; margin-bottom:20px;
     border-bottom:2px solid #e8eaf6; padding-bottom:10px; }
h3 { font-size:15px; color:#1a237e; margin:20px 0 10px; }
input, select {
  width:100%; padding:12px 14px; border:2px solid #c5cae9;
  border-radius:10px; font-size:15px;
  font-family:'Times New Roman',serif; color:#1a237e; outline:none;
  margin-bottom:12px; transition:border .2s;
}
input:focus, select:focus { border-color:#1a237e; }
.btn {
  padding:12px 24px; border:none; border-radius:10px;
  font-size:15px; font-family:'Times New Roman',serif;
  font-weight:bold; cursor:pointer; transition:background .2s;
  text-decoration:none; display:inline-block; text-align:center;
}
.btn-primary { background:#1a237e; color:white; width:100%; }
.btn-primary:hover { background:#283593; }
.btn-success { background:#2e7d32; color:white; }
.btn-success:hover { background:#1b5e20; }
.btn-warning { background:#e65100; color:white; }
.btn-warning:hover { background:#bf360c; }
.btn-danger  { background:#c62828; color:white; }
.btn-danger:hover  { background:#b71c1c; }
.btn-secondary { background:#546e7a; color:white; }
.btn-secondary:hover { background:#37474f; }
.btn-sm { padding:7px 16px; font-size:13px; }
.nav {
  display:flex; gap:10px; flex-wrap:wrap;
  margin-bottom:22px; padding-bottom:16px;
  border-bottom:2px solid #e8eaf6;
}
.nav a { font-size:14px; }
table { width:100%; border-collapse:collapse; margin-top:8px; font-size:13px; }
th {
  background:#1a237e; color:white; padding:10px 12px;
  font-family:'Times New Roman',serif; text-align:left;
}
td { padding:9px 12px; border-bottom:1px solid #e8eaf6; }
tr:hover td { background:#f5f5f5; }
tr:nth-child(even) td { background:#fafafa; }
.badge {
  padding:4px 12px; border-radius:20px; font-size:12px;
  font-weight:bold; display:inline-block;
}
.badge-green  { background:#e8f5e9; color:#2e7d32; }
.badge-blue   { background:#e3f2fd; color:#1565c0; }
.badge-orange { background:#fff3e0; color:#e65100; }
.badge-red    { background:#ffebee; color:#c62828; }
.badge-purple { background:#f3e5f5; color:#6a1b9a; }
.alert {
  padding:12px 16px; border-radius:10px;
  margin-bottom:16px; font-size:14px;
}
.alert-success { background:#e8f5e9; color:#2e7d32;
                 border-left:4px solid #2e7d32; }
.alert-error   { background:#ffebee; color:#c62828;
                 border-left:4px solid #c62828; }
.alert-warning { background:#fff3e0; color:#e65100;
                 border-left:4px solid #e65100; }
.stats-grid {
  display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr));
  gap:14px; margin-bottom:22px;
}
.stat-box {
  background:#f5f7ff; border-radius:12px;
  padding:16px; text-align:center;
  border:1px solid #e8eaf6;
}
.stat-box .val { font-size:28px; font-weight:bold; }
.stat-box .lbl { font-size:12px; color:#78909c; margin-top:4px; }
.footer {
  text-align:center; color:rgba(255,255,255,.6);
  font-size:12px; margin-top:20px;
}
"""

# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def load_students():
    s = {}
    if os.path.isfile(STUDENTS_FILE):
        with open(STUDENTS_FILE, newline="") as f:
            for row in csv.DictReader(f):
                s[row["RegNo"].strip()] = row["Name"].strip()
    return s

def load_all_records():
    files, rows = glob.glob(os.path.join(ATTENDANCE_DIR, "attendance_*.csv")), []
    for f in sorted(files):
        with open(f, newline="") as fp:
            rows.extend(list(csv.DictReader(fp)))
    return rows

def load_today_records():
    today = datetime.now().strftime("%Y-%m-%d")
    path  = os.path.join(ATTENDANCE_DIR, f"attendance_{today}.csv")
    if not os.path.isfile(path): return [], path
    with open(path, newline="") as f:
        return list(csv.DictReader(f)), path

def save_records(path, records):
    if not records: return
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=records[0].keys())
        w.writeheader(); w.writerows(records)

def load_reasons(date_str):
    reasons = {}
    if not os.path.isfile(LATE_REASONS_FILE): return reasons
    with open(LATE_REASONS_FILE, newline="") as f:
        for row in csv.DictReader(f):
            if row["Date"] == date_str:
                reasons[f"{row['RegNo']}_{row['Period']}"] = row["Reason"]
    return reasons

def save_reason(reg_no, name, period, reason, date):
    exists = os.path.isfile(LATE_REASONS_FILE)
    with open(LATE_REASONS_FILE, "a", newline="") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(["RegNo","Name","Date","Period","Reason","UpdatedBy","UpdatedAt"])
        w.writerow([reg_no, name, date, period, reason, "Tutor",
                    datetime.now().strftime("%H:%M:%S")])

def status_badge(s):
    if s == "ON_TIME":           return '<span class="badge badge-green">On Time</span>'
    elif s == "LATE":            return '<span class="badge badge-orange">Late</span>'
    elif s == "Absent":          return '<span class="badge badge-red">Absent</span>'
    elif s == "Present(Reason)": return '<span class="badge badge-purple">Excused</span>'
    return f'<span class="badge badge-blue">{s}</span>'

def now_str(): return datetime.now().strftime("%d %B %Y, %I:%M %p")

# ══════════════════════════════════════════════════════════════════════════════
#  HOME PAGE
# ══════════════════════════════════════════════════════════════════════════════
HOME_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Attendance Portal</title>
<style>{{ css }}
.portal-grid { display:grid; grid-template-columns:1fr 1fr; gap:20px; }
@media(max-width:600px){ .portal-grid{ grid-template-columns:1fr; } }
.portal-card {
  border-radius:14px; padding:28px; text-align:center;
  cursor:pointer; transition:transform .2s, box-shadow .2s;
  text-decoration:none; display:block;
}
.portal-card:hover { transform:translateY(-4px);
  box-shadow:0 12px 40px rgba(0,0,0,.15); }
.portal-card .icon { font-size:48px; margin-bottom:14px; }
.portal-card h3 { font-size:18px; font-weight:bold; margin-bottom:8px; }
.portal-card p  { font-size:13px; opacity:.8; }
.student-card { background:linear-gradient(135deg,#1565c0,#0d47a1); color:white; }
.tutor-card   { background:linear-gradient(135deg,#1b5e20,#2e7d32); color:white; }
</style></head><body>
<div class="header">
  <h1>Paavai Engineering College (Autonomous)</h1>
  <p>Department of {{ dept }} &nbsp;|&nbsp; Attendance Portal</p>
</div>
<div class="card" style="max-width:600px;margin:0 auto;">
  <h2 style="text-align:center;">Welcome — Select Portal</h2>
  <div class="portal-grid">
    <a href="/student" class="portal-card student-card">
      <div class="icon">🎓</div>
      <h3>Student Portal</h3>
      <p>Check your attendance percentage and status</p>
    </a>
    <a href="/tutor" class="portal-card tutor-card">
      <div class="icon">👨‍🏫</div>
      <h3>Tutor Portal</h3>
      <p>Manage attendance, late comers and reports</p>
    </a>
  </div>
</div>
<div class="footer">{{ now }} &nbsp;|&nbsp; Automated Attendance Monitoring System</div>
</body></html>"""

# ══════════════════════════════════════════════════════════════════════════════
#  STUDENT PORTAL
# ══════════════════════════════════════════════════════════════════════════════
STUDENT_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Student Portal</title>
<style>{{ css }}
.pct-circle {
  width:140px; height:140px; border-radius:50%;
  display:flex; flex-direction:column;
  align-items:center; justify-content:center;
  margin:0 auto 16px;
  box-shadow:0 4px 20px rgba(0,0,0,.15);
}
.pct-circle .pct  { font-size:36px; font-weight:bold; color:white; }
.pct-circle .lbl  { font-size:12px; color:rgba(255,255,255,.9); }
.status-bar {
  text-align:center; padding:10px; border-radius:10px;
  font-size:15px; font-weight:bold; margin-bottom:18px;
}
.info-box {
  padding:12px 16px; border-radius:8px;
  font-size:13px; margin-top:12px;
}
</style></head><body>
<div class="header">
  <h1>Paavai Engineering College (Autonomous)</h1>
  <p>Student Attendance Portal</p>
</div>
<div class="card card-sm">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
    <h2 style="margin:0;border:none;">Check Your Attendance</h2>
    <a href="/" class="btn btn-secondary btn-sm">← Home</a>
  </div>
  {% if msg %}<div class="alert alert-{{ msg_type }}">{{ msg }}</div>{% endif %}
  <form method="POST">
    <input type="text" name="reg_no" placeholder="Enter Your Register Number"
           value="{{ reg_no or '' }}" autocomplete="off"/>
    <button class="btn btn-primary" type="submit">Check Attendance</button>
  </form>
  {% if data %}
  <div style="margin-top:24px;">
    <div style="text-align:center;font-size:20px;font-weight:bold;
                color:#1a237e;margin-bottom:4px;">{{ data.name }}</div>
    <div style="text-align:center;font-size:13px;color:#78909c;
                margin-bottom:18px;">Reg No: {{ data.reg_no }}</div>
    <div class="pct-circle" style="background:{{ data.color }};">
      <div class="pct">{{ data.pct }}%</div>
      <div class="lbl">Attendance</div>
    </div>
    <div class="status-bar"
         style="background:{{ data.badge_bg }};color:{{ data.badge_fg }};">
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
    <div class="info-box" style="background:#ffebee;color:#c62828;
         border-left:4px solid #c62828;">
      ⚠️ Below 75%! You need <strong>{{ data.days_needed }} more present days</strong>
      to reach 75%. Meet your tutor immediately.
    </div>
    {% else %}
    <div class="info-box" style="background:#e8f5e9;color:#2e7d32;
         border-left:4px solid #2e7d32;">
      ✅ Good attendance! You can miss up to
      <strong>{{ data.can_miss }} more days</strong> and stay above 75%.
    </div>
    {% endif %}
  </div>
  {% endif %}
</div>
<div class="footer">{{ now }} &nbsp;|&nbsp; Automated Attendance Monitoring System</div>
</body></html>"""

# ══════════════════════════════════════════════════════════════════════════════
#  TUTOR LOGIN
# ══════════════════════════════════════════════════════════════════════════════
LOGIN_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Tutor Login</title>
<style>{{ css }}</style></head><body>
<div class="header">
  <h1>Paavai Engineering College (Autonomous)</h1>
  <p>Tutor Portal — Login</p>
</div>
<div class="card card-sm">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
    <h2 style="margin:0;border:none;">👨‍🏫 Tutor Login</h2>
    <a href="/" class="btn btn-secondary btn-sm">← Home</a>
  </div>
  {% if error %}<div class="alert alert-error">{{ error }}</div>{% endif %}
  <form method="POST">
    <input type="text"     name="username" placeholder="Username" autocomplete="off"/>
    <input type="password" name="password" placeholder="Password"/>
    <button class="btn btn-primary" type="submit">Login</button>
  </form>
</div>
<div class="footer">Automated Attendance Monitoring System</div>
</body></html>"""

# ══════════════════════════════════════════════════════════════════════════════
#  TUTOR DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
DASHBOARD_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Tutor Dashboard</title>
<style>{{ css }}</style></head><body>
<div class="header">
  <h1>Paavai Engineering College (Autonomous)</h1>
  <p>Tutor Dashboard &nbsp;|&nbsp; {{ dept }}</p>
</div>
<div class="card">
  <div style="display:flex;justify-content:space-between;
              align-items:center;flex-wrap:wrap;gap:10px;margin-bottom:20px;">
    <h2 style="margin:0;border:none;">📊 Today's Overview — {{ date }}</h2>
    <div style="display:flex;gap:8px;flex-wrap:wrap;">
      <a href="/tutor/report" class="btn btn-success btn-sm">📄 Download PDF</a>
      <a href="/tutor/logout" class="btn btn-secondary btn-sm">Logout</a>
    </div>
  </div>
  {% if msg %}<div class="alert alert-{{ msg_type }}">{{ msg }}</div>{% endif %}
  <div class="stats-grid">
    <div class="stat-box">
      <div class="val" style="color:#1a237e;">{{ stats.total }}</div>
      <div class="lbl">Total Students</div>
    </div>
    <div class="stat-box">
      <div class="val" style="color:#2e7d32;">{{ stats.on_time }}</div>
      <div class="lbl">On Time</div>
    </div>
    <div class="stat-box">
      <div class="val" style="color:#e65100;">{{ stats.late }}</div>
      <div class="lbl">Late</div>
    </div>
    <div class="stat-box">
      <div class="val" style="color:#c62828;">{{ stats.absent }}</div>
      <div class="lbl">Absent</div>
    </div>
    <div class="stat-box">
      <div class="val" style="color:#6a1b9a;">{{ stats.excused }}</div>
      <div class="lbl">Excused</div>
    </div>
  </div>
  <div class="nav">
    <a href="/tutor/dashboard"  class="btn btn-primary  btn-sm">🏠 Dashboard</a>
    <a href="/tutor/late"       class="btn btn-warning  btn-sm">⏰ Late Comers</a>
    <a href="/tutor/absent"     class="btn btn-danger   btn-sm">❌ Absent</a>
    <a href="/tutor/summary"    class="btn btn-secondary btn-sm">📋 Full Summary</a>
    <a href="/tutor/report"     class="btn btn-success  btn-sm">📄 PDF Report</a>
  </div>
  <h3>⏰ Late Comers ({{ stats.late }})</h3>
  {% if late_records %}
  <table>
    <tr><th>Reg No</th><th>Name</th><th>Period</th><th>Time</th><th>Action</th></tr>
    {% for r in late_records %}
    <tr>
      <td>{{ r.RegNo }}</td><td>{{ r.Name }}</td>
      <td>{{ r.Period }}</td><td>{{ r.MarkedTime }}</td>
      <td>
        <a href="/tutor/add_reason?reg={{ r.RegNo }}&period={{ r.Period }}"
           class="btn btn-warning btn-sm">Add Reason</a>
      </td>
    </tr>
    {% endfor %}
  </table>
  {% else %}
  <p style="color:#78909c;font-size:14px;">✅ No late comers today!</p>
  {% endif %}

  <h3 style="margin-top:24px;">❌ Absent Students ({{ stats.absent }})</h3>
  {% if absent_records %}
  <table>
    <tr><th>Reg No</th><th>Name</th><th>Period</th><th>Status</th></tr>
    {% for r in absent_records %}
    <tr>
      <td>{{ r.RegNo }}</td><td>{{ r.Name }}</td>
      <td>{{ r.Period }}</td>
      <td><span class="badge badge-red">Absent</span></td>
    </tr>
    {% endfor %}
  </table>
  {% else %}
  <p style="color:#78909c;font-size:14px;">✅ No absent students today!</p>
  {% endif %}
</div>
<div class="footer">{{ now }} &nbsp;|&nbsp; Automated Attendance Monitoring System</div>
</body></html>"""

# ══════════════════════════════════════════════════════════════════════════════
#  ADD REASON PAGE
# ══════════════════════════════════════════════════════════════════════════════
REASON_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Add Reason</title>
<style>{{ css }}</style></head><body>
<div class="header">
  <h1>Paavai Engineering College (Autonomous)</h1>
  <p>Tutor Portal — Add Late Reason</p>
</div>
<div class="card card-sm">
  <div style="display:flex;justify-content:space-between;
              align-items:center;margin-bottom:16px;">
    <h2 style="margin:0;border:none;">Add Reason for Late Comer</h2>
    <a href="/tutor/dashboard" class="btn btn-secondary btn-sm">← Back</a>
  </div>
  <div style="background:#f5f7ff;border-radius:10px;
              padding:16px;margin-bottom:20px;">
    <p><strong>Name   :</strong> {{ name }}</p>
    <p style="margin-top:6px;"><strong>Reg No :</strong> {{ reg_no }}</p>
    <p style="margin-top:6px;"><strong>Period :</strong> {{ period }}</p>
    <p style="margin-top:6px;"><strong>Time   :</strong> {{ time }}</p>
  </div>
  <form method="POST">
    <input type="hidden" name="reg_no"  value="{{ reg_no }}"/>
    <input type="hidden" name="period"  value="{{ period }}"/>
    <textarea name="reason"
      placeholder="Enter reason (e.g. Medical appointment, Traffic, etc.)"
      style="width:100%;padding:12px;border:2px solid #c5cae9;border-radius:10px;
             font-size:14px;font-family:'Times New Roman',serif;
             min-height:100px;outline:none;resize:vertical;margin-bottom:12px;"
    ></textarea>
    <button class="btn btn-success" type="submit" style="width:100%;">
      ✅ Save Reason & Mark Present
    </button>
  </form>
</div>
<div class="footer">Automated Attendance Monitoring System</div>
</body></html>"""

# ══════════════════════════════════════════════════════════════════════════════
#  FULL SUMMARY PAGE
# ══════════════════════════════════════════════════════════════════════════════
SUMMARY_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Full Summary</title>
<style>{{ css }}</style></head><body>
<div class="header">
  <h1>Paavai Engineering College (Autonomous)</h1>
  <p>Tutor Portal — Full Attendance Summary</p>
</div>
<div class="card">
  <div style="display:flex;justify-content:space-between;
              align-items:center;margin-bottom:16px;flex-wrap:wrap;gap:10px;">
    <h2 style="margin:0;border:none;">📋 Full Summary — {{ date }}</h2>
    <a href="/tutor/dashboard" class="btn btn-secondary btn-sm">← Back</a>
  </div>
  <table>
    <tr>
      <th>Reg No</th><th>Name</th><th>Period</th>
      <th>Time</th><th>Status</th>
    </tr>
    {% for r in records %}
    <tr>
      <td>{{ r.RegNo }}</td><td>{{ r.Name }}</td>
      <td>{{ r.Period }}</td><td>{{ r.MarkedTime }}</td>
      <td>{{ r.status_html | safe }}</td>
    </tr>
    {% endfor %}
  </table>
</div>
<div class="footer">{{ now }} &nbsp;|&nbsp; Automated Attendance Monitoring System</div>
</body></html>"""

# ══════════════════════════════════════════════════════════════════════════════
#  ROUTES — HOME
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/")
def home():
    return render_template_string(HOME_HTML,
        css=BASE_CSS, dept=DEPARTMENT, now=now_str())

# ══════════════════════════════════════════════════════════════════════════════
#  ROUTES — STUDENT
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/student", methods=["GET","POST"])
def student():
    data, msg, msg_type, reg_no = None, None, "error", None
    if request.method == "POST":
        reg_no   = request.form.get("reg_no","").strip()
        students = load_students()
        records  = load_all_records()
        if not reg_no:
            msg = "Please enter your Register Number."
        elif reg_no not in students:
            msg = f"Register Number '{reg_no}' not found."
        else:
            my  = [r for r in records if r["RegNo"].strip() == reg_no]
            if not my:
                msg = "No attendance records found yet."
            else:
                dates   = set(r["Date"] for r in records)
                total   = len(dates)
                present = len(set(r["Date"] for r in my
                               if r["Status"] in ("ON_TIME","LATE","Present(Reason)")))
                absent  = len(set(r["Date"] for r in my if r["Status"]=="Absent"))
                late    = sum(1 for r in my if r["Status"]=="LATE")
                pct     = round(present/total*100,1) if total else 0

                x = 0
                if pct < DEFAULTER_THRESHOLD:
                    while total > 0:
                        if (present+x)/(total+x)*100 >= DEFAULTER_THRESHOLD: break
                        x += 1
                    days_needed, can_miss = x, 0
                else:
                    days_needed = 0
                    while True:
                        if present/(total+x+1)*100 < DEFAULTER_THRESHOLD: break
                        x += 1
                    can_miss = x

                if pct >= 85:
                    color,badge_bg,badge_fg = "#2e7d32","#e8f5e9","#2e7d32"
                    st = "✅ Excellent Attendance"
                elif pct >= 75:
                    color,badge_bg,badge_fg = "#1565c0","#e3f2fd","#1565c0"
                    st = "👍 Good Attendance"
                elif pct >= 65:
                    color,badge_bg,badge_fg = "#e65100","#fff3e0","#e65100"
                    st = "⚠️ Low — Needs Improvement"
                else:
                    color,badge_bg,badge_fg = "#c62828","#ffebee","#c62828"
                    st = "❌ Defaulter — Meet Tutor"

                data = dict(name=students[reg_no], reg_no=reg_no,
                            pct=pct, color=color, badge_bg=badge_bg,
                            badge_fg=badge_fg, status_text=st,
                            total_days=total, present=present,
                            absent=absent, late=late,
                            is_defaulter=pct<DEFAULTER_THRESHOLD,
                            days_needed=days_needed, can_miss=can_miss)
                msg_type = "success"
    return render_template_string(STUDENT_HTML,
        css=BASE_CSS, data=data, msg=msg,
        msg_type=msg_type, reg_no=reg_no, now=now_str())

# ══════════════════════════════════════════════════════════════════════════════
#  ROUTES — TUTOR LOGIN / LOGOUT
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/tutor", methods=["GET","POST"])
def tutor_login():
    if session.get("tutor"): return redirect(url_for("tutor_dashboard"))
    error = None
    if request.method == "POST":
        u = request.form.get("username","")
        p = request.form.get("password","")
        if u == TUTOR_USERNAME and p == TUTOR_PASSWORD:
            session["tutor"] = True
            return redirect(url_for("tutor_dashboard"))
        error = "Invalid username or password."
    return render_template_string(LOGIN_HTML, css=BASE_CSS, error=error)

@app.route("/tutor/logout")
def tutor_logout():
    session.pop("tutor", None)
    return redirect(url_for("home"))

# ══════════════════════════════════════════════════════════════════════════════
#  ROUTES — TUTOR DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/tutor/dashboard")
def tutor_dashboard():
    if not session.get("tutor"): return redirect(url_for("tutor_login"))
    records, _ = load_today_records()
    msg      = session.pop("msg",      None)
    msg_type = session.pop("msg_type", "success")
    stats = dict(
        total   = len(set(r["RegNo"] for r in records)),
        on_time = sum(1 for r in records if r["Status"]=="ON_TIME"),
        late    = sum(1 for r in records if r["Status"]=="LATE"),
        absent  = sum(1 for r in records if r["Status"]=="Absent"),
        excused = sum(1 for r in records if r["Status"]=="Present(Reason)"),
    )
    late_records   = [r for r in records if r["Status"]=="LATE"]
    absent_records = [r for r in records if r["Status"]=="Absent"]
    today = datetime.now().strftime("%d %B %Y (%A)")
    return render_template_string(DASHBOARD_HTML,
        css=BASE_CSS, stats=stats, late_records=late_records,
        absent_records=absent_records, date=today,
        dept=DEPARTMENT, msg=msg, msg_type=msg_type, now=now_str())

# ══════════════════════════════════════════════════════════════════════════════
#  ROUTES — ADD REASON
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/tutor/add_reason", methods=["GET","POST"])
def add_reason():
    if not session.get("tutor"): return redirect(url_for("tutor_login"))
    records, path = load_today_records()
    today = datetime.now().strftime("%Y-%m-%d")

    if request.method == "POST":
        reg_no = request.form.get("reg_no","").strip()
        period = request.form.get("period","").strip()
        reason = request.form.get("reason","").strip()
        if not reason:
            session["msg"]      = "Reason cannot be empty!"
            session["msg_type"] = "error"
            return redirect(url_for("tutor_dashboard"))
        # Update status
        name = ""
        for r in records:
            if r["RegNo"]==reg_no and r["Period"]==period and r["Status"]=="LATE":
                r["Status"] = "Present(Reason)"
                name = r["Name"]
                break
        save_records(path, records)
        save_reason(reg_no, name, period, reason, today)
        session["msg"]      = f"✅ {name} updated to Present with reason recorded."
        session["msg_type"] = "success"
        return redirect(url_for("tutor_dashboard"))

    # GET — show form
    reg_no = request.args.get("reg","")
    period = request.args.get("period","")
    record = next((r for r in records
                   if r["RegNo"]==reg_no and r["Period"]==period), None)
    if not record:
        return redirect(url_for("tutor_dashboard"))
    return render_template_string(REASON_HTML, css=BASE_CSS,
        name=record["Name"], reg_no=reg_no,
        period=period, time=record["MarkedTime"])

# ══════════════════════════════════════════════════════════════════════════════
#  ROUTES — FULL SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/tutor/summary")
def tutor_summary():
    if not session.get("tutor"): return redirect(url_for("tutor_login"))
    records, _ = load_today_records()
    for r in records:
        r["status_html"] = status_badge(r["Status"])
    today = datetime.now().strftime("%d %B %Y (%A)")
    return render_template_string(SUMMARY_HTML, css=BASE_CSS,
        records=records, date=today, now=now_str())

# ══════════════════════════════════════════════════════════════════════════════
#  ROUTES — PDF REPORT
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/tutor/report")
def tutor_report():
    if not session.get("tutor"): return redirect(url_for("tutor_login"))
    import importlib.util
    spec = importlib.util.spec_from_file_location("send_report", "6_send_report.py")
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    generate_pdf = mod.generate_pdf

    today    = datetime.now().strftime("%Y-%m-%d")
    pdf_path = generate_pdf(today)
    if pdf_path and os.path.isfile(pdf_path):
        return send_file(pdf_path, as_attachment=True,
                         download_name=f"attendance_report_{today}.pdf")
    session["msg"]      = "❌ Could not generate PDF. No records found for today."
    session["msg_type"] = "error"
    return redirect(url_for("tutor_dashboard"))

# ══════════════════════════════════════════════════════════════════════════════
#  SHORTCUT ROUTES
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/tutor/late")
def tutor_late():
    if not session.get("tutor"): return redirect(url_for("tutor_login"))
    return redirect(url_for("tutor_dashboard") + "#late")

@app.route("/tutor/absent")
def tutor_absent():
    if not session.get("tutor"): return redirect(url_for("tutor_login"))
    return redirect(url_for("tutor_dashboard") + "#absent")

# ══════════════════════════════════════════════════════════════════════════════
#  RUN
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import socket
    print("\n" + "═"*55)
    print("   ATTENDANCE WEB PORTAL — TUTOR + STUDENT")
    print("═"*55)
    print("\n  Open in browser:")
    print("  → http://localhost:5000")
    try:
        ip = socket.gethostbyname(socket.gethostname())
        print(f"  → http://{ip}:5000  (share on WiFi)")
    except: pass
    print("\n  Tutor Login → Username: tutor | Password: paavai123")
    print("\n  Press Ctrl+C to stop.\n")
    app.run(debug=False, host="0.0.0.0", port=5000)
