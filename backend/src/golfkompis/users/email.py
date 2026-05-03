"""Email sender for verification and password-reset flows.

Uses fastapi-mail with Jinja2 HTML templates. Templates are in
``users/templates/email/`` and can be edited without touching Python code.
Credentials and server config come from ``golfkompis.config.settings``
(``MAIL_*`` env vars / .env).
"""

import pathlib

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import NameEmail, SecretStr

from golfkompis.config import settings

TEMPLATE_DIR = pathlib.Path(__file__).parent / "templates" / "email"

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
    TEMPLATE_FOLDER=TEMPLATE_DIR,
)

_fm = FastMail(_mail_config)


async def send_verification_email(email: str, token: str) -> None:
    url = f"{settings.auth_frontend_verify_url}?token={token}"
    message = MessageSchema(
        subject="Bekräfta din e-postadress - Golfkompis",
        recipients=[NameEmail(email, email)],
        template_body={"url": url},
        subtype=MessageType.html,
    )
    await _fm.send_message(message, template_name="verification.html")


async def send_reset_email(email: str, token: str) -> None:
    url = f"{settings.auth_frontend_reset_url}?token={token}"
    message = MessageSchema(
        subject="Återställ ditt lösenord - Golfkompis",
        recipients=[NameEmail(email, email)],
        template_body={"url": url},
        subtype=MessageType.html,
    )
    await _fm.send_message(message, template_name="reset.html")
