"""Shared pytest fixtures for the test suite."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture(autouse=True)
def mock_mail_send() -> pytest.FixtureRequest:
    """Prevent fastapi-mail from attempting real SMTP connections in tests."""
    with patch(
        "golfkompis.users.email._fm.send_message",
        new_callable=AsyncMock,
    ):
        yield
