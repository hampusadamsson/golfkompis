"""Stub email sender for verification and password-reset flows.

Logs token URLs via structlog instead of sending real email.
Replace with a fastapi-mail integration once SMTP is configured.
Tokens are visible in logs so development flows work without an SMTP server.
"""

import structlog

from golfkompis.config import settings

log = structlog.get_logger()  # pyright: ignore[reportAny]


async def send_verification_email(email: str, token: str) -> None:
    url = f"{settings.auth_frontend_verify_url}?token={token}"
    log.info("verification_email_stub", to=email, url=url)  # pyright: ignore[reportAny]


async def send_reset_email(email: str, token: str) -> None:
    url = f"{settings.auth_frontend_reset_url}?token={token}"
    log.info("reset_email_stub", to=email, url=url)  # pyright: ignore[reportAny]
