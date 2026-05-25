"""Application configuration via environment variables.

All settings derive from env. Defaults keep local development frictionless.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ANNOUNCEMENTS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_key: str = Field(
        default="dev-key-change-me",
        description="Required in the x-api-key header on every mutating request.",
    )
    database_url: str = Field(
        default="postgresql+psycopg://announcements:announcements@localhost:5432/announcements",
        description="SQLAlchemy URL for the Postgres database.",
    )
    webhook_subscribers: list[str] = Field(
        default_factory=list,
        description="List of URLs to POST webhook events to.",
    )
    log_level: str = Field(default="INFO")

    @property
    def use_real_database(self) -> bool:
        """True for any SQLAlchemy-backed URL. ``memory://`` means in-memory repo only."""
        return not self.database_url.startswith("memory://")
