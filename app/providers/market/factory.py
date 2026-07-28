from app.providers.market.base import MarketDataProvider
from app.providers.market.yahoo import YahooMarketProvider


class MarketProviderFactory:
    @staticmethod
    def create(provider_name: str) -> MarketDataProvider:
        clean_name = provider_name.strip().lower()

        if clean_name == "yahoo":
            return YahooMarketProvider()

        raise ValueError(
            f"Desteklenmeyen market veri sağlayıcısı: {provider_name}"
        )