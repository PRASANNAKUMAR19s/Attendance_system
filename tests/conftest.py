"""Project-wide pytest fixtures for CI-friendly testing.

- Autouse fixture to mock external network calls (email and SMS) so tests run
  deterministically in CI without real credentials.
"""
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def mock_external_notifications():
    """Mock EmailService.send_email and SMSService.send_sms across tests."""
    from services.email_service import EmailService
    from services.sms_service import SMSService

    with patch.object(EmailService, "send_email", return_value=True):
        with patch.object(SMSService, "send_sms", return_value=True):
            yield
