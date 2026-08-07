from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str
    app_version: str
    app_env: str
    debug: bool

    database_url: str
    redis_url: str

    provider_timeout_seconds: float = Field(
        default=15.0,
        gt=0,
    )

    provider_max_attempts: int = Field(
        default=3,
        ge=1,
        le=10,
    )

    provider_retry_delay_seconds: float = Field(
        default=0.5,
        ge=0,
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()