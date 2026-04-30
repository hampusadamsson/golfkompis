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


settings = Settings()
