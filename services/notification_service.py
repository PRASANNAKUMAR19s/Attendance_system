"""
services/notification_service.py — Combined Notification Service
----------------------------------------------------------------
Centralises email + SMS notifications for attendance events.
"""

from __future__ import annotations

import logging
import threading
from typing import Optional

import config as _config

from services.email_service import EmailService
from services.sms_service import SMSService
from models.student import Student

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self) -> None:
        self.email = EmailService()
        self.sms = SMSService()

    def _build_message(
        self, student_name: str, reg_no: str, date: str, period: str, status: str
    ) -> str:
        return (
            f"Attendance: {student_name} ({reg_no}) is {status} on {date} for {period}."
        )

    def send_attendance_notifications(
        self,
        reg_no: str,
        name: str,
        status: str,
        date: Optional[str] = None,
        period: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> int:
        """Send attendance notifications (email + SMS) to student + tutor + HOD.

        Returns number of successful sends (email or sms counted per recipient).
        """
        date = date or __import__("datetime").datetime.now().strftime("%Y-%m-%d")
        period = period or ""

        # Best-effort lookup for parent contact info
        student = Student.get_by_reg_no(reg_no)
        email_to = student.email if student and student.email else None
        phone_to = student.phone if student and student.phone else None

        msg_text = self._build_message(name, reg_no, date, period, status)

        sent = 0

        # Send email to parent/student
        if email_to:
            try:
                if self.email.send_attendance_alert(
                    to_email=email_to,
                    student_name=name,
                    reg_no=reg_no,
                    date=date,
                    period=period or "",
                    status=status,
                    reason=reason,
                ):
                    sent += 1
            except Exception as exc:
                logger.error("Email notification failed for %s: %s", email_to, exc)
        else:
            logger.debug("No student email on record for %s", reg_no)

        # Send SMS to parent/student
        if phone_to:
            try:
                if self.sms.send_sms(phone_to, msg_text):
                    sent += 1
            except Exception as exc:
                logger.error("SMS notification failed for %s: %s", phone_to, exc)
        else:
            logger.debug("No student phone on record for %s", reg_no)

        # Always notify tutor and HOD via email (not via SMS)
        try:
            if self.email.send_attendance_alert(
                to_email=_config.TUTOR_EMAIL,
                student_name=name,
                reg_no=reg_no,
                date=date,
                period=period or "",
                status=status,
                reason=reason,
            ):
                sent += 1
        except Exception:
            logger.exception("Failed to notify tutor for %s", reg_no)

        try:
            if self.email.send_attendance_alert(
                to_email=_config.HOD_EMAIL,
                student_name=name,
                reg_no=reg_no,
                date=date,
                period=period or "",
                status=status,
                reason=reason,
            ):
                sent += 1
        except Exception:
            logger.exception("Failed to notify HOD for %s", reg_no)

        return sent

    def send_attendance_notifications_async(self, *args, **kwargs) -> None:
        thread = threading.Thread(
            target=self.send_attendance_notifications,
            args=args,
            kwargs=kwargs,
            daemon=True,
        )
        thread.start()
