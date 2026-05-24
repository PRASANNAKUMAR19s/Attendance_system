"""
9_behavior_analysis.py — Simple attendance behavior analysis utilities
-------------------------------------------------------------------
Generates summary statistics from `attendance/` CSV files and writes
defaulters and summary reports into the `reports/` folder.
"""

from __future__ import annotations

import csv
import logging
import os
from collections import defaultdict
from datetime import datetime

import config as _config

logger = logging.getLogger(__name__)


def collect_attendance_records(attendance_dir: str):
    records = []
    if not os.path.isdir(attendance_dir):
        return records
    for fname in sorted(os.listdir(attendance_dir)):
        if not fname.lower().endswith(".csv"):
            continue
        path = os.path.join(attendance_dir, fname)
        try:
            with open(path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    records.append(r)
        except Exception:
            logger.exception("Failed reading attendance file %s", path)
    return records


def analyze(records):
    per_student = defaultdict(
        lambda: {"present": 0, "late": 0, "absent": 0, "total": 0, "name": ""}
    )
    for r in records:
        reg = r.get("reg_no") or r.get("RegNo") or r.get("Reg_No")
        name = r.get("name") or r.get("Name") or ""
        status = (r.get("status") or "").upper()
        if not reg:
            continue
        per_student[reg]["name"] = name
        per_student[reg]["total"] += 1
        if status in ("ON_TIME", "PRESENT"):
            per_student[reg]["present"] += 1
        elif status == "LATE":
            per_student[reg]["late"] += 1
        elif status == "ABSENT":
            per_student[reg]["absent"] += 1

    # compute percentages
    results = []
    for reg, stats in per_student.items():
        total = stats["total"] or 1
        attended = stats["present"] + stats["late"]
        pct = round(attended / total * 100, 1)
        results.append(
            {
                "reg_no": reg,
                "name": stats["name"],
                "present": stats["present"],
                "late": stats["late"],
                "absent": stats["absent"],
                "total": total,
                "attendance_pct": pct,
            }
        )
    return results


def save_defaulters(results, threshold, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["reg_no", "name", "attendance_pct"])
        writer.writeheader()
        for r in sorted(results, key=lambda x: x["attendance_pct"]):
            if r["attendance_pct"] < threshold:
                writer.writerow(
                    {
                        "reg_no": r["reg_no"],
                        "name": r["name"],
                        "attendance_pct": r["attendance_pct"],
                    }
                )


def main():
    records = collect_attendance_records(_config.ATTENDANCE_DIR)
    results = analyze(records)
    report_time = datetime.now().strftime("%Y-%m-%d_%H%M")
    out_dir = _config.REPORTS_DIR or "reports"
    os.makedirs(out_dir, exist_ok=True)
    defaulters_path = os.path.join(out_dir, f"defaulters_{report_time}.csv")
    save_defaulters(results, _config.DEFAULTER_THRESHOLD, defaulters_path)
    print(
        f"Wrote defaulters to {defaulters_path} (threshold { _config.DEFAULTER_THRESHOLD }%)"
    )


if __name__ == "__main__":
    main()
