"""
STEP 5 — Tutor Portal
======================
Tutor can:
  1. View all late comers for today
  2. Add reason for a late comer → updates status to Present
  3. View full attendance summary

HOW TO RUN:
    python 5_tutor_portal.py
"""

import csv
import os
from datetime import datetime
from config import ATTENDANCE_DIR, LATE_REASONS_FILE

# ── Paths ─────────────────────────────────────────────────────────────────────
def get_today_path():
    today = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(ATTENDANCE_DIR, f"attendance_{today}.csv")

def get_date_path(date_str):
    return os.path.join(ATTENDANCE_DIR, f"attendance_{date_str}.csv")

# ── Load attendance records ───────────────────────────────────────────────────
def load_records(path):
    if not os.path.isfile(path):
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f))

# ── Save all records back ─────────────────────────────────────────────────────
def save_records(path, records):
    if not records:
        return
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)

# ── Save reason to late_reasons.csv ──────────────────────────────────────────
def save_reason(reg_no, name, period, reason, date):
    file_exists = os.path.isfile(LATE_REASONS_FILE)
    with open(LATE_REASONS_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["RegNo", "Name", "Date", "Period", "Reason", "UpdatedBy", "UpdatedAt"])
        writer.writerow([
            reg_no, name, date, period, reason,
            "Tutor", datetime.now().strftime("%H:%M:%S")
        ])

# ── View late comers ──────────────────────────────────────────────────────────
def view_late_comers(records):
    late = [r for r in records if r["Status"] == "LATE"]
    if not late:
        print("\n  ✅ No late comers today!\n")
        return late
    print("\n" + "─" * 65)
    print("                    LATE COMERS LIST")
    print("─" * 65)
    print(f"  {'#':<4} {'Reg No':<15} {'Name':<22} {'Period':<12} {'Time'}")
    print("─" * 65)
    for i, row in enumerate(late, 1):
        print(f"  {i:<4} {row['RegNo']:<15} {row['Name']:<22} {row['Period']:<12} {row['MarkedTime']}")
    print("─" * 65)
    return late

# ── View absent students ──────────────────────────────────────────────────────
def view_absents(records):
    absent = [r for r in records if r["Status"] == "Absent"]
    if not absent:
        print("\n  ✅ No absent students today!\n")
        return
    print("\n" + "─" * 65)
    print("                    ABSENT STUDENTS")
    print("─" * 65)
    print(f"  {'#':<4} {'Reg No':<15} {'Name':<22} {'Period':<12}")
    print("─" * 65)
    for i, row in enumerate(absent, 1):
        print(f"  {i:<4} {row['RegNo']:<15} {row['Name']:<22} {row['Period']:<12}")
    print("─" * 65 + "\n")

# ── View full summary ─────────────────────────────────────────────────────────
def view_full_summary(records):
    print("\n" + "─" * 70)
    print("                    FULL ATTENDANCE SUMMARY")
    print("─" * 70)
    print(f"  {'Reg No':<15} {'Name':<22} {'Period':<12} {'Status':<12} {'Time'}")
    print("─" * 70)
    for row in records:
        status = row["Status"]
        print(
            f"  {row['RegNo']:<15} {row['Name']:<22}"
            f" {row['Period']:<12} {status:<12} {row['MarkedTime']}"
        )
    print("─" * 70 + "\n")

# ── Add reason for late comer ─────────────────────────────────────────────────
def add_reason(records, path, date):
    late = view_late_comers(records)
    if not late:
        return records

    print("\nEnter the NUMBER of the student to update (or 0 to cancel): ", end="")
    try:
        choice = int(input().strip())
    except ValueError:
        print("[ERROR] Invalid input.")
        return records

    if choice == 0:
        return records

    if choice < 1 or choice > len(late):
        print("[ERROR] Invalid number.")
        return records

    selected = late[choice - 1]
    print(f"\nStudent   : {selected['Name']}")
    print(f"Reg No    : {selected['RegNo']}")
    print(f"Period    : {selected['Period']}")
    print(f"Late Time : {selected['MarkedTime']}")
    print("\nEnter reason (tutor description): ", end="")
    reason = input().strip()

    if not reason:
        print("[ERROR] Reason cannot be empty.")
        return records

    # Update status to Present with reason
    for row in records:
        if (row["RegNo"]  == selected["RegNo"] and
            row["Period"] == selected["Period"] and
            row["Status"] == "LATE"):
            row["Status"] = "Present(Reason)"
            break

    save_records(path, records)
    save_reason(
        selected["RegNo"], selected["Name"],
        selected["Period"], reason, date
    )

    print(f"\n  ✅ Updated! {selected['Name']} → Present (Reason recorded)")
    print(f"     Reason: {reason}\n")
    return records

# ── Main Menu ─────────────────────────────────────────────────────────────────
def tutor_portal():
    print("\n" + "═" * 50)
    print("         TUTOR PORTAL — ATTENDANCE MANAGER")
    print("═" * 50)

    # Ask for date
    print("\nEnter date to manage (YYYY-MM-DD) or press Enter for today: ", end="")
    date_input = input().strip()

    if not date_input:
        date_str = datetime.now().strftime("%Y-%m-%d")
    else:
        date_str = date_input

    path = get_date_path(date_str)

    if not os.path.isfile(path):
        print(f"\n[ERROR] No attendance file found for {date_str}")
        return

    print(f"\n[INFO] Loaded: {path}")

    while True:
        records = load_records(path)

        on_time = sum(1 for r in records if r["Status"] == "ON_TIME")
        late    = sum(1 for r in records if r["Status"] == "LATE")
        absent  = sum(1 for r in records if r["Status"] == "Absent")
        reason  = sum(1 for r in records if r["Status"] == "Present(Reason)")

        print(f"\n  Date     : {date_str}")
        print(f"  On Time  : {on_time}  |  Late: {late}  |  Absent: {absent}  |  Excused: {reason}")
        print("\n  1. View Late Comers")
        print("  2. Add Reason for Late Comer → Mark Present")
        print("  3. View Absent Students")
        print("  4. View Full Summary")
        print("  5. Exit")
        print("\n  Choose option (1-5): ", end="")

        try:
            choice = int(input().strip())
        except ValueError:
            print("[ERROR] Enter a number 1-5.")
            continue

        if choice == 1:
            view_late_comers(records)
        elif choice == 2:
            records = add_reason(records, path, date_str)
        elif choice == 3:
            view_absents(records)
        elif choice == 4:
            view_full_summary(records)
        elif choice == 5:
            print("\n[EXIT] Tutor Portal closed.\n")
            break
        else:
            print("[ERROR] Enter 1-5 only.")

if __name__ == "__main__":
    tutor_portal()
