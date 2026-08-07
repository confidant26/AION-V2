from typing import Any

from app.providers.company.base import (
    CompanyDataProvider,
)
from app.providers.fallback import (
    execute_with_fallback,
)


class FallbackCompanyProvider(
    CompanyDataProvider
):
    def __init__(
        self,
        providers: list[
            CompanyDataProvider
        ],
    ) -> None:
        if not providers:
            raise ValueError(
                "At least one company provider "
                "is required."
            )

        self.providers = providers

    @property
    def provider_name(self) -> str:
        names = [
            provider.provider_name
            for provider in self.providers
        ]

        return (
            "Fallback Company Provider "
            f"({', '.join(names)})"
        )

    async def get_company_profile(
        self,
        symbol: str,
    ) -> dict[str, Any]:
        return await execute_with_fallback(
            providers=self.providers,
            operation=lambda provider: (
                provider.get_company_profile(
                    symbol
                )
            ),
            operation_name=(
                f"company profile for "
                f"{symbol.strip().upper()}"
            ),
        )