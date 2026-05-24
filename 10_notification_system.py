"""
10_notification_system.py — CLI runner to send daily attendance summaries
--------------------------------------------------------------------
Uses existing EmailService / FaceRecognitionService to compute today's
attendance and email a daily summary to Tutor and HOD.
"""

from __future__ import annotations

import logging
from datetime import datetime

from services.email_service import EmailService
from services.face_recognition_service import FaceRecognitionService
import config as _config

logger = logging.getLogger(__name__)


def send_daily_summary():
    svc = FaceRecognitionService()
    stats = svc.get_today_attendance()
    # prepare details list
    present = stats.get("present", 0)
    late = stats.get("late", 0)
    absent = stats.get("absent", 0)
    total = stats.get("total", 0)

    # fetch a small sample of present students
    present_students = svc.get_present_students_today()
    details = [
        {"reg_no": k, "name": v, "status": "Present"}
        for k, v in list(present_students.items())[:20]
    ]

    email = EmailService()
    date = datetime.now().strftime("%Y-%m-%d")

    # Send to Tutor
    sent1 = email.send_daily_summary(
        to_email=_config.TUTOR_EMAIL,
        date=date,
        present_count=present,
        late_count=late,
        absent_count=absent,
        total_students=total,
        details=details,
    )

    # Send to HOD
    sent2 = email.send_daily_summary(
        to_email=_config.HOD_EMAIL,
        date=date,
        present_count=present,
        late_count=late,
        absent_count=absent,
        total_students=total,
        details=details,
    )

    logger.info("Daily summary sent: tutor=%s hod=%s", sent1, sent2)
    return sent1 + sent2


if __name__ == "__main__":
    cnt = send_daily_summary()
    print(f"Sent {cnt} daily summary messages")
