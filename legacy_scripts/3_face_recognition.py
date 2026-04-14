"""
STEP 3 — Real-Time Face Recognition & Smart Attendance Marking
==============================================================
- Marks PRESENT if student enters within 10 min of period start
- Marks LATE if student enters after 10 min grace period
- Marks ABSENT at period end if not detected at all
- Saves all records to attendance/attendance_YYYY-MM-DD.csv

HOW TO RUN:
    python 3_face_recognition.py

CONTROLS:
    Press 'q' → Quit
    Press 's' → Show today's summary
"""

import cv2
import numpy as np
import csv
import os
from datetime import datetime, time as dtime
from config import (
    CASCADE_PATH, TRAINER_FILE, NAME_MAP, ATTENDANCE_DIR,
    CONFIDENCE_THRESHOLD, MIN_FACE_SIZE, PERIODS
)

# ── Get current period info ───────────────────────────────────────────────────
def get_current_period():
    now = datetime.now().time()
    for name, start_str, late_str, end_str in PERIODS:
        start = dtime(*map(int, start_str.split(":")))
        late  = dtime(*map(int, late_str.split(":")))
        end   = dtime(*map(int, end_str.split(":")))
        if start <= now <= end:
            return {
                "name"  : name,
                "start" : start,
                "late"  : late,
                "end"   : end,
                "status": "ON_TIME" if now <= late else "LATE"
            }
    return None   # Break / Lunch / After college

# ── Attendance file path ──────────────────────────────────────────────────────
def get_attendance_path():
    os.makedirs(ATTENDANCE_DIR, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(ATTENDANCE_DIR, f"attendance_{today}.csv")

def init_attendance_file(path):
    if not os.path.isfile(path):
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "RegNo", "Name", "Date", "Period",
                "MarkedTime", "Status"
            ])

# ── Check already marked for this period ─────────────────────────────────────
def already_marked(path, reg_no, period_name):
    if not os.path.isfile(path):
        return False
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["RegNo"] == str(reg_no) and row["Period"] == period_name:
                return True
    return False

# ── Mark attendance ───────────────────────────────────────────────────────────
def mark_attendance(path, reg_no, name, period_name, status):
    now  = datetime.now()
    date = now.strftime("%Y-%m-%d")
    t    = now.strftime("%H:%M:%S")
    with open(path, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([reg_no, name, date, period_name, t, status])
    print(f"  [{status}] {name} | {period_name} | {t}")

# ── Mark absent for students not detected in a period ────────────────────────
def mark_absents(path, student_map, period_name):
    present_reg_nos = set()
    if os.path.isfile(path):
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["Period"] == period_name:
                    present_reg_nos.add(row["RegNo"])

    now  = datetime.now()
    date = now.strftime("%Y-%m-%d")
    t    = now.strftime("%H:%M:%S")

    with open(path, "a", newline="") as f:
        writer = csv.writer(f)
        for sid, info in student_map.items():
            reg_no = info["reg_no"]
            name   = info["name"]
            if str(reg_no) not in present_reg_nos:
                writer.writerow([reg_no, name, date, period_name, t, "Absent"])
                print(f"  [ABSENT] {name} | {period_name}")

# ── Load name map ─────────────────────────────────────────────────────────────
def load_student_map():
    mapping = {}
    if not os.path.isfile(NAME_MAP):
        print(f"[WARNING] name_map.csv not found. Run 2_train_model.py first.")
        return mapping
    with open(NAME_MAP, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            mapping[int(row["ID"])] = {
                "reg_no": row["ID"],
                "name"  : row["Name"]
            }
    return mapping

# ── Show summary ──────────────────────────────────────────────────────────────
def show_summary(path):
    if not os.path.isfile(path):
        print("[INFO] No attendance recorded yet.")
        return
    print("\n" + "─" * 65)
    print("              TODAY'S ATTENDANCE SUMMARY")
    print("─" * 65)
    print(f"  {'Reg No':<12} {'Name':<22} {'Period':<12} {'Status'}")
    print("─" * 65)
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            print(
                f"  {row['RegNo']:<12} {row['Name']:<22}"
                f" {row['Period']:<12} {row['Status']}"
            )
    print("─" * 65 + "\n")

# ── Check requirements ────────────────────────────────────────────────────────
def check_requirements():
    ok = True
    for f, msg in [
        (CASCADE_PATH, "Run 1_dataset_collector.py first."),
        (TRAINER_FILE, "Run 2_train_model.py first."),
        (NAME_MAP,     "Run 2_train_model.py first."),
    ]:
        if not os.path.isfile(f):
            print(f"[ERROR] Not found: {f} → {msg}")
            ok = False
    return ok

# ── Main ──────────────────────────────────────────────────────────────────────
def start_recognition():
    if not check_requirements():
        return

    student_map     = load_student_map()
    attendance_path = get_attendance_path()
    init_attendance_file(attendance_path)

    face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
    recognizer   = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(TRAINER_FILE)

    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        print("[ERROR] Cannot open webcam.")
        return

    print("\n[INFO] Attendance System Started.")
    print("       Press 'q' to quit | Press 's' for summary\n")

    recently_marked  = {}
    FLASH_FRAMES     = 40
    frame_count      = 0
    last_period_name = None

    while True:
        ret, frame = cam.read()
        if not ret:
            break

        frame_count  += 1
        period        = get_current_period()

        # ── Auto mark absents when period ends ────────────────────────────────
        if last_period_name and (
            period is None or period["name"] != last_period_name
        ):
            print(f"\n[INFO] {last_period_name} ended. Marking absents...")
            mark_absents(attendance_path, student_map, last_period_name)

        last_period_name = period["name"] if period else None

        # ── No active period ──────────────────────────────────────────────────
        if period is None:
            now = datetime.now().time()
            if now < dtime(9, 15):
                msg = "Classes start at 9:15 AM"
            elif dtime(11, 5) <= now < dtime(11, 15):
                msg = "Break Time  (11:05 - 11:15)"
            elif dtime(13, 0) <= now < dtime(14, 0):
                msg = "Lunch Time  (1:00 - 2:00 PM)"
            elif now >= dtime(16, 30):
                msg = "Classes Over for Today"
            else:
                msg = "Between Periods"

            cv2.putText(frame, msg, (10, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
            cv2.imshow("Automated Attendance System", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
            continue

        # ── Active period — run face recognition ──────────────────────────────
        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.3, minNeighbors=5, minSize=MIN_FACE_SIZE
        )

        for (x, y, w, h) in faces:
            face_roi = gray[y:y+h, x:x+w]
            try:
                label, confidence = recognizer.predict(face_roi)
            except Exception:
                continue

            if label in student_map:
                reg_no = student_map[label]["reg_no"]
                name   = student_map[label]["name"]
            else:
                reg_no = str(label)
                name   = "Unknown"

            recognized = confidence < CONFIDENCE_THRESHOLD

            if recognized and name != "Unknown":
                if not already_marked(attendance_path, reg_no, period["name"]):
                    status = period["status"]   # ON_TIME or LATE
                    mark_attendance(
                        attendance_path, reg_no, name, period["name"], status
                    )
                    recently_marked[label] = frame_count

                just_marked = (
                    label in recently_marked
                    and frame_count - recently_marked[label] < FLASH_FRAMES
                )

                already = already_marked(attendance_path, reg_no, period["name"])
                if already:
                    # Check their status
                    with open(attendance_path, newline="") as f:
                        for row in csv.DictReader(f):
                            if row["RegNo"] == str(reg_no) and row["Period"] == period["name"]:
                                disp_status = row["Status"]
                                break
                else:
                    disp_status = period["status"]

                if disp_status == "ON_TIME":
                    color = (0, 255, 0)
                elif disp_status == "LATE":
                    color = (0, 165, 255)
                else:
                    color = (255, 200, 0)

                label_text  = f"{name} ({int(confidence)}%)"
                status_text = disp_status
            else:
                color       = (0, 0, 255)
                label_text  = "Unknown"
                status_text = f"Conf: {int(confidence)}%"

            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            cv2.rectangle(frame, (x, y-35), (x+w, y), color, -1)
            cv2.putText(frame, label_text, (x+5, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, status_text, (x, y+h+22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # ── HUD ───────────────────────────────────────────────────────────────
        now_str     = datetime.now().strftime("%d-%m-%Y  %H:%M:%S")
        period_info = (
            f"{period['name']}  |  "
            f"On-Time till {period['late'].strftime('%I:%M %p')}"
        )
        status_color = (0, 255, 0) if period["status"] == "ON_TIME" else (0, 165, 255)

        cv2.rectangle(frame, (0, 0), (frame.shape[1], 55), (30, 30, 30), -1)
        cv2.putText(frame, f"  {period_info}",
                    (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, status_color, 2)
        cv2.putText(frame, f"  {now_str}",
                    (5, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)
        cv2.putText(frame, "Q = Quit  |  S = Summary",
                    (10, frame.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)

        cv2.imshow("Automated Attendance System", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            print("\n[INFO] Quit by user.")
            break
        elif key == ord("s"):
            show_summary(attendance_path)

    cam.release()
    cv2.destroyAllWindows()
    show_summary(attendance_path)
    print("[NEXT] Run:  python 5_tutor_portal.py  to manage late comers\n")


if __name__ == "__main__":
    start_recognition()
