from typing import Any

from app.providers.market.factory import MarketProviderFactory


class MarketDataService:
    def __init__(self, provider_name: str = "yahoo") -> None:
        self.provider = MarketProviderFactory.create(provider_name)

    async def get_latest_price(self, symbol: str) -> dict[str, Any]:
        clean_symbol = symbol.strip().upper()

        if not clean_symbol:
            raise ValueError("Symbol cannot be empty.")

        return await self.provider.get_latest_price(clean_symbol)