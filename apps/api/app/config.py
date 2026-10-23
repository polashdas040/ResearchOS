from functools import lru_cache
from typing import cast

from pydantic import AnyHttpUrl, Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="RESEARCHOS_",
        extra="ignore",
    )

    environment: str = "local"
    database_url: PostgresDsn = Field(
        default=cast(
            PostgresDsn,
            "postgresql+asyncpg://researchos:researchos@localhost:5432/researchos",
        )
    )
    redis_url: str = "redis://localhost:6379/0"
    chroma_url: AnyHttpUrl = Field(default=cast(AnyHttpUrl, "http://localhost:8001"))
    object_storage_endpoint: AnyHttpUrl = Field(
        default=cast(AnyHttpUrl, "http://localhost:9000")
    )
    object_storage_bucket: str = "researchos"
    object_storage_access_key: str = "minioadmin"
    object_storage_secret_key: str = "minioadmin"
    auth_secret_key: str = "development-only-change-me"
    access_token_minutes: int = 15
    refresh_token_days: int = 30
    openai_api_key: str | None = None
    openai_chat_model: str = "gpt-4o-mini"
    openai_compatible_api_key: str | None = None
    openai_compatible_base_url: AnyHttpUrl | None = None
    openai_compatible_chat_model: str = "deepseek-chat"
    gemini_api_key: str | None = None
    gemini_chat_model: str = "gemini-1.5-flash"
    model_provider_timeout_seconds: float = 180.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
