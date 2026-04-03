"""
Firebase Service Layer
======================
Provides a unified interface for Firebase Firestore, Firebase Auth,
and Firebase Storage.  When Firebase is not configured (USE_FIREBASE=false
or credentials are missing) the system falls back to the existing CSV
storage so that all existing scripts continue to work unchanged.

Usage:
    from firebase_service import FirebaseService
    svc = FirebaseService()
    svc.add_student("622123207042", "PRASANNAKUMAR S", "AI&DS", 2024)
"""

from __future__ import annotations

import csv
import glob
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import config as _config

logger = logging.getLogger(__name__)

# Date strings accepted in file paths must be exactly YYYY-MM-DD (digits only).
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _safe_date(date: Optional[str]) -> Optional[str]:
    """Validate and normalise *date* to a YYYY-MM-DD string safe for file paths.

    Parses the string through ``datetime.strptime`` and re-formats it with
    ``strftime``, so the returned value is always produced by the standard
    library rather than coming directly from user input.  This removes the
    taint that static analysis tools track from external input.

    Raises ValueError for any string that does not match YYYY-MM-DD.
    """
    if date is None:
        return None
    if not _DATE_RE.match(date):
        raise ValueError(f"Invalid date format: {date!r}. Expected YYYY-MM-DD.")
    # Re-derive the string from a parsed datetime to produce a trusted value.
    parsed = datetime.strptime(date, "%Y-%m-%d")
    return parsed.strftime("%Y-%m-%d")

# ---------------------------------------------------------------------------
# Helper: initialise Firebase Admin SDK once
# ---------------------------------------------------------------------------
_firebase_app = None


def _init_firebase() -> bool:
    """Initialise the Firebase Admin SDK.  Returns True on success."""
    global _firebase_app
    if _firebase_app is not None:
        return True
    try:
        import firebase_admin  # type: ignore
        from firebase_admin import credentials  # type: ignore

        creds_path = _config.FIREBASE_CREDENTIALS_PATH
        if not os.path.isfile(creds_path):
            logger.warning(
                "Firebase credentials file '%s' not found.  "
                "Falling back to CSV storage.",
                creds_path,
            )
            return False

        cred = credentials.Certificate(creds_path)
        kwargs: Dict[str, Any] = {}
        if _config.FIREBASE_STORAGE_BUCKET:
            kwargs["storageBucket"] = _config.FIREBASE_STORAGE_BUCKET

        _firebase_app = firebase_admin.initialize_app(cred, kwargs)
        logger.info("Firebase Admin SDK initialised successfully.")
        return True
    except Exception as exc:  # pragma: no cover
        logger.error("Firebase initialisation failed: %s", exc)
        return False


# ---------------------------------------------------------------------------
# FirebaseService
# ---------------------------------------------------------------------------
class FirebaseService:
    """
    Unified service layer.  Uses Firebase when USE_FIREBASE=true and
    credentials are present; otherwise delegates to CSV helpers.
    """

    def __init__(self) -> None:
        self.use_firebase: bool = _config.USE_FIREBASE and _init_firebase()
        if self.use_firebase:
            from firebase_admin import firestore, storage  # type: ignore
            self._db = firestore.client()
            self._bucket = storage.bucket() if _config.FIREBASE_STORAGE_BUCKET else None
            logger.info("FirebaseService: Firestore backend active.")
        else:
            logger.info("FirebaseService: CSV backend active.")

    # ------------------------------------------------------------------ #
    #  Student Management                                                  #
    # ------------------------------------------------------------------ #

    def get_students(self) -> List[Dict[str, Any]]:
        """Return all students."""
        if self.use_firebase:
            return self._fs_get_students()
        return self._csv_get_students()

    def add_student(
        self,
        reg_no: str,
        name: str,
        department: str = "",
        year: int = 0,
        email: str = "",
        phone: str = "",
    ) -> Dict[str, Any]:
        """Add a new student.  Returns the created record."""
        record = {
            "reg_no": reg_no,
            "name": name,
            "department": department,
            "year": year,
            "email": email,
            "phone": phone,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        if self.use_firebase:
            self._db.collection("students").document(reg_no).set(record)
        else:
            self._csv_add_student(reg_no, name)
        return record

    def update_student(self, reg_no: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing student."""
        if self.use_firebase:
            self._db.collection("students").document(reg_no).update(data)
            doc = self._db.collection("students").document(reg_no).get()
            return doc.to_dict() or {}
        return self._csv_update_student(reg_no, data)

    def delete_student(self, reg_no: str) -> bool:
        """Delete a student record.  Returns True on success."""
        if self.use_firebase:
            self._db.collection("students").document(reg_no).delete()
            return True
        return self._csv_delete_student(reg_no)

    def get_student(self, reg_no: str) -> Optional[Dict[str, Any]]:
        """Return a single student or None."""
        if self.use_firebase:
            doc = self._db.collection("students").document(reg_no).get()
            return doc.to_dict() if doc.exists else None
        students = {s["reg_no"]: s for s in self._csv_get_students()}
        return students.get(reg_no)

    # ------------------------------------------------------------------ #
    #  Attendance                                                          #
    # ------------------------------------------------------------------ #

    def mark_attendance(
        self,
        reg_no: str,
        name: str,
        date: str,
        period: str,
        status: str,
        marked_time: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Mark attendance for a student."""
        if marked_time is None:
            marked_time = datetime.now().strftime("%H:%M:%S")
        record = {
            "reg_no": reg_no,
            "name": name,
            "date": date,
            "period": period,
            "status": status,
            "marked_time": marked_time,
        }
        if self.use_firebase:
            doc_id = f"{reg_no}_{date}_{period}"
            self._db.collection("attendance").document(doc_id).set(record)
        else:
            self._csv_mark_attendance(reg_no, name, date, period, marked_time, status)
        return record

    def get_attendance(
        self,
        date: Optional[str] = None,
        reg_no: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Return attendance records, optionally filtered by date/reg_no."""
        if self.use_firebase:
            return self._fs_get_attendance(date=date, reg_no=reg_no)
        return self._csv_get_attendance(date=date, reg_no=reg_no)

    def get_student_summary(self, reg_no: str) -> Dict[str, Any]:
        """Return attendance summary for a single student."""
        records = self.get_attendance(reg_no=reg_no)
        total = len(records)
        present = sum(
            1 for r in records if r.get("status", "").upper() in ("ON_TIME", "LATE", "PRESENT")
        )
        pct = round(present / total * 100, 2) if total else 0.0
        return {
            "reg_no": reg_no,
            "total_records": total,
            "present": present,
            "absent": total - present,
            "percentage": pct,
        }

    # ------------------------------------------------------------------ #
    #  Late Reasons                                                        #
    # ------------------------------------------------------------------ #

    def get_late_reasons(
        self,
        date: Optional[str] = None,
        reg_no: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Return late-reason records."""
        if self.use_firebase:
            return self._fs_get_late_reasons(date=date, reg_no=reg_no)
        return self._csv_get_late_reasons(date=date, reg_no=reg_no)

    def add_late_reason(
        self,
        reg_no: str,
        name: str,
        date: str,
        period: str,
        reason: str,
        updated_by: str = "Tutor",
    ) -> Dict[str, Any]:
        """Record a reason for a late arrival."""
        record = {
            "reg_no": reg_no,
            "name": name,
            "date": date,
            "period": period,
            "reason": reason,
            "updated_by": updated_by,
            "updated_at": datetime.now().strftime("%H:%M:%S"),
        }
        if self.use_firebase:
            doc_id = f"{reg_no}_{date}_{period}"
            self._db.collection("late_reasons").document(doc_id).set(record)
        else:
            self._csv_add_late_reason(record)
        return record

    # ------------------------------------------------------------------ #
    #  Firebase Storage helpers                                            #
    # ------------------------------------------------------------------ #

    def upload_face_image(
        self, reg_no: str, image_path: str
    ) -> Optional[str]:
        """
        Upload a face image to Firebase Storage.
        Returns the public URL or None on failure.
        """
        if not self.use_firebase or self._bucket is None:
            logger.warning("Firebase Storage is not configured.")
            return None
        try:
            blob_path = f"dataset/{reg_no}/{os.path.basename(image_path)}"
            blob = self._bucket.blob(blob_path)
            blob.upload_from_filename(image_path)
            blob.make_public()
            return blob.public_url
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to upload image: %s", exc)
            return None

    # ================================================================== #
    #  Firebase (Firestore) back-end helpers                               #
    # ================================================================== #

    def _fs_get_students(self) -> List[Dict[str, Any]]:
        docs = self._db.collection("students").stream()
        return [d.to_dict() for d in docs]

    def _fs_get_attendance(
        self,
        date: Optional[str] = None,
        reg_no: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        query = self._db.collection("attendance")
        if date:
            query = query.where("date", "==", date)
        if reg_no:
            query = query.where("reg_no", "==", reg_no)
        return [d.to_dict() for d in query.stream()]

    def _fs_get_late_reasons(
        self,
        date: Optional[str] = None,
        reg_no: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        query = self._db.collection("late_reasons")
        if date:
            query = query.where("date", "==", date)
        if reg_no:
            query = query.where("reg_no", "==", reg_no)
        return [d.to_dict() for d in query.stream()]

    # ================================================================== #
    #  CSV back-end helpers (preserve existing behaviour)                 #
    # ================================================================== #

    def _csv_get_students(self) -> List[Dict[str, Any]]:
        students: List[Dict[str, Any]] = []
        students_file = _config.STUDENTS_FILE
        if not os.path.isfile(students_file):
            return students
        with open(students_file, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                raw_year = row.get("year", "")
                try:
                    year = int(raw_year) if raw_year else 0
                except (ValueError, TypeError):
                    year = 0
                students.append(
                    {
                        "reg_no": row.get("RegNo", row.get("reg_no", "")),
                        "name": row.get("Name", row.get("name", "")),
                        "department": row.get("department", ""),
                        "year": year,
                        "email": row.get("email", ""),
                        "phone": row.get("phone", ""),
                    }
                )
        return students

    def _csv_add_student(self, reg_no: str, name: str) -> None:
        students_file = _config.STUDENTS_FILE
        file_exists = os.path.isfile(students_file)
        with open(students_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["RegNo", "Name"])
            writer.writerow([reg_no, name])

    def _csv_update_student(
        self, reg_no: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        updated: Dict[str, Any] = {}
        rows: List[Dict[str, str]] = []
        students_file = _config.STUDENTS_FILE
        if os.path.isfile(students_file):
            with open(students_file, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames or ["RegNo", "Name"]
                for row in reader:
                    key = row.get("RegNo", row.get("reg_no", ""))
                    if key == reg_no:
                        row.update(
                            {k: str(v) for k, v in data.items()}
                        )
                        updated = dict(row)
                    rows.append(row)
            with open(students_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
        return updated

    def _csv_delete_student(self, reg_no: str) -> bool:
        students_file = _config.STUDENTS_FILE
        if not os.path.isfile(students_file):
            return False
        rows: List[Dict[str, str]] = []
        found = False
        with open(students_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or ["RegNo", "Name"]
            for row in reader:
                key = row.get("RegNo", row.get("reg_no", ""))
                if key == reg_no:
                    found = True
                else:
                    rows.append(row)
        if found:
            with open(students_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
        return found

    def _csv_mark_attendance(
        self,
        reg_no: str,
        name: str,
        date: str,
        period: str,
        marked_time: str,
        status: str,
    ) -> None:
        safe = _safe_date(date)  # Validates date is YYYY-MM-DD before path use
        attendance_dir = os.path.realpath(_config.ATTENDANCE_DIR)
        os.makedirs(attendance_dir, exist_ok=True)
        path = os.path.realpath(os.path.join(attendance_dir, f"attendance_{safe}.csv"))
        if not path.startswith(attendance_dir + os.sep) and path != attendance_dir:
            raise ValueError("Unsafe attendance file path detected.")
        file_exists = os.path.isfile(path)
        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(
                    ["RegNo", "Name", "Date", "Period", "MarkedTime", "Status"]
                )
            writer.writerow([reg_no, name, date, period, marked_time, status])

    def _csv_get_attendance(
        self,
        date: Optional[str] = None,
        reg_no: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        safe = _safe_date(date)  # Validates date is YYYY-MM-DD before path use
        attendance_dir = os.path.realpath(_config.ATTENDANCE_DIR)
        pattern = (
            os.path.join(attendance_dir, f"attendance_{safe}.csv")
            if safe
            else os.path.join(attendance_dir, "attendance_*.csv")
        )
        records: List[Dict[str, Any]] = []
        for path in sorted(glob.glob(pattern)):
            real_path = os.path.realpath(path)
            if not real_path.startswith(attendance_dir + os.sep):
                continue  # Skip any path that escapes the attendance directory
            if not os.path.isfile(real_path):
                continue
            with open(real_path, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    r = {
                        "reg_no": row.get("RegNo", row.get("reg_no", "")),
                        "name": row.get("Name", row.get("name", "")),
                        "date": row.get("Date", row.get("date", "")),
                        "period": row.get("Period", row.get("period", "")),
                        "marked_time": row.get(
                            "MarkedTime", row.get("marked_time", "")
                        ),
                        "status": row.get("Status", row.get("status", "")),
                    }
                    if reg_no and r["reg_no"] != reg_no:
                        continue
                    records.append(r)
        return records

    def _csv_get_late_reasons(
        self,
        date: Optional[str] = None,
        reg_no: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        late_reasons_file = _config.LATE_REASONS_FILE
        if not os.path.isfile(late_reasons_file):
            return records
        with open(late_reasons_file, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                r = {
                    "reg_no": row.get("RegNo", row.get("reg_no", "")),
                    "name": row.get("Name", row.get("name", "")),
                    "date": row.get("Date", row.get("date", "")),
                    "period": row.get("Period", row.get("period", "")),
                    "reason": row.get("Reason", row.get("reason", "")),
                    "updated_by": row.get("UpdatedBy", row.get("updated_by", "")),
                    "updated_at": row.get("UpdatedAt", row.get("updated_at", "")),
                }
                if date and r["date"] != date:
                    continue
                if reg_no and r["reg_no"] != reg_no:
                    continue
                records.append(r)
        return records

    def _csv_add_late_reason(self, record: Dict[str, Any]) -> None:
        late_reasons_file = _config.LATE_REASONS_FILE
        file_exists = os.path.isfile(late_reasons_file)
        with open(late_reasons_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(
                    [
                        "RegNo",
                        "Name",
                        "Date",
                        "Period",
                        "Reason",
                        "UpdatedBy",
                        "UpdatedAt",
                    ]
                )
            writer.writerow(
                [
                    record["reg_no"],
                    record["name"],
                    record["date"],
                    record["period"],
                    record["reason"],
                    record["updated_by"],
                    record["updated_at"],
                ]
            )
