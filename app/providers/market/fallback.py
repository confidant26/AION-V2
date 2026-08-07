from typing import Any

from app.providers.fallback import (
    execute_with_fallback,
)
from app.providers.market.base import (
    MarketDataProvider,
)


class FallbackMarketProvider(
    MarketDataProvider
):
    def __init__(
        self,
        providers: list[
            MarketDataProvider
        ],
    ) -> None:
        if not providers:
            raise ValueError(
                "At least one market provider "
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
            "Fallback Market Provider "
            f"({', '.join(names)})"
        )

    async def get_latest_price(
        self,
        symbol: str,
    ) -> dict[str, Any]:
        return await execute_with_fallback(
            providers=self.providers,
            operation=lambda provider: (
                provider.get_latest_price(
                    symbol
                )
            ),
            operation_name=(
                f"latest market price for "
                f"{symbol.strip().upper()}"
            ),
        )