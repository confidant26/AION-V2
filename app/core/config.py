from functools import lru_cache

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    app_name: str = "AION V2 API"
    app_version: str = "0.1.0"
    app_env: str = "development"
    debug: bool = False

    database_url: str = (
        "postgresql+psycopg://aion:aion_password@localhost:5432/aion_db"
    )
    redis_url: str = "redis://localhost:6379/0"

    log_level: str = "INFO"
    request_id_header: str = "X-Request-ID"

    rate_limit_enabled: bool = False
    rate_limit_requests_per_minute: int = Field(
        default=120,
        ge=1,
        le=100_000,
    )
    rate_limit_exempt_paths: str = (
        "/,/health,/health/database,/health/readiness,"
        "/docs,/redoc,/openapi.json"
    )

    market_price_max_age_minutes: int = Field(
        default=1440,
        ge=1,
    )
    financial_period_max_age_days: int = Field(
        default=150,
        ge=1,
    )

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

    company_provider_chain: str = "yahoo"
    market_provider_chain: str = "yahoo"
    financial_provider_chain: str = "sec,yahoo"

    sec_user_agent: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    @staticmethod
    def _parse_provider_chain(
        value: str,
    ) -> list[str]:
        names: list[str] = []
        seen: set[str] = set()

        for raw_name in value.split(","):
            name = raw_name.strip().lower()

            if not name or name in seen:
                continue

            seen.add(name)
            names.append(name)

        if not names:
            raise ValueError(
                "Provider chain cannot be empty."
            )

        return names

    def get_company_provider_names(
        self,
    ) -> list[str]:
        return self._parse_provider_chain(
            self.company_provider_chain
        )

    def get_market_provider_names(
        self,
    ) -> list[str]:
        return self._parse_provider_chain(
            self.market_provider_chain
        )

    def get_financial_provider_names(
        self,
    ) -> list[str]:
        return self._parse_provider_chain(
            self.financial_provider_chain
        )

    def get_rate_limit_exempt_paths(
        self,
    ) -> set[str]:
        return {
            value.strip()
            for value in self.rate_limit_exempt_paths.split(",")
            if value.strip()
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
