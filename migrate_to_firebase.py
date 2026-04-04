"""
migrate_to_firebase.py
======================
One-time migration script: copies all existing CSV data to Firebase Firestore.

What it migrates:
  1. students.csv          → Firestore "students" collection
  2. attendance/*.csv      → Firestore "attendance" collection
  3. late_reasons.csv      → Firestore "late_reasons" collection

REQUIREMENTS:
  - USE_FIREBASE=true in .env (or set environment variable)
  - FIREBASE_CREDENTIALS_PATH pointing to your serviceAccountKey.json

RUN:
    python migrate_to_firebase.py [--dry-run]

FLAGS:
    --dry-run     Print what would be migrated without writing to Firebase.
    --force       Skip confirmation prompt.
"""

from __future__ import annotations

import argparse
import csv
import glob
import logging
import os
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s — %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Migrate CSV data to Firebase Firestore")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print records without writing to Firebase.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt.",
    )
    return parser.parse_args()


def load_students(students_file: str) -> list[dict]:
    records: list[dict] = []
    if not os.path.isfile(students_file):
        logger.warning("Students file not found: %s", students_file)
        return records
    with open(students_file, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            records.append(
                {
                    "reg_no":     row.get("RegNo", row.get("reg_no", "")).strip(),
                    "name":       row.get("Name",  row.get("name",  "")).strip(),
                    "department": row.get("department", "").strip(),
                    "year":       row.get("year", "").strip(),
                    "email":      row.get("email", "").strip(),
                    "phone":      row.get("phone", "").strip(),
                }
            )
    return records


def load_attendance(attendance_dir: str) -> list[dict]:
    records: list[dict] = []
    pattern = os.path.join(attendance_dir, "attendance_*.csv")
    for path in sorted(glob.glob(pattern)):
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                records.append(
                    {
                        "reg_no":      row.get("RegNo",       row.get("reg_no", "")).strip(),
                        "name":        row.get("Name",        row.get("name",   "")).strip(),
                        "date":        row.get("Date",        row.get("date",   "")).strip(),
                        "period":      row.get("Period",      row.get("period", "")).strip(),
                        "marked_time": row.get("MarkedTime",  row.get("marked_time", "")).strip(),
                        "status":      row.get("Status",      row.get("status", "")).strip(),
                    }
                )
    return records


def load_late_reasons(reasons_file: str) -> list[dict]:
    records: list[dict] = []
    if not os.path.isfile(reasons_file):
        logger.warning("Late reasons file not found: %s", reasons_file)
        return records
    with open(reasons_file, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            records.append(
                {
                    "reg_no":     row.get("RegNo",     row.get("reg_no",     "")).strip(),
                    "name":       row.get("Name",      row.get("name",       "")).strip(),
                    "date":       row.get("Date",      row.get("date",       "")).strip(),
                    "period":     row.get("Period",    row.get("period",     "")).strip(),
                    "reason":     row.get("Reason",    row.get("reason",     "")).strip(),
                    "updated_by": row.get("UpdatedBy", row.get("updated_by", "")).strip(),
                    "updated_at": row.get("UpdatedAt", row.get("updated_at", "")).strip(),
                }
            )
    return records


def migrate_to_firestore(
    db,
    students: list[dict],
    attendance: list[dict],
    late_reasons: list[dict],
    dry_run: bool,
) -> None:
    """Write all records to Firestore in batches."""
    from google.cloud.firestore_v1 import WriteBatch  # type: ignore

    BATCH_SIZE = 400  # Firestore max is 500 ops per batch

    def flush_batch(batch, count: int, collection: str) -> tuple:
        if not dry_run:
            batch.commit()
            logger.info("  Committed %d records to '%s'", count, collection)
        return db.batch(), 0

    # ── Students ──
    logger.info("Migrating %d students …", len(students))
    batch = db.batch()
    batch_count = 0
    for s in students:
        if not s["reg_no"]:
            continue
        ref = db.collection("students").document(s["reg_no"])
        if dry_run:
            print(f"  [DRY-RUN] students/{s['reg_no']} → {s}")
        else:
            batch.set(ref, s)
        batch_count += 1
        if batch_count >= BATCH_SIZE:
            batch, batch_count = flush_batch(batch, batch_count, "students")
    if batch_count:
        flush_batch(batch, batch_count, "students")

    # ── Attendance ──
    logger.info("Migrating %d attendance records …", len(attendance))
    batch = db.batch()
    batch_count = 0
    for r in attendance:
        if not r["reg_no"] or not r["date"] or not r["period"]:
            continue
        doc_id = f"{r['reg_no']}_{r['date']}_{r['period'].replace(' ', '_')}"
        ref = db.collection("attendance").document(doc_id)
        if dry_run:
            print(f"  [DRY-RUN] attendance/{doc_id} → {r}")
        else:
            batch.set(ref, r)
        batch_count += 1
        if batch_count >= BATCH_SIZE:
            batch, batch_count = flush_batch(batch, batch_count, "attendance")
    if batch_count:
        flush_batch(batch, batch_count, "attendance")

    # ── Late reasons ──
    logger.info("Migrating %d late-reason records …", len(late_reasons))
    batch = db.batch()
    batch_count = 0
    for r in late_reasons:
        if not r["reg_no"] or not r["date"] or not r["period"]:
            continue
        doc_id = f"{r['reg_no']}_{r['date']}_{r['period'].replace(' ', '_')}"
        ref = db.collection("late_reasons").document(doc_id)
        if dry_run:
            print(f"  [DRY-RUN] late_reasons/{doc_id} → {r}")
        else:
            batch.set(ref, r)
        batch_count += 1
        if batch_count >= BATCH_SIZE:
            batch, batch_count = flush_batch(batch, batch_count, "late_reasons")
    if batch_count:
        flush_batch(batch, batch_count, "late_reasons")


def main() -> None:
    args = parse_args()

    # Load config (also loads .env)
    from config import (
        ATTENDANCE_DIR,
        FIREBASE_CREDENTIALS_PATH,
        FIREBASE_STORAGE_BUCKET,
        LATE_REASONS_FILE,
        STUDENTS_FILE,
    )

    # ── Confirm ──
    if not args.dry_run and not args.force:
        print("\n⚠️  This will write all CSV data to Firebase Firestore.")
        print(f"   Credentials: {FIREBASE_CREDENTIALS_PATH}")
        confirm = input("Type 'yes' to continue: ").strip().lower()
        if confirm != "yes":
            print("Aborted.")
            sys.exit(0)

    # ── Load data ──
    students     = load_students(STUDENTS_FILE)
    attendance   = load_attendance(ATTENDANCE_DIR)
    late_reasons = load_late_reasons(LATE_REASONS_FILE)

    logger.info(
        "Loaded: %d students, %d attendance records, %d late-reason records",
        len(students), len(attendance), len(late_reasons),
    )

    if args.dry_run:
        logger.info("DRY RUN — no data will be written to Firebase.")
        # Initialise a dummy db just to show the records
        db = None

        class _FakeDB:
            def batch(self): ...
            def collection(self, _): ...

        # Print records
        for s in students:
            print(f"[DRY-RUN] students/{s.get('reg_no')} → {s}")
        for r in attendance:
            doc_id = f"{r['reg_no']}_{r['date']}_{r['period']}"
            print(f"[DRY-RUN] attendance/{doc_id} → {r}")
        for r in late_reasons:
            doc_id = f"{r['reg_no']}_{r['date']}_{r['period']}"
            print(f"[DRY-RUN] late_reasons/{doc_id} → {r}")
        logger.info("Dry run complete. No data written.")
        return

    # ── Initialise Firebase ──
    try:
        import firebase_admin  # type: ignore
        from firebase_admin import credentials, firestore  # type: ignore

        if not os.path.isfile(FIREBASE_CREDENTIALS_PATH):
            logger.error(
                "Firebase credentials file not found: %s", FIREBASE_CREDENTIALS_PATH
            )
            sys.exit(1)

        cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
        kwargs = {}
        if FIREBASE_STORAGE_BUCKET:
            kwargs["storageBucket"] = FIREBASE_STORAGE_BUCKET
        firebase_admin.initialize_app(cred, kwargs)
        db = firestore.client()
        logger.info("Firebase connected.")
    except ImportError:
        logger.error("firebase-admin is not installed. Run: pip install firebase-admin")
        sys.exit(1)

    # ── Run migration ──
    migrate_to_firestore(db, students, attendance, late_reasons, dry_run=False)
    logger.info("✅ Migration complete!")


if __name__ == "__main__":
    main()
