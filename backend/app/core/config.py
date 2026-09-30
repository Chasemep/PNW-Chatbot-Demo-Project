"""Application settings loaded from environment variables and .env files."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the backend services."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Purdue Policy Chatbot"
    environment: str = "development"
    log_level: str = "INFO"

    database_url: str = Field(
        default="postgresql+psycopg://purdue:purdue@localhost:5432/purdue_policy_chatbot"
    )
    gemini_api_key: str | None = None
    gemini_model: str | None = None
    embedding_api_key: str | None = None
    embedding_model: str | None = None
    embedding_dimension: int = Field(default=768, gt=0)

    backend_host: str = "0.0.0.0"
    backend_port: int = Field(default=8000, ge=1, le=65535)


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings instance."""

    return Settings()