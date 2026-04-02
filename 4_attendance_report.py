"""
STEP 4 — Attendance Report & Visualization
==========================================
Reads all attendance CSV files, calculates statistics,
identifies defaulters, and generates charts.

HOW TO RUN:
    python 4_attendance_report.py

OUTPUT:
    - Terminal summary table
    - attendance_report.png (bar chart + pie chart)
    - defaulters_list.csv
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os
import csv
import glob
from datetime import datetime

# ── Config ─────────────────────────────────────────────────────────────────────
ATTENDANCE_DIR       = "attendance"
STUDENTS_FILE        = "students.csv"
DEFAULTER_THRESHOLD  = 75       # Below this % = defaulter
REPORT_IMAGE         = "attendance_report.png"
DEFAULTERS_FILE      = "defaulters_list.csv"

# ── Load all student names ────────────────────────────────────────────────────
def load_all_students():
    students = {}
    if not os.path.isfile(STUDENTS_FILE):
        return students
    with open(STUDENTS_FILE, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            students[row["RollNo"]] = row["Name"]
    return students

# ── Load and merge all attendance CSVs ───────────────────────────────────────
def load_all_attendance():
    pattern = os.path.join(ATTENDANCE_DIR, "attendance_*.csv")
    files   = glob.glob(pattern)

    if not files:
        print("[ERROR] No attendance files found in /attendance/ folder.")
        print("        Run 3_face_recognition.py to mark attendance first.")
        return None

    frames = []
    for f in sorted(files):
        try:
            df = pd.read_csv(f)
            frames.append(df)
        except Exception as e:
            print(f"[WARNING] Could not read {f}: {e}")

    if not frames:
        return None

    combined = pd.concat(frames, ignore_index=True)
    combined.drop_duplicates(subset=["RollNo", "Date"], inplace=True)
    return combined

# ── Calculate stats per student ───────────────────────────────────────────────
def calculate_stats(df, all_students):
    total_days  = df["Date"].nunique()
    present_per = df.groupby("RollNo")["Date"].nunique().reset_index()
    present_per.columns = ["RollNo", "DaysPresent"]
    present_per["Name"] = present_per["RollNo"].map(
        lambda r: all_students.get(str(r), "Unknown")
    )
    present_per["TotalDays"]   = total_days
    present_per["Percentage"]  = (
        present_per["DaysPresent"] / total_days * 100
    ).round(2)
    present_per["Status"] = present_per["Percentage"].apply(
        lambda p: "⚠️ Defaulter" if p < DEFAULTER_THRESHOLD else "✅ Regular"
    )
    present_per.sort_values("Percentage", ascending=False, inplace=True)
    return present_per, total_days

# ── Print terminal summary ────────────────────────────────────────────────────
def print_summary(stats, total_days):
    print("\n" + "═" * 65)
    print("           ATTENDANCE REPORT SUMMARY")
    print("═" * 65)
    print(f"  Total Working Days Tracked : {total_days}")
    print(f"  Defaulter Threshold        : < {DEFAULTER_THRESHOLD}%")
    print("═" * 65)
    print(f"  {'Roll No':<12} {'Name':<20} {'Present':>8} {'%':>8}  Status")
    print("─" * 65)
    for _, row in stats.iterrows():
        print(
            f"  {str(row['RollNo']):<12} {str(row['Name']):<20}"
            f" {int(row['DaysPresent']):>8} {row['Percentage']:>7.1f}%"
            f"  {row['Status']}"
        )
    print("─" * 65)

    defaulters = stats[stats["Percentage"] < DEFAULTER_THRESHOLD]
    regulars   = stats[stats["Percentage"] >= DEFAULTER_THRESHOLD]
    print(f"\n  ✅ Regular Students  : {len(regulars)}")
    print(f"  ⚠️  Defaulters        : {len(defaulters)}")
    if not defaulters.empty:
        print("\n  DEFAULTER LIST:")
        for _, row in defaulters.iterrows():
            print(f"    → {row['Name']} ({row['RollNo']})  —  {row['Percentage']}%")
    print("═" * 65 + "\n")

# ── Save defaulters CSV ───────────────────────────────────────────────────────
def save_defaulters(stats):
    defaulters = stats[stats["Percentage"] < DEFAULTER_THRESHOLD].copy()
    if defaulters.empty:
        print("[INFO] No defaulters found. Great!")
        return
    defaulters.to_csv(DEFAULTERS_FILE, index=False)
    print(f"[SAVED] Defaulters list → {DEFAULTERS_FILE}")

# ── Generate charts ───────────────────────────────────────────────────────────
def generate_charts(stats, total_days):
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    fig.patch.set_facecolor("#1a1a2e")

    names       = stats["Name"].tolist()
    percentages = stats["Percentage"].tolist()

    # ── Chart 1: Horizontal Bar Chart ────────────────────────────────────────
    ax1 = axes[0]
    ax1.set_facecolor("#16213e")

    colors = [
        "#e94560" if p < DEFAULTER_THRESHOLD else "#0f3460"
        for p in percentages
    ]
    highlight = [
        "#ff6b9d" if p < DEFAULTER_THRESHOLD else "#4fc3f7"
        for p in percentages
    ]

    bars = ax1.barh(names, percentages, color=highlight, edgecolor="none", height=0.6)

    # Threshold line
    ax1.axvline(
        x=DEFAULTER_THRESHOLD,
        color="#e94560",
        linestyle="--",
        linewidth=1.5,
        label=f"{DEFAULTER_THRESHOLD}% Threshold",
    )

    # Value labels
    for bar, pct in zip(bars, percentages):
        ax1.text(
            bar.get_width() + 0.5,
            bar.get_y() + bar.get_height() / 2,
            f"{pct:.1f}%",
            va="center",
            ha="left",
            color="white",
            fontsize=9,
            fontweight="bold",
        )

    ax1.set_xlim(0, 115)
    ax1.set_xlabel("Attendance %", color="white", fontsize=11)
    ax1.set_title(
        "Student Attendance Percentage",
        color="white",
        fontsize=13,
        fontweight="bold",
        pad=15,
    )
    ax1.tick_params(colors="white")
    ax1.spines[:].set_color("#444")
    ax1.legend(facecolor="#1a1a2e", labelcolor="white", fontsize=9)

    regular_patch   = mpatches.Patch(color="#4fc3f7", label="Regular (≥75%)")
    defaulter_patch = mpatches.Patch(color="#ff6b9d", label="Defaulter (<75%)")
    ax1.legend(
        handles=[regular_patch, defaulter_patch],
        facecolor="#1a1a2e",
        labelcolor="white",
        fontsize=9,
    )

    # ── Chart 2: Pie Chart ────────────────────────────────────────────────────
    ax2 = axes[1]
    ax2.set_facecolor("#16213e")

    n_regular   = sum(1 for p in percentages if p >= DEFAULTER_THRESHOLD)
    n_defaulter = sum(1 for p in percentages if p < DEFAULTER_THRESHOLD)
    total_s     = n_regular + n_defaulter

    if total_s > 0:
        pie_data   = [n_regular, n_defaulter]
        pie_labels = [
            f"Regular\n({n_regular} students)",
            f"Defaulters\n({n_defaulter} students)",
        ]
        pie_colors  = ["#4fc3f7", "#ff6b9d"]
        explode     = (0.05, 0.1)

        wedges, texts, autotexts = ax2.pie(
            pie_data,
            labels=pie_labels,
            autopct="%1.1f%%",
            colors=pie_colors,
            explode=explode,
            startangle=140,
            textprops={"color": "white", "fontsize": 11},
            wedgeprops={"edgecolor": "#1a1a2e", "linewidth": 2},
        )
        for at in autotexts:
            at.set_fontsize(12)
            at.set_fontweight("bold")

    ax2.set_title(
        "Regular vs Defaulters",
        color="white",
        fontsize=13,
        fontweight="bold",
        pad=15,
    )

    # ── Overall title ─────────────────────────────────────────────────────────
    generated_on = datetime.now().strftime("%d %b %Y, %H:%M")
    fig.suptitle(
        f"Automated Attendance Monitoring System\nGenerated: {generated_on}  |  Total Working Days: {total_days}",
        color="white",
        fontsize=14,
        fontweight="bold",
        y=1.02,
    )

    plt.tight_layout()
    plt.savefig(
        REPORT_IMAGE,
        dpi=150,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
    )
    plt.show()
    print(f"[SAVED] Chart saved → {REPORT_IMAGE}")

# ── Main ─────────────────────────────────────────────────────────────────────
def generate_report():
    print("\n[INFO] Loading attendance data...")
    df = load_all_attendance()
    if df is None:
        return

    all_students = load_all_students()
    stats, total_days = calculate_stats(df, all_students)

    print_summary(stats, total_days)
    save_defaulters(stats)
    generate_charts(stats, total_days)

    print("\n[DONE] Report generation complete!\n")


if __name__ == "__main__":
    generate_report()
