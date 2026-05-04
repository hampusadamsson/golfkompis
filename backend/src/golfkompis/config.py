"""Centralized configuration loaded from environment / .env."""

from datetime import time

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mingolf_username: str = ""
    mingolf_password: str = ""
    default_range_weeks: int = 10
    mock: bool = False
    session_ttl_minutes: int = 30
    session_cache_max: int = 256

    # EMAIL

    mail_username: str = ""
    mail_password: str = ""
    mail_from: str = "noreply@example.com"
    mail_port: int = 1025
    mail_server: str = "localhost"
    mail_starttls: bool = False
    mail_ssl_tls: bool = False

    # ---------------------------------------------------------------------------
    # User management (fastapi-users)
    # ---------------------------------------------------------------------------
    # auth_database_url: path is relative to the process cwd.
    # Set AUTH_DATABASE_URL in production to an absolute path or a proper DSN.
    auth_secret: str = "changeme-replace-in-production"
    auth_database_url: str = "sqlite+aiosqlite:///./users.db"
    auth_cookie_lifetime_seconds: int = 3600
    auth_cookie_secure: bool = False
    auth_frontend_base_url: str = "http://localhost:5173"

    @property
    def auth_frontend_verify_url(self) -> str:
        return f"{self.auth_frontend_base_url.rstrip('/')}/verify"

    @property
    def auth_frontend_reset_url(self) -> str:
        return f"{self.auth_frontend_base_url.rstrip('/')}/reset-password"

    # ---------------------------------------------------------------------------
    # Tee-time search queue
    # ---------------------------------------------------------------------------
    queue_enabled: bool = True
    queue_poll_interval_minutes: int = 60
    queue_active_window_start: time = time(8, 0)
    queue_active_window_stop: time = time(23, 0)
    queue_email_max_slots: int = 20


settings = Settings()
