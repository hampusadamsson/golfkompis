"""Stub email sender for verification and password-reset flows.

Logs token URLs via structlog instead of sending real email.
Replace with a fastapi-mail integration once SMTP is configured.
Tokens are visible in logs so development flows work without an SMTP server.
"""

import structlog
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import NameEmail, SecretStr

from golfkompis.config import settings

log = structlog.get_logger()  # pyright: ignore[reportAny]


_mail_config = ConnectionConfig(
    MAIL_USERNAME=settings.mail_username,
    MAIL_PASSWORD=SecretStr(settings.mail_password),
    MAIL_FROM=settings.mail_from,
    MAIL_PORT=settings.mail_port,
    MAIL_SERVER=settings.mail_server,
    MAIL_STARTTLS=settings.mail_starttls,
    MAIL_SSL_TLS=settings.mail_ssl_tls,
    USE_CREDENTIALS=bool(settings.mail_username),
    VALIDATE_CERTS=False,
)

_fm = FastMail(_mail_config)


async def send_verification_email(email: str, token: str) -> None:
    url = f"{settings.auth_frontend_verify_url}?token={token}"
    message = MessageSchema(
        subject="Verify your email",
        recipients=[NameEmail(email, email)],
        body=f"<p>Click to verify your account: <a href='{url}'>{url}</a></p>",
        subtype=MessageType.html,
    )
    await _fm.send_message(message)


async def send_reset_email(email: str, token: str) -> None:
    url = f"{settings.auth_frontend_reset_url}?token={token}"
    message = MessageSchema(
        subject="Reset your password",
        recipients=[NameEmail(email, email)],
        body=f"<p>Click to reset your password: <a href='{url}'>{url}</a></p>",
        subtype=MessageType.html,
    )
    await _fm.send_message(message)
