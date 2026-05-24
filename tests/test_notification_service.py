"""tests/test_notification_service.py

Unit tests for NotificationService with mocked EmailService and SMSService.
"""
from __future__ import annotations

from unittest.mock import patch

from services.notification_service import NotificationService


def test_send_attendance_notifications_monkeypatched():
    svc = NotificationService()

    # Patch EmailService.send_attendance_alert and SMSService.send_sms to avoid network
    with patch.object(svc.email, "send_attendance_alert", return_value=True) as mock_email:
        with patch.object(svc.sms, "send_sms", return_value=True) as mock_sms:
            sent = svc.send_attendance_notifications(
                reg_no="622123207001",
                name="Test Student",
                status="Absent",
                date="2026-05-24",
                period="P1",
            )

    # Expect 3 sends: student email, student SMS, tutor email, HOD email -> 4
    assert sent >= 3
    # Ensure the mocked methods were called at least once
    assert mock_email.called
    assert mock_sms.called
