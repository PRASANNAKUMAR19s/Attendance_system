"""
services/sms_service.py — SMS Notification Service
-------------------------------------------------
Provides a thin wrapper for sending SMS alerts. Uses Twilio if available
and configured; otherwise logs and returns False so the application remains
operational without SMS credentials.
"""

from __future__ import annotations

import logging

import config as _config

logger = logging.getLogger(__name__)


class SMSService:
    def __init__(self) -> None:
        self.enabled = _config.SMS_ENABLED
        self.from_number = _config.TWILIO_FROM_NUMBER
        # Lazy import of twilio client to keep dependency optional
        try:
            from twilio.rest import Client

            self._twilio_client = Client(
                _config.TWILIO_ACCOUNT_SID, _config.TWILIO_AUTH_TOKEN
            )
        except Exception:
            self._twilio_client = None

    def is_configured(self) -> bool:
        return self.enabled and self._twilio_client is not None

    def send_sms(self, to_number: str, message: str) -> bool:
        """Send an SMS message. Returns True on success."""
        if not to_number:
            logger.debug("No destination number provided, skipping SMS")
            return False

        if not self.is_configured():
            logger.warning(
                "SMS service not configured. Would send to %s: %s", to_number, message
            )
            return False

        try:
            msg = self._twilio_client.messages.create(
                from_=self.from_number, to=to_number, body=message
            )
            logger.info(
                "Sent SMS to %s: sid=%s", to_number, getattr(msg, "sid", "<unknown>")
            )
            return True
        except Exception as exc:
            logger.error("Failed to send SMS to %s: %s", to_number, exc)
            return False
