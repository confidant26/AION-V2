from app.core.config import settings
from app.providers.market.base import (
    MarketDataProvider,
)
from app.providers.market.fallback import (
    FallbackMarketProvider,
)
from app.providers.market.yahoo import (
    YahooMarketProvider,
)


def create_market_provider(
    provider_name: str,
) -> MarketDataProvider:
    clean_name = (
        provider_name
        .strip()
        .lower()
    )

    if clean_name == "yahoo":
        return YahooMarketProvider()

    raise ValueError(
        f"Unsupported market data provider: "
        f"{provider_name}"
    )


class MarketProviderFactory:
    @staticmethod
    def create(
        provider_name: str | None = None,
    ) -> MarketDataProvider:
        if provider_name is not None:
            return create_market_provider(
                provider_name
            )

        provider_names = (
            settings.get_market_provider_names()
        )

        providers = [
            create_market_provider(
                name
            )
            for name in provider_names
        ]

        if len(providers) == 1:
            return providers[0]

        return FallbackMarketProvider(
            providers
        )