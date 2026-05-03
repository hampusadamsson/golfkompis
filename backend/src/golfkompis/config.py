"""Centralized configuration loaded from environment / .env."""

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
    auth_frontend_verify_url: str = "http://localhost:5173/verify"
    auth_frontend_reset_url: str = "http://localhost:5173/reset-password"


settings = Settings()
