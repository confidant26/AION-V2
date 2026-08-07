from functools import lru_cache

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


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

    company_provider_chain: str = (
        "yahoo"
    )

    market_provider_chain: str = (
        "yahoo"
    )

    financial_provider_chain: str = (
        "yahoo"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )

    @staticmethod
    def _parse_provider_chain(
        value: str,
    ) -> list[str]:
        names: list[str] = []
        seen: set[str] = set()

        for raw_name in value.split(","):
            name = (
                raw_name
                .strip()
                .lower()
            )

            if not name:
                continue

            if name in seen:
                continue

            seen.add(
                name
            )

            names.append(
                name
            )

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


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()